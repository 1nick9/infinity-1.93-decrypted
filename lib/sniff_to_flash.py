#!/usr/bin/env python3
"""Rebuild the SPI flash bytes the PS2 EE read from an Infinity/Modbo chip, from a DSLogic .dsl sniff
of the BIOS data bus (D0-D7 = probe0-7, /OE-ish read strobe = probe8).
Chip I/O (EE side): for cmd16 -> sb 'M'(0x4D), sb cmd>>8, sb cmd&0xFF to 0x1FC00000, each preceded by
lbu 0x1F40200F (the isolated '01' reads); then lq 0x1FC00070 (16B), lhu 0x1FC006FA (2B 'ff5c'),
ld 0x1FC006F8 (8B 'e0 00 5c XX e8 00 5c ff') -> XX = SPI MISO byte.
Commands: A000 CS low, A001 CS high, A1xx xfer byte xx, A2xx last byte, A4xx/AExx chip control.
Usage: python3 sniff_to_flash.py capture.dsl out_flash.bin [t_start t_end]
"""
import sys, zipfile, numpy as np
MINRUN = 3
def main():
    z = zipfile.ZipFile(sys.argv[1]); outp = sys.argv[2]
    t0, t1 = (float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 else (0.0, 1e9)
    hdr = dict(l.split(' = ', 1) for l in z.read('header').decode().splitlines() if ' = ' in l)
    total, nblk = int(hdr['total samples']), int(hdr['total blocks'])
    rate = float(hdr['samplerate'].split()[0]) * 1e6
    s0, s1 = int(t0*rate), int(min(t1*rate, total))
    ts_all, val_all, wr_all, base, carry = [], [], [], 0, None
    BL = None
    for b in range(nblk):
        ch = [np.unpackbits(np.frombuffer(z.read(f'L-{c}/{b}'), np.uint8), bitorder='little') for c in range(9)]
        n = min(len(ch[0]), total-base); ch = [c[:n] for c in ch]
        if base + n < s0 or base > s1: base += n; carry = ch[8][-8:]; continue
        clk = np.concatenate((carry if carry is not None else ch[8][:8], ch[8]))
        for _ in range(3):
            e = np.nonzero(np.diff(clk))[0]+1; st = np.concatenate(([0], e)); en = np.concatenate((e, [len(clk)]))
            sh = np.nonzero((en-st) < MINRUN)[0]; sh = sh[sh > 0]
            if not len(sh): break
            for i in sh: clk[st[i]:en[i]] = clk[st[i]-1]
        prev = clk[7]; clk = clk[8:]
        idx = np.nonzero(np.diff(np.concatenate(([prev], clk)).astype(np.int8)) == 1)[0]
        data = np.zeros(n, np.uint8)
        for c in range(8): data |= ch[c].astype(np.uint8) << c
        ts_all.append(idx+base); val_all.append(data[np.maximum(idx-1, 0)])
        wr_all.append(data[np.maximum(idx-8, 0)])          # value held on bus just before the read = last write
        carry = clk[-8:]; base += n
    T = np.concatenate(ts_all); V = np.concatenate(val_all); W = np.concatenate(wr_all)
    gp = np.diff(np.concatenate(([0], T)))*8e9/rate; gn = np.diff(np.concatenate((T, [T[-1]+10**6])))*8e9/rate
    sync = np.nonzero((gp > 300) & (gn > 300) & (V == 1))[0]
    flash = {}; cur = None; i = 0
    while i+3 < len(sync):
        if sync[i+3]-sync[i] != 3: i += 1; continue
        M, hi, lo = int(W[sync[i+1]]), int(W[sync[i+2]]), int(W[sync[i+3]]); j = sync[i+3]+1+16+2; i += 4
        if M != 0x4d or j+8 > len(V) or V[j] != 0xe0 or V[j+4] != 0xe8: continue
        miso = int(V[j+3]); cmd = (hi << 8) | lo
        if hi == 0xa0: cur = {'out': [], 'in': []} if lo == 0 else None; continue
        if cur is None or hi not in (0xa1, 0xa2): continue
        cur['out'].append(lo); cur['in'].append(miso)
        o = cur['out']
        if len(o) > 4 and o[0] == 0x03:
            addr = (o[1] << 16) | (o[2] << 8) | o[3]; flash[addr + len(o) - 5] = miso
    if not flash: sys.exit('no SPI READ traffic found')
    top = max(flash) + 1; img = bytearray(b'\xff' * top)
    for a, v in flash.items(): img[a] = v
    missing = top - len(flash)
    open(outp, 'wb').write(img)
    print(f'{len(flash)} flash bytes recovered (0..{top:#x}), {missing} gaps -> {outp}')
if __name__ == '__main__': main()
