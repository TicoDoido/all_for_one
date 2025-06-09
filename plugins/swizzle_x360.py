# Swizzle code from REVERSE BOX https://github.com/bartlomiejduda/ReverseBox
from tkinter import filedialog, messagebox
import os

# no topo do seu plugin.py
logger = print
get_option = lambda name: None  # stub até receber do host

def register_plugin(log_func, option_getter):
    global logger, get_option
    # atribui o logger e a função de consulta de opções vindos do host
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
                "values": ["DXT5"]
            },
        ],
        "commands": [
            {"label": "Selecionar DDS", "action": choose_and_process},
        ]
    }

def _xg_address_2d_tiled(block_index: int, width_in_blocks: int, texel_byte_pitch: int) -> int:
    aligned_width = (width_in_blocks + 31) & ~31
    log_bpp = (texel_byte_pitch >> 2) + ((texel_byte_pitch >> 1) >> (texel_byte_pitch >> 2))
    offset_byte = block_index << log_bpp
    offset_tile = (((offset_byte & ~0xFFF) >> 3) +
                   ((offset_byte & 0x700) >> 2) +
                   (offset_byte & 0x3F))
    offset_macro = offset_tile >> (7 + log_bpp)
    macro_x = (offset_macro % (aligned_width >> 5)) << 2
    macro_y = (offset_macro // (aligned_width >> 5)) << 2

    tile_x = (((offset_tile >> (5 + log_bpp)) & 2) + (offset_byte >> 6)) & 3
    tile_y = ((offset_tile >> (6 + log_bpp)) & 1) + ((offset_byte & 0x800) >> 10)

    micro_x = ((((offset_tile >> 1) & ~0xF) + (offset_tile & 0xF)) &
               ((texel_byte_pitch << 3) - 1)) >> log_bpp
    micro_y = (((offset_tile & ((texel_byte_pitch << 6) - 1 & ~0x1F)) +
               ((offset_tile & 0xF) << 1)) >> (3 + log_bpp)) & ~1
    micro_y += (offset_tile & 0x10) >> 4

    x = (macro_x + tile_x) << 3
    y = (macro_y + tile_y) << 3
    x += micro_x
    y += micro_y

    return y * width_in_blocks + x

def _convert_x360_image_data(image_data: bytes, width: int, height: int, block_pixel_size: int, texel_byte_pitch: int, swizzle: bool) -> bytes:
    width_in_blocks = width // block_pixel_size
    height_in_blocks = height // block_pixel_size
    num_blocks = width_in_blocks * height_in_blocks

    converted = bytearray(len(image_data))

    for block_index in range(num_blocks):
        swizzled_index = _xg_address_2d_tiled(block_index, width_in_blocks, texel_byte_pitch)

        src_offset = block_index * texel_byte_pitch
        dst_offset = swizzled_index * texel_byte_pitch

        if dst_offset + texel_byte_pitch > len(image_data) or src_offset + texel_byte_pitch > len(image_data):
            continue

        if not swizzle:
            converted[dst_offset:dst_offset+texel_byte_pitch] = image_data[src_offset:src_offset+texel_byte_pitch]
        else:
            converted[src_offset:src_offset+texel_byte_pitch] = image_data[dst_offset:dst_offset+texel_byte_pitch]

    return converted

def swap_byte_order_x360(image_data: bytes) -> bytes:
    if len(image_data) % 2 != 0:
        raise Exception("Data size must be a multiple of 2 bytes!")

    swapped = bytearray()
    for i in range(0, len(image_data), 2):
        swapped.extend(image_data[i:i+2][::-1])
    return swapped

def unswizzle_x360(image_data: bytes, width: int, height: int, block_pixel_size: int = 4, texel_byte_pitch: int = 16) -> bytes:
    image_data = image_data[: (width // block_pixel_size) * (height // block_pixel_size) * texel_byte_pitch]
    swapped = swap_byte_order_x360(image_data)
    return _convert_x360_image_data(swapped, width, height, block_pixel_size, texel_byte_pitch, swizzle=False)

def swizzle_x360(image_data: bytes, width: int, height: int, block_pixel_size: int = 4, texel_byte_pitch: int = 16) -> bytes:
    image_data = image_data[: (width // block_pixel_size) * (height // block_pixel_size) * texel_byte_pitch]
    swapped = swap_byte_order_x360(image_data)
    return _convert_x360_image_data(swapped, width, height, block_pixel_size, texel_byte_pitch, swizzle=True)

def choose_and_process(_=None):
    mode = get_option("var_mode")
    fmt  = get_option("var_format")

    file_path = filedialog.askopenfilename(filetypes=[("DDS files", "*.dds")])
    if not file_path:
        return

    try:
        with open(file_path, "rb") as f:
            dds_data = f.read()

        header = dds_data[:128]
        image_data = dds_data[128:]

        width = int.from_bytes(header[16:20], byteorder="little")
        height = int.from_bytes(header[12:16], byteorder="little")

        block_pixel_size = 4
        texel_byte_pitch = 16

        if mode == "Swizzle":
            new_data = swizzle_x360(image_data, width, height, block_pixel_size, texel_byte_pitch)
            out_path = file_path
        else:
            new_data = unswizzle_x360(image_data, width, height, block_pixel_size, texel_byte_pitch)
            out_path = file_path

        with open(out_path, "wb") as f:
            f.write(header + new_data)

        logger(f"File saved as: {out_path}")
        messagebox.showinfo("Success", f"File saved as:\n{out_path}")

    except Exception as e:
        logger(f"Error processing DDS: {e}")
        messagebox.showerror("Error", f"Failed to process DDS:\n{e}")
