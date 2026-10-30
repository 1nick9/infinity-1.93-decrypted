def nrv(s, variant='2e', start=0, limit=None):
    dst = bytearray(); i = start; bb = 0; last = 1
    def gb():
        nonlocal bb, i
        if not (bb & 0x7f): bb = s[i]*2 + 1; i += 1
        else: bb *= 2
        return (bb >> 8) & 1
    while True:
        while gb(): dst.append(s[i]); i += 1
        m_off = 1
        if variant == '2b':
            while True:
                m_off = m_off*2 + gb()
                if gb(): break
        else:
            while True:
                m_off = m_off*2 + gb()
                if gb(): break
                m_off = (m_off-1)*2 + gb()
        if m_off == 2:
            m_off = last
            m_len = gb() if variant != '2b' else None
        else:
            m_off = (m_off-3)*256 + s[i]; i += 1
            if m_off == 0xffffffff or m_off < 0: break
            if variant == '2b':
                m_off += 1; last = m_off; m_len = None
            else:
                m_len = (m_off ^ 1) & 1; m_off >>= 1; m_off += 1; last = m_off
        if variant == '2b':
            m_len = gb(); m_len = m_len*2 + gb()
            if m_len == 0:
                m_len = 1
                while True:
                    m_len = m_len*2 + gb()
                    if gb(): break
                m_len += 2
            m_len += (m_off > 0xd00)
        elif variant == '2d':
            m_len = m_len*2 + gb()
            if m_len == 0:
                m_len = 1
                while True:
                    m_len = m_len*2 + gb()
                    if gb(): break
                m_len += 2
            m_len += (m_off > 0x500)
        else:
            if m_len: m_len = 1 + gb()
            elif gb(): m_len = 3 + gb()
            else:
                m_len = 1
                while True:
                    m_len = m_len*2 + gb()
                    if gb(): break
                m_len += 3
            m_len += (m_off > 0x500)
        p = len(dst) - m_off
        if p < 0: raise ValueError('bad offset at in=%d out=%d' % (i, len(dst)))
        for k in range(m_len+1): dst.append(dst[p+k])
        if limit and len(dst) > limit: raise ValueError('overrun')
    return bytes(dst), i
