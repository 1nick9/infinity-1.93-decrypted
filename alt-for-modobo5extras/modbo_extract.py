#!/usr/bin/env python3
"""
modbo_extract.py -- extraction toolkit for Infinity 1.93 / Modbo 5.0 SPI flash images.

Maps a 512 KB (Modbo) or 64 KB (Infinity) flash dump and extracts every component:

  * the decrypted EE core            (core_codedecrypted.bin)
  * the Infinity configuration menu  (infinity_config_menu.elf)   -- the settings screen
  * the Modbo "USBADV" boot menu     (modbo_boot_menu.elf)        -- Modbo 5.0 only
  * the boot logo bitmap             (boot_logo.bin)
  * the configuration record         (config_record.bin)

Decode chains used:
  core    : flash -> stage-1 XOR -> stage-2 LCG (checksummed) -> LZMA (0x100000) -> break-crypt removal
  config  : LZMA stream inside the core at core+0x5120 -> flat image, wrapped as ELF (entry 0x100830)
  bootmenu: container at flash 0x20000, UCL NRV2E -> flat image, wrapped as ELF (entry 0x100108)

Usage:
  python3 modbo_extract.py MODBO50.BIN                 # map + extract everything to ./out
  python3 modbo_extract.py infv193.bin -o ud           # Infinity 1.93 flash (no boot menu)
  python3 modbo_extract.py capture.dsl --t 1.28 1.80   # from a DSLogic BIOS-bus sniff
  python3 modbo_extract.py MODBO50.BIN --map           # just print the image map
"""
import sys, os, struct, lzma, argparse
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))
from infinity_decrypt import decrypt
from breakcrypt import decrypt_blocks
from nrv import nrv

RES_SRC, RES_DST, RES_LEN = 0x110650 - 0x110000, 0x50000, 48348


# ---------------------------------------------------------------- core
def ram_image(flash):
    return decrypt(flash, verbose=True)


def lzma_at(buf, off):
    usz = struct.unpack('<I', buf[off + 4:off + 8])[0]
    lc, lp, pb = buf[off + 9], buf[off + 10], buf[off + 11]
    d = lzma.LZMADecompressor(lzma.FORMAT_ALONE)
    out = d.decompress(bytes([(pb * 5 + lp) * 9 + lc]) + struct.pack('<IQ', 1 << 20, usz) + buf[off + 12:])
    if len(out) != usz:
        raise ValueError('LZMA size mismatch at %#x: %d != %d' % (off, len(out), usz))
    return out


def decrypt_core(ram):
    core = bytearray(lzma_at(ram, 0xaf8))                 # core @0x110000
    for s, e, base in ((0, RES_SRC, 0x110000), (RES_SRC, RES_SRC + RES_LEN, RES_DST)):
        part, _ = decrypt_blocks(bytes(core[s:e]), base, verbose=False, mul=0x41a7)
        core[s:e] = part
    return bytes(core)


def make_elf(image, vaddr, entry, memsz):
    memsz = max(memsz, len(image))
    eh = struct.pack('<4s5B7x2H5I6H', b'\x7fELF', 1, 1, 1, 0, 0, 2, 8, 1, entry, 52, 0,
                     0x20924001, 52, 32, 1, 0, 0, 0)
    ph = struct.pack('<8I', 1, 0x1000, vaddr, vaddr, len(image), memsz, 7, 0x1000)
    return eh + ph + b'\0' * (0x1000 - 84) + image


def find_config_menu(core):
    for i in range(0, len(core) - 16, 4):
        if core[i + 9:i + 12] == b'\x03\x00\x02' and core[i + 12] == 0:
            usz = struct.unpack('<I', core[i + 4:i + 8])[0]
            if not 0 < usz < 0x100000:
                continue
            try:
                m = lzma_at(core, i)
            except Exception:
                continue
            return i, m
    return None, None


# ---------------------------------------------------------------- image map
def image_map(flash):
    rows = []
    off = 0x3fc
    while off + 4 <= len(flash) and flash[off:off + 4] != b'\0\0\0\0':
        off += 0x400
    core_end = off + 4
    rows.append((0, core_end, 'Infinity core chain (stage1+2 encrypted: core + config menu + add-on)'))
    if len(flash) > 0xf000 and any(b != 0xff for b in flash[0xe000:0xf000]):
        rows.append((0xe000, 0xf000, 'boot logo bitmap'))
    if any(b != 0xff for b in flash[0xfc00:0xfc10]):
        rows.append((0xfc00, 0xfc10, 'configuration record'))
    seed = flash[0xf500:0xf510]
    if seed != b'\xff' * 16:
        copies = [i for i in range(0, len(flash) - 16, 0x100) if flash[i:i + 16] == seed]
        rows.append((0xf500, 0xf5e8, 'stage-1 seed loader (copies at %s)' % ', '.join('0x%x' % c for c in copies)))
    if len(flash) >= 0x21000 and flash[0x20000:0x20004] != b'\xff\xff\xff\xff':
        hdr = struct.unpack('<4I', flash[0x20000:0x20010])
        be = min(len(flash), 0x60000)
        while be > 0x20000 and flash[be - 1] == 0xff:
            be -= 1
        rows.append((0x20000, be, 'Modbo "USBADV" boot menu (NRV2E; entry %#x load %#x)' % (hdr[0], hdr[3])))
    return rows


def extract_boot_logo(flash):
    seg = flash[0xe000:0xf000]
    return seg if any(b != 0xff for b in seg) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('input', help='SPI flash dump (.bin) or DSLogic capture (.dsl)')
    ap.add_argument('-o', '--out', default='out', help='output directory')
    ap.add_argument('--t', nargs=2, type=float, default=[1.28, 1.80], help='for a .dsl: boot-transfer window (s)')
    ap.add_argument('--map', action='store_true', help='print the image map and exit')
    a = ap.parse_args()

    if a.input.lower().endswith('.dsl'):
        import importlib.util, tempfile
        spec = importlib.util.spec_from_file_location('s2f', os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'lib', 'sniff_to_flash.py'))
        s2f = importlib.util.module_from_spec(spec); spec.loader.exec_module(s2f)
        tmp = os.path.join(tempfile.gettempdir(), '_flash_from_sniff.bin')
        old = sys.argv; sys.argv = ['sniff_to_flash.py', a.input, tmp, str(a.t[0]), str(a.t[1])]
        try: s2f.main()
        finally: sys.argv = old
        flash = open(tmp, 'rb').read()
    else:
        flash = open(a.input, 'rb').read()

    print('\n=== image map (%d bytes) ===' % len(flash))
    for s, e, what in image_map(flash):
        print('  0x%05x-0x%05x  %s' % (s, e, what))
    print('  (everything else is erased flash, 0xFF)')
    if a.map:
        return

    os.makedirs(a.out, exist_ok=True)
    print('\n=== extracting to %s/ ===' % a.out)

    ram = ram_image(flash)
    core = decrypt_core(ram)
    open(f'{a.out}/core_codedecrypted.bin', 'wb').write(core)
    print('  core_codedecrypted.bin      %d bytes' % len(core))

    off, menu = find_config_menu(core)
    if menu:
        open(f'{a.out}/infinity_config_menu.elf', 'wb').write(make_elf(menu, 0x100000, 0x100830, 0x10000))
        open(f'{a.out}/infinity_config_menu_0x100000.bin', 'wb').write(menu)
        print('  infinity_config_menu.elf    %d bytes  (core+%#x, entry 0x100830)' % (len(menu), off))

    if len(flash) >= 0x21000 and flash[0x20000:0x20004] != b'\xff\xff\xff\xff':
        hdr = struct.unpack('<4I', flash[0x20000:0x20010])   # [entry, load_size, unk, load_addr]
        bm, _ = nrv(flash, '2e', 0x20010)
        bm = bytearray(bm) + b'\0' * max(0, hdr[1] - len(bm))  # pad to the stored LOAD size
        open(f'{a.out}/modbo_boot_menu_0x100000.bin', 'wb').write(bm)
        if bm[:4] == b'\x7fELF':
            # the decompressed image is already a full ELF; its section table sits past the
            # stored LOAD size, so blank the section-table fields and ship it as-is.
            struct.pack_into('<I', bm, 32, 0)        # e_shoff
            struct.pack_into('<HHH', bm, 46, 0, 0, 0)  # e_shentsize, e_shnum, e_shstrndx
            out_elf = bytes(bm)
        else:
            out_elf = make_elf(bytes(bm), hdr[3], hdr[0], 0x10000)
        open(f'{a.out}/modbo_boot_menu.elf', 'wb').write(out_elf)
        print('  modbo_boot_menu.elf         %d bytes  (flash 0x20000, entry %#x)' % (len(out_elf), hdr[0]))

    logo = extract_boot_logo(flash)
    if logo:
        open(f'{a.out}/boot_logo.bin', 'wb').write(logo)
        print('  boot_logo.bin               %d bytes  (flash 0xE000)' % len(logo))

    if any(b != 0xff for b in flash[0xfc00:0xfc10]):
        open(f'{a.out}/config_record.bin', 'wb').write(flash[0xfc00:0xfc10])
        print('  config_record.bin           16 bytes  (flash 0xFC00)')

    print('\ndone.')


if __name__ == '__main__':
    main()
