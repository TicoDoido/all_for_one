import os

# ----------------------------
# Descompressor (mantive igual)
# ----------------------------
EI = 12
EJ = 4
P = 2
rless = 0
init_chr = 0x00

def parse_params(parameters):
    vals = list(map(int, parameters.split())) if parameters else []
    if len(vals) >= 5:
        return vals[:5]
    return [12,4,2,0,0]

def lzss_set_window(window: bytearray, init_chr: int):
    n = len(window)

    if init_chr == -1:
        window[:] = b"\x00" * n
        i = 0
        while True:
            pos = (i * 8) + 6
            if pos >= n:
                break
            window[pos] = i & 0xFF
            i += 1

    elif init_chr == -2:
        for i in range(n):
            window[i] = i & 0xFF

    elif init_chr == -3:
        for i in range(n - 1, -1, -1):
            window[i] = i & 0xFF

    else:
        window[:] = bytes([init_chr & 0xFF]) * n

def unlzss(src: bytes, parameters: Optional[str] = None) -> bytes:
    EI, EJ, P, rless, init_chr = parse_params(parameters)

    N = 1 << EI
    F = 1 << EJ

    slide = bytearray(N)
    lzss_set_window(slide, init_chr)

    dst = bytearray()
    r = (N - F) - rless
    flags = 0
    pos = 0

    N_mask = N - 1
    F_mask = F - 1

    while pos < len(src):
        flags >>= 1
        if not (flags & 0x100):
            flags = src[pos] | 0xFF00
            pos += 1

        if flags & 1:
            c = src[pos]
            pos += 1
            dst.append(c)
            slide[r] = c
            r = (r + 1) & N_mask
        else:
            i = src[pos]
            j = src[pos + 1]
            pos += 2

            i |= ((j >> EJ) << 8)
            length = (j & F_mask) + P

            for k in range(length + 1):
                c = slide[(i + k) & N_mask]
                dst.append(c)
                slide[r] = c
                r = (r + 1) & N_mask

    return bytes(dst)


# ----------------------------
# Simple compressor
# ----------------------------
def lzss_compress(data: bytes, parameters: Optional[str] = None) -> bytes:
    EI, EJ, P, _, init_chr = parse_params(parameters)

    N = (EI if EI >= 16 else 1 << EI)
    F = (1 << EJ) + P
    THRESHOLD = P
    NIL = N

    text_buf = bytearray(N + F - 1)
    lson = [-1] * (N + 1)
    rson = [-1] * (N + 257)
    dad = [-1] * (N + 1)

    match_position = 0
    match_length = 0

    def InitTree():
        for i in range(N + 1, N + 257):
            rson[i] = NIL
        for i in range(N):
            dad[i] = NIL

    def InsertNode(r):
        nonlocal match_length, match_position
        cmp = 1
        p = N + 1 + text_buf[r]
        lson[r] = rson[r] = NIL
        match_length = 0

        while True:
            if cmp >= 0:
                if rson[p] != NIL:
                    p = rson[p]
                else:
                    rson[p] = r
                    dad[r] = p
                    return
            else:
                if lson[p] != NIL:
                    p = lson[p]
                else:
                    lson[p] = r
                    dad[r] = p
                    return

            i = 1
            while i < F:
                cmp = text_buf[r + i] - text_buf[p + i]
                if cmp != 0:
                    break
                i += 1

            if i > match_length:
                match_length = i
                match_position = p
                if match_length >= F:
                    break

        dad[r] = dad[p]
        lson[r] = lson[p]
        rson[r] = rson[p]
        dad[lson[p]] = r
        dad[rson[p]] = r

        if rson[dad[p]] == p:
            rson[dad[p]] = r
        else:
            lson[dad[p]] = r

        dad[p] = NIL

    def DeleteNode(p):
        if dad[p] == NIL:
            return

        if rson[p] == NIL:
            q = lson[p]
        elif lson[p] == NIL:
            q = rson[p]
        else:
            q = lson[p]
            while rson[q] != NIL:
                q = rson[q]
            rson[dad[q]] = lson[q]
            dad[lson[q]] = dad[q]
            lson[q] = lson[p]
            dad[lson[p]] = q
            rson[q] = rson[p]
            dad[rson[p]] = q

        dad[q] = dad[p]
        if rson[dad[p]] == p:
            rson[dad[p]] = q
        else:
            lson[dad[p]] = q

        dad[p] = NIL

    InitTree()
    lzss_set_window(text_buf, init_chr)

    in_pos = 0
    out = bytearray()

    s = 0
    r = N - F

    read_len = min(len(data), F)
    text_buf[r:r + read_len] = data[:read_len]
    in_pos += read_len
    textsize = read_len

    for i in range(1, F + 1):
        InsertNode(r - i)
    InsertNode(r)

    code_buf = bytearray(33)
    code_buf_ptr = 1
    mask = 1

    while textsize > 0:
        if match_length > textsize:
            match_length = textsize

        if match_length <= THRESHOLD:
            match_length = 1
            code_buf[0] |= mask
            code_buf[code_buf_ptr] = text_buf[r]
            code_buf_ptr += 1
        else:
            pos = match_position
            code_buf[code_buf_ptr] = pos & 0xFF
            code_buf_ptr += 1
            code_buf[code_buf_ptr] = (
                ((pos >> (8 - EJ)) & ~((1 << EJ) - 1)) |
                ((match_length - (THRESHOLD + 1)) & ((1 << EJ) - 1))
            )
            code_buf_ptr += 1

        mask <<= 1
        if mask == 0x100:
            out.extend(code_buf[:code_buf_ptr])
            code_buf = bytearray(33)
            code_buf_ptr = 1
            mask = 1

        last = match_length

        for _ in range(last):
            if in_pos < len(data):
                DeleteNode(s)
                c = data[in_pos]
                in_pos += 1
                text_buf[s] = c
                if s < F - 1:
                    text_buf[s + N] = c
                s = (s + 1) & (N - 1)
                r = (r + 1) & (N - 1)
                InsertNode(r)
            else:
                DeleteNode(s)
                s = (s + 1) & (N - 1)
                r = (r + 1) & (N - 1)

        textsize -= last

    if code_buf_ptr > 1:
        out.extend(code_buf[:code_buf_ptr])

    return bytes(out)


