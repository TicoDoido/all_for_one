import os
import struct
from tkinter import filedialog, messagebox

# no topo do seu plugin.py
logger = print
get_option = lambda name: None  # stub até receber do host

def register_plugin(log_func, option_getter):
    global logger, get_option
    # atribui o logger e a função de consulta de opções vindos do host
    logger     = log_func or print
    get_option = option_getter or (lambda name: None)
            
    return {
        "name": "MSG1 Lost Planet (PS3), Dead Rising(Xbox360)",
        "description": "Converte arquivos .msg(MSG1) para texto e vice-versa",
        "options": [
            {
                "name": "tabela_jogo",
                "label": "Escolha o jogo",
                "values": ["Lost Planet EC(PS3)", "Dead Rising (Xbox360)"]
            }
        ],
        "commands": [
            {"label": "Converter MSG para TXT", "action": convert_msg_to_txt},
            {"label": "Converter TXT para MSG", "action": convert_txt_to_msg}
        ]
    }

# Tabela para Dead Rising Xbox 360
tabela_dead_rising_xbox360 = {
    b'\x01\x00\x00\x00\x00\x04': b'[FIM]\n',
    b'\x03\x00\x00\x00\x00\x04': b'\n',
    b'\x20\x00\x1C\x00\x1E\x00': ' '.encode('utf-8'),  # espaço
    b'\x61\x00\x6C\x00\x3C\x00': 'a'.encode('utf-8'),  # a
    b'\x62\x00\x6E\x00\x41\x00': 'b'.encode('utf-8'),  # b
    b'\x63\x00\x70\x00\x3A\x00': 'c'.encode('utf-8'),  # c
    b'\x64\x00\x72\x00\x41\x00': 'd'.encode('utf-8'),  # d
    b'\x65\x00\x74\x00\x3D\x00': 'e'.encode('utf-8'),  # e
    b'\x66\x00\x76\x00\x22\x00': 'f'.encode('utf-8'),  # f
    b'\x67\x00\x78\x00\x40\x00': 'g'.encode('utf-8'),  # g
    b'\x68\x00\x7A\x00\x40\x00': 'h'.encode('utf-8'),  # h
    b'\x69\x00\x7C\x00\x1C\x00': 'i'.encode('utf-8'),  # i
    b'\x6A\x00\x7E\x00\x1C\x00': 'j'.encode('utf-8'),  # j
    b'\x6B\x00\x80\x00\x3A\x00': 'k'.encode('utf-8'),  # k
    b'\x6C\x00\x82\x00\x1C\x00': 'l'.encode('utf-8'),  # l
    b'\x6D\x00\x84\x00\x5D\x00': 'm'.encode('utf-8'),  # m
    b'\x6E\x00\x86\x00\x3F\x00': 'n'.encode('utf-8'),  # n
    b'\x6F\x00\x88\x00\x40\x00': 'o'.encode('utf-8'),  # o
    b'\x70\x00\x8A\x00\x41\x00': 'p'.encode('utf-8'),  # p
    b'\x71\x00\x8C\x00\x41\x00': 'q'.encode('utf-8'),  # q
    b'\x72\x00\x8E\x00\x29\x00': 'r'.encode('utf-8'),  # r
    b'\x73\x00\x90\x00\x39\x00': 's'.encode('utf-8'),  # s
    b'\x74\x00\x92\x00\x22\x00': 't'.encode('utf-8'),  # t
    b'\x75\x00\x94\x00\x3F\x00': 'u'.encode('utf-8'),  # u
    b'\x76\x00\x96\x00\x38\x00': 'v'.encode('utf-8'),  # v
    b'\x77\x00\x98\x00\x51\x00': 'w'.encode('utf-8'),  # w
    b'\x78\x00\x9A\x00\x36\x00': 'x'.encode('utf-8'),  # x
    b'\x79\x00\x9C\x00\x38\x00': 'y'.encode('utf-8'),  # y
    b'\x7A\x00\x9E\x00\x35\x00': 'z'.encode('utf-8'),  # z
    b'\x41\x00\x38\x00\x49\x00': 'A'.encode('utf-8'),  # A
    b'\x42\x00\x3A\x00\x4A\x00': 'B'.encode('utf-8'),  # B
    b'\x43\x00\x3C\x00\x4F\x00': 'C'.encode('utf-8'),  # C
    b'\x44\x00\x3E\x00\x4D\x00': 'D'.encode('utf-8'),  # D
    b'\x45\x00\x40\x00\x45\x00': 'E'.encode('utf-8'),  # E
    b'\x46\x00\x42\x00\x3F\x00': 'F'.encode('utf-8'),  # F
    b'\x47\x00\x44\x00\x52\x00': 'G'.encode('utf-8'),  # G
    b'\x48\x00\x46\x00\x4F\x00': 'H'.encode('utf-8'),  # H
    b'\x49\x00\x48\x00\x20\x00': 'I'.encode('utf-8'),  # I
    b'\x4A\x00\x4A\x00\x3A\x00': 'J'.encode('utf-8'),  # J
    b'\x4B\x00\x4C\x00\x4A\x00': 'K'.encode('utf-8'),  # K
    b'\x4C\x00\x4E\x00\x3E\x00': 'L'.encode('utf-8'),  # L
    b'\x4D\x00\x50\x00\x5C\x00': 'M'.encode('utf-8'),  # M
    b'\x4E\x00\x52\x00\x4F\x00': 'N'.encode('utf-8'),  # N
    b'\x4F\x00\x54\x00\x53\x00': 'O'.encode('utf-8'),  # O
    b'\x50\x00\x56\x00\x47\x00': 'P'.encode('utf-8'),  # P
    b'\x51\x00\x58\x00\x53\x00': 'Q'.encode('utf-8'),  # Q
    b'\x52\x00\x5A\x00\x4B\x00': 'R'.encode('utf-8'),  # R
    b'\x53\x00\x5C\x00\x47\x00': 'S'.encode('utf-8'),  # S
    b'\x54\x00\x5E\x00\x3F\x00': 'T'.encode('utf-8'),  # T
    b'\x55\x00\x60\x00\x4C\x00': 'U'.encode('utf-8'),  # U
    b'\x56\x00\x62\x00\x42\x00': 'V'.encode('utf-8'),  # V
    b'\x57\x00\x64\x00\x63\x00': 'W'.encode('utf-8'),  # W
    b'\x58\x00\x66\x00\x42\x00': 'X'.encode('utf-8'),  # X
    b'\x59\x00\x68\x00\x42\x00': 'Y'.encode('utf-8'),  # Y
    b'\x5A\x00\x6A\x00\x3F\x00': 'Z'.encode('utf-8'),  # Z
    b'\x30\x00\x00\x00\x3C\x00': '0'.encode('utf-8'),  # 0
    b'\x31\x00\x02\x00\x3C\x00': '1'.encode('utf-8'),  # 1
    b'\x32\x00\x04\x00\x3C\x00': '2'.encode('utf-8'),  # 2
    b'\x33\x00\x06\x00\x3C\x00': '3'.encode('utf-8'),  # 3
    b'\x34\x00\x08\x00\x3C\x00': '4'.encode('utf-8'),  # 4
    b'\x35\x00\x0A\x00\x3C\x00': '5'.encode('utf-8'),  # 5
    b'\x36\x00\x0C\x00\x3C\x00': '6'.encode('utf-8'),  # 6
    b'\x37\x00\x0E\x00\x3C\x00': '7'.encode('utf-8'),  # 7
    b'\x38\x00\x10\x00\x3C\x00': '8'.encode('utf-8'),  # 8
    b'\x39\x00\x12\x00\x3C\x00': '9'.encode('utf-8'),  # 9
    b'\x3F\x00\x16\x00\x3A\x00': '?'.encode('utf-8'),  # ?
    b'\x3A\x00\x20\x00\x20\x00': ':'.encode('utf-8'),  # :
    b'\x5B\x00\xA0\x00\x28\x00': '['.encode('utf-8'),  # [
    b'\x5D\x00\xA2\x00\x28\x00': ']'.encode('utf-8'),  # ]
    b'\x22\x00\x28\x00\x23\x00': '"'.encode('utf-8'),  # "
    b'\x27\x00\x2A\x00\x12\x00': "'".encode('utf-8'),  # '
    b'\x2C\x00\x24\x00\x1E\x00': ','.encode('utf-8'),  # ,
    b'\x2D\x00\x2E\x00\x23\x00': '-'.encode('utf-8'),  # -
    b'\x2E\x00\x26\x00\x1E\x00': '.'.encode('utf-8'),  # .
    b'\x2B\x00\x30\x00\x59\x00': '+'.encode('utf-8'),  # +
    b'\x28\x00\x18\x00\x26\x00': '('.encode('utf-8'),  # (
    b'\x29\x00\x1A\x00\x26\x00': ')'.encode('utf-8'),  # )
    b'\x25\x00\x16\x01\x5B\x00': '%'.encode('utf-8'),  # %
    b'\x21\x00\x14\x00\x23\x00': '!'.encode('utf-8'),  # !
    b'\xBF\x00\xA6\x00\x3A\x00': '¿'.encode('utf-8'),  # ¿
    b'\xC0\x00\xAC\x00\x49\x00': 'À'.encode('utf-8'),  # À
    b'\xC1\x00\xAE\x00\x49\x00': 'Á'.encode('utf-8'),  # Á
    b'\xC2\x00\xB0\x00\x49\x00': 'Â'.encode('utf-8'),  # Â
    b'\xC4\x00\xB2\x00\x49\x00': 'Ä'.encode('utf-8'),  # Ä
    b'\xC7\x00\xB4\x00\x4F\x00': 'Ç'.encode('utf-8'),  # Ç
    b'\xC8\x00\xB6\x00\x45\x00': 'È'.encode('utf-8'),  # È
    b'\xC9\x00\xB8\x00\x45\x00': 'É'.encode('utf-8'),  # É
    b'\xCA\x00\xBA\x00\x45\x00': 'Ê'.encode('utf-8'),  # Ê
    b'\xCB\x00\xBC\x00\x45\x00': 'Ë'.encode('utf-8'),  # Ë
    b'\xCC\x00\xBE\x00\x20\x00': 'Ì'.encode('utf-8'),  # Ì
    b'\xCD\x00\xC0\x00\x20\x00': 'Í'.encode('utf-8'),  # Í
    b'\xCE\x00\xC2\x00\x20\x00': 'Î'.encode('utf-8'),  # Î
    b'\xCF\x00\xC4\x00\x20\x00': 'Ï'.encode('utf-8'),  # Ï
    b'\xD2\x00\xC8\x00\x53\x00': 'Ò'.encode('utf-8'),  # Ò
    b'\xD3\x00\xCA\x00\x53\x00': 'Ó'.encode('utf-8'),  # Ó
    b'\xD4\x00\xCC\x00\x53\x00': 'Ô'.encode('utf-8'),  # Ô
    b'\xD6\x00\xCE\x00\x53\x00': 'Ö'.encode('utf-8'),  # Ö
    b'\xE0\x00\xD8\x00\x3C\x00': 'à'.encode('utf-8'),  # à
    b'\xE1\x00\xDA\x00\x3C\x00': 'á'.encode('utf-8'),  # á
    b'\xE2\x00\xDC\x00\x3C\x00': 'â'.encode('utf-8'),  # â
    b'\xE4\x00\xDE\x00\x3C\x00': 'ä'.encode('utf-8'),  # ä
    b'\xE7\x00\xE0\x00\x3A\x00': 'ç'.encode('utf-8'),  # ç
    b'\xE8\x00\xE2\x00\x3D\x00': 'è'.encode('utf-8'),  # è
    b'\xE9\x00\xE4\x00\x3D\x00': 'é'.encode('utf-8'),  # é
    b'\xEA\x00\xE6\x00\x3D\x00': 'ê'.encode('utf-8'),  # ê
    b'\xEB\x00\xE8\x00\x3D\x00': 'ë'.encode('utf-8'),  # ë
    b'\xEC\x00\xEA\x00\x1C\x00': 'ì'.encode('utf-8'),  # ì
    b'\xED\x00\xEC\x00\x1C\x00': 'í'.encode('utf-8'),  # í
    b'\xEE\x00\xEE\x00\x1C\x00': 'î'.encode('utf-8'),  # î
    b'\xEF\x00\xF0\x00\x1C\x00': 'ï'.encode('utf-8'),  # ï
    b'\xF1\x00\xF2\x00\x3F\x00': 'ñ'.encode('utf-8'),  # ñ
    b'\xF2\x00\xF4\x00\x40\x00': 'ò'.encode('utf-8'),  # ò
    b'\xF3\x00\xF6\x00\x40\x00': 'ó'.encode('utf-8'),  # ó
    b'\xF4\x00\xF8\x00\x40\x00': 'ô'.encode('utf-8'),  # ô
    b'\xF6\x00\xFA\x00\x40\x00': 'ö'.encode('utf-8'),  # ö
    b'\xFA\x00\xFE\x00\x3F\x00': 'ú'.encode('utf-8'),  # ú
    b'\xF9\x00\xFC\x00\x3F\x00': 'ù'.encode('utf-8'),  # ù

}
# Tabela de conversão completa
tabela_lost_planet_ps3 = {
    b'\x00\x01\x00\x00\x00\x04': b'[FIM]\n',
    b'\x00\x03\x00\x00\x00\x04': b'\n',
    b'\x00\x20\x00\x0E\x40\x02': ' '.encode('utf-8'),  # espaço
    b'\x00\x21\x00\x0A\x40\x02': '!'.encode('utf-8'),  # !
    b'\x00\x22\x00\x14\x50\x02': '"'.encode('utf-8'),  # "
    b'\x00\x23\x00\x57\x7E\x02': '#'.encode('utf-8'),  # #
    b'\x00\x24\x00\x1B\x7E\x02': '$'.encode('utf-8'),  # $
    b'\x00\x25\x00\x7F\xCA\x02': '%'.encode('utf-8'),  # %
    b'\x00\x26\x00\x0F\x98\x02': '&'.encode('utf-8'),  # &
    b'\x00\x27\x00\x15\x31\x02': "'".encode('utf-8'),  # '
    b'\x00\x28\x00\x0C\x4C\x02': '('.encode('utf-8'),  # (
    b'\x00\x29\x00\x0D\x4C\x02': ')'.encode('utf-8'),  # )
    b'\x00\x2A\x00\x54\x58\x02': '*'.encode('utf-8'),  # *
    b'\x00\x2B\x00\x18\x85\x02': '+'.encode('utf-8'),  # +
    b'\x00\x2C\x00\x12\x40\x02': ','.encode('utf-8'),  # ,
    b'\x00\x2D\x00\x17\x4C\x02': '-'.encode('utf-8'),  # -
    b'\x00\x2E\x00\x13\x40\x02': '.'.encode('utf-8'),  # .
    b'\x00\x2F\x00\x19\x40\x02': '/'.encode('utf-8'),  # /
    b'\x00\x30\x00\x00\x7E\x02': '0'.encode('utf-8'),  # 0
    b'\x00\x31\x00\x01\x7E\x02': '1'.encode('utf-8'),  # 1
    b'\x00\x32\x00\x02\x7E\x02': '2'.encode('utf-8'),  # 2
    b'\x00\x33\x00\x03\x7E\x02': '3'.encode('utf-8'),  # 3
    b'\x00\x34\x00\x04\x7E\x02': '4'.encode('utf-8'),  # 4
    b'\x00\x35\x00\x05\x7E\x02': '5'.encode('utf-8'),  # 5
    b'\x00\x36\x00\x06\x7E\x02': '6'.encode('utf-8'),  # 6
    b'\x00\x37\x00\x07\x7E\x02': '7'.encode('utf-8'),  # 7
    b'\x00\x38\x00\x08\x7E\x02': '8'.encode('utf-8'),  # 8
    b'\x00\x39\x00\x09\x7E\x02': '9'.encode('utf-8'),  # 9
    b'\x00\x3A\x00\x10\x40\x02': ':'.encode('utf-8'),  # :
    b'\x00\x3B\x00\x11\x40\x02': ';'.encode('utf-8'),  # ;
    b'\x00\x3D\x00\x78\x85\x02': '='.encode('utf-8'),  # =
    b'\x00\x3F\x00\x0B\x7E\x02': '?'.encode('utf-8'),  # ?
    b'\x00\x40\x00\x1A\xE9\x02': '@'.encode('utf-8'),  # @
    b'\x00\x41\x00\x1C\x98\x02': 'A'.encode('utf-8'),  # A
    b'\x00\x42\x00\x1D\x98\x02': 'B'.encode('utf-8'),  # B
    b'\x00\x43\x00\x1E\xA4\x02': 'C'.encode('utf-8'),  # C
    b'\x00\x44\x00\x1F\xA4\x02': 'D'.encode('utf-8'),  # D
    b'\x00\x45\x00\x20\x98\x02': 'E'.encode('utf-8'),  # E
    b'\x00\x46\x00\x21\x8C\x02': 'F'.encode('utf-8'),  # F
    b'\x00\x47\x00\x22\xB2\x02': 'G'.encode('utf-8'),  # G
    b'\x00\x48\x00\x23\xA4\x02': 'H'.encode('utf-8'),  # H
    b'\x00\x49\x00\x24\x40\x02': 'I'.encode('utf-8'),  # I
    b'\x00\x4A\x00\x25\x72\x02': 'J'.encode('utf-8'),  # J
    b'\x00\x4B\x00\x26\x98\x02': 'K'.encode('utf-8'),  # K
    b'\x00\x4C\x00\x27\x7E\x02': 'L'.encode('utf-8'),  # L
    b'\x00\x4D\x00\x28\xBE\x02': 'M'.encode('utf-8'),  # M
    b'\x00\x4E\x00\x29\xA4\x02': 'N'.encode('utf-8'),  # N
    b'\x00\x4F\x00\x2A\xB2\x02': 'O'.encode('utf-8'),  # O
    b'\x00\x50\x00\x2B\x98\x02': 'P'.encode('utf-8'),  # P
    b'\x00\x51\x00\x2C\xB2\x02': 'Q'.encode('utf-8'),  # Q
    b'\x00\x52\x00\x2D\xA4\x02': 'R'.encode('utf-8'),  # R
    b'\x00\x53\x00\x2E\x98\x02': 'S'.encode('utf-8'),  # S
    b'\x00\x54\x00\x2F\x8C\x02': 'T'.encode('utf-8'),  # T
    b'\x00\x55\x00\x30\xA4\x02': 'U'.encode('utf-8'),  # U
    b'\x00\x56\x00\x31\x98\x02': 'V'.encode('utf-8'),  # V
    b'\x00\x57\x00\x32\xD8\x02': 'W'.encode('utf-8'),  # W
    b'\x00\x58\x00\x33\x98\x02': 'X'.encode('utf-8'),  # X
    b'\x00\x59\x00\x34\x98\x02': 'Y'.encode('utf-8'),  # Y
    b'\x00\x5A\x00\x35\x8C\x02': 'Z'.encode('utf-8'),  # Z
    b'\x00\x5B\x00\x50\x40\x02': '<'.encode('utf-8'),  # [
    b'\x00\x5C\x00\x55\x40\x02': '\\'.encode('utf-8'),  # \
    b'\x00\x5D\x00\x51\x40\x02': '>'.encode('utf-8'),  # ]
    b'\x00\x5E\x00\x56\x6B\x02': '^'.encode('utf-8'),  # ^
    b'\x00\x5F\x00\x7A\x7E\x02': '_'.encode('utf-8'),  # _
    b'\x00\x60\x00\x58\x4C\x02': '`'.encode('utf-8'),  # `
    b'\x00\x61\x00\x36\x7E\x02': 'a'.encode('utf-8'),  # a
    b'\x00\x62\x00\x37\x7E\x02': 'b'.encode('utf-8'),  # b
    b'\x00\x63\x00\x38\x72\x02': 'c'.encode('utf-8'),  # c
    b'\x00\x64\x00\x39\x7E\x02': 'd'.encode('utf-8'),  # d
    b'\x00\x65\x00\x3A\x7E\x02': 'e'.encode('utf-8'),  # e
    b'\x00\x66\x00\x3B\x40\x02': 'f'.encode('utf-8'),  # f
    b'\x00\x67\x00\x3C\x7E\x02': 'g'.encode('utf-8'),  # g
    b'\x00\x68\x00\x3D\x7E\x02': 'h'.encode('utf-8'),  # h
    b'\x00\x69\x00\x3E\x31\x02': 'i'.encode('utf-8'),  # i
    b'\x00\x6A\x00\x3F\x31\x02': 'j'.encode('utf-8'),  # j
    b'\x00\x6B\x00\x40\x72\x02': 'k'.encode('utf-8'),  # k
    b'\x00\x6C\x00\x41\x31\x02': 'l'.encode('utf-8'),  # l
    b'\x00\x6D\x00\x42\xBE\x02': 'm'.encode('utf-8'),  # m
    b'\x00\x6E\x00\x43\x7E\x02': 'n'.encode('utf-8'),  # n
    b'\x00\x6F\x00\x44\x7E\x02': 'o'.encode('utf-8'),  # o
    b'\x00\x70\x00\x45\x7E\x02': 'p'.encode('utf-8'),  # p
    b'\x00\x71\x00\x46\x7E\x02': 'q'.encode('utf-8'),  # q
    b'\x00\x72\x00\x47\x4C\x02': 'r'.encode('utf-8'),  # r
    b'\x00\x73\x00\x48\x72\x02': 's'.encode('utf-8'),  # s
    b'\x00\x74\x00\x49\x40\x02': 't'.encode('utf-8'),  # t
    b'\x00\x75\x00\x4A\x7E\x02': 'u'.encode('utf-8'),  # u
    b'\x00\x76\x00\x4B\x72\x02': 'v'.encode('utf-8'),  # v
    b'\x00\x77\x00\x4C\xA4\x02': 'w'.encode('utf-8'),  # w
    b'\x00\x78\x00\x4D\x72\x02': 'x'.encode('utf-8'),  # x
    b'\x00\x79\x00\x4E\x72\x02': 'y'.encode('utf-8'),  # y
    b'\x00\x7A\x00\x4F\x72\x02': 'z'.encode('utf-8'),  # z
    b'\x00\x7B\x00\x59\x4C\x02': '{'.encode('utf-8'),  # {
    b'\x00\x7C\x00\x79\x3B\x02': '|'.encode('utf-8'),  # |
    b'\x00\x7D\x00\x5A\x4C\x02': '}'.encode('utf-8'),  # }
    b'\x00\x7E\x00\x16\x85\x02': '~'.encode('utf-8'),  # ~
    b'\x21\x92\x00\xB7\x85\x00': '‚'.encode('utf-8'),  # ‚
    b'\x21\x93\x00\xB3\x85\x00': '“'.encode('utf-8'),  # “
    b'\x00\xA1\x00\xAB\x4C\x02': '¡'.encode('utf-8'),  # ¡
    b'\x00\xA5\x7E\x02\x73\x20': '¥'.encode('utf-8'),  # ¥
    b'\x00\xAA\x00\xAC\x53\x02': 'ª'.encode('utf-8'),  # ª
    b'\x00\xB0\x00\xBB\x5C\x02': '°'.encode('utf-8'),  # °
    b'\x00\xBF\x00\xA6\x8C\x02': '¿'.encode('utf-8'),  # ¿
    b'\x00\xC0\x00\x97\x98\x02': 'À'.encode('utf-8'),  # À
    b'\x00\xC4\x00\x83\x98\x02': 'Ä'.encode('utf-8'),  # Ä
    b'\x00\xC7\x00\x9C\xA4\x02': 'Ç'.encode('utf-8'),  # Ç
    b'\x00\xC9\x00\x98\x98\x02': 'É'.encode('utf-8'),  # É
    b'\x00\xDC\x00\x85\xA4\x02': 'Ü'.encode('utf-8'),  # Ü
    b'\x00\xE0\x00\x91\x7E\x02': 'à'.encode('utf-8'),  # à
    b'\x00\xE1\x00\xA5\x7E\x02': 'á'.encode('utf-8'),  # á
    b'\x00\xE4\x00\x81\x7E\x02': 'ä'.encode('utf-8'),  # ä
    b'\x00\xE7\x00\x9B\x72\x02': 'ç'.encode('utf-8'),  # ç
    b'\x00\xE8\x00\x90\x7E\x02': 'è'.encode('utf-8'),  # è
    b'\x00\xE9\x00\x8E\x7E\x02': 'é'.encode('utf-8'),  # é
    b'\x00\xEA\x00\x92\x7E\x02': 'ê'.encode('utf-8'),  # ê
    b'\x00\xED\x00\xA3\x40\x02': 'í'.encode('utf-8'),  # í
    b'\x00\xF1\x00\xA8\x7E\x02': 'ñ'.encode('utf-8'),  # ñ
    b'\x00\xF2\x00\xA1\x7E\x02': 'ò'.encode('utf-8'),  # ò
    b'\x00\xF3\x00\xA7\x7E\x02': 'ó'.encode('utf-8'),  # ó
    b'\x00\xF4\x00\x95\x7E\x02': 'ô'.encode('utf-8'),  # ô
    b'\x00\xF6\x00\x84\x7E\x02': 'ö'.encode('utf-8'),  # ö
    b'\x00\xFA\x00\xA4\x7E\x02': 'ú'.encode('utf-8'),  # ú
}

def converter_binario_para_txt(input_file, output_file):
    
    
    modo = get_option("tabela_jogo")
    if modo == "Lost Planet EC(PS3)":
        tabela = tabela_lost_planet_ps3
        endiam = '>I'
    else:
        tabela = tabela_dead_rising_xbox360
        endiam = '<I'
    try:
        # Primeiro verifica o magic number sem criar o arquivo de saída
        with open(input_file, 'rb') as bin_file:
            magic = bin_file.read(4)
            if magic != b'MSG1':
                raise ValueError("Arquivo não é um .msg válido (Magic Number incorreto).")
        
        # Se o magic number estiver correto, prossegue com a conversão
        with open(input_file, 'rb') as bin_file, open(output_file, 'w', encoding='utf-8') as txt_file:
            bin_file.seek(4)
            inicio_texto = struct.unpack(endiam, bin_file.read(4))[0]
            bin_file.seek(inicio_texto)
            while True:
                bloco = bin_file.read(6)
                if not bloco:
                    break
                    
                if bloco in tabela:
                    caractere = tabela[bloco].decode('utf-8', errors='replace')
                else:
                    caractere = f"[{''.join(f'{b:02X}' for b in bloco)}]"

                txt_file.write(caractere)
        return True
    except Exception as e:
        messagebox.showerror("Erro", f"Erro na conversão: {str(e)}")
        return False

def convert_msg_to_txt():
    arquivo_msg = filedialog.askopenfilename(
        title="Selecione o arquivo .msg",
        filetypes=[("Arquivos MSG", "*.msg"), ("Todos os arquivos", "*.*")]
    )
    if not arquivo_msg:
        return

    arquivo_txt = os.path.splitext(arquivo_msg)[0] + '.txt'
    if converter_binario_para_txt(arquivo_msg, arquivo_txt):
        messagebox.showinfo("Sucesso", f"Arquivo convertido:\n{arquivo_txt}")

def converter_txt_para_binario(input_file, output_file):
    try:
        modo = get_option("tabela_jogo")
        if modo == "Lost Planet EC(PS3)":
            tabela = tabela_lost_planet_ps3
            endiam = '>I'
        else:
            tabela = tabela_dead_rising_xbox360
            endiam = '<I'
            
        conversao_reversa = {v.decode('utf-8', errors='replace'): k for k, v in tabela.items()}

        with open(input_file, 'r', encoding='utf-8') as txt_file, open(output_file, 'r+b') as bin_file:
            buffer = ''
            bin_file.seek(64)

            while True:
                caractere = txt_file.read(1)
                if not caractere:
                    break

                buffer += caractere

                if buffer.endswith('['):
                    next_chars = txt_file.read(3)
                    if not next_chars:
                        break

                    buffer += next_chars

                    if buffer.endswith('FIM'):
                        next_two_chars = txt_file.read(2)
                        buffer += next_two_chars
                        
                        if next_two_chars == ']\n':
                            if modo == "Lost Planet EC(PS3)":
                                bloco = b'\x00\x01\x00\x00\x00\x04'
                            else:
                                bloco = b'\x01\x00\x00\x00\x00\x04'
                        else:
                            buffer = buffer[:-5]
                    else:
                        buffer = buffer[:-5]
                        hex_restante = txt_file.read(9)
                        hex_seq = next_chars + hex_restante
                        buffer += hex_restante

                        try:
                            bloco = bytes.fromhex(hex_seq)
                            txt_file.read(1)
                        except ValueError as e:
                            continue
                
                elif caractere in conversao_reversa:
                    bloco = conversao_reversa[caractere]
                else:
                    continue
                
                bin_file.write(bloco)
            
            bin_file.truncate()
            tamanho_total = bin_file.tell()
            bin_file.seek(8)
            bin_file.write(struct.pack(endiam, tamanho_total))
        
        return True
    except Exception as e:
        messagebox.showerror("Erro", f"Erro na conversão reversa: {str(e)}")
        return False


def convert_txt_to_msg():
    arquivo_txt = filedialog.askopenfilename(
        title="Selecione o arquivo .txt",
        filetypes=[("Arquivos TXT", "*.txt"), ("Todos os arquivos", "*.*")]
    )
    if not arquivo_txt:
        return

    # Primeiro tenta com a extensão .msg
    arquivo_bin_com_ext = os.path.splitext(arquivo_txt)[0] + '.msg'
    
    # Se não existir, tenta sem extensão
    if not os.path.exists(arquivo_bin_com_ext):
        arquivo_bin_sem_ext = os.path.splitext(arquivo_txt)[0]
        if os.path.exists(arquivo_bin_sem_ext):
            arquivo_bin = arquivo_bin_sem_ext
        else:
            arquivo_bin = arquivo_bin_com_ext
    else:
        arquivo_bin = arquivo_bin_com_ext

    if converter_txt_para_binario(arquivo_txt, arquivo_bin):
        messagebox.showinfo("Sucesso", f"Arquivo recriado:\n{arquivo_bin}")