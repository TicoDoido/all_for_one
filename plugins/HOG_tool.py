import struct
import os
import threading
from tkinter import filedialog, messagebox

# ------------------ TRADUÇÕES ------------------
plugin_translations = {
    "pt_BR": {
        "plugin_name": "HOG Meet The Robinsons (PS2)",
        "plugin_description": "Extrai e recria arquivos HOG do jogo Meet The Robinsons (PS2)",
        "extract_file": "Extrair .HOG",
        "rebuild_file": "Remontar .HOG",
        "invalid_file_magic": "Arquivo inválido: Magic incorreto (esperado 01 00 02 00).",
        "extracting": "Extraindo: {file}",
        "completed": "Concluído",
        "extraction_completed": "Extração de {count} arquivos concluída em:\n{path}",
        "insertion_completed": "Remontagem concluída com sucesso.",
        "file_not_found": "Arquivo não encontrado: {file}",
        "unexpected_error": "Ocorreu um erro inesperado: {error}",
        "select_hog_file": "Selecione um arquivo HOG",
        "hog_files": "Arquivos HOG",
        "all_files": "Todos os arquivos"
    },
    "en_US": {
        "plugin_name": "HOG Meet The Robinsons (PS2)",
        "plugin_description": "Extracts and rebuilds HOG files from Meet The Robinsons (PS2)",
        "extract_file": "Extract .HOG",
        "rebuild_file": "Rebuild .HOG",
        "invalid_file_magic": "Invalid file: Incorrect magic (expected 01 00 02 00).",
        "extracting": "Extracting: {file}",
        "completed": "Completed",
        "extraction_completed": "Extraction of {count} files completed in:\n{path}",
        "insertion_completed": "Rebuild completed successfully.",
        "file_not_found": "File not found: {file}",
        "unexpected_error": "An unexpected error occurred: {error}",
        "select_hog_file": "Select a HOG file",
        "hog_files": "HOG files",
        "all_files": "All files"
    },
    "es_ES": {
        "plugin_name": "HOG Meet The Robinsons (PS2)",
        "plugin_description": "Extrae y reconstruye archivos HOG del juego Meet The Robinsons (PS2)",
        "extract_file": "Extraer .HOG",
        "rebuild_file": "Reconstruir .HOG",
        "invalid_file_magic": "Archivo inválido: Magic incorrecto (se esperaba 01 00 02 00).",
        "extracting": "Extrayendo: {file}",
        "completed": "Completado",
        "extraction_completed": "Extracción de {count} archivos completada en:\n{path}",
        "insertion_completed": "Reconstrucción completada con éxito.",
        "file_not_found": "Archivo no encontrado: {file}",
        "unexpected_error": "Ocurrió un error inesperado: {error}",
        "select_hog_file": "Seleccionar un archivo HOG",
        "hog_files": "Archivos HOG",
        "all_files": "Todos los archivos"
    }
}

# ------------------ VARIÁVEIS ------------------
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

# ------------------ EXTRAÇÃO ------------------
def extract_hog(filepath):
    entradas = []
    with open(filepath, "rb") as f:
        magic = f.read(4)
        if magic != b"\x01\x00\x02\x00":
            messagebox.showerror(translate("completed"), translate("invalid_file_magic"))
            return

        header_start = struct.unpack("<I", f.read(4))[0]
        f.seek(8, 1)
        total_files = struct.unpack("<I", f.read(4))[0]
        f.seek(header_start)

        for _ in range(total_files):
            filename_pos = struct.unpack("<I", f.read(4))[0]
            pos = struct.unpack("<I", f.read(4))[0]
            size = struct.unpack("<I", f.read(4))[0]
            f.seek(4, 1)
            entradas.append((filename_pos, pos, size))

        out_dir = os.path.splitext(filepath)[0]
        os.makedirs(out_dir, exist_ok=True)

        for filename_pos, pos, size in entradas:
            f.seek(filename_pos)
            name_bytes = bytearray()
            while True:
                b = f.read(1)
                if b == b"\x00" or b == b"":
                    break
                name_bytes.extend(b)
            filename = name_bytes.decode("utf-8", errors="ignore")

            f.seek(pos)
            data = f.read(size)

            out_path = os.path.join(out_dir, filename)
            logger(translate("extracting", file=out_path))
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "wb") as out_file:
                out_file.write(data)

    messagebox.showinfo(translate("completed"), translate("extraction_completed", count=total_files, path=out_dir))

# ------------------ INSERÇÃO ------------------
def insert_hog(filepath, folder):
    with open(filepath, "r+b") as f:
        f.seek(0)
        magic = f.read(4)
        f.seek(4)
        header_start = struct.unpack("<I", f.read(4))[0]
        f.seek(16)
        total_files = struct.unpack("<I", f.read(4))[0]

        f.seek(header_start + 4)
        insert_position = struct.unpack("<I", f.read(4))[0]
        f.seek(header_start)

        entradas = []
        for _ in range(total_files):
            filename_pos = struct.unpack("<I", f.read(4))[0]
            f.seek(12, 1)
            entradas.append(filename_pos)

        arquivos = []
        for entry in entradas:
            f.seek(entry)
            name_bytes = bytearray()
            while True:
                b = f.read(1)
                if b == b"\x00" or b == b"":
                    break
                name_bytes.extend(b)
            arquivos.append(name_bytes.decode("utf-8", errors="ignore"))

        f.seek(insert_position)
        novos_parametros = []
        for file_to_insert in arquivos:
            file_path = os.path.join(folder, file_to_insert)
            if not os.path.isfile(file_path):
                logger(translate("file_not_found", file=file_to_insert))
                continue

            with open(file_path, "rb") as infile:
                data = infile.read()
                new_size = len(data)

            new_pos = f.tell()
            f.write(data)

            pad = ((2048 - (new_size % 2048)) % 2048)
            if pad > 0:
                f.write(b"\x00" * pad)

            novos_parametros.append((new_size, new_pos))

        f.truncate()
        f.seek(header_start)
        for new_size, new_pos in novos_parametros:
            f.seek(4, 1)
            f.write(struct.pack("<I", new_pos))
            f.write(struct.pack("<I", new_size))
            f.seek(4, 1)

    messagebox.showinfo(translate("completed"), translate("insertion_completed"))

# ------------------ AÇÕES ------------------
def selecionar_extrair():
    caminho = filedialog.askopenfilename(
        title=translate("select_hog_file"),
        filetypes=[(translate("hog_files"), "*.hog"), (translate("all_files"), "*.*")]
    )
    if caminho:
        threading.Thread(target=extract_hog, args=(caminho,), daemon=True).start()

def selecionar_inserir():
    caminho = filedialog.askopenfilename(
        title=translate("select_hog_file"),
        filetypes=[(translate("hog_files"), "*.hog"), (translate("all_files"), "*.*")]
    )
    if caminho:
        pasta = os.path.splitext(caminho)[0]
        threading.Thread(target=insert_hog, args=(caminho, pasta), daemon=True).start()

# ------------------ REGISTRO ------------------
def register_plugin(log_func, option_getter, host_language="pt_BR"):
    global logger, current_language
    logger = log_func or print
    current_language = host_language

    def get_plugin_info():
        return {
            "name": translate("plugin_name"),
            "description": translate("plugin_description"),
            "commands": [
                {"label": translate("extract_file"), "action": selecionar_extrair},
                {"label": translate("rebuild_file"), "action": selecionar_inserir},
            ]
        }

    return get_plugin_info
