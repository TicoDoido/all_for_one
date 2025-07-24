import struct
import os
from tkinter import filedialog, messagebox

logger = print
get_option = lambda name: None

def register_plugin(log_func, option_getter):
    global logger, get_option
    logger = log_func or print
    get_option = option_getter or (lambda name: None)
            
    return {
        "name": "GMD Arquivos de texto MT Framework (RE6)",
        "description": "Extrai e reinsere textos dos arquivos GMD da MT Framework, testado com Resident Evil 6",
        "commands": [
            {"label": "Extrair Textos", "action": extrair_textos},
            {"label": "Reinserir Textos", "action": inserir_textos},
        ]
    }

# Read a 4-byte little-endian integer from file
def read_little_endian_int(file):
    data = file.read(4)
    value = struct.unpack('<I', data)[0]
    return value

# Extract texts from binary GMD file
def extract_texts_from_binary(file_path):
    logger(f"Opening file: {file_path}")
    with open(file_path, 'rb') as file:
        file.seek(20)
        pointers = read_little_endian_int(file)

        pointer_block_size = pointers * 4

        real_pointers = []
        pointer_table_end = pointer_block_size + 28

        for i in range(pointers):
            pointer_data = file.read(4)
            if pointer_data != b'\xFF\xFF\xFF\xFF':
                pointer = struct.unpack('<I', pointer_data)[0]
                real_pointers.append(pointer)

        logger(f"Extracting texts ({len(real_pointers)} valid)...")
        texts = []

        for i, pointer in enumerate(real_pointers):
            text_offset = pointer_table_end + pointer
            file.seek(text_offset)

            text_bytes = b""
            while True:
                byte = file.read(1)
                if byte == b'\x00' or byte == b'':
                    break
                text_bytes += byte

            try:
                text = text_bytes.decode('utf-8')
            except UnicodeDecodeError:
                text = "<DECODING ERROR>"
                logger(f"Text[{i:03}] contains invalid UTF-8 bytes.")
            texts.append(text)

    return texts

def save_texts_to_file(texts, file_path):
    output_file = f"{os.path.splitext(file_path)[0]}.txt"
    logger(f"Saving texts to: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        for text in texts:
            text = text.replace("\r\n", "[BR]")
            f.write(f"{text}[END]\n")
    logger("Output file saved successfully.")
    messagebox.showinfo("Success", f"Texts were extracted and saved to:\n{output_file}")


def insert_texts_into_binary(file_path):
    txt_file_path = f"{os.path.splitext(file_path)[0]}.txt"
    
    if not os.path.exists(txt_file_path):
        messagebox.showerror("Error", f"Text file not found:\n{txt_file_path}")
        return

    with open(txt_file_path, 'r', encoding='utf8') as f:
        texts = f.read().split("[END]\n")
        if texts and texts[-1] == "":
            texts.pop()

    with open(file_path, 'r+b') as file:
        file.seek(20)
        pointers = read_little_endian_int(file)

        pointer_block_size = pointers * 4
        pointer_table_end = pointer_block_size + 28

        file.seek(pointer_table_end)
        offsets = []

        for idx, text in enumerate(texts):
            offset = file.tell()
            relative_offset = offset - pointer_table_end
            offsets.append(relative_offset)

            text_bytes = text.replace("[BR]", "\r\n").encode('utf8') + b'\x00'
            file.write(text_bytes)

        file.truncate()
        total_size = file.tell()

        # Update only valid pointers (skip 0xFFFFFFFF)
        file.seek(24)
        text_idx = 0

        for i in range(pointers):
            pointer_pos = file.tell()
            pointer_data = file.read(4)

            if pointer_data == b'\xFF\xFF\xFF\xFF':
                logger(f"Skipping Pointer[{i:03}] (0xFFFFFFFF)")
                continue

            if text_idx < len(offsets):
                file.seek(pointer_pos)
                file.write(struct.pack('<I', offsets[text_idx]))
                logger(f"Pointer[{i:03}] updated with offset {offsets[text_idx]}")
                text_idx += 1
            else:
                logger(f"No more texts to assign to Pointer[{i:03}]")
                break
                
        file.seek(pointer_table_end - 4)
        file.write(struct.pack('<I', total_size - pointer_table_end))

        if text_idx < len(offsets):
            logger(f"Warning: More texts ({len(offsets)}) than valid pointers ({text_idx})!")
            messagebox.showwarning("Warning", "There are more texts than available valid pointers.")

    messagebox.showinfo("Success", "Texts were successfully reinserted into the binary file.")

# Open file dialog and extract
def extrair_textos():
    file_path = filedialog.askopenfilename(
        title="Select GMD File",
        filetypes=(("GMD File", "*.gmd"), ("All Files", "*.*"))
    )
    
    if file_path:
        try:
            texts = extract_texts_from_binary(file_path)
            save_texts_to_file(texts, file_path)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while processing the file:\n{e}")


def inserir_textos():
    file_path = filedialog.askopenfilename(
                title="Select GMD to insert texts",
                filetypes=(("GMD files", "*.gmd"), ("All Files", "*.*"))
        )
        
    if file_path:
        try:
            insert_texts_into_binary(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while processing the file:\n{e}")