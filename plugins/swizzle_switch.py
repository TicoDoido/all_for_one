# Swizzle code for Nintendo Switch (adapted from REVERSE BOX plugin)
from tkinter import filedialog, messagebox
import os
import threading

# Dicionários de tradução do plugin
plugin_translations = {
    "pt_BR": {
        "plugin_name": "SWIZZLER para Nintendo Switch",
        "plugin_description": "Aplica ou retira o Swizzle de texturas do Nintendo Switch.",
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
        "plugin_name": "Nintendo Switch Swizzler",
        "plugin_description": "Apply or remove Switch texture swizzle.",
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
        "plugin_name": "SWIZZLER para Nintendo Switch",
        "plugin_description": "Aplica o quita el Swizzle de Nintendo Switch.",
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

# Variáveis globais
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
                {"name": "var_format", "label": translate("format_label"),    "values": ["DXT1", "DXT3", "DXT5", "RGBA8888", "BC7"]}
            ],
            "commands": [
                {"label": translate("select_file"), "action": choose_and_process}
            ]
        }
    return get_plugin_info


# ============================================================
# Nintendo Switch Swizzle / Unswizzle (GOB layout)
# ============================================================

def _convert_switch(input_image_data: bytes, img_width: int, img_height: int,
                    bytes_per_block: int = 4, block_height: int = 8,
                    width_pad: int = 8, height_pad: int = 8, swizzle_flag: bool = False):
    converted_data = bytearray(len(input_image_data))
    if img_width % width_pad or img_height % height_pad:
        width_show = img_width
        height_show = img_height
        img_width = width_real = ((img_width + width_pad - 1) // width_pad) * width_pad
        img_height = height_real = ((img_height + height_pad - 1) // height_pad) * height_pad
    else:
        width_show = width_real = img_width
        height_show = height_real = img_height

    image_width_in_gobs = img_width * bytes_per_block // 64

    for Y in range(img_height):
        for X in range(img_width):
            Z = Y * img_width + X
            gob_address = (Y // (8 * block_height)) * 512 * block_height * image_width_in_gobs + \
                          (X * bytes_per_block // 64) * 512 * block_height + \
                          (Y % (8 * block_height) // 8) * 512
            Xb = X * bytes_per_block
            address = gob_address + ((Xb % 64) // 32) * 256 + ((Y % 8) // 2) * 64 + \
                      ((Xb % 32) // 16) * 32 + (Y % 2) * 16 + (Xb % 16)

            if not swizzle_flag:
                converted_data[Z * bytes_per_block:(Z + 1) * bytes_per_block] = \
                    input_image_data[address:address + bytes_per_block]
            else:
                converted_data[address:address + bytes_per_block] = \
                    input_image_data[Z * bytes_per_block:(Z + 1) * bytes_per_block]

    # Crop (caso tenha padding)
    if width_show != width_real or height_show != height_real:
        crop = bytearray(width_show * height_show * bytes_per_block)
        for Y in range(height_show):
            offset_in = Y * width_real * bytes_per_block
            offset_out = Y * width_show * bytes_per_block
            if not swizzle_flag:
                crop[offset_out:offset_out + width_show * bytes_per_block] = \
                    converted_data[offset_in:offset_in + width_show * bytes_per_block]
            else:
                crop[offset_in:offset_in + width_show * bytes_per_block] = \
                    converted_data[offset_out:offset_out + width_show * bytes_per_block]
        converted_data = crop

    return converted_data


def unswizzle_switch(input_image_data: bytes, img_width: int, img_height: int,
                     bytes_per_block: int = 4, block_height: int = 8,
                     width_pad: int = 8, height_pad: int = 8) -> bytes:
    return _convert_switch(input_image_data, img_width, img_height, bytes_per_block, block_height, width_pad, height_pad, False)


def swizzle_switch(input_image_data: bytes, img_width: int, img_height: int,
                   bytes_per_block: int = 4, block_height: int = 8,
                   width_pad: int = 8, height_pad: int = 8) -> bytes:
    return _convert_switch(input_image_data, img_width, img_height, bytes_per_block, block_height, width_pad, height_pad, True)


# ============================================================
# GUI File Chooser and Processor
# ============================================================

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
                hdr = f.read(148) if fmt == "RGBA8888" else f.read(128)
                w = int.from_bytes(hdr[16:20], 'little')
                h = int.from_bytes(hdr[12:16], 'little')
                data = f.read()

            logger(translate("processing", name=os.path.basename(path), width=w, height=h))

            format_map = {
                "DXT1": 8,
                "DXT3": 16,
                "DXT5": 16,
                "RGBA8888": 4,
                "BC7": 8
            }

            bpp = format_map.get(fmt)
            if bpp is None:
                raise ValueError(translate("unsupported_format", fmt=fmt))

            if mode == translate("swizzle"):
                new_data = swizzle_switch(data, w, h, bpp)
            else:
                new_data = unswizzle_switch(data, w, h, bpp)

            with open(path, "wb") as f:
                f.write(hdr + new_data)

            messagebox.showinfo(translate("success_title"), translate("success_message", path=path))

        except Exception as e:
            logger(e)
            messagebox.showerror(translate("error_title"), translate("error_message", error=str(e)))

    threading.Thread(target=task, daemon=True).start()
