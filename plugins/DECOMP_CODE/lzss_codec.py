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

def lzss_set_window(window_size, init_chr=0x00):
    return bytearray([init_chr] * window_size)

def unlzss(src: bytes, parameters: str = "12 4 2 0 0") -> bytes:
    global EI, EJ, P, rless, init_chr
    EI, EJ, P, rless, init_chr = parse_params(parameters)

    N = (1 << EI)
    F = (1 << EJ)
    slide_win = lzss_set_window(N, init_chr)

    dst = bytearray()
    src_pos = 0
    r = (N - F) - rless
    N_mask = N - 1
    F -= 1  # decoder uses F-1 for length mask

    flags = 0
    while src_pos < len(src):
        flags >>= 1
        if not (flags & 0x100):
            if src_pos >= len(src):
                break
            flags = src[src_pos] | 0xff00
            src_pos += 1

        if flags & 1:
            if src_pos >= len(src):
                break
            c = src[src_pos]
            src_pos += 1
            dst.append(c)
            slide_win[r] = c
            r = (r + 1) & N_mask
        else:
            if src_pos + 1 >= len(src):
                break
            i = src[src_pos]
            j = src[src_pos + 1]
            src_pos += 2
            # rebuild position and length exactly like the C decoder expects
            i |= ((j >> EJ) << 8)
            j = (j & F) + P
            for k in range(j + 1):
                c = slide_win[(i + k) & N_mask]
                dst.append(c)
                slide_win[r] = c
                r = (r + 1) & N_mask

    return bytes(dst)


# ----------------------------
# Simple correct compressor (naive search) compatible with the decoder above
# ----------------------------
def lzss_compress(data: bytes, parameters: str = "12 4 2 0 0") -> bytes:
    # parse parameters
    EI, EJ, P, rless, init_chr = parse_params(parameters)
    N = 1 << EI
    N_mask = N - 1
    F_decoder = 1 << EJ         # decoder's F before -1
    # maximum encodable match length:
    # decoder uses (j & ((1<<EJ)-1)) + P where j & mask ranges 0..(1<<EJ)-1,
    # and then decoder uses loop k=0..j inclusive -> j+1 bytes total.
    # We must be able to encode up to ((1<<EJ)-1) + P bytes.
    max_match = ((1 << EJ) - 1) + P

    # init sliding window identical to decoder
    window = bytearray([init_chr] * N)
    r = (N - (1 << EJ)) - rless  # same r as decoder initial

    out = bytearray()
    i_in = 0
    n = len(data)

    # We'll write in blocks of up to 8 units with a flag byte (1=literal, 0=pair)
    while i_in < n:
        flag = 0
        block = bytearray()
        for bit in range(8):
            if i_in >= n:
                break

            # find longest match in window for data[i_in...]
            best_len = 0
            best_pos = 0

            # threshold: if match length <= P then output literal
            # naive search: scan full window for matching starting bytes
            first_byte = data[i_in]
            # scan window positions (0..N-1)
            # optimization: skip positions that don't match first byte
            # (works well enough)
            jpos = 0
            while jpos < N:
                if window[jpos] == first_byte:
                    # attempt match
                    ml = 1
                    # compare up to max_match and up to remaining bytes
                    while ml < max_match and (i_in + ml) < n:
                        # compare window at (jpos + ml) with input
                        if window[(jpos + ml) & N_mask] != data[i_in + ml]:
                            break
                        ml += 1
                    if ml > best_len:
                        best_len = ml
                        best_pos = jpos
                        # early exit if we reached absolute maximum
                        if best_len >= max_match:
                            break
                jpos += 1

            if best_len <= P:
                # emit literal
                flag |= (1 << bit)
                c = data[i_in]
                block.append(c & 0xFF)
                # update window as decoder would
                window[r] = c & 0xFF
                r = (r + 1) & N_mask
                i_in += 1
            else:
                # emit pair: position (low byte) + second byte combining high pos bits and length_field
                pos = best_pos & 0xFFFF
                match_length = best_len
                # low byte
                low = pos & 0xFF
                # length field stored = match_length - (P + 1)
                length_field = (match_length - (P + 1)) & ((1 << EJ) - 1)
                # build second byte so decoder recovers pos via ((j >> EJ) << 8)
                second = ((pos >> 8) << EJ) | (length_field & ((1 << EJ) - 1))
                block.append(low)
                block.append(second & 0xFF)
                # Now, we must also update the window with the emitted match bytes,
                # exactly like the decoder will when expanding the match.
                for k in range(match_length):
                    b = window[(pos + k) & N_mask]
                    window[r] = b
                    r = (r + 1) & N_mask
                i_in += match_length

        # flush this code unit (flag + block)
        out.append(flag & 0xFF)
        out.extend(block)

    return bytes(out)

