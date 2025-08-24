# Script de extração original nesse repositório LinkOFF7
# https://github.com/LinkOFF7/GameReverseScripts
import os
import struct
import json
import threading
from tkinter import Tk, Button, filedialog, messagebox


plugin_translations = {
    "pt_BR": {
        "plugin_name": "VFS Extrator / Repacker (Base Plugin)",
        "plugin_description": "Extrai e reinsere arquivos de um VFS (modelo de plugin)",
        "extract_file": "Extrair VFS",
        "reinsert_file": "Reinserir arquivos no VFS",
        "select_vfs_file": "Selecione o arquivo VFS",
        "log_magic": "Magic {magic_hex} no offset {offset}",
        "log_invalid_magic": "Arquivo inválido (magic mismatch): {magic_hex}",
        "log_directory_count": "Contagem de diretórios: {count} no offset {offset}",
        "log_directory_offset": "Diretório {i}: offset {offset}",
        "log_data_start_aligned": "Data start alinhado em: {data_start}",
        "log_file_entry_offset": "File entry {i}: offset {offset}",
        "log_filename_table": "Tabela de nomes em offset {offset}",
        "log_processing": "Processando: {filepath} no offset de dados {data_offset}",
        "log_reinsert_data_start": "data_start = {data_start}",
        "log_reinsert_filename_ptr": "filename_offset (original) = {filename_offset}, pointer pos = {pointer_pos}",
        "log_warn_not_in_metadata": "Aviso: {path} não encontrado no metadata, pulando...",
        "log_warn_invalid_entry_index": "Aviso: entry_index inválido para {path}, pulando...",
        "log_warn_local_missing": "Arquivo local não encontrado, pulando: {path}",
        "log_reinserted": "Reinserted {path} at {abs_pos} (rel {rel_pos}) size {size}",
        "log_reinsert_done_filename_written": "Escreveu tabela de nomes no final, novo offset {new_offset}",
    },
    "en_US": {
        "plugin_name": "VFS Extractor / Repacker (Base Plugin)",
        "plugin_description": "Extracts and reinserts files from a VFS (plugin template)",
        "extract_file": "Extract VFS",
        "reinsert_file": "Reinsert files into VFS",
        "select_vfs_file": "Select VFS file",
        "log_magic": "Magic {magic_hex} at offset {offset}",
        "log_invalid_magic": "Invalid file (magic mismatch): {magic_hex}",
        "log_directory_count": "Directory count: {count} at offset {offset}",
        "log_directory_offset": "Directory {i}: offset {offset}",
        "log_data_start_aligned": "Data start aligned at: {data_start}",
        "log_file_entry_offset": "File entry {i}: offset {offset}",
        "log_filename_table": "Filename table at offset {offset}",
        "log_processing": "Processing: {filepath} at data offset {data_offset}",
        "log_reinsert_data_start": "data_start = {data_start}",
        "log_reinsert_filename_ptr": "filename_offset (original) = {filename_offset}, pointer pos = {pointer_pos}",
        "log_warn_not_in_metadata": "Warning: {path} not found in metadata, skipping...",
        "log_warn_invalid_entry_index": "Warning: invalid entry_index for {path}, skipping...",
        "log_warn_local_missing": "Local file not found, skipping: {path}",
        "log_reinserted": "Reinserted {path} at {abs_pos} (rel {rel_pos}) size {size}",
        "log_reinsert_done_filename_written": "Wrote filename table to end, new offset {new_offset}",
    },
    "es_ES": {
        "plugin_name": "VFS Extractor / Repacker (Plantilla)",
        "plugin_description": "Extrae y reinserta archivos de un VFS (plantilla de plugin)",
        "extract_file": "Extraer VFS",
        "reinsert_file": "Reinsertar archivos en VFS",
        "select_vfs_file": "Seleccionar archivo VFS",
        "log_magic": "Magic {magic_hex} en offset {offset}",
        "log_invalid_magic": "Archivo inválido (magic mismatch): {magic_hex}",
        "log_directory_count": "Número de directorios: {count} en offset {offset}",
        "log_directory_offset": "Directorio {i}: offset {offset}",
        "log_data_start_aligned": "Inicio de datos alineado en: {data_start}",
        "log_file_entry_offset": "Entrada de archivo {i}: offset {offset}",
        "log_filename_table": "Tabla de nombres en offset {offset}",
        "log_processing": "Procesando: {filepath} en offset de datos {data_offset}",
        "log_reinsert_data_start": "data_start = {data_start}",
        "log_reinsert_filename_ptr": "filename_offset (original) = {filename_offset}, pointer pos = {pointer_pos}",
        "log_warn_not_in_metadata": "Aviso: {path} no encontrado en metadata, saltando...",
        "log_warn_invalid_entry_index": "Aviso: entry_index inválido para {path}, saltando...",
        "log_warn_local_missing": "Archivo local no encontrado, saltando: {path}",
        "log_reinserted": "Reinsertado {path} en {abs_pos} (rel {rel_pos}) tamaño {size}",
        "log_reinsert_done_filename_written": "Escribió tabla de nombres al final, nuevo offset {new_offset}",
    }
}

# ==========================
# Globais e utilidades de plugin
# ==========================
logger = print
current_language = "pt_BR"

def translate(key, **kwargs):
    lang_dict = plugin_translations.get(current_language, plugin_translations["pt_BR"])
    translation = lang_dict.get(key, key)
    if kwargs:
        try:
            return translation.format(**kwargs)
        except Exception:
            return translation
    return translation

def register_plugin(log_func, option_getter, host_language="pt_BR"):
    """
    Assinatura padrão: register_plugin(log_func, option_getter, host_language="pt_BR")
    Retorna get_plugin_info() que o host (ALL FOR ONE) espera.
    """
    global logger, current_language
    logger = log_func or print
    current_language = host_language

    def get_plugin_info():
        return {
            "name": translate("plugin_name"),
            "description": translate("plugin_description"),
            "commands": [
                {"label": translate("extract_file"), "action": select_file},
                {"label": translate("reinsert_file"), "action": select_file_reinsert},
            ]
        }
    return get_plugin_info

# ==========================
# Seu código original (sem alterações lógicas, apenas logger+translate nos logs)
# ==========================
class DirEntry:
    def __init__(self, f):
        self.start_pos = f.tell()
        self.index, self.var04, self.var08, self.var0C = struct.unpack('<4i', f.read(0x10))
        self.var10, self.var14, self.var18 = struct.unpack('<iiI', f.read(0xC))

class FileEntry:
    def __init__(self, f):
        self.start_pos = f.tell()
        self.offset, self.compressedSize, self.decompressedSize = struct.unpack('<3Q', f.read(0x18))
        # next 16 bytes
        self.unk18, self.filenameIndex, self.dirIndex, self.unk24, self.unk26 = struct.unpack('<3I2h', f.read(0x10))
        # entry_index will be atribuído pelo chamador (leitura em loop)

def readcstr(f):
    cstr = bytearray()
    while True:
        ch = f.read(2)
        if ch == b'':
            # EOF safety
            return str(cstr, "utf-16")
        if ch == b'\x00\x00':
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
    dirs = []
    files = []
    for i in range(file_count):
        files.append(readcstr(f))
    dir_count = struct.unpack('<I', f.read(4))[0]
    for i in range(dir_count):
        dirs.append(readcstr(f))
    f.seek(cur)
    return files, dirs

def extract(vfs_file):
    metadata = {}
    with open(vfs_file, 'rb') as f:
        magic_offset = f.tell()
        magic, start_offset, dir_count, pad = struct.unpack('<4I', f.read(16))
        magic_hex = f"0x{magic:X}"
        logger(translate("log_magic", magic_hex=magic_hex, offset=magic_offset))
        if magic != 0x33534656:
            logger(translate("log_invalid_magic", magic_hex=magic_hex))
            messagebox.showerror("Error", "Invalid file (magic mismatch)")
            return

        logger(translate("log_directory_count", count=dir_count, offset=(f.tell()-4)))

        dirs = []
        for i in range(dir_count):
            d = DirEntry(f)
            dirs.append(d)

        # pega o count a partir do último DirEntry.var18 (como seu código original)
        count = dirs[-1].var18
        # calcula data_start igual ao original
        data_start = f.tell() + (count * 0x28) + (0x8 * 3)
        data_start = align(data_start)
        logger(translate("log_data_start_aligned", data_start=data_start))

        entries = []
        for i in range(count):
            e = FileEntry(f)
            e.entry_index = i
            entries.append(e)

        # move adiante como no original para ler filename offset
        f.read(16)
        filename_offset = struct.unpack('<Q', f.read(8))[0]
        logger(translate("log_filename_table", offset=filename_offset))

        filenames, dirnames = read_filenames(f, filename_offset)

        # calcula data_pointer_start para cada entrada (offset relativo + data_start)
        for entry in entries:
            entry.data_pointer_start = data_start + entry.offset

        # cria lista ordenada por data_pointer_start (usado para extrair e gerar o TXT)
        entries_sorted = sorted(entries, key=lambda x: x.data_pointer_start)

        # Salva a lista em txt (ordem de extração)
        txt_list_path = os.path.splitext(vfs_file)[0] + '_extraction_order.txt'
        extrac_patch = os.path.splitext(vfs_file)[0]
        with open(txt_list_path, 'w', encoding='utf-8') as list_file:
            for entry in entries_sorted:
                # tenta obter o nome do arquivo a partir das tabelas
                try:
                    dir_path = dirnames[entry.dirIndex]
                    filename = filenames[entry.filenameIndex]
                except Exception:
                    dir_path = ''
                    filename = f'UNKNOWN_{entry.entry_index}'
                filepath = os.path.join(dir_path, filename)
                list_file.write(f'{entry.data_pointer_start}: {filepath}\n')

        # Extrai os arquivos na ordem correta
        metadata['files'] = []
        metadata['dirs'] = dirnames

        for entry in entries_sorted:
            # resolve nome com segurança
            dir_path = ''
            try:
                dir_path = dirnames[entry.dirIndex]
            except Exception:
                dir_path = ''
            try:
                filename = filenames[entry.filenameIndex]
            except Exception:
                filename = f'UNKNOWN_{entry.entry_index}'

            # normaliza caminho e cria diretório se necessário
            if dir_path == '' or dir_path is None:
                filepath = filename
            else:
                filepath = os.path.join(extrac_patch, dir_path, filename)
            filepath = os.path.normpath(filepath)
            full_dir = os.path.dirname(filepath)
            if full_dir and not os.path.exists(full_dir):
                os.makedirs(full_dir, exist_ok=True)

            logger(translate("log_processing", filepath=filepath, data_offset=entry.data_pointer_start))

            f.seek(entry.data_pointer_start)
            data = f.read(entry.decompressedSize)
            with open(filepath, 'wb') as r:
                r.write(data)

            # Vamos guardar metadados correspondentes à entrada original (entry_index)
            metadata['files'].append({
                'filepath': filepath,
                'dirIndex': entry.dirIndex,
                'filenameIndex': entry.filenameIndex,
                'offset': entry.offset,
                'compressedSize': entry.compressedSize,
                'decompressedSize': entry.decompressedSize,
                'data_pointer_start': entry.data_pointer_start,
                'start_pos': entry.start_pos,
                'entry_index': entry.entry_index
            })

    # Save metadata to JSON (observação: metadata['files'] está na ordem de extração; se preferir manter a ordem de entry_index, podemos ordenar antes de salvar)
    json_path = os.path.splitext(vfs_file)[0] + '_metadata.json'
    with open(json_path, 'w', encoding='utf-8') as jf:
        json.dump(metadata, jf, indent=4, ensure_ascii=False)

    messagebox.showinfo("Done", f"Extraction completed!\nMetadata saved at {json_path}\nExtraction order saved at {txt_list_path}")

def reinsert_files(vfs_file):
    # Carrega metadata
    json_path = os.path.splitext(vfs_file)[0] + '_metadata.json'
    if not os.path.exists(json_path):
        messagebox.showerror("Error", f"Metadata JSON not found: {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as jf:
        metadata = json.load(jf)

    # Carrega ordem de reinserção
    txt_list_path = os.path.splitext(vfs_file)[0] + '_extraction_order.txt'
    if not os.path.exists(txt_list_path):
        messagebox.showerror("Error", f"Extraction order TXT not found: {txt_list_path}")
        return

    reinsertion_order = []
    with open(txt_list_path, 'r', encoding='utf-8') as tf:
        for line in tf:
            if not line.strip():
                continue
            try:
                offset_str, filepath = line.strip().split(': ', 1)
                reinsertion_order.append((int(offset_str), os.path.normpath(filepath)))
            except Exception:
                # linha malformada: ignora
                continue

    if not reinsertion_order:
        messagebox.showerror("Error", "No valid lines found in extraction order file.")
        return

    # a posição do primeiro é a base para insertion
    first_offset = reinsertion_order[0][0]
    current_data_pos = first_offset

    # cria lookup dos metadados por filepath (normalizado)
    file_lookup = {os.path.normpath(f['filepath']): f for f in metadata['files']}

    repack_info = []

    # Abre o arquivo VFS e lê estrutura para conseguir atualizar as entradas
    with open(vfs_file, 'r+b') as f:
        # Cabeçalho
        f.seek(0)
        magic, start_offset, dir_count, pad = struct.unpack('<4I', f.read(16))

        # Lê diretórios
        dirs = []
        for i in range(dir_count):
            d = DirEntry(f)
            dirs.append(d)

        # count a partir do último dir.var18 (mesma lógica)
        count = dirs[-1].var18

        # calcula data_start como na extração
        data_start = f.tell() + (count * 0x28) + (0x8 * 3)
        data_start = align(data_start)
        logger(translate("log_reinsert_data_start", data_start=data_start))

        # Lê entradas de arquivos (e guarda FileEntry)
        entries = []
        for i in range(count):
            e = FileEntry(f)
            e.entry_index = i
            entries.append(e)

        # pula 16 e lê o ponteiro da tabela de nomes (posição onde está armazenado o offset)
        f.read(16)
        filename_offset_pos = f.tell()
        filename_offset = struct.unpack('<Q', f.read(8))[0]
        logger(translate("log_reinsert_filename_ptr", filename_offset=filename_offset, pointer_pos=filename_offset_pos))

        # Lê a tabela de nomes completa (para reescrever no final caso seja necessário)
        cur = f.tell()
        f.seek(filename_offset)
        filename_table = f.read()
        f.seek(cur)
        extrac_patch = os.path.splitext(vfs_file)[0]

        # Agora percorre a lista de reinserção (pela ordem do TXT)
        for offset_val, filepath in reinsertion_order:
            norm_path = os.path.join(extrac_patch, filepath)
            norm_path = os.path.normpath(norm_path)

            if norm_path not in file_lookup:
                logger(translate("log_warn_not_in_metadata", path=norm_path))
                continue

            file_meta = file_lookup[norm_path]
            entry_index = int(file_meta.get('entry_index', -1))
            if entry_index < 0 or entry_index >= len(entries):
                logger(translate("log_warn_invalid_entry_index", path=norm_path))
                continue

            entry = entries[entry_index]

            # verifica existência do arquivo para inserir
            if not os.path.exists(norm_path):
                logger(translate("log_warn_local_missing", path=norm_path))
                continue

            with open(norm_path, 'rb') as rf:
                data = rf.read()
            new_size = len(data)

            # escreve dados no current_data_pos (posição absoluta no VFS)
            f.seek(current_data_pos)
            f.write(data)
            f.truncate()

            # atualiza header da entrada: offset relativo (current_data_pos - data_start) e tamanhos
            new_rel_offset = current_data_pos - data_start
            # move até o início da entrada (start_pos) e escreve 3Q (offset, compressedSize, decompressedSize)
            f.seek(entry.start_pos)
            f.write(struct.pack('<3Q', new_rel_offset, new_size, new_size))

            logger(translate("log_reinserted", path=norm_path, abs_pos=current_data_pos, rel_pos=new_rel_offset, size=new_size))

            repack_info.append({
                'filepath': norm_path,
                'entry_index': entry.entry_index,
                'new_absolute_offset': current_data_pos,
                'new_relative_offset': new_rel_offset,
                'new_size': new_size
            })

            # Avança posição atual e alinha a 16 bytes
            current_data_pos = align(current_data_pos + new_size, 16)

        # Escreve a tabela de nomes (filename_table) no final do arquivo e atualiza o ponteiro
        f.seek(0, os.SEEK_END)
        new_filename_offset = f.tell()
        f.write(filename_table)
        logger(translate("log_reinsert_done_filename_written", new_offset=new_filename_offset))

        # Atualiza ponteiro da tabela de nomes no local reservado
        f.seek(filename_offset_pos)
        f.write(struct.pack('<Q', new_filename_offset))
        f.flush()

    # Salva metadata atualizado do repack
    repack_json_path = os.path.splitext(vfs_file)[0] + '_repacked_metadata.json'
    with open(repack_json_path, 'w', encoding='utf-8') as jf:
        json.dump(repack_info, jf, indent=4, ensure_ascii=False)

    messagebox.showinfo("Done", f"Files reinserted in {vfs_file}\nRepacked metadata saved at {repack_json_path}")

# ==========================
# Funções de seleção (integradas ao host via register_plugin)
# ==========================
def select_file_reinsert():
    file_path = filedialog.askopenfilename(title=translate("select_vfs_file"), filetypes=[("VFS files", "*.vfs"), ("All files", "*.*")])
    if file_path:
        # roda em thread para não travar o host/GUI
        threading.Thread(target=reinsert_files, args=(file_path,), daemon=True).start()

def select_file():
    file_path = filedialog.askopenfilename(title=translate("select_vfs_file"), filetypes=[("VFS files", "*.vfs"), ("All files", "*.*")])
    if file_path:
        # roda em thread para não travar o host/GUI
        threading.Thread(target=extract, args=(file_path,), daemon=True).start()
