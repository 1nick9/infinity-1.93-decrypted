import struct, sys
def is_break(w): return (w & 0xfc00003f) == 0x0d
def decrypt_blocks(buf, base, verbose=True, mul=0x41a7):
    b = bytearray(buf); n = len(b)//4; i = 0; blocks = []
    while i < n:
        w = struct.unpack_from('<I', b, 4*i)[0]
        if is_break(w) and (w >> 24) == 1:
            k = w; j = i + 1
            while j < n:
                k = ((k * mul) & 0xffffffff) % 0x7fffffff
                t = struct.unpack_from('<I', b, 4*j)[0]
                p = (t - k) & 0xffffffff
                struct.pack_into('<I', b, 4*j, p)
                if is_break(p): break
                j += 1
            blocks.append((base+4*i, base+4*j, w, p))
            i = j + 1
        else: i += 1
    if verbose:
        for s, e, w, p in blocks: print(f'  block {s:#x}-{e:#x} ({(e-s)//4-1} words) start {w:#010x} end {p:#010x}')
    return bytes(b), blocks
