# Swizzle code from REVERSE BOX https://github.com/bartlomiejduda/ReverseBox
from tkinter import filedialog, messagebox
import os
import threading

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

def swap_byte_order_x360(image_data: bytes) -> bytes:
    if len(image_data) % 2 != 0:
        pass

    swapped = bytearray(image_data)
    for i in range(0, len(swapped) & ~1, 2):
        swapped[i], swapped[i+1] = swapped[i+1], swapped[i]
    return bytes(swapped)

def _xg_address_2d_tiled_x(block_offset: int, width_in_blocks: int, texel_byte_pitch: int) -> int:
    aligned_width: int = (width_in_blocks + 31) & ~31
    log_bpp: int = (texel_byte_pitch >> 2) + ((texel_byte_pitch >> 1) >> (texel_byte_pitch >> 2))
    offset_byte: int = block_offset << log_bpp
    offset_tile: int = (((offset_byte & ~0xFFF) >> 3) + ((offset_byte & 0x700) >> 2) + (offset_byte & 0x3F))
    offset_macro: int = offset_tile >> (7 + log_bpp)

    macro_x: int = (offset_macro % (aligned_width >> 5)) << 2
    tile: int = (((offset_tile >> (5 + log_bpp)) & 2) + (offset_byte >> 6)) & 3
    macro: int = (macro_x + tile) << 3
    micro: int = ((((offset_tile >> 1) & ~0xF) + (offset_tile & 0xF)) & ((texel_byte_pitch << 3) - 1)) >> log_bpp

    return macro + micro


def _xg_address_2d_tiled_y(block_offset: int, width_in_blocks: int, texel_byte_pitch: int) -> int:
    aligned_width: int = (width_in_blocks + 31) & ~31
    log_bpp: int = (texel_byte_pitch >> 2) + ((texel_byte_pitch >> 1) >> (texel_byte_pitch >> 2))
    offset_byte: int = block_offset << log_bpp
    offset_tile: int = (((offset_byte & ~0xFFF) >> 3) + ((offset_byte & 0x700) >> 2) + (offset_byte & 0x3F))
    offset_macro: int = offset_tile >> (7 + log_bpp)

    macro_y: int = (offset_macro // (aligned_width >> 5)) << 2
    tile: int = ((offset_tile >> (6 + log_bpp)) & 1) + ((offset_byte & 0x800) >> 10)
    macro: int = (macro_y + tile) << 3
    micro: int = (((offset_tile & ((texel_byte_pitch << 6) - 1 & ~0x1F)) + ((offset_tile & 0xF) << 1)) >> (3 + log_bpp)) & ~1

    return macro + micro + ((offset_tile & 0x10) >> 4)


def _convert_x360_image_data(image_data: bytes, image_width: int, image_height: int, block_pixel_size: int, texel_byte_pitch: int, swizzle_flag: bool) -> bytes:
    width_in_blocks: int = image_width // block_pixel_size
    height_in_blocks: int = image_height // block_pixel_size

    padded_width_in_blocks: int = (width_in_blocks + 31) & ~31
    padded_height_in_blocks: int = (height_in_blocks + 31) & ~31
    total_padded_blocks = padded_width_in_blocks * padded_height_in_blocks

    if not swizzle_flag:
        converted_data: bytearray = bytearray(width_in_blocks * height_in_blocks * texel_byte_pitch)
    else:
        converted_data: bytearray = bytearray(total_padded_blocks * texel_byte_pitch)

    for block_offset in range(total_padded_blocks):
        x = _xg_address_2d_tiled_x(block_offset, padded_width_in_blocks, texel_byte_pitch)
        y = _xg_address_2d_tiled_y(block_offset, padded_width_in_blocks, texel_byte_pitch)

        if x < width_in_blocks and y < height_in_blocks:
            if not swizzle_flag:
                src_byte_offset = block_offset * texel_byte_pitch
                dest_byte_offset = (y * width_in_blocks + x) * texel_byte_pitch
                if src_byte_offset + texel_byte_pitch <= len(image_data):
                    converted_data[dest_byte_offset: dest_byte_offset + texel_byte_pitch] = image_data[src_byte_offset: src_byte_offset + texel_byte_pitch]
            else:
                src_byte_offset = (y * width_in_blocks + x) * texel_byte_pitch
                dest_byte_offset = block_offset * texel_byte_pitch
                if src_byte_offset + texel_byte_pitch <= len(image_data):
                    converted_data[dest_byte_offset: dest_byte_offset + texel_byte_pitch] = image_data[src_byte_offset: src_byte_offset + texel_byte_pitch]

    return bytes(converted_data)


def unswizzle_x360(image_data: bytes, img_width: int, img_height: int, block_pixel_size: int = 4, texel_byte_pitch: int = 8) -> bytes:
    swapped_data: bytes = swap_byte_order_x360(image_data)
    unswizzled_data: bytes = _convert_x360_image_data(swapped_data, img_width, img_height, block_pixel_size, texel_byte_pitch, False)
    return unswizzled_data


def swizzle_x360(image_data: bytes, img_width: int, img_height: int, block_pixel_size: int = 4, texel_byte_pitch: int = 8) -> bytes:
    swapped_data: bytes = swap_byte_order_x360(image_data)
    swizzled_data: bytes = _convert_x360_image_data(swapped_data, img_width, img_height, block_pixel_size, texel_byte_pitch, True)
    return swizzled_data

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
            
            format_map = {
                "DXT1": 8,
                "DXT3": 16,
                "DXT5": 16,
                "RGBA8888": 64
            }
            
            pitch = format_map.get(fmt)
            if pitch is None:
                raise ValueError(translate("unsupported_format", fmt=fmt))
            
            if mode == translate("swizzle"):
                new_data = swizzle_x360(data, w, h, 4, pitch)
            else:
                new_data = unswizzle_x360(data, w, h, 4, pitch)
                
            with open(path, "wb") as f:
                f.write(hdr + new_data)
                
            messagebox.showinfo(translate("success_title"), translate("success_message", path=path))
            
        except Exception as e:
            logger(e)
            messagebox.showerror(translate("error_title"), translate("error_message", error=str(e)))
            
    threading.Thread(target=task, daemon=True).start()