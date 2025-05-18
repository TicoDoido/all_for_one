# Morton code from REVERSE BOX https://github.com/bartlomiejduda/ReverseBox
# round_up_multiple ideia from Piken (DwayneR) MANY THANKS TO BOTH !!!

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
        "name": "SWIZZLER para PS4",
        "description": "Aplica ou retira o Swizzle de PS4(MORTON).",
        "options": [
            {
                "name": "var_mode",
                "label": "Operação",
                "values": ["Swizzle", "Unswizzle"]
            },
            {
                "name": "var_format",
                "label": "Formato do DDS",
                "values": ["DXT5", "DXT1"]
            },
        ],
        "commands": [
            {"label": "Selecionar DDS", "action": choose_and_process},
        ]
    }


def calculate_morton_index_ps4(t: int, input_img_width: int, input_img_height: int) -> int:
    num1 = num2 = 1
    num3 = num4 = 0
    img_width = input_img_width
    img_height = input_img_height
    while img_width > 1 or img_height > 1:
        if img_width > 1:
            num3 += num2 * (t & 1)
            t   >>= 1
            num2 <<= 1
            img_width >>= 1
        if img_height > 1:
            num4 += num1 * (t & 1)
            t   >>= 1
            num1 <<= 1
            img_height >>= 1
    return num4 * input_img_width + num3

def swizzle_ps4(image_data: bytes, img_width: int, img_height: int,
                block_width: int = 4, block_height: int = 4, block_data_size: int = 16) -> bytes:
    swizzled = bytearray(len(image_data))
    src_idx = 0
    w_blocks = img_width  // block_width
    h_blocks = img_height // block_height

    for y in range((h_blocks + 7) // 8):
        for x in range((w_blocks + 7) // 8):
            for t in range(64):
                morton = calculate_morton_index_ps4(t, 8, 8)
                dy = morton // 8
                dx = morton % 8
                if (x*8 + dx) < w_blocks and (y*8 + dy) < h_blocks:
                    dst = block_data_size * ((y*8 + dy) * w_blocks + (x*8 + dx))
                    swizzled[src_idx:src_idx+block_data_size] = image_data[dst:dst+block_data_size]
                    src_idx += block_data_size
    return swizzled

def unswizzle_ps4(image_data: bytes, img_width: int, img_height: int,
                  block_width: int = 4, block_height: int = 4, block_data_size: int = 16) -> bytes:
    unswizzled = bytearray(len(image_data))
    src_idx = 0
    w_blocks = img_width  // block_width
    h_blocks = img_height // block_height

    for y in range((h_blocks + 7) // 8):
        for x in range((w_blocks + 7) // 8):
            for t in range(64):
                morton = calculate_morton_index_ps4(t, 8, 8)
                dy = morton // 8
                dx = morton % 8
                if (x*8 + dx) < w_blocks and (y*8 + dy) < h_blocks:
                    dst = block_data_size * ((y*8 + dy) * w_blocks + (x*8 + dx))
                    unswizzled[dst:dst+block_data_size] = image_data[src_idx:src_idx+block_data_size]
                    src_idx += block_data_size
    return unswizzled

def read_be_uint32(file, offset: int) -> int:
    file.seek(offset)
    return int.from_bytes(file.read(4), byteorder='little')

def round_up_multiple(value: int, multiple: int) -> int:
    return ((value + multiple - 1) // multiple) * multiple

def process_file(input_path: str, output_path: str, mode: str, fmt: str):
    block_data_size = 8 if fmt == "DXT1" else 16

    with open(input_path, "rb") as f:
        header = f.read(128)  # Ler cabeçalho uma única vez
        height = int.from_bytes(header[12:16], byteorder='little')
        width  = int.from_bytes(header[16:20], byteorder='little')
        data = f.read()  # Restante dos dados após o cabeçalho

    aligned_w = round_up_multiple(width, 32)
    aligned_h = round_up_multiple(height, 32)
    block_w = aligned_w // 4
    block_h = aligned_h // 4

    orig_block_w = width  // 4
    orig_block_h = height // 4

    # Cria buffer com padding (zeros)
    padded_data = bytearray(block_w * block_h * block_data_size)

    # Copia dados originais linha por linha
    for y in range(orig_block_h):
        src_offset = y * orig_block_w * block_data_size
        dst_offset = y * block_w * block_data_size
        padded_data[dst_offset : dst_offset + (orig_block_w * block_data_size)] = \
            data[src_offset : src_offset + (orig_block_w * block_data_size)]

    if mode == 'Swizzle':
        out = swizzle_ps4(padded_data, aligned_w, aligned_h,
                          block_width=4, block_height=4,
                          block_data_size=block_data_size)
    else:
        unswizzled = unswizzle_ps4(data, aligned_w, aligned_h,
                                   block_width=4, block_height=4,
                                   block_data_size=block_data_size)
        # Remove o padding após o unswizzle
        out = bytearray(orig_block_w * orig_block_h * block_data_size)
        for y in range(orig_block_h):
            src_offset = y * block_w * block_data_size
            dst_offset = y * orig_block_w * block_data_size
            out[dst_offset : dst_offset + (orig_block_w * block_data_size)] = \
                unswizzled[src_offset : src_offset + (orig_block_w * block_data_size)]

    with open(output_path, "wb") as out_f:
        out_f.write(header)  # Escrever cabeçalho original
        out_f.write(out)


def choose_and_process():
    mode   = get_option("var_mode")
    fmt    = get_option("var_format")
    input_file = filedialog.askopenfilename(
        title="Select the DDS file",
        filetypes=[("DDS files", "*.dds")]
    )
    if not input_file:
        return

    dir_name  = os.path.dirname(input_file)
    base, ext = os.path.splitext(os.path.basename(input_file))

    try:
        process_file(input_file, input_file, mode, fmt)
        messagebox.showinfo("Sucess", f"File saved:\n{input_file}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

