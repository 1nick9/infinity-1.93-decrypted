#!/usr/bin/env python3
"""Decrypt an Infinity/Modbo SPI flash image (as read by the EE boot loader) into the RAM image at 0x100000.
Stage 1 (CPLD-patched kernel): flash[0:0x3FC] -> 0x100004, rolling XOR key k=0x2D; k=((k^0xA7)+addr)
Stage 2: chunks at 0x3FC+0x400n: BE16 rawsum, BE16 plainsum, 1020 bytes; key LCG k=(k*32749+32649)%32497 seed 0x1337, byte^=(k>>5)
"""
import sys, struct
def stage1(flash):
    ram = bytearray(0x400); raw = b'\xff'*4 + flash[:0x3fc]; k = 0x2d; a = 0x100000
    for i, v in enumerate(raw):
        ram[i] = (v ^ k) & 0xff; k = (k ^ 0xa7) + a; a += 1
    return ram

def find_seed(ram):
    import struct
    for o in range(0x20, 0x300, 4):
        w = struct.unpack('<I', ram[o:o+4])[0]
        if w >> 16 == 0x2413 and struct.unpack('<I', ram[o+4:o+8])[0] >> 16 == 0x2414: return w & 0xffff
    return 0x1337

def decrypt(flash, verbose=True, seed=None):
    ram = bytearray(0x400)
    # stage 1: 4 response bytes for READ cmd+addr (0xFF), then flash[0:0x3FC]
    raw = b'\xff'*4 + flash[:0x3fc]
    k = 0x2d; a = 0x100000
    for i, v in enumerate(raw):
        ram[i] = (v ^ k) & 0xff; k = ((k ^ 0xa7) + a) & 0xffffffffffffffff; a += 1
    # stage 2
    if seed is None: seed = find_seed(ram)
    if verbose: print(f'stage-2 LCG seed {seed:#x}')
    k = seed; off = 0x3fc; dst = 0x3fc; n = 0; bad = 0
    while off + 4 <= len(flash):
        s1, s2 = struct.unpack('>HH', flash[off:off+4])
        if s1 == 0 and s2 == 0: break
        data = flash[off+4:off+0x400]
        if len(data) < 0x3fc: print('truncated chunk at', hex(off)); break
        out = bytearray(); t5 = t6 = 0
        for v in data:
            t5 += v
            k = (k * 32749) & 0xffffffff
            k = (k + 32649) & 0xffffffff
            k = k % 32497
            p = (v ^ (k >> 5)) & 0xff
            out.append(p); t6 += p
        ok = (t5 & 0xffff) == s1 and (t6 & 0xffff) == s2
        bad += not ok
        if verbose and (not ok or n < 2): print(f'chunk {n:2d} @flash {off:#06x} -> ram {0x100000+dst:#x} rawsum {"ok" if (t5&0xffff)==s1 else "BAD"} plainsum {"ok" if (t6&0xffff)==s2 else "BAD"}')
        ram[dst:dst+0x3fc] = out
        dst += 0x3fc; off += 0x400; n += 1
    if verbose: print(f'{n} chunks, {bad} checksum failures, ram image {len(ram):#x} bytes, ended at flash {off:#x}')
    return bytes(ram)
if __name__ == '__main__':
    flash = open(sys.argv[1], 'rb').read()
    ram = decrypt(flash)
    open(sys.argv[2] if len(sys.argv) > 2 else 'ram_0x100000.bin', 'wb').write(ram)
