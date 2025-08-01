import os
import struct
import zlib
import math
import re
from pathlib import Path
from tkinter import filedialog, messagebox

# Logger padrão substituído na integração
logger = print
get_option = lambda name: None

def register_plugin(log_func, option_getter):
    global logger, get_option
    logger     = log_func or print
    get_option = option_getter or (lambda name: None)
    
    return {
        "name": ".dat Angry Birds Trilogy para arquyivos de texto",
        "description": "Extrai e reinsere strings .loc em arquivos .dat Angry Birds Trilogy",
        "commands": [
            {"label": "Extrair Strings", "action": extract_command},
            {"label": "Reinserir Strings", "action": reinsert_command}
        ]
    }

# --- Constantes ---
HEADER_SIZE = 0x30
ALIGN       = 0x40
RAWM_TAG    = b'RAWM'
MARKER      = b'\xFA\xD8\xC1\x68'
ID_TAG      = b'KSP0'

LOC_HEADER_SIZE = 0x10
LOC_ID_TAG      = 0x10
LOC_STRING_TERM = b'\x00'

# --- Funções para GUI ---
def extract_command():
    file_path = filedialog.askopenfilename(title="Selecione o arquivo .dat", filetypes=[("Arquivos .dat", "*.dat")])
    if not file_path:
        return
    try:
        extract(Path(file_path))
        messagebox.showinfo("Sucesso", f"Arquivo extraído com sucesso: {Path(file_path).with_suffix('.txt')}")
    except Exception as e:
        logger(f"[ERRO] {e}")
        messagebox.showerror("Erro", f"Erro durante extração: {e}")

def reinsert_command():
    file_path = filedialog.askopenfilename(title="Selecione o arquivo .dat", filetypes=[("Arquivos .dat", "*.dat")])
    if not file_path:
        return
    try:
        reinsert(Path(file_path))
        out_file = Path(file_path).with_name(f"{Path(file_path).stem}_mod.dat")
        messagebox.showinfo("Sucesso", f"Arquivo modificado salvo em: {out_file}")
    except Exception as e:
        logger(f"[ERRO] {e}")
        messagebox.showerror("Erro", f"Erro durante reinserção: {e}")

# --- Funções LOC ---
def parse_loc_to_txt_lines(loc_data: bytes) -> list[str]:
    loc_id = struct.unpack('>I', loc_data[0:4])[0]
    if loc_id != LOC_ID_TAG:
        raise ValueError(f"ID inválido no .loc. Esperado {LOC_ID_TAG}, encontrado {loc_id}")
    
    txt_lines = []
    cursor = LOC_HEADER_SIZE
    while cursor < len(loc_data):
        hash_val = struct.unpack('>I', loc_data[cursor:cursor+4])[0]
        num_tags = struct.unpack('>H', loc_data[cursor+4:cursor+6])[0]
        cursor += 6 + (num_tags * 4)

        str_end = loc_data.find(LOC_STRING_TERM, cursor)
        if str_end == -1:
            raise ValueError(f"String não terminada após 0x{cursor:X}")
        
        string_bytes = loc_data[cursor:str_end]
        decoded_string = string_bytes.decode('utf-8')
        cursor = str_end + 1
        
        processed = decoded_string.replace('\n', '<nl>')
        txt_lines.append(f"{hash_val:08X} = {processed}")
    
    return txt_lines

def build_loc_from_txt(txt: str) -> bytes:
    body = bytearray()
    tag_pattern = re.compile(b'<<.*?>>')

    for i, line in enumerate(txt.splitlines(), 1):
        if not line.strip() or line.strip().startswith('#'):
            continue
        
        parts = line.split('=', 1)
        if len(parts) != 2:
            raise ValueError(f"Formato inválido na linha {i}: {line}")
        
        try:
            hash_val = int(parts[0].strip(), 16)
        except ValueError:
            raise ValueError(f"Hash inválido na linha {i}: {parts[0]}")

        final_str = parts[1].strip().replace('<nl>', '\n')
        encoded = final_str.encode('utf-8')
        
        tag_positions = []
        for match in tag_pattern.finditer(encoded):
            tag_positions.extend([match.start(), match.end()])

        body.extend(struct.pack('>I', hash_val))
        body.extend(struct.pack('>H', len(tag_positions) // 2))
        if tag_positions:
            body.extend(struct.pack(f'>{len(tag_positions)}H', *tag_positions))
        body.extend(encoded + LOC_STRING_TERM)
    
    header = struct.pack('>II', LOC_ID_TAG, LOC_HEADER_SIZE + len(body)) + b'\x00' * 8
    return header + body

# --- Manipulação de .dat ---
def find_chunk_offset(data: bytes) -> int:
    pos_rawm = data.find(RAWM_TAG)
    if pos_rawm < 0: raise ValueError("RAWM não encontrado")
    pos_marker = data.find(MARKER, pos_rawm + len(RAWM_TAG))
    if pos_marker < 0: raise ValueError("MARKER não encontrado após RAWM")
    count = struct.unpack('>I', data[pos_marker+len(MARKER):pos_marker+len(MARKER)+4])[0]
    return count * ALIGN

def detect_patch(data: bytes) -> int | None:
    return max([off for off in range(0, len(data), ALIGN) if data[off:off+4] == ID_TAG and data[off+0x10:off+0x14] == ID_TAG], default=None)

def extract(input_path: Path):
    data = input_path.read_bytes()
    off = find_chunk_offset(data)
    header = data[off:off+HEADER_SIZE]
    comp_size = struct.unpack('>I', header[4:8])[0]
    comp_data = data[off+HEADER_SIZE:off+HEADER_SIZE+comp_size]

    try:
        decomp_data = zlib.decompress(comp_data, -zlib.MAX_WBITS)
    except zlib.error:
        decomp_data = zlib.decompress(comp_data)
    
    txt_lines = parse_loc_to_txt_lines(decomp_data)
    txt_path = input_path.with_suffix('.txt')
    txt_path.write_text('\n'.join(txt_lines) + '\n', encoding='utf-8')
    logger(f"Extração concluída: {txt_path}")

def reinsert(input_path: Path):
    raw_data = input_path.read_bytes()
    orig_off = find_chunk_offset(raw_data)
    header_original = raw_data[orig_off:orig_off+HEADER_SIZE]
    data = raw_data
    p_off = detect_patch(data)
    if p_off is not None:
        data = data[:p_off]
    prefix = bytearray(data)

    txt_path = input_path.with_suffix('.txt')
    if not txt_path.exists():
        raise FileNotFoundError(f"Arquivo .txt não encontrado: {txt_path}")
    
    txt_content = txt_path.read_text(encoding='utf-8')
    loc_data = build_loc_from_txt(txt_content)

    comp_data = zlib.compress(loc_data, -zlib.MAX_WBITS) + b'\x00\x01'
    comp_size, decomp_size = len(comp_data), len(loc_data)
    pad1 = (-len(prefix)) % ALIGN
    new_offset = len(prefix) + pad1
    new_count = new_offset // ALIGN

    pos_rawm = prefix.find(RAWM_TAG)
    pos_marker = prefix.find(MARKER, pos_rawm + len(RAWM_TAG))
    count_pos = pos_marker + len(MARKER)
    prefix[count_pos:count_pos+4] = struct.pack('>I', new_count)
    prefix.extend(b'\x00' * pad1)

    new_chunk_count = math.ceil((HEADER_SIZE + comp_size) / ALIGN)
    header = bytearray(header_original)
    header[0:4] = header[0x10:0x14] = ID_TAG
    header[4:8] = struct.pack('>I', comp_size)
    header[8:12] = struct.pack('>I', decomp_size)
    header[12:16] = struct.pack('>I', new_chunk_count)

    buf = prefix + header + comp_data
    buf.extend(b'\x00' * ((-len(buf)) % ALIGN))

    out_path = input_path.with_name(f"{input_path.stem}_mod{input_path.suffix}")
    out_path.write_bytes(buf)
    logger(f"Reinserção concluída: {out_path}")
