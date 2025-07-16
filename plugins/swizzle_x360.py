# Swizzle code from REVERSE BOX https://github.com/bartlomiejduda/ReverseBox
# Correção na ordem dos pixeis necessariamente múltiplo de 32 por Krisp

from tkinter import filedialog, messagebox
import os

logger = print
get_option = lambda name: None  # Stub até receber do host

def register_plugin(log_func, option_getter):
    global logger, get_option
    logger     = log_func or print
    get_option = option_getter or (lambda name: None)
            
    return {
        "name": "SWIZZLER para Xbox 360",
        "description": "Aplica ou retira o Swizzle de Xbox 360.",
        "options": [
            {
                "name": "var_mode",
                "label": "Operação",
                "values": ["Swizzle", "Unswizzle"]
            },
            {
                "name": "var_format",
                "label": "Formato do DDS",
                "values": ["DXT1", "DXT3", "DXT5", "RGBA8888"]
            },
        ],
        "commands": [
            {"label": "Selecionar DDS", "action": choose_and_process},
        ]
    }

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

def choose_and_process(_=None):
    mode = get_option("var_mode")
    fmt  = get_option("var_format")

    file_path = filedialog.askopenfilename(
        title="Selecione o arquivo .dds",
        filetypes=[("DDS files", "*.dds"), ("All files", "*.*")]
    )
    if not file_path:
        return

    try:
        with open(file_path, "rb") as f:
            dds_data = f.read()

        header = dds_data[:128]
        image_data = dds_data[128:]

        height = int.from_bytes(header[12:16], byteorder="little")
        width = int.from_bytes(header[16:20], byteorder="little")
        
        logger(f"Processando: {os.path.basename(file_path)} ({width}x{height})")
        logger(f"Operação: {mode}, Formato: {fmt}")

        block_pixel_size = 4
        
        format_map = {
            "DXT1": 8,
            "DXT3": 16,
            "DXT5": 16,
            "RGBA8888": 64
        }

        texel_byte_pitch = format_map.get(fmt)
        if texel_byte_pitch is None:
            raise ValueError(f"Formato DDS não suportado: {fmt}")
        
        if mode == "Swizzle":
            new_data = swizzle_x360(image_data, width, height, block_pixel_size, texel_byte_pitch)
        else:
            new_data = unswizzle_x360(image_data, width, height, block_pixel_size, texel_byte_pitch)

        out_path = file_path

        with open(out_path, "wb") as f:
            f.write(header + new_data)

        logger(f"Arquivo salvo com sucesso em: {out_path}")
        messagebox.showinfo("Sucesso", f"O arquivo foi processado e salvo em:\n{out_path}")

    except Exception as e:
        logger(f"Erro ao processar o arquivo DDS: {e}")
        messagebox.showerror("Erro", f"Falha ao processar o arquivo DDS:\n{e}")