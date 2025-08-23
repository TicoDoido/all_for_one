# Script de extração original nesse repositório LinkOFF7
# https://github.com/LinkOFF7/GameReverseScripts
import os
import struct
import json
import threading
from tkinter import filedialog, messagebox

# ------------------ TRADUÇÕES ------------------
plugin_translations = {
    "pt_BR": {
        "plugin_name": "VFS3 Extrator e Repacker",
        "plugin_description": "Extrai e reinsere arquivos VFS3(Shadows of the Damned: Hella Remastered)",
        "extract_file": "Extrair VFS",
        "reinsert_file": "Reinserir VFS",
        "invalid_file_magic": "Arquivo inválido (magic incorreto).",
        "processing_file": "Processando: {file}",
        "completed": "Concluído",
        "extraction_completed": "Extração concluída!\nMetadados salvos em:\n{json_path}\nOrdem de extração em:\n{txt_path}",
        "reinsertion_completed": "Reinserção concluída!\nMetadados salvos em:\n{json_path}",
        "file_not_found": "Arquivo não encontrado: {file}",
        "unexpected_error": "Ocorreu um erro inesperado: {error}",
        "select_vfs_file": "Selecione um arquivo VFS",
        "vfs_files": "Arquivos VFS",
        "all_files": "Todos os arquivos"
    },
    "en_US": {
        "plugin_name": "VFS3 Extractor and Repacker",
        "plugin_description": "Extracts and reinserts VFS3 files(Shadows of the Damned: Hella Remastered)",
        "extract_file": "Extract VFS",
        "reinsert_file": "Reinsert VFS",
        "invalid_file_magic": "Invalid file (magic mismatch).",
        "processing_file": "Processing: {file}",
        "completed": "Completed",
        "extraction_completed": "Extraction completed!\nMetadata saved at:\n{json_path}\nExtraction order saved at:\n{txt_path}",
        "reinsertion_completed": "Reinsertion completed!\nMetadata saved at:\n{json_path}",
        "file_not_found": "File not found: {file}",
        "unexpected_error": "An unexpected error occurred: {error}",
        "select_vfs_file": "Select a VFS file",
        "vfs_files": "VFS files",
        "all_files": "All files"
    },
    "es_ES": {
        "plugin_name": "VFS3 Extracción y Repacker",
        "plugin_description": "Extrae y reinserta archivos VFS3(Shadows of the Damned: Hella Remastered)",
        "extract_file": "Extraer VFS",
        "reinsert_file": "Reinsertar VFS",
        "invalid_file_magic": "Archivo inválido (magic incorrecto).",
        "processing_file": "Procesando: {file}",
        "completed": "Completado",
        "extraction_completed": "Extracción completada!\nMetadatos guardados en:\n{json_path}\nOrden de extracción en:\n{txt_path}",
        "reinsertion_completed": "Reinserción completada!\nMetadatos guardados en:\n{json_path}",
        "file_not_found": "Archivo no encontrado: {file}",
        "unexpected_error": "Ocurrió un error inesperado: {error}",
        "select_vfs_file": "Seleccionar archivo VFS",
        "vfs_files": "Archivos VFS",
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

# ------------------ CLASSES AUXILIARES ------------------
class DirEntry:
    def __init__(self, f):
        self.start_pos = f.tell()
        self.index, self.var04, self.var08, self.var0C = struct.unpack('<4i', f.read(0x10))
        self.var10, self.var14, self.var18 = struct.unpack('<iiI', f.read(0xC))

class FileEntry:
    def __init__(self, f):
        self.start_pos = f.tell()
        self.offset, self.compressedSize, self.decompressedSize = struct.unpack('<3Q', f.read(0x18))
        self.unk18, self.filenameIndex, self.dirIndex, self.unk24, self.unk26 = struct.unpack('<3I2h', f.read(0x10))

def readcstr(f):
    cstr = bytearray()
    while True:
        ch = f.read(2)
        if ch == b'' or ch == b'\x00\x00':
            return str(cstr, "utf-16")
        cstr += ch

def align(var, boundary=16):
    if var % boundary != 0:
        return var + (boundary - (var % boundary))
    return var

def read_filenames(f, offset):
    cur = f.tell()
    f.seek(offset)
    file_count = struct.unpack('<I', f.read(4))[0]
    files = [readcstr(f) for _ in range(file_count)]
    dir_count = struct.unpack('<I', f.read(4))[0]
    dirs = [readcstr(f) for _ in range(dir_count)]
    f.seek(cur)
    return files, dirs

# ------------------ EXTRAÇÃO ------------------
def extract(vfs_file):
    try:
        metadata = {}
        with open(vfs_file, 'rb') as f:
            magic_offset = f.tell()
            magic, start_offset, dir_count, pad = struct.unpack('<4I', f.read(16))
            if magic != 0x33534656:
                messagebox.showerror(translate("completed"), translate("invalid_file_magic"))
                return

            dirs = [DirEntry(f) for _ in range(dir_count)]
            count = dirs[-1].var18
            data_start = align(f.tell() + (count * 0x28) + (0x8 * 3))

            entries = [FileEntry(f) for i in range(count)]
            for i, e in enumerate(entries):
                e.entry_index = i

            f.read(16)
            filename_offset = struct.unpack('<Q', f.read(8))[0]
            filenames, dirnames = read_filenames(f, filename_offset)

            extrac_patch = os.path.splitext(vfs_file)[0]
            txt_list_path = extrac_patch + '_extraction_order.txt'
            json_path = extrac_patch + '_metadata.json'
            os.makedirs(extrac_patch, exist_ok=True)

            metadata['files'] = []
            metadata['dirs'] = dirnames

            entries_sorted = sorted(entries, key=lambda x: x.offset + data_start)

            with open(txt_list_path, 'w', encoding='utf-8') as list_file:
                for entry in entries_sorted:
                    try:
                        dir_path = dirnames[entry.dirIndex]
                        filename = filenames[entry.filenameIndex]
                    except:
                        dir_path = ''
                        filename = f'UNKNOWN_{entry.entry_index}'
                    filepath = os.path.join(dir_path, filename)
                    list_file.write(f'{entry.offset + data_start}: {filepath}\n')

            for entry in entries_sorted:
                try:
                    dir_path = dirnames[entry.dirIndex]
                    filename = filenames[entry.filenameIndex]
                except:
                    dir_path = ''
                    filename = f'UNKNOWN_{entry.entry_index}'

                filepath = os.path.normpath(os.path.join(extrac_patch, dir_path, filename))
                os.makedirs(os.path.dirname(filepath), exist_ok=True)

                logger(translate("processing_file", file=filepath))
                f.seek(entry.offset + data_start)
                data = f.read(entry.decompressedSize)
                with open(filepath, 'wb') as out_file:
                    out_file.write(data)

                metadata['files'].append({
                    'filepath': filepath,
                    'entry_index': entry.entry_index,
                    'offset': entry.offset,
                    'compressedSize': entry.compressedSize,
                    'decompressedSize': entry.decompressedSize
                })

            with open(json_path, 'w', encoding='utf-8') as jf:
                json.dump(metadata, jf, indent=4, ensure_ascii=False)

        messagebox.showinfo(translate("completed"), translate("extraction_completed", json_path=json_path, txt_path=txt_list_path))
    except Exception as e:
        messagebox.showerror(translate("completed"), translate("unexpected_error", error=str(e)))

# ------------------ REINSERT ------------------
def reinsert_files(vfs_file):
    try:
        extrac_patch = os.path.splitext(vfs_file)[0]
        json_path = extrac_patch + '_metadata.json'
        txt_list_path = extrac_patch + '_extraction_order.txt'

        if not os.path.exists(json_path):
            messagebox.showerror(translate("completed"), translate("file_not_found", file=json_path))
            return
        if not os.path.exists(txt_list_path):
            messagebox.showerror(translate("completed"), translate("file_not_found", file=txt_list_path))
            return

        with open(json_path, 'r', encoding='utf-8') as jf:
            metadata = json.load(jf)

        reinsertion_order = []
        with open(txt_list_path, 'r', encoding='utf-8') as tf:
            for line in tf:
                if not line.strip():
                    continue
                try:
                    offset_str, filepath = line.strip().split(': ', 1)
                    reinsertion_order.append((int(offset_str), os.path.normpath(os.path.join(extrac_patch, filepath))))
                except:
                    continue

        file_lookup = {f['filepath']: f for f in metadata['files']}
        current_data_pos = reinsertion_order[0][0]

        with open(vfs_file, 'r+b') as f:
            magic, start_offset, dir_count, pad = struct.unpack('<4I', f.read(16))
            dirs = [DirEntry(f) for _ in range(dir_count)]
            count = dirs[-1].var18
            data_start = align(f.tell() + (count * 0x28) + (0x8 * 3))
            entries = [FileEntry(f) for _ in range(count)]
            for i, e in enumerate(entries):
                e.entry_index = i

            f.read(16)
            filename_offset_pos = f.tell()
            filename_offset = struct.unpack('<Q', f.read(8))[0]
            f.seek(filename_offset)
            filename_table = f.read()
            f.seek(0, os.SEEK_END)

            for _, filepath in reinsertion_order:
                if filepath not in file_lookup:
                    continue
                entry_index = file_lookup[filepath]['entry_index']
                entry = entries[entry_index]

                if not os.path.exists(filepath):
                    continue

                with open(filepath, 'rb') as rf:
                    data = rf.read()
                new_size = len(data)

                f.seek(current_data_pos)
                f.write(data)
                f.flush()
                f.truncate()

                new_rel_offset = current_data_pos - data_start
                f.seek(entry.start_pos)
                f.write(struct.pack('<3Q', new_rel_offset, new_size, new_size))
                f.flush()

                current_data_pos = align(current_data_pos + new_size, 16)

            new_filename_offset = f.tell()
            f.write(filename_table)
            f.flush()
            f.seek(filename_offset_pos)
            f.write(struct.pack('<Q', new_filename_offset))
            f.flush()

        repack_json_path = extrac_patch + '_repacked_metadata.json'
        with open(repack_json_path, 'w', encoding='utf-8') as jf:
            json.dump(reinsertion_order, jf, indent=4, ensure_ascii=False)

        messagebox.showinfo(translate("completed"), translate("reinsertion_completed", json_path=repack_json_path))

    except Exception as e:
        messagebox.showerror(translate("completed"), translate("unexpected_error", error=str(e)))

# ------------------ AÇÕES ------------------
def select_file_extract():
    path = filedialog.askopenfilename(title=translate("select_vfs_file"),
                                      filetypes=[(translate("vfs_files"), "*.vfs"), (translate("all_files"), "*.*")])
    if path:
        threading.Thread(target=extract, args=(path,), daemon=True).start()

def select_file_reinsert():
    path = filedialog.askopenfilename(title=translate("select_vfs_file"),
                                      filetypes=[(translate("vfs_files"), "*.vfs"), (translate("all_files"), "*.*")])
    if path:
        threading.Thread(target=reinsert_files, args=(path,), daemon=True).start()

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
                {"label": translate("extract_file"), "action": select_file_extract},
                {"label": translate("reinsert_file"), "action": select_file_reinsert},
            ]
        }

    return get_plugin_info
