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
                "values": ["DXT5", "DXT1", "BC7", "BGRA 8888"]
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
    # 1) Define block_data_size e header_size por formato
    if fmt == "DXT1":
        block_data_size = 8
        header_size     = 128
    elif fmt == "DXT5":
        block_data_size = 16
        header_size     = 128
    elif fmt == "BC7":
        block_data_size = 16
        header_size     = 148        # DDS + DX10 header
    elif fmt == "BGRA 8888":
        block_data_size = 4 * 4 * 4  # 4×4 pixels × 4 bytes
        header_size     = 148        # DDS + DX10 header
    else:
        raise ValueError(f"Formato não suportado: {fmt}")

    # 2) Leitura de header + dados
    with open(input_path, "rb") as f:
        header = f.read(header_size)
        height = int.from_bytes(header[12:16], byteorder='little')
        width  = int.from_bytes(header[16:20], byteorder='little')
        data   = f.read()

    # 3) Alinhamento para múltiplos de 32 pixels
    aligned_w = round_up_multiple(width,  32)
    aligned_h = round_up_multiple(height, 32)

    # 4) Define blocos e tamanho unitário:
    if fmt == "BGRA 8888":
        # para BGRA, cada pixel é um "bloco" de 1×1, 4 bytes
        block_w = block_h = 1
        unit_sz = 4
    else:
        # para DXT/BC7, blocos de 4×4 pixels
        block_w = block_h = 4
        unit_sz = block_data_size

    w_blocks = aligned_w  // block_w
    h_blocks = aligned_h // block_h
    orig_wb  = width  // block_w
    orig_hb  = height // block_h

    # 5) Cria buffer com padding e copia linha a linha
    padded_data = bytearray(w_blocks * h_blocks * unit_sz)
    for y in range(orig_hb):
        src_off = y * orig_wb * unit_sz
        dst_off = y * w_blocks * unit_sz
        padded_data[dst_off:dst_off + orig_wb*unit_sz] = data[src_off:src_off + orig_wb*unit_sz]

    # 6) Executa swizzle ou unswizzle sempre sobre padded_data
    if mode == "Swizzle":
        processed_full = swizzle_ps4(
            padded_data,
            aligned_w, aligned_h,
            block_width=block_w,
            block_height=block_h,
            block_data_size=unit_sz
        )
    else:  # Unswizzle
        processed_full = unswizzle_ps4(
            padded_data,
            aligned_w, aligned_h,
            block_width=block_w,
            block_height=block_h,
            block_data_size=unit_sz
        )

    # 7) Se for unswizzle, ou mesmo swizzle no final, recorta de volta ao tamanho original
    processed = bytearray(orig_wb * orig_hb * unit_sz)
    for y in range(orig_hb):
        src_off = y * w_blocks * unit_sz
        dst_off = y * orig_wb   * unit_sz
        processed[dst_off:dst_off + orig_wb*unit_sz] = processed_full[src_off:src_off + orig_wb*unit_sz]

    # 8) Grava saída
    with open(output_path, "wb") as out_f:
        out_f.write(header)
        out_f.write(processed)


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

