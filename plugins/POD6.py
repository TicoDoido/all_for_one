import os
import struct
import zlib
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

# ==========================
# Traduções do plugin POD6
# ==========================
plugin_translations = {
    "pt_BR": {
        "plugin_name": "POD6 Tool - Extrair/Inserir",
        "plugin_description": "Extrai e reinsere arquivos de containers POD6",
        "extract_pod": "Extrair POD6",
        "insert_pod": "Inserir no POD6 (in-place)",
        "select_pod_file": "Selecione o arquivo POD",
        "select_pod_file_insert": "Selecione o arquivo POD para inserir",
        "select_folder_files": "Selecione a pasta de saída/entrada",
        "msg_title_error": "Erro",
        "msg_title_done": "Pronto",
        "msg_extract_done": "Extração concluída. Pasta: {outdir}",
        "msg_insert_done": "Inserção concluída no arquivo: {res}",
        "log_magic_invalid": "Magic POD6 não encontrada no início do arquivo.",
        "log_header_info": "total_items={total_items} some_size={some_size} header_pos={header_pos} name_block_size={name_block_size}",
        "log_reading_entries": "Lendo {n} entradas do header.",
        "log_entry_truncated": "Entrada {i} truncada (esperado 24 bytes).",
        "log_name_block_short": "Aviso: name_block_size lido menor que esperado ({have} < {expect})",
        "log_extract_entry_empty": "[{idx}] {name} — arquivo vazio criado",
        "log_extract_decompress": "[{idx}] {name} — descomprimido {in_bytes} -> {out_bytes} bytes",
        "log_extract_raw": "[{idx}] {name} — salvo bruto ({size} bytes)",
        "log_file_pos_invalid": "ERRO: entrada {idx} ({name}) tem file_pos={file_pos}, mas o arquivo tem {file_size} bytes.",
        "log_extract_finished": "Extração finalizada.",
        "log_insert_start": "Inserindo arquivos no original: {path}",
        "log_inserting": "Inserindo: {src}",
        "log_insert_compress": "Inserido {name}: comp_size={comp_size} uncomp_size={uncomp_size} file_pos={file_pos_new}",
        "log_insert_finish": "Inserção finalizada e arquivo truncado ao novo tamanho.",
        "msg_error_open": "Erro ao processar arquivo: {err}",
    },
    "en_US": {
        "plugin_name": "POD6 Tool - Extract/Insert",
        "plugin_description": "Extracts and reinserts files from POD6 containers",
        "extract_pod": "Extract POD6",
        "insert_pod": "Insert into POD6 (in-place)",
        "select_pod_file": "Select the POD file",
        "select_pod_file_insert": "Select the POD file to insert into",
        "select_folder_files": "Select the output/input folder",
        "msg_title_error": "Error",
        "msg_title_done": "Done",
        "msg_extract_done": "Extraction finished. Folder: {outdir}",
        "msg_insert_done": "Insertion finished on file: {res}",
        "log_magic_invalid": "POD6 magic not found at file start.",
        "log_header_info": "total_items={total_items} some_size={some_size} header_pos={header_pos} name_block_size={name_block_size}",
        "log_reading_entries": "Reading {n} entries from header.",
        "log_entry_truncated": "Entry {i} truncated (expected 24 bytes).",
        "log_name_block_short": "Warning: name_block_size read smaller than expected ({have} < {expect})",
        "log_extract_entry_empty": "[{idx}] {name} — empty file created",
        "log_extract_decompress": "[{idx}] {name} — decompressed {in_bytes} -> {out_bytes} bytes",
        "log_extract_raw": "[{idx}] {name} — saved raw ({size} bytes)",
        "log_file_pos_invalid": "ERROR: entry {idx} ({name}) has file_pos={file_pos}, file size {file_size}.",
        "log_extract_finished": "Extraction finished.",
        "log_insert_start": "Inserting files into original: {path}",
        "log_inserting": "Inserting: {src}",
        "log_insert_compress": "Inserted {name}: comp_size={comp_size} uncomp_size={uncomp_size} file_pos={file_pos_new}",
        "log_insert_finish": "Insertion finished and file truncated to new size.",
        "msg_error_open": "Error processing file: {err}",
    },
    "es_ES": {
        "plugin_name": "POD6 Tool - Extraer/Insertar",
        "plugin_description": "Extrae y reinyecta archivos de contenedores POD6",
        "extract_pod": "Extraer POD6",
        "insert_pod": "Insertar en POD6 (in-place)",
        "select_pod_file": "Seleccione el archivo POD",
        "select_pod_file_insert": "Seleccione el archivo POD para insertar",
        "select_folder_files": "Seleccione la carpeta de salida/entrada",
        "msg_title_error": "Error",
        "msg_title_done": "Listo",
        "msg_extract_done": "Extracción completada. Carpeta: {outdir}",
        "msg_insert_done": "Inserción completada en el archivo: {res}",
        "log_magic_invalid": "Magic POD6 no encontrada al inicio del archivo.",
        "log_header_info": "total_items={total_items} some_size={some_size} header_pos={header_pos} name_block_size={name_block_size}",
        "log_reading_entries": "Leyendo {n} entradas del header.",
        "log_entry_truncated": "Entrada {i} truncada (se esperaban 24 bytes).",
        "log_name_block_short": "Aviso: name_block_size leído menor que el esperado ({have} < {expect})",
        "log_extract_entry_empty": "[{idx}] {name} — archivo vacío creado",
        "log_extract_decompress": "[{idx}] {name} — descomprimido {in_bytes} -> {out_bytes} bytes",
        "log_extract_raw": "[{idx}] {name} — guardado bruto ({size} bytes)",
        "log_file_pos_invalid": "ERROR: entrada {idx} ({name}) tiene file_pos={file_pos}, tamaño del archivo {file_size}.",
        "log_extract_finished": "Extracción finalizada.",
        "log_insert_start": "Insertando archivos en el original: {path}",
        "log_inserting": "Insertando: {src}",
        "log_insert_compress": "Insertado {name}: comp_size={comp_size} uncomp_size={uncomp_size} file_pos={file_pos_new}",
        "log_insert_finish": "Inserción finalizada y archivo truncado al nuevo tamaño.",
        "msg_error_open": "Error al procesar archivo: {err}",
    }
}

# ==========================
# Globais e utilitários do plugin
# ==========================
logger = print
current_language = "pt_BR"

def translate(key, **kwargs):
    lang_dict = plugin_translations.get(current_language, plugin_translations["pt_BR"])
    text = lang_dict.get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text

def u32le_from_bytes(b):
    return int.from_bytes(b, byteorder='little', signed=False)

def u32le_to_bytes(v):
    return int(int(v)).to_bytes(4, byteorder='little', signed=False)

# ==========================
# Funções principais (mantive sua lógica)
# ==========================
def extract_pod6_file(path: Path, outdir: Path, log_fn=None):
    if log_fn is None:
        log_fn = logger

    try:
        with open(path, 'rb') as f:
            magic = f.read(4)
            if magic != b'POD6':
                log_fn(translate("log_magic_invalid"))
                raise ValueError(translate("log_magic_invalid"))

            total_items = u32le_from_bytes(f.read(4))
            some_size = u32le_from_bytes(f.read(4))
            header_pos = u32le_from_bytes(f.read(4))
            name_block_size = u32le_from_bytes(f.read(4))

            log_fn(translate("log_header_info", total_items=total_items, some_size=some_size,
                             header_pos=header_pos, name_block_size=name_block_size))

            # ler entradas
            f.seek(header_pos)
            entries = []
            for i in range(total_items):
                chunk = f.read(24)
                if len(chunk) < 24:
                    log_fn(translate("log_entry_truncated", i=i))
                    raise EOFError(translate("log_entry_truncated", i=i))
                entries.append({
                    'name_offset': u32le_from_bytes(chunk[0:4]),
                    'comp_size':   u32le_from_bytes(chunk[4:8]),
                    'file_pos':    u32le_from_bytes(chunk[8:12]),
                    'uncomp_size': u32le_from_bytes(chunk[12:16]),
                    'comp_level':  u32le_from_bytes(chunk[16:20]),
                    'reserved':    u32le_from_bytes(chunk[20:24])
                })

            log_fn(translate("log_reading_entries", n=len(entries)))

            # bloco de nomes
            name_block = f.read(name_block_size)
            if len(name_block) < name_block_size:
                log_fn(translate("log_name_block_short", have=len(name_block), expect=name_block_size))

            outdir.mkdir(parents=True, exist_ok=True)
            file_size = path.stat().st_size

            for idx, e in enumerate(entries):
                off = e['name_offset']
                name = ""
                if off < len(name_block):
                    length = name_block.find(b'\x00', off)
                    raw = name_block[off:length]
                    raw = raw.split(b'\x00', 1)[0]
                    try:
                        name = raw.decode("utf-8", errors="replace").strip()
                    except Exception:
                        name = f"entry_{idx:04d}"
                if not name:
                    name = f"entry_{idx:04d}"

                candidate = outdir / name
                comp_size = e['comp_size']
                file_pos  = e['file_pos']
                comp_level = e['comp_level']

                if file_pos >= file_size:
                    log_fn(translate("log_file_pos_invalid", idx=idx, name=name, file_pos=file_pos, file_size=file_size))
                    raise ValueError(translate("log_file_pos_invalid", idx=idx, name=name, file_pos=file_pos, file_size=file_size))

                if comp_size == 0:
                    log_fn(translate("log_extract_entry_empty", idx=idx, name=name))
                    candidate.parent.mkdir(parents=True, exist_ok=True)
                    with open(candidate, "wb") as fo:
                        pass
                    continue

                to_read = min(comp_size, file_size - file_pos)
                f.seek(file_pos)
                block = f.read(to_read)
                if len(block) != to_read:
                    raise ValueError(f"ERRO: leitura incompleta de {name}: esperado {to_read}, lido {len(block)}")

                outdata = block
                if comp_level > 0:
                    try:
                        outdata = zlib.decompress(block)
                        log_fn(translate("log_extract_decompress", idx=idx, name=name, in_bytes=len(block), out_bytes=len(outdata)))
                    except Exception as ex:
                        log_fn(translate("log_extract_decompress", idx=idx, name=name, in_bytes=len(block), out_bytes=0))
                        out_path = candidate.with_suffix(candidate.suffix + ".z")
                        candidate.parent.mkdir(parents=True, exist_ok=True)
                        with open(out_path, "wb") as fo:
                            fo.write(block)
                        continue
                else:
                    log_fn(translate("log_extract_raw", idx=idx, name=name, size=len(block)))

                candidate.parent.mkdir(parents=True, exist_ok=True)
                with open(candidate, 'wb') as fo:
                    fo.write(outdata)

            log_fn(translate("log_extract_finished"))
            return outdir

    except Exception as ex:
        log_fn(translate("msg_error_open", err=str(ex)))
        raise

def insert_into_original(original_path: Path, log_fn=None):
    if log_fn is None:
        log_fn = logger

    p = Path(original_path)
    stem = p.stem
    src_dir = p.parent / stem

    if not p.exists():
        raise ValueError(str(p))

    try:
        with open(p, 'rb') as f:
            magic = f.read(4)
            if magic != b'POD6':
                log_fn(translate("log_magic_invalid"))
                raise ValueError(translate("log_magic_invalid"))

            total_items = u32le_from_bytes(f.read(4))
            header_size_orig = u32le_from_bytes(f.read(4))
            header_pos = u32le_from_bytes(f.read(4))
            name_block_size = u32le_from_bytes(f.read(4))

            f.seek(header_pos)
            header_tail_bytes = f.read()

        expected_items_bytes = total_items * 24
        if len(header_tail_bytes) < expected_items_bytes:
            raise ValueError("Header pos indica menos bytes do que total_items*24 — abortando insert.")

        entries = []
        for i in range(total_items):
            base = i * 24
            chunk = header_tail_bytes[base: base + 24]
            entries.append({
                'name_offset': u32le_from_bytes(chunk[0:4]),
                'comp_size': u32le_from_bytes(chunk[4:8]),
                'file_pos': u32le_from_bytes(chunk[8:12]),
                'uncomp_size': u32le_from_bytes(chunk[12:16]),
                'comp_level': u32le_from_bytes(chunk[16:20]),
                'reserved': u32le_from_bytes(chunk[20:24]),
            })

        name_block = header_tail_bytes[expected_items_bytes: expected_items_bytes + name_block_size]

        # obter nomes
        names = []
        for e in entries:
            off = e['name_offset']
            if off < len(name_block):
                length = name_block.find(b'\x00', off)
                raw = name_block[off:length]
                raw = raw.split(b'\x00', 1)[0]
                name = raw.decode('utf-8', errors='replace')
            else:
                name = ''
            names.append(name)

        # abrir para reescrever
        with open(p, 'r+b') as fh:
            fh.seek(0, os.SEEK_END)
            orig_size = fh.tell()
            fh.seek(0)
            first_128 = fh.read(128)
            if len(first_128) < 128:
                first_128 = first_128 + b'\x00' * (128 - len(first_128))

            write_pos = 128
            fh.seek(write_pos)

            updated_entries = []

            for idx, e in enumerate(entries):
                name = names[idx] or f"entry_{idx:04d}"
                src_path = src_dir / name
                log_fn(translate("log_inserting", src=str(src_path)))

                if not src_path.exists():
                    file_bytes = b''
                else:
                    with open(src_path, 'rb') as rf:
                        file_bytes = rf.read()

                uncomp_size = len(file_bytes)
                comp_level = int(e.get('comp_level', 0)) or 0

                if comp_level > 0 and uncomp_size > 0:
                    lvl = comp_level + 1
                    if lvl < 1: lvl = 1
                    if lvl > 9: lvl = 9
                    comp_bytes = zlib.compress(file_bytes, lvl)
                else:
                    comp_bytes = file_bytes

                comp_size = len(comp_bytes)
                file_pos_new = write_pos

                fh.seek(write_pos)
                if comp_size > 0:
                    fh.write(comp_bytes)

                write_pos += comp_size
                pad = (16 - (write_pos % 16)) % 16
                if pad:
                    fh.write(b'\x00' * pad)
                    write_pos += pad

                updated_entries.append({
                    'name_offset': e['name_offset'],
                    'comp_size': comp_size,
                    'file_pos': file_pos_new,
                    'uncomp_size': uncomp_size,
                    'comp_level': comp_level,
                    'reserved': e.get('reserved', 0)
                })

                log_fn(translate("log_insert_compress", name=name, comp_size=comp_size, uncomp_size=uncomp_size, file_pos_new=file_pos_new))

            header_write_pos = write_pos
            fh.seek(header_write_pos)

            for ue in updated_entries:
                fh.write(u32le_to_bytes(ue['name_offset']))
                fh.write(u32le_to_bytes(ue['comp_size']))
                fh.write(u32le_to_bytes(ue['file_pos']))
                fh.write(u32le_to_bytes(ue['uncomp_size']))
                fh.write(u32le_to_bytes(ue['comp_level']))
                fh.write(u32le_to_bytes(ue.get('reserved', 0)))

            fh.write(name_block)
            write_pos_after_header = fh.tell()

            fh.seek(0)
            fh.write(b'POD6')
            fh.write(u32le_to_bytes(total_items))
            fh.seek(4, 1)
            fh.write(u32le_to_bytes(header_write_pos))
            fh.write(u32le_to_bytes(len(name_block)))

            fh.truncate(write_pos_after_header)

        log_fn(translate("log_insert_finish"))
        return p

    except Exception as ex:
        log_fn(translate("msg_error_open", err=str(ex)))
        raise

# ==========================
# Selecionadores / integração com host
# ==========================
def selecionar_extrair_pod():
    path = filedialog.askopenfilename(
        title=translate("select_pod_file"),
        filetypes=[("POD6 files", "*.pod;*.pod6"), ("All files", "*.*")]
    )
    if not path:
        return
    p = Path(path)
    outdir = p.parent / p.stem
    threading.Thread(target=_run_extract_pod, args=(p, outdir), daemon=True).start()

def _run_extract_pod(p: Path, outdir: Path):
    try:
        out = extract_pod6_file(p, outdir, log_fn=logger)
        messagebox.showinfo(translate("msg_title_done"), translate("msg_extract_done", outdir=str(out)))
    except Exception as e:
        logger(str(e))
        messagebox.showerror(translate("msg_title_error"), str(e))

def selecionar_inserir_pod():
    path = filedialog.askopenfilename(
        title=translate("select_pod_file_insert"),
        filetypes=[("POD6 files", "*.pod;*.pod6"), ("All files", "*.*")]
    )
    if not path:
        return
    threading.Thread(target=_run_insert_pod, args=(Path(path),), daemon=True).start()

def _run_insert_pod(p: Path):
    try:
        res = insert_into_original(p, log_fn=logger)
        messagebox.showinfo(translate("msg_title_done"), translate("msg_insert_done", res=str(res)))
    except Exception as e:
        logger(str(e))
        messagebox.showerror(translate("msg_title_error"), str(e))

# ==========================
# Registro do plugin (padrão)
# ==========================
def register_plugin(log_func, option_getter, host_language="pt_BR"):
    global logger, current_language
    logger = log_func or print
    current_language = host_language

    def get_plugin_info():
        return {
            "name": translate("plugin_name"),
            "description": translate("plugin_description"),
            "commands": [
                {"label": translate("extract_pod"), "action": selecionar_extrair_pod},
                {"label": translate("insert_pod"), "action": selecionar_inserir_pod},
            ]
        }
    return get_plugin_info
