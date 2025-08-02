import os
import struct
import threading
from tkinter import filedialog, messagebox

# Dicionários de tradução do plugin
plugin_translations = {
    "pt_BR": {
        "plugin_name": "SWIZZLER para PS4",
        "plugin_description": "Aplica ou retira o Swizzle de PS4 (MORTON).",
        "operation_label": "Operação",
        "format_label": "Formato do DDS",
        "swizzle": "Swizzle",
        "unswizzle": "Unswizzle",
        "select_file": "Selecionar DDS",
        "dds_files": "Arquivos DDS",
        "all_files": "Todos os arquivos",
        "success_title": "Sucesso",
        "success_message": "Arquivo salvo em:\n{path}",
        "error_title": "Erro",
        "error_message": "{error}",
        "unsupported_format": "Formato não suportado: {fmt}"
    },
    "en_US": {
        "plugin_name": "PS4 Swizzler",
        "plugin_description": "Apply or remove PS4 Morton swizzle.",
        "operation_label": "Operation",
        "format_label": "DDS Format",
        "swizzle": "Swizzle",
        "unswizzle": "Unswizzle",
        "select_file": "Select DDS file",
        "dds_files": "DDS files",
        "all_files": "All files",
        "success_title": "Success",
        "success_message": "File saved at:\n{path}",
        "error_title": "Error",
        "error_message": "{error}",
        "unsupported_format": "Unsupported format: {fmt}"
    },
    "es_ES": {
        "plugin_name": "SWIZZLER para PS4",
        "plugin_description": "Aplica o quita el Swizzle de PS4 (MORTON).",
        "operation_label": "Operación",
        "format_label": "Formato DDS",
        "swizzle": "Swizzle",
        "unswizzle": "Unswizzle",
        "select_file": "Seleccionar DDS",
        "dds_files": "Archivos DDS",
        "all_files": "Todos los archivos",
        "success_title": "Éxito",
        "success_message": "Archivo guardado en:\n{path}",
        "error_title": "Error",
        "error_message": "{error}",
        "unsupported_format": "Formato no soportado: {fmt}"
    }
}

# Variáveis globais do plugin
logger = print
get_option = lambda name: None
current_language = "pt_BR"

def translate(key, **kwargs):
    lang_dict = plugin_translations.get(current_language, plugin_translations["pt_BR"])
    text = lang_dict.get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except:
            return text
    return text


def register_plugin(log_func, option_getter, host_language="pt_BR"):
    global logger, get_option, current_language
    logger = log_func or print
    get_option = option_getter or (lambda name: None)
    current_language = host_language

    def get_plugin_info():
        return {
            "name": translate("plugin_name"),
            "description": translate("plugin_description"),
            "options": [
                {"name": "var_mode",   "label": translate("operation_label"), "values": [translate("swizzle"), translate("unswizzle")]},
                {"name": "var_format", "label": translate("format_label"),    "values": ["DXT1", "DXT5", "BC7", "BGRA 8888"]}
            ],
            "commands": [
                {"label": translate("select_file"), "action": choose_and_process}
            ]
        }

    return get_plugin_info


def calculate_morton_index_ps4(t: int, w: int, h: int) -> int:
    num1 = num2 = 1
    num3 = num4 = 0
    img_w, img_h = w, h
    while img_w > 1 or img_h > 1:
        if img_w > 1:
            num3 += num2 * (t & 1)
            t >>= 1
            num2 <<= 1
            img_w >>= 1
        if img_h > 1:
            num4 += num1 * (t & 1)
            t >>= 1
            num1 <<= 1
            img_h >>= 1
    return num4 * w + num3


def swizzle_ps4(data: bytes, width: int, height: int, block_width=4, block_height=4, block_size=16) -> bytes:
    out = bytearray(len(data))
    src = 0
    w_blocks = width  // block_width
    h_blocks = height // block_height
    for y in range((h_blocks + 7) // 8):
        for x in range((w_blocks + 7) // 8):
            for t in range(64):
                morton = calculate_morton_index_ps4(t, 8, 8)
                dy, dx = divmod(morton, 8)
                if (x*8+dx)<w_blocks and (y*8+dy)<h_blocks:
                    dst = block_size * ((y*8+dy)*w_blocks + (x*8+dx))
                    out[src:src+block_size] = data[dst:dst+block_size]
                    src += block_size
    return out


def unswizzle_ps4(data: bytes, width: int, height: int, block_width=4, block_height=4, block_size=16) -> bytes:
    out = bytearray(len(data))
    src = 0
    w_blocks = width  // block_width
    h_blocks = height // block_height
    for y in range((h_blocks + 7) // 8):
        for x in range((w_blocks + 7) // 8):
            for t in range(64):
                morton = calculate_morton_index_ps4(t, 8, 8)
                dy, dx = divmod(morton, 8)
                if (x*8+dx)<w_blocks and (y*8+dy)<h_blocks:
                    dst = block_size * ((y*8+dy)*w_blocks + (x*8+dx))
                    out[dst:dst+block_size] = data[src:src+block_size]
                    src += block_size
    return out


def round_up_multiple(val: int, mult: int) -> int:
    return ((val + mult - 1) // mult) * mult


def process_file(input_path: str, output_path: str, mode: str, fmt: str):
    # Define tamanhos por formato
    if fmt == "DXT1":
        block_size, header = 8, 128
    elif fmt == "DXT5":
        block_size, header = 16, 128
    elif fmt == "BC7":
        block_size, header = 16, 148
    elif fmt == "BGRA 8888":
        block_size, header = 16, 148
    else:
        raise ValueError(translate("unsupported_format", fmt=fmt))

    with open(input_path, "rb") as f:
        hdr = f.read(header)
        height = int.from_bytes(hdr[12:16], 'little')
        width  = int.from_bytes(hdr[16:20], 'little')
        data   = f.read()

    aligned_w = round_up_multiple(width,  32)
    aligned_h = round_up_multiple(height, 32)
    unit_sz = block_size if fmt != "BGRA 8888" else 4
    block_w = block_h = 4 if fmt != "BGRA 8888" else 1
    w_blocks = aligned_w  // block_w
    h_blocks = aligned_h // block_h
    orig_wb  = width  // block_w
    orig_hb  = height // block_h

    padded = bytearray(w_blocks * h_blocks * unit_sz)
    for y in range(orig_hb):
        src_o = y * orig_wb * unit_sz
        dst_o = y * w_blocks * unit_sz
        padded[dst_o:dst_o+orig_wb*unit_sz] = data[src_o:src_o+orig_wb*unit_sz]

    if mode == translate("swizzle"):
        full = swizzle_ps4(padded, aligned_w, aligned_h, block_size=unit_sz)
    else:
        full = unswizzle_ps4(padded, aligned_w, aligned_h, block_size=unit_sz)

    result = bytearray(orig_wb * orig_hb * unit_sz)
    for y in range(orig_hb):
        src_o = y * w_blocks * unit_sz
        dst_o = y * orig_wb * unit_sz
        result[dst_o:dst_o+orig_wb*unit_sz] = full[src_o:src_o+orig_wb*unit_sz]

    with open(output_path, "wb") as out_f:
        out_f.write(hdr)
        out_f.write(result)


def choose_and_process():
    mode = get_option("var_mode")
    fmt  = get_option("var_format")
    path = filedialog.askopenfilename(
        title=translate("select_file"),
        filetypes=[(translate("dds_files"), "*.dds"), (translate("all_files"), "*.*")]
    )
    if not path:
        return

    try:
        threading.Thread(target=process_file, args=(path, path, mode, fmt), daemon=True).start()
        messagebox.showinfo(translate("success_title"), translate("success_message", path=path))
    except Exception as e:
        messagebox.showerror(translate("error_title"), translate("error_message", error=str(e)))
