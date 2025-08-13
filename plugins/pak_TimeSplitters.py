import os
import struct
import threading
import glob
from tkinter import filedialog, messagebox

plugin_translations = {
    "pt_BR": {
        "plugin_name": "PAK TimeSplitters Future Perfect (PS2)",
        "plugin_description": "Ferramenta completa para extrair, modificar e recriar arquivos PAK do TimeSplitters Future Perfect no PlayStation 2, incluindo suporte para edição de textos em formato ANSI.",
        "select_pak_file": "Selecionar arquivo PAK",
        "select_folder": "Selecionar pasta com arquivos extraídos",
        "extract_text": "Extrair texto de arquivo BIN",
        "insert_text": "Inserir texto no arquivo BIN",
        "invalid_file_magic": "Arquivo inválido: Magic incorreto (esperado 'P5CK').",
        "no_bin_files": "Nenhum arquivo .bin encontrado na pasta selecionada.",
        "invalid_filename": "Nome do arquivo inválido para extrair ID:\n{filename}",
        "repack_created": "Arquivo repack criado:\n{file}",
        "extraction_completed": "{count} arquivos extraídos para:\n{path}",
        "text_extracted": "Texto extraído para:\n{file}",
        "text_inserted": "Texto reinserido em:\n{file}",
        "original_not_found": "Arquivo original não encontrado:\n{file}",
        "error": "Erro",
        "completed": "Concluído",
        "success": "Sucesso"
    },
    "en_US": {
        "plugin_name": "PAK TimeSplitters Future Perfect (PS2)",
        "plugin_description": "Complete tool to extract, modify, and rebuild PAK files from TimeSplitters Future Perfect on PlayStation 2, including support for editing ANSI text files.",
        "select_pak_file": "Select PAK file",
        "select_folder": "Select folder with extracted files",
        "extract_text": "Extract text from BIN file",
        "insert_text": "Insert text into BIN file",
        "invalid_file_magic": "Invalid file: Incorrect magic (expected 'P5CK').",
        "no_bin_files": "No .bin files found in the selected folder.",
        "invalid_filename": "Invalid filename to extract ID:\n{filename}",
        "repack_created": "Repack file created:\n{file}",
        "extraction_completed": "{count} files extracted to:\n{path}",
        "text_extracted": "Text extracted to:\n{file}",
        "text_inserted": "Text inserted into:\n{file}",
        "original_not_found": "Original file not found:\n{file}",
        "error": "Error",
        "completed": "Completed",
        "success": "Success"
    },
    "es_ES": {
        "plugin_name": "PAK TimeSplitters Future Perfect (PS2)",
        "plugin_description": "Herramienta completa para extraer, modificar y reconstruir archivos PAK de TimeSplitters Future Perfect en PlayStation 2, incluyendo soporte para editar textos en formato ANSI.",
        "select_pak_file": "Seleccionar archivo PAK",
        "select_folder": "Seleccionar carpeta con archivos extraídos",
        "extract_text": "Extraer texto de archivo BIN",
        "insert_text": "Insertar texto en archivo BIN",
        "invalid_file_magic": "Archivo inválido: Magic incorrecto (se esperaba 'P5CK').",
        "no_bin_files": "No se encontraron archivos .bin en la carpeta seleccionada.",
        "invalid_filename": "Nombre de archivo inválido para extraer ID:\n{filename}",
        "repack_created": "Archivo reempaquetado creado:\n{file}",
        "extraction_completed": "{count} archivos extraídos a:\n{path}",
        "text_extracted": "Texto extraído en:\n{file}",
        "text_inserted": "Texto insertado en:\n{file}",
        "original_not_found": "Archivo original no encontrado:\n{file}",
        "error": "Error",
        "completed": "Completado",
        "success": "Éxito"
    }
}

logger = print
current_language = "pt_BR"

def translate(key, **kwargs):
    lang_dict = plugin_translations.get(current_language, plugin_translations["pt_BR"])
    translation = lang_dict.get(key, key)
    if kwargs:
        try:
            return translation.format(**kwargs)
        except:
            return translation
    return translation

def extrair_pak(file_path):
    try:
        with open(file_path, "rb") as f:
            magic = f.read(4)
            if magic != b"P5CK":
                messagebox.showerror(translate("error"), translate("invalid_file_magic"))
                return

            header_offset = struct.unpack("<I", f.read(4))[0]
            header_size = struct.unpack("<I", f.read(4))[0]
            num_files = header_size // 16

            f.seek(header_offset)
            entries = []
            for _ in range(num_files):
                file_id = f.read(4)
                pos = struct.unpack("<I", f.read(4))[0]
                size = struct.unpack("<I", f.read(4))[0]
                f.read(4)  # 4 bytes nulos
                entries.append((file_id, pos, size))

            base_dir = os.path.dirname(file_path)
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            output_dir = os.path.join(base_dir, base_name)
            os.makedirs(output_dir, exist_ok=True)

            for idx, (file_id, pos, size) in enumerate(entries, start=1):
                f.seek(pos)
                data = f.read(size)
                file_id_hex = file_id.hex().upper()
                filename = f"{idx:04d}_{file_id_hex}.bin"
                with open(os.path.join(output_dir, filename), "wb") as out:
                    out.write(data)

            messagebox.showinfo(translate("completed"), translate("extraction_completed", count=num_files, path=output_dir))
    except Exception as e:
        messagebox.showerror(translate("error"), str(e))
        logger(str(e))

def repack_pak(folder_path):
    try:
        base_name = os.path.basename(folder_path.rstrip("/\\"))
        base_dir = os.path.dirname(folder_path.rstrip("/\\"))

        output_path = os.path.join(base_dir, f"{base_name}_MOD.PAK")

        files = sorted(glob.glob(os.path.join(folder_path, "*.bin")))
        if not files:
            messagebox.showerror(translate("error"), translate("no_bin_files"))
            return

        with open(output_path, "wb") as out_f:
            out_f.write(b"P5CK")
            out_f.write(b"\x00" * 8)  # placeholder

            out_f.seek(2048)

            entries = []

            for file_path in files:
                size = os.path.getsize(file_path)
                pos = out_f.tell()

                filename = os.path.basename(file_path)
                try:
                    id_hex = filename.split("_")[1].split(".")[0]
                    id_bin = bytes.fromhex(id_hex)
                except Exception:
                    messagebox.showerror(translate("error"), translate("invalid_filename", filename=filename))
                    return

                with open(file_path, "rb") as f_in:
                    out_f.write(f_in.read())
                    
                    end = out_f.tell()
                    if end % 2048  != 0:
                        pad = 2048  - (end % 2048 )
                        out_f.write(b"\x00" * pad)

                entries.append((id_bin, pos, size))

            header_pos = out_f.tell()
            header_size = len(entries) * 16

            for id_bin, pos, size in entries:
                out_f.write(id_bin)
                out_f.write(struct.pack("<I", pos))
                out_f.write(struct.pack("<I", size))
                out_f.write(b"\x00\x00\x00\x00")

            out_f.seek(4)
            out_f.write(struct.pack("<I", header_pos))
            out_f.write(struct.pack("<I", header_size))

        messagebox.showinfo(translate("completed"), translate("repack_created", file=output_path))
    except Exception as e:
        messagebox.showerror(translate("error"), str(e))
        logger(str(e))

def extract_text(file_path):
    try:
        with open(file_path, "rb") as f:
            first_ptr = struct.unpack("<I", f.read(4))[0]
            pointer_block_size = first_ptr

            f.seek(0)
            pointers = []
            while f.tell() < pointer_block_size:
                ptr = struct.unpack("<I", f.read(4))[0]
                pointers.append(ptr)

            texts = []
            for ptr in pointers:
                f.seek(ptr)
                text_bytes = bytearray()
                while True:
                    b = f.read(1)
                    if not b or b == b'\x00':
                        break
                    text_bytes.extend(b)
                texts.append(text_bytes.decode("ansi", errors="ignore"))

            out_txt = file_path + ".txt"
            with open(out_txt, "w", encoding="ansi") as out_f:
                for t in texts:
                    t = t.replace("\n", "[BR]")
                    out_f.write(t + "[FIM]\n")

        messagebox.showinfo(translate("completed"), translate("text_extracted", file=out_txt))
    except Exception as e:
        messagebox.showerror(translate("error"), str(e))

def insert_text(txt_path):
    try:
        bin_path = txt_path[:-4]
        if not os.path.exists(bin_path):
            raise FileNotFoundError(translate("original_not_found", file=bin_path))

        with open(txt_path, "r", encoding="ansi") as f:
            texts = f.read().split("[FIM]\n")
            if texts[-1].strip() == "":
                texts = texts[:-1]

        with open(bin_path, "rb") as f:
            data = bytearray(f.read())

        first_ptr = struct.unpack("<I", data[0:4])[0]
        pointer_count = first_ptr // 4

        pointers = []
        for i in range(pointer_count):
            ptr = struct.unpack("<I", data[i*4:i*4+4])[0]
            pointers.append(ptr)

        offset = pointers[0]
        for i, text in enumerate(texts):
            encoded = text.replace("[BR]", "\n").encode("ansi") + b"\x00"
            data[offset:offset+len(encoded)] = encoded
            pointers[i] = offset
            offset += len(encoded)

        for i, ptr in enumerate(pointers):
            data[i*4:i*4+4] = struct.pack("<I", ptr)

        with open(bin_path, "wb") as f:
            f.write(data)
            f.truncate()

        messagebox.showinfo(translate("success"), translate("text_inserted", file=bin_path))
    except Exception as e:
        messagebox.showerror(translate("error"), str(e))

def extract_text_ansi():
    file_path = filedialog.askopenfilename(title="BIN files", filetypes=[("BIN files", "*.bin")])
    if file_path:
        extract_text(file_path)

def insert_text_ansi():
    txt_path = filedialog.askopenfilename(title="TXT files", filetypes=[("Text files", "*.txt")])
    if txt_path:
        insert_text(txt_path)

def selecionar_arquivo_pak():
    caminho = filedialog.askopenfilename(
        title=translate("select_pak_file"),
        filetypes=[("PAK Files", "*.pak"), ("All files", "*.*")]
    )
    if caminho:
        threading.Thread(target=extrair_pak, args=(caminho,), daemon=True).start()

def selecionar_pasta():
    caminho = filedialog.askdirectory(title=translate("select_folder"))
    if caminho:
        threading.Thread(target=repack_pak, args=(caminho,), daemon=True).start()

def register_plugin(log_func=None, option_getter=None, host_language="pt_BR"):
    global logger, current_language
    logger = log_func or print
    current_language = host_language

    def get_plugin_info():
        return {
            "name": translate("plugin_name"),
            "description": translate("plugin_description"),
            "commands": [
                {"label": translate("select_pak_file"), "action": selecionar_arquivo_pak},
                {"label": translate("select_folder"), "action": selecionar_pasta},
                {"label": translate("extract_text"), "action": extract_text_ansi},
                {"label": translate("insert_text"), "action": insert_text_ansi},
            ],
        }
    return get_plugin_info
