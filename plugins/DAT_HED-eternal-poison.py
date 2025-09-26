import os
import struct
import json
import threading
from tkinter import filedialog, messagebox

# ==========================
# Traduções completas
# ==========================
# ==========================
# Traduções completas
# ==========================
plugin_translations = {
    "pt_BR": {
        "plugin_name": "DAT/HED/DB Eternal Poison (PS2)",
        "plugin_description": "Extrai e reempacota arquivos de containers DAT/HED do Eternal Poison (PS2)",
        "extract_file": "Extrair arquivos .DAT/.HED",
        "rebuild_file": "Reempacotar arquivos .DAT/.HED",
        "extract_db": "Extrair textos .DB",
        "insert_db": "Inserir textos .DB",
        "select_hed_file": "Selecione o arquivo .HED",
        "select_db_file": "Selecione o arquivo .DB ou .TXT",
        "hed_file": "Arquivos HED",
        "all_files": "Todos os arquivos",

        # mensagens / títulos
        "msg_title_error": "Erro",
        "msg_title_done": "Concluído",
        "msg_done_extract": "Arquivos extraídos em: {folder}",
        "msg_done_repack": "Repack concluído: {dat}\nHED atualizado: {hed}",
        "msg_done_extract_db": "Textos extraídos em: {txt}",
        "msg_done_insert_db": "DB atualizado com sucesso: {db}",

        # logs
        "log_read_entry": "Entrada {i}: name='{name}' offset={offset} size={size} id={id_hex}",
        "log_skipped": "Entrada {i} ignorada (inválida)",
        "log_extracting": "Extraindo: {name} (offset={offset}, size={size})",
        "log_saved": "Salvo: {path}",
        "log_json_written": "JSON salvo em: {json_path}",
        "log_repacked": "Reinserido: {name} offset={offset} size={size}",
        "warn_missing": "[AVISO] Arquivo não encontrado para reinserção: {name}",
        "log_read_db_entry": "Entrada DB {i}: ID={id_hex} TEXTO='{text}'",

        # erros
        "err_unexpected": "Erro inesperado: {error}",
    },

    "en_US": {
        "plugin_name": "DAT/HED/DB Eternal Poison (PS2)",
        "plugin_description": "Extracts and repacks DAT/HED container files from Eternal Poison (PS2)",
        "extract_file": "Extract .DAT/.HED files",
        "rebuild_file": "Repack .DAT/.HED files",
        "extract_db": "Extract .DB texts",
        "insert_db": "Insert .DB texts",
        "select_hed_file": "Select the .HED file",
        "select_db_file": "Select the .DB or .TXT file",
        "hed_file": "HED files",
        "all_files": "All files",

        # messages / titles
        "msg_title_error": "Error",
        "msg_title_done": "Done",
        "msg_done_extract": "Files extracted to: {folder}",
        "msg_done_repack": "Repack finished: {dat}\nHED updated: {hed}",
        "msg_done_extract_db": "Texts extracted to: {txt}",
        "msg_done_insert_db": "DB successfully updated: {db}",

        # logs
        "log_read_entry": "Entry {i}: name='{name}' offset={offset} size={size} id={id_hex}",
        "log_skipped": "Entry {i} skipped (invalid)",
        "log_extracting": "Extracting: {name} (offset={offset}, size={size})",
        "log_saved": "Saved: {path}",
        "log_json_written": "JSON saved at: {json_path}",
        "log_repacked": "Reinserted: {name} offset={offset} size={size}",
        "warn_missing": "[WARN] File missing for reinsertion: {name}",
        "log_read_db_entry": "DB Entry {i}: ID={id_hex} TEXT='{text}'",

        # errors
        "err_unexpected": "Unexpected error: {error}",
    },

    "es_ES": {
        "plugin_name": "DAT/HED/DB Eternal Poison (PS2)",
        "plugin_description": "Extrae y reempaqueta archivos contenedores DAT/HED de Eternal Poison (PS2)",
        "extract_file": "Extraer archivos .DAT/.HED",
        "rebuild_file": "Reempaquetar archivos .DAT/.HED",
        "extract_db": "Extraer textos .DB",
        "insert_db": "Insertar textos .DB",
        "select_hed_file": "Seleccione el archivo .HED",
        "select_db_file": "Seleccione el archivo .DB o .TXT",
        "hed_file": "Archivos HED",
        "all_files": "Todos los archivos",

        # mensajes / títulos
        "msg_title_error": "Error",
        "msg_title_done": "Completado",
        "msg_done_extract": "Archivos extraídos en: {folder}",
        "msg_done_repack": "Repack completado: {dat}\nHED actualizado: {hed}",
        "msg_done_extract_db": "Textos extraídos en: {txt}",
        "msg_done_insert_db": "DB actualizado con éxito: {db}",

        # logs
        "log_read_entry": "Entrada {i}: nombre='{name}' offset={offset} tamaño={size} id={id_hex}",
        "log_skipped": "Entrada {i} omitida (inválida)",
        "log_extracting": "Extrayendo: {name} (offset={offset}, tamaño={size})",
        "log_saved": "Guardado: {path}",
        "log_json_written": "JSON guardado en: {json_path}",
        "log_repacked": "Reinsertado: {name} offset={offset} tamaño={size}",
        "warn_missing": "[AVISO] Archivo no encontrado para reinsertar: {name}",
        "log_read_db_entry": "Entrada DB {i}: ID={id_hex} TEXTO='{text}'",

        # errores
        "err_unexpected": "Error inesperado: {error}",
    }
}


# ==========================
# Globais e utilitários
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

def pad_to_boundary_size(n, boundary):
    return (boundary - (n % boundary)) % boundary

# ==========================
# Registro do plugin
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
                {"label": translate("extract_file"), "action": selecionar_extrair},
                {"label": translate("rebuild_file"), "action": selecionar_remontar},
                {"label": translate("extract_db"), "action": selecionar_extrair_db},
                {"label": translate("insert_db"), "action": selecionar_inserir_db},
            ]
        }
    return get_plugin_info


def selecionar_extrair():
    path = filedialog.askopenfilename(
        title=translate("select_hed_file"),
        filetypes=[(translate("hed_file"), "*.hed"), (translate("all_files"), "*.*")]
    )
    if path:
        threading.Thread(target=extract_ep, args=(path,), daemon=True).start()

def selecionar_remontar():
    path = filedialog.askopenfilename(
        title=translate("select_hed_file"),
        filetypes=[(translate("hed_file"), "*.hed"), (translate("all_files"), "*.*")]
    )
    if path:
        threading.Thread(target=repack_ep, args=(path,), daemon=True).start()

# ==========================
# Leitura do HED (size, offset, name, id)
# ==========================
def read_hed_entries(hed_path):
    entries = []
    try:
        with open(hed_path, "rb") as f:
            f.seek(88)
            i = 0
            while True:
                pos = f.tell()
                data = f.read(44)   # 4 (size) + 4 (offset) + 32 (name) + 4 (id)
                if not data or len(data) < 44:
                    break

                offset, size = struct.unpack("<II", data[:8])  # size then offset (LE)
                raw_name = data[8:40]
                name = raw_name.split(b"\x00", 1)[0].decode("utf-8", errors="ignore")
                file_id = data[40:44]
                id_hex = file_id.hex().upper()

                # validar entradas
                if name == "--DirEnd--" or file_id == b"\x00\x00\x00\x00":
                    logger(translate("log_skipped", i=i))
                    i += 1
                    continue

                entries.append({
                    "NAME": name,
                    "OFFSET": offset,
                    "SIZE": size,
                    "ID_BIN": file_id,
                    "ID_HEX": id_hex,
                    "HED_POS": pos
                })
                logger(translate("log_read_entry", i=i, name=name, offset=offset, size=size, id_hex=id_hex))
                i += 1

    except Exception as e:
        logger(translate("err_unexpected", error=str(e)))
        raise

    return entries

# ==========================
# EXTRAÇÃO
# ==========================
def extract_ep(hed_path):
    try:
        if not os.path.exists(hed_path):
            messagebox.showerror(translate("msg_title_error"), translate("err_unexpected", error=f"HED not found: {hed_path}"))
            return None, None

        dat_path = os.path.splitext(hed_path)[0] + ".dat"
        if not os.path.exists(dat_path):
            messagebox.showerror(translate("msg_title_error"), translate("err_unexpected", error=f"DAT not found: {dat_path}"))
            return None, None

        entries = read_hed_entries(hed_path)
        if not entries:
            messagebox.showinfo(translate("msg_title_done"), translate("msg_done_extract", folder=os.path.splitext(hed_path)[0]))
            return None, None

        base_dir = os.path.dirname(hed_path)
        base_name = os.path.splitext(os.path.basename(dat_path))[0]
        out_dir = os.path.join(base_dir, base_name)
        os.makedirs(out_dir, exist_ok=True)

        with open(dat_path, "rb") as df:
            for e in entries:
                df.seek(e["OFFSET"])
                data = df.read(e["SIZE"])
                out_path = os.path.join(out_dir, e["NAME"])
                out_dirname = os.path.dirname(out_path)
                if out_dirname and not os.path.exists(out_dirname):
                    os.makedirs(out_dirname, exist_ok=True)
                with open(out_path, "wb") as outf:
                    outf.write(data)
                logger(translate("log_extracting", name=e["NAME"], offset=e["OFFSET"], size=e["SIZE"]))
                logger(translate("log_saved", path=out_path))

        messagebox.showinfo(translate("msg_title_done"), translate("msg_done_extract", folder=out_dir))

    except Exception as e:
        messagebox.showerror(translate("msg_title_error"), translate("err_unexpected", error=str(e)))
        logger(translate("err_unexpected", error=str(e)))
        return None, None

# ==========================
# REPACK (sobrescreve HED em disco)
# ==========================
def repack_ep(hed_path):
    try:
        entries = read_hed_entries(hed_path)
        if not entries:
            messagebox.showinfo(translate("msg_title_done"), translate("msg_done_repack", dat="", hed=hed_path))
            return None, None

        base_dir = os.path.dirname(hed_path)
        base_name = os.path.splitext(os.path.basename(hed_path))[0]
        extracted_folder = os.path.join(base_dir, base_name)
        new_dat_path = os.path.splitext(hed_path)[0] + ".dat"

        with open(new_dat_path, "wb") as dat_out, open(hed_path, "rb+") as hed_io:
            current_offset = 0
            for e in entries:
                in_path = os.path.join(extracted_folder, e["NAME"])
                if not os.path.exists(in_path):
                    logger(translate("warn_missing", name=e["NAME"]))
                    continue

                with open(in_path, "rb") as inf:
                    data = inf.read()

                # escreve no novo DAT
                dat_out.seek(current_offset)
                dat_out.write(data)

                # padding até múltiplo de 0x4000
                pad = pad_to_boundary_size(len(data), 0x4000)
                if pad:
                    dat_out.write(b"\x00" * pad)

                # sobrescreve diretamente no HED: primeiro offset, depois size (LE)
                hed_io.seek(e["HED_POS"])
                hed_io.write(struct.pack("<II", current_offset, len(data)))

                logger(translate("log_repacked", name=e["NAME"], offset=current_offset, size=len(data)))

                current_offset = dat_out.tell()
                
            dat_out.truncate()

        messagebox.showinfo(translate("msg_title_done"),
                            translate("msg_done_repack", dat=new_dat_path, hed=hed_path))
        logger(translate("msg_done_repack", dat=new_dat_path, hed=hed_path))
        return new_dat_path, hed_path

    except Exception as e:
        messagebox.showerror(translate("msg_title_error"), translate("err_unexpected", error=str(e)))
        logger(translate("err_unexpected", error=str(e)))
        return None, None


# ==========================
# Seleção DB
# ==========================
def selecionar_extrair_db():
    path = filedialog.askopenfilename(
        title=translate("select_db_file"),
        filetypes=[("DB files", "*.db"), (translate("all_files"), "*.*")]
    )
    if path:
        threading.Thread(target=extract_db, args=(path,), daemon=True).start()

# ==========================
# Extração DB
# ==========================
def extract_db(db_path):
    try:
        if not os.path.exists(db_path):
            messagebox.showerror(translate("msg_title_error"), f"DB not found: {db_path}")
            return

        base_dir = os.path.dirname(db_path)
        base_name = os.path.splitext(os.path.basename(db_path))[0]
        out_txt = os.path.join(base_dir, base_name + ".txt")

        texts = []
        i = 0
        with open(db_path, "rb") as f:
            total_texts_byte = f.read(1)
            total_texts = total_texts_byte[0]
            for i in range(total_texts):
                id_bytes = f.read(4)
                if not id_bytes or len(id_bytes) < 4:
                    break
                size_byte = f.read(1)
                if not size_byte:
                    break
                size = size_byte[0]
                text_bytes = f.read(size)
                if not text_bytes:
                    break
                text = text_bytes.rstrip(b"\x00").decode("ansi", errors="ignore").replace("\n", "[BR]")
                id_hex = id_bytes.hex().upper()
                texts.append(f"{id_hex}:{text}")
                logger(translate("log_read_db_entry", i=i, id_hex=id_hex, text=text))
                i += 1

        with open(out_txt, "w", encoding="ansi") as out_file:
            out_file.write("\n".join(texts))

        messagebox.showinfo(translate("msg_title_done"), translate("msg_done_extract_db", txt=out_txt))

    except Exception as e:
        messagebox.showerror(translate("msg_title_error"), translate("err_unexpected", error=str(e)))
        logger(translate("err_unexpected", error=str(e)))

# ==========================
# Seleção DB para reinserção
# ==========================
def selecionar_inserir_db():
    db_path = filedialog.askopenfilename(
        title=translate("select_db_file"),
        filetypes=[("DB files", "*.db"), (translate("all_files"), "*.*")]
    )
    if not db_path:
        return  # retorna se o usuário cancelar

    base_dir = os.path.dirname(db_path)
    base_name = os.path.splitext(os.path.basename(db_path))[0]
    txt_path = os.path.join(base_dir, base_name + ".txt")

    threading.Thread(target=insert_db, args=(db_path, txt_path), daemon=True).start()


# ==========================
# Inserção DB
# ==========================
def insert_db(db_path, txt_path):
    try:
        if not os.path.exists(db_path):
            messagebox.showerror(translate("msg_title_error"), f"DB not found: {db_path}")
            return
        if not os.path.exists(txt_path):
            messagebox.showerror(translate("msg_title_error"), f"TXT not found: {txt_path}")
            return

        # Lê o TXT
        lines = []
        with open(txt_path, "r", encoding="ansi") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if ":" not in line:
                    continue
                id_hex, text = line.split(":", 1)
                text_bytes = text.replace("[BR]", "\n").encode("ansi") + b"\x00"
                lines.append((id_hex, text_bytes))

        total_texts = len(lines)

        # Sobrescreve o DB
        with open(db_path, "wb") as f:
            f.write(bytes([total_texts]))  # 1 byte para total de textos
            for id_bytes, text_bytes in lines[:total_texts]:
                id_bytes_hex = bytes.fromhex(id_bytes)  # con
                size = len(text_bytes)
                f.write(id_bytes_hex)            # 4 bytes ID
                f.write(bytes([size]))       # 1 byte tamanho do texto
                f.write(text_bytes)          # texto em ANSI
            
            f.truncate()

        messagebox.showinfo(translate("msg_title_done"), f"DB atualizado com sucesso: {db_path}")

    except Exception as e:
        messagebox.showerror(translate("msg_title_error"), translate("err_unexpected", error=str(e)))
        logger(translate("err_unexpected", error=str(e)))