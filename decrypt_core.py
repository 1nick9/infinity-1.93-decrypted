#!/usr/bin/env python3
"""
decrypt_core.py -- Infinity/Modbo 1.93 flash -> decrypted core (core_codedecrypted.bin)

Runs the full decode chain:
    SPI flash bytes
      -> stage-1 rolling XOR  (first 0x3FC bytes)
      -> stage-2 LCG chunks   (checksummed 1 KB units, seed auto-detected)
      -> LZMA core            (header at 0x100AF8 -> image at 0x110000, ~50 KB)
      -> break-crypt removal  (the 24 per-function 'break'-encrypted routines)

Input may be a raw SPI flash dump (.bin) or a DSLogic .dsl capture of the BIOS bus.
Output is core_codedecrypted.bin plus (optionally) the stage-2 RAM image.

Usage:
    python3 decrypt_core.py flash.bin
    python3 decrypt_core.py flash.bin -o core_codedecrypted.bin
    python3 decrypt_core.py capture.dsl --t 1.28 1.80
"""
import sys, os, struct, lzma, argparse
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))
from infinity_decrypt import decrypt            # stage-1 XOR + stage-2 LCG
from breakcrypt import decrypt_blocks           # in-core break-crypt remover

RES_SRC, RES_DST, RES_LEN = 0x110650 - 0x110000, 0x50000, 48348


def lzma_core(ram):
    off = 0xaf8
    usz = struct.unpack('<I', ram[off + 4:off + 8])[0]
    lc, lp, pb = ram[off + 9], ram[off + 10], ram[off + 11]
    d = lzma.LZMADecompressor(lzma.FORMAT_ALONE)
    out = d.decompress(bytes([(pb * 5 + lp) * 9 + lc]) + struct.pack('<IQ', 1 << 20, usz) + ram[off + 12:])
    if len(out) != usz:
        raise ValueError('core size mismatch: %d != %d' % (len(out), usz))
    return out


def remove_breakcrypt(core):
    dec = bytearray(core)
    for s, e, base in ((0, RES_SRC, 0x110000), (RES_SRC, RES_SRC + RES_LEN, RES_DST)):
        part, _ = decrypt_blocks(bytes(dec[s:e]), base, verbose=False, mul=0x41a7)
        dec[s:e] = part
    return bytes(dec)


def flash_from_dsl(path, t0, t1):
    import importlib.util, tempfile
    spec = importlib.util.spec_from_file_location('s2f', os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'lib', 'sniff_to_flash.py'))
    s2f = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(s2f)
    out = os.path.join(tempfile.gettempdir(), '_flash_from_sniff.bin')
    old = sys.argv
    sys.argv = ['sniff_to_flash.py', path, out, str(t0), str(t1)]
    try:
        s2f.main()
    finally:
        sys.argv = old
    return open(out, 'rb').read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('input', help='SPI flash dump (.bin) or DSLogic capture (.dsl)')
    ap.add_argument('-o', '--out', default='core_codedecrypted.bin')
    ap.add_argument('--t', nargs=2, type=float, default=[1.28, 1.80],
                    help='for a .dsl: boot-transfer time window (seconds)')
    ap.add_argument('--ram', help='also write the stage-2 RAM image here')
    a = ap.parse_args()

    if a.input.lower().endswith('.dsl'):
        print('[*] decoding bus sniff %s (window %.3f-%.3f s)' % (a.input, a.t[0], a.t[1]))
        flash = flash_from_dsl(a.input, a.t[0], a.t[1])
    else:
        flash = open(a.input, 'rb').read()
        print('[*] flash dump: %d bytes' % len(flash))

    ram = decrypt(flash, verbose=True)          # prints chunk/checksum progress
    if a.ram:
        open(a.ram, 'wb').write(ram)
        print('[*] wrote stage-2 RAM image -> %s (%d bytes)' % (a.ram, len(ram)))
    core = lzma_core(ram)
    print('[*] LZMA core: %d bytes @0x110000' % len(core))
    core = remove_breakcrypt(core)
    open(a.out, 'wb').write(core)
    print('[*] break-crypt removed; wrote decrypted core -> %s (%d bytes)' % (a.out, len(core)))


if __name__ == '__main__':
    main()
