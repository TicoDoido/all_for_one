import os
import threading
from tkinter import filedialog, messagebox

# Dicionários de tradução do plugin
plugin_translations = {
    "pt_BR": {
        "plugin_name": "SWIZZLER para Xbox 360",
        "plugin_description": "Aplica ou retira o Swizzle de Xbox 360.",
        "operation_label": "Operação",
        "format_label": "Formato do DDS",
        "swizzle": "Swizzle",
        "unswizzle": "Unswizzle",
        "select_file": "Selecionar DDS",
        "dds_files": "Arquivos DDS",
        "all_files": "Todos os arquivos",
        "processing": "Processando: {name} ({width}x{height})",
        "success_title": "Sucesso",
        "success_message": "Arquivo salvo em:\n{path}",
        "error_title": "Erro",
        "error_message": "Falha ao processar o arquivo:\n{error}",
        "unsupported_format": "Formato não suportado: {fmt}"
    },
    "en_US": {
        "plugin_name": "Xbox360 Swizzler",
        "plugin_description": "Apply or remove Xbox 360 texture swizzle.",
        "operation_label": "Operation",
        "format_label": "DDS Format",
        "swizzle": "Swizzle",
        "unswizzle": "Unswizzle",
        "select_file": "Select DDS file",
        "dds_files": "DDS files",
        "all_files": "All files",
        "processing": "Processing: {name} ({width}x{height})",
        "success_title": "Success",
        "success_message": "File saved at:\n{path}",
        "error_title": "Error",
        "error_message": "Failed to process file:\n{error}",
        "unsupported_format": "Unsupported format: {fmt}"
    },
    "es_ES": {
        "plugin_name": "SWIZZLER para Xbox 360",
        "plugin_description": "Aplica o quita el Swizzle de Xbox 360.",
        "operation_label": "Operación",
        "format_label": "Formato DDS",
        "swizzle": "Swizzle",
        "unswizzle": "Unswizzle",
        "select_file": "Seleccionar DDS",
        "dds_files": "Archivos DDS",
        "all_files": "Todos los archivos",
        "processing": "Procesando: {name} ({width}x{height})",
        "success_title": "Éxito",
        "success_message": "Archivo guardado en:\n{path}",
        "error_title": "Error",
        "error_message": "Error al procesar el archivo:\n{error}",
        "unsupported_format": "Formato no soportado: {fmt}"
    }
}

# Variáveis globais do plugin
logger = print
get_option = lambda name: None
current_language = "pt_BR"

def translate(key, **kwargs):
    lang = plugin_translations.get(current_language, plugin_translations["pt_BR"])
    text = lang.get(key, key)
    return text.format(**kwargs) if kwargs else text


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
                {"name": "var_format", "label": translate("format_label"),    "values": ["DXT1", "DXT3", "DXT5", "RGBA8888"]}
            ],
            "commands": [
                {"label": translate("select_file"), "action": choose_and_process}
            ]
        }
    return get_plugin_info


def swap_byte_order_x360(data: bytes) -> bytes:
    paired = bytearray(data)
    for i in range(0, len(paired) & ~1, 2):
        paired[i], paired[i+1] = paired[i+1], paired[i]
    return bytes(paired)


def _xg_address_2d_tiled_x(off, w_blocks, pitch):
    aligned = (w_blocks + 31) & ~31
    log_bpp = (pitch >> 2) + ((pitch >> 1) >> (pitch >> 2))
    ob = off << log_bpp
    ot = (((ob & ~0xFFF) >> 3) + ((ob & 0x700) >> 2) + (ob & 0x3F))
    om = ot >> (7 + log_bpp)
    mx = (om % (aligned >> 5)) << 2
    tile = (((ot >> (5 + log_bpp)) & 2) + (ob >> 6)) & 3
    return ((mx + tile) << 3) + ((((ot >> 1) & ~0xF) + (ot & 0xF)) & ((pitch << 3) - 1)) >> log_bpp


def _xg_address_2d_tiled_y(off, w_blocks, pitch):
    aligned = (w_blocks + 31) & ~31
    log_bpp = (pitch >> 2) + ((pitch >> 1) >> (pitch >> 2))
    ob = off << log_bpp
    ot = (((ob & ~0xFFF) >> 3) + ((ob & 0x700) >> 2) + (ob & 0x3F))
    om = ot >> (7 + log_bpp)
    my = (om // (aligned >> 5)) << 2
    tile = ((ot >> (6 + log_bpp)) & 1) + ((ob & 0x800) >> 10)
    return (my + tile) << 3 | (((ot & ((pitch << 6) - 1 & ~0x1F)) + ((ot & 0xF) << 1)) >> (3 + log_bpp)) & ~1 | ((ot & 0x10) >> 4)


def _convert_x360(data, w, h, bps, pitch, swizz):
    wb = w // bps; hb = h // bps
    pb = (wb + 31) & ~31; ph = (hb + 31) & ~31
    total = pb * ph
    out = bytearray((total if swizz else wb*hb) * pitch)
    for off in range(total):
        x = _xg_address_2d_tiled_x(off, pb, pitch)
        y = _xg_address_2d_tiled_y(off, pb, pitch)
        if x < wb and y < hb:
            if not swizz:
                out[(y*wb+x)*pitch:(y*wb+x+1)*pitch] = data[off*pitch:(off+1)*pitch]
            else:
                out[off*pitch:(off+1)*pitch] = data[(y*wb+x)*pitch:(y*wb+x+1)*pitch]
    return bytes(out)


def swizzle_x360(data: bytes, w: int, h: int, bps=4, pitch=8) -> bytes:
    return _convert_x360(swap_byte_order_x360(data), w, h, bps, pitch, True)


def unswizzle_x360(data: bytes, w: int, h: int, bps=4, pitch=8) -> bytes:
    return _convert_x360(swap_byte_order_x360(data), w, h, bps, pitch, False)


def choose_and_process():
    mode = get_option("var_mode")
    fmt = get_option("var_format")
    path = filedialog.askopenfilename(
        title=translate("select_file"),
        filetypes=[(translate("dds_files"), "*.dds"), (translate("all_files"), "*.*")]
    )
    if not path:
        return

    def task():
        try:
            with open(path, "rb") as f:
                hdr = f.read(128)
                w = int.from_bytes(hdr[16:20], 'little')
                h = int.from_bytes(hdr[12:16], 'little')
                data = f.read()
            logger(translate("processing", name=os.path.basename(path), width=w, height=h))
            pitch_map = {"DXT1":8, "DXT3":16, "DXT5":16, "RGBA8888":64}
            pitch = pitch_map.get(fmt) or (_ for _ in ()).throw(ValueError(translate("unsupported_format", fmt=fmt)))
            new = swizzle_x360(data, w, h, 4, pitch) if mode==translate("swizzle") else unswizzle_x360(data, w, h, 4, pitch)
            with open(path, "wb") as f:
                f.write(hdr + new)
            messagebox.showinfo(translate("success_title"), translate("success_message", path=path))
        except Exception as e:
            logger(e)
            messagebox.showerror(translate("error_title"), translate("error_message", error=str(e)))
    threading.Thread(target=task, daemon=True).start()
