#!/usr/bin/env python3
"""
Implementação ajustada do algoritmo aPLib (compressão e descompressão) em Python 3.
Baseada no código de referência do Kabopan e na implementação oficial:
https://github.com/snemes/aplib/blob/master/src/aplib.py

Principais ajustes:
  • Uso de bytearray para o buffer de saída na máquina de bits (evita erros de imutabilidade)
  • Manutenção exata da lógica de números variáveis e marcação dos blocos
"""

def int2lebin(value, size):
    """Retorna o valor em bytes little-endian com tamanho 'size'."""
    result = bytearray()
    for i in range(size):
        result.append((value >> (8 * i)) & 0xFF)
    return bytes(result)

def modifybuffer(buf, sub, offset):
    """Substitui em 'buf' (bytearray) os bytes a partir do offset por 'sub'."""
    buf[offset:offset+len(sub)] = sub
    return buf

def getbinlen(value):
    """Retorna o número de bits necessários para representar 'value'."""
    result = 0
    if value == 0:
        return 1
    while value:
        value //= 2
        result += 1
    return result

def lengthdelta(offset):
    if offset < 0x80 or 0x7D00 <= offset:
        return 2
    elif 0x500 <= offset:
        return 1
    return 0

###############################################################################
# Máquina de bits para compressão
###############################################################################
class _bits_compress:
    """Escreve bits com tags de tamanho variável usando um bytearray para saída."""
    def __init__(self, tagsize):
        self.out = bytearray()  # agora mutável
        self.__tagsize = tagsize
        self.__tag = 0
        self.__tagoffset = None
        self.__maxbit = (self.__tagsize * 8) - 1
        self.__curbit = 0
        self.__isfirsttag = True

    def getdata(self):
        tag_bytes = int2lebin(self.__tag, self.__tagsize)
        modifybuffer(self.out, tag_bytes, self.__tagoffset)
        return self.out

    def write_bit(self, value):
        if self.__curbit != 0:
            self.__curbit -= 1
        else:
            # Se não é o primeiro tag, já insere os bits escritos
            if not self.__isfirsttag:
                self.getdata()
            else:
                self.__isfirsttag = False
            self.__tagoffset = len(self.out)
            self.out += b"\x00" * self.__tagsize
            self.__curbit = self.__maxbit
            self.__tag = 0
        if value:
            self.__tag |= (1 << self.__curbit)
        return

    def write_bitstring(self, s):
        for c in s:
            self.write_bit(1 if c == "1" else 0)
        return

    def write_byte(self, b):
        if isinstance(b, int):
            self.out.append(b)
        else:
            self.out += b[:1]
        return

    def write_fixednumber(self, value, nbbit):
        for i in range(nbbit - 1, -1, -1):
            self.write_bit((value >> i) & 1)
        return

    def write_variablenumber(self, value):
        """Codifica um número variável (valor >=2) conforme a lógica do Kabopan."""
        assert value >= 2
        length = getbinlen(value) - 2  # o bit mais significativo já é 1
        # Escreve o bit mais significativo (pode ser 0 ou 1)
        self.write_bit(1 if (value & (1 << length)) else 0)
        for i in range(length - 1, -1, -1):
            self.write_bit(1)
            self.write_bit(1 if (value & (1 << i)) else 0)
        self.write_bit(0)
        return

###############################################################################
# Máquina de bits para descompressão
###############################################################################
class _bits_decompress:
    """Lê bits de um buffer de dados (bytes ou bytearray) com tags de tamanho variável."""
    def __init__(self, data, tagsize):
        self.__curbit = 0
        self.__offset = 0
        self.__tag = None
        self.__tagsize = tagsize
        self._in = data  # pode ser bytes ou bytearray
        self.out = bytearray()

    def getoffset(self):
        return self.__offset

    def read_bit(self):
        if self.__curbit != 0:
            self.__curbit -= 1
        else:
            self.__curbit = (self.__tagsize * 8) - 1
            self.__tag = int.from_bytes(self._in[self.__offset:self.__offset+self.__tagsize], 'little')
            self.__offset += self.__tagsize
        bit = (self.__tag >> ((self.__tagsize * 8) - 1)) & 0x01
        self.__tag = (self.__tag << 1) & ((1 << (self.__tagsize * 8)) - 1)
        return bit

    def is_end(self):
        return self.__offset == len(self._in) and self.__curbit == 1

    def read_byte(self):
        result = self._in[self.__offset:self.__offset+1]
        self.__offset += 1
        return result

    def read_fixednumber(self, nbbit, init=0):
        result = init
        for i in range(nbbit):
            result = (result << 1) | self.read_bit()
        return result

    def read_variablenumber(self):
        result = 1
        result = (result << 1) | self.read_bit()
        while self.read_bit():
            result = (result << 1) | self.read_bit()
        return result

    def read_setbits(self, max_, set_=1):
        result = 0
        while result < max_ and self.read_bit() == set_:
            result += 1
        return result

    def back_copy(self, offset, length=1):
        for i in range(length):
            # Copia o byte anterior relativo ao offset
            self.out.append(self.out[-offset])
        return

    def read_literal(self, value=None):
        if value is None:
            self.out += self.read_byte()
        else:
            self.out += value
        return False

###############################################################################
# Função para busca de correspondência (LZ77)
###############################################################################
def find_longest_match(s, sub):
    """
    Procura a maior sequência em 's' (dicionário) que casa com o início de 'sub'.
    Retorna (offset, tamanho_da_correspondência).
    """
    if not sub:
        return 0, 0
    limit = len(s)
    dic = s[:]  # cópia do dicionário
    l = 0
    offset = 0
    length = 0
    word = b""
    word += sub[l:l+1]
    pos = dic.rfind(word, 0, limit + 1)
    if pos == -1:
        return offset, length
    offset = limit - pos
    length = len(word)
    dic += sub[l:l+1]
    while l < len(sub) - 1:
        l += 1
        word += sub[l:l+1]
        pos = dic.rfind(word, 0, limit + 1)
        if pos == -1:
            return offset, length
        offset = limit - pos
        length = len(word)
        dic += sub[l:l+1]
    return offset, length

###############################################################################
# Compressor aPLib
###############################################################################
class AplibCompressor(_bits_compress):
    """Implementa a compressão aPLib (baseada em LZ77)."""
    def __init__(self, data, length=None):
        super().__init__(1)
        self.__in = data  # dados do tipo bytes
        self.__length = length if length is not None else len(data)
        self.__offset = 0
        self.__lastoffset = 0
        self.__pair = True

    def __literal(self, marker=True):
        if marker:
            self.write_bit(0)
        self.write_byte(self.__in[self.__offset:self.__offset+1])
        self.__offset += 1
        self.__pair = True

    def __block(self, offset, match_len):
        assert offset >= 2
        self.write_bitstring("10")
        if self.__pair and self.__lastoffset == offset:
            self.write_variablenumber(2)
            self.write_variablenumber(match_len)
        else:
            high = (offset >> 8) + 2
            if self.__pair:
                high += 1
            self.write_variablenumber(high)
            low = offset & 0xFF
            self.write_byte(low)
            self.write_variablenumber(match_len - lengthdelta(offset))
        self.__offset += match_len
        self.__lastoffset = offset
        self.__pair = False

    def __shortblock(self, offset, match_len):
        assert 2 <= match_len <= 3
        assert 0 < offset <= 127
        self.write_bitstring("110")
        b_val = (offset << 1) + (match_len - 2)
        self.write_byte(b_val)
        self.__offset += match_len
        self.__lastoffset = offset
        self.__pair = False

    def __singlebyte(self, offset):
        assert 0 <= offset < 16
        self.write_bitstring("111")
        self.write_fixednumber(offset, 4)
        self.__offset += 1
        self.__pair = True

    def __end(self):
        self.write_bitstring("110")
        self.write_byte(0)

    def do(self):
        # Inicia com um literal sem marcador
        self.__literal(False)
        while self.__offset < self.__length:
            offset, match_len = find_longest_match(self.__in[:self.__offset],
                                                    self.__in[self.__offset:])
            if match_len == 0:
                c = self.__in[self.__offset:self.__offset+1]
                if c == b"\x00":
                    self.__singlebyte(0)
                else:
                    self.__literal()
            elif match_len == 1 and 0 <= offset < 16:
                self.__singlebyte(offset)
            elif 2 <= match_len <= 3 and 0 < offset <= 127:
                self.__shortblock(offset, match_len)
            elif match_len >= 3 and offset >= 2:
                self.__block(offset, match_len)
            else:
                self.__literal()
        self.__end()
        return bytes(self.getdata())

###############################################################################
# Descompressor aPLib
###############################################################################
class AplibDecompressor(_bits_decompress):
    """Implementa a descompressão aPLib."""
    def __init__(self, data):
        super().__init__(data, tagsize=1)
        self.__pair = True
        self.__lastoffset = 0
        self.__functions = [
            self.__literal,
            self.__block,
            self.__shortblock,
            self.__singlebyte
        ]

    def __literal(self):
        self.read_literal()
        self.__pair = True
        return False

    def __block(self):
        b_val = self.read_variablenumber()
        if b_val == 2 and self.__pair:
            offset = self.__lastoffset
            match_len = self.read_variablenumber()
        else:
            high = b_val - 2
            if self.__pair:
                high -= 1
            offset = (high << 8) + int.from_bytes(self.read_byte(), 'little')
            match_len = self.read_variablenumber()
            match_len += lengthdelta(offset)
        self.__lastoffset = offset
        self.back_copy(offset, match_len)
        self.__pair = False
        return False

    def __shortblock(self):
        b_val = int.from_bytes(self.read_byte(), 'little')
        if b_val <= 1:
            return True
        match_len = 2 + (b_val & 0x01)
        offset = b_val >> 1
        self.back_copy(offset, match_len)
        self.__lastoffset = offset
        self.__pair = False
        return False

    def __singlebyte(self):
        offset = self.read_fixednumber(4)
        if offset:
            self.back_copy(offset)
        else:
            self.read_literal(b"\x00")
        self.__pair = True
        return False

    def do(self):
        self.read_literal()  # lê o primeiro literal (sem marcador)
        while True:
            idx = self.read_setbits(3)
            if self.__functions[idx]():
                break
        return bytes(self.out)

###############################################################################
# Funções wrapper
###############################################################################
def compress(data, length=None):
    """
    Retorna os dados comprimidos (tipo bytes).
    'data' deve ser do tipo bytes.
    """
    return AplibCompressor(data, length).do()

def decompress(data):
    """
    Retorna os dados descomprimidos (tipo bytes).
    'data' deve ser do tipo bytes.
    """
    return AplibDecompressor(data).do()

