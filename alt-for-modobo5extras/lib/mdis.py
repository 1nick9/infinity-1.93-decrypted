import struct
R=['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7','s0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra']
def s16(x): return x-0x10000 if x&0x8000 else x
OPI={0x08:'addi',0x09:'addiu',0x0a:'slti',0x0b:'sltiu',0x0c:'andi',0x0d:'ori',0x0e:'xori',0x18:'daddi',0x19:'daddiu'}
MEM={0x20:'lb',0x21:'lh',0x22:'lwl',0x23:'lw',0x24:'lbu',0x25:'lhu',0x26:'lwr',0x27:'lwu',0x28:'sb',0x29:'sh',0x2a:'swl',0x2b:'sw',0x2c:'sdl',0x2d:'sdr',0x2e:'swr',0x2f:'cache',0x37:'ld',0x3f:'sd',0x1a:'ldl',0x1b:'ldr',0x1e:'lq',0x1f:'sq',0x31:'lwc1',0x39:'swc1'}
SP={0x00:'sll',0x02:'srl',0x03:'sra',0x04:'sllv',0x06:'srlv',0x07:'srav',0x08:'jr',0x09:'jalr',0x0a:'movz',0x0b:'movn',0x0c:'syscall',0x0d:'break',0x0f:'sync',0x10:'mfhi',0x12:'mflo',0x14:'dsllv',0x16:'dsrlv',0x18:'mult',0x19:'multu',0x1a:'div',0x1b:'divu',0x20:'add',0x21:'addu',0x22:'sub',0x23:'subu',0x24:'and',0x25:'or',0x26:'xor',0x27:'nor',0x2a:'slt',0x2b:'sltu',0x2c:'dadd',0x2d:'daddu',0x2f:'dsubu',0x38:'dsll',0x3a:'dsrl',0x3b:'dsra',0x3c:'dsll32',0x3e:'dsrl32',0x3f:'dsra32'}
def dis(w,pc=0):
    op=w>>26; rs=(w>>21)&31; rt=(w>>16)&31; rd=(w>>11)&31; sa=(w>>6)&31; fn=w&63; im=w&0xffff
    if w==0: return 'nop'
    if op==0:
        n=SP.get(fn,'sp%02x'%fn)
        if fn in (0,2,3,0x38,0x3a,0x3b,0x3c,0x3e,0x3f): return f'{n} {R[rd]},{R[rt]},{sa}'
        if fn==8: return f'jr {R[rs]}'
        if fn==9: return f'jalr {R[rd]},{R[rs]}'
        if fn in (0x10,0x12): return f'{n} {R[rd]}'
        if fn in (0x18,0x19,0x1a,0x1b): return f'{n} {R[rs]},{R[rt]}'
        if fn in (0xc,0xd,0xf): return n
        if fn in (4,6,7,0x14,0x16): return f'{n} {R[rd]},{R[rt]},{R[rs]}'
        return f'{n} {R[rd]},{R[rs]},{R[rt]}'
    if op==1:
        n={0:'bltz',1:'bgez',2:'bltzl',3:'bgezl',0x11:'bgezal'}.get(rt,'regimm%x'%rt)
        return f'{n} {R[rs]},{pc+4+4*s16(im):#x}'
    if op in (2,3): return f"{'j' if op==2 else 'jal'} {((pc+4)&0xf0000000)|((w&0x3ffffff)<<2):#x}"
    if op in (4,5,0x14,0x15): return f"{ {4:'beq',5:'bne',0x14:'beql',0x15:'bnel'}[op]} {R[rs]},{R[rt]},{pc+4+4*s16(im):#x}"
    if op in (6,7,0x16,0x17): return f"{ {6:'blez',7:'bgtz',0x16:'blezl',0x17:'bgtzl'}[op]} {R[rs]},{pc+4+4*s16(im):#x}"
    if op==0xf: return f'lui {R[rt]},{im:#x}'
    if op in OPI: return f'{OPI[op]} {R[rt]},{R[rs]},{s16(im) if op not in (0xc,0xd,0xe) else hex(im)}'
    if op in MEM: return f'{MEM[op]} {R[rt]},{s16(im)}({R[rs]})'
    if op==0x10:
        if rs==0: return f'mfc0 {R[rt]},${rd}'
        if rs==4: return f'mtc0 {R[rt]},${rd}'
        if rs==0x10: return {0x18:'eret',0x38:'ei',0x39:'di',2:'tlbwi',6:'tlbwr',8:'tlbp',1:'tlbr'}.get(fn,'cop0 %x'%fn)
        if rs==8: return f'bc0 {rt} {pc+4+4*s16(im):#x}'
    if op==0x1c: return f'mmi {w:08x}'
    return f'.word {w:#010x}'
def dump(b,pc=0):
    for i in range(0,len(b)-3,4):
        w=struct.unpack('<I',b[i:i+4])[0]; print(f'{pc+i:08x}: {w:08x}  {dis(w,pc+i)}')
