import os
import struct
import json
import threading
from tkinter import filedialog, messagebox

# ==========================
# Traduções (todas as strings de UI/log/erros aqui)
# ==========================
plugin_translations = {
    "pt_BR": {
        "plugin_name": "DAT TT Games TOOL",
        "plugin_description": "Extrai e reimporta arquivos .DAT TT Games",
        "extract_file": "Extrair arquivos",
        "reinsert_file": "Reinserir arquivos (selecionar JSON)",
        "select_dat_file": "Selecione o arquivo DAT",
        "select_json_file": "Selecione o JSON",

        # logs
        "log_extracting": "EXTRAINDO: {filename}",
        "log_parse_error_short": "Arquivo muito curto para conter header válido.",
        "log_info_off_invalid": "INFO_OFF inválido.",
        "log_unsupported_new_format": "Formato novo (CC40TAD) não suportado",
        "log_failed_old_header": "Falha ao ler cabeçalho do formato antigo.",
        "log_entry_invalid": "Entrada #{i} inválida.",
        "log_written_json": "JSON salvo em: {json_path}",
        "log_extracted_folder": "Arquivos extraídos para: {folder}",
        "log_rebuild_started": "Iniciando rebuild a partir do JSON: {json_path}",
        "log_inserting": "Inserindo: {filename} -> {path}",
        "log_rebuild_completed": "Reconstrução finalizada: {out_path}",
        "log_rebuild_updated_json": "JSON atualizado: {json_path}",
        "log_wrote_info_block": "Escreveu bloco INFO modificado no novo DAT (NEW_INFO_OFF={off}).",

        # messagebox titles / messages
        "message_title_error": "Erro",
        "message_title_success": "Sucesso",
        "message_extraction_complete": "Arquivos extraídos para:\n{folder}\nJSON salvo em:\n{json_path}",
        "message_dat_not_found": "Arquivo DAT original não encontrado:\n{path}",
        "message_extracted_folder_missing": "Pasta extraída não encontrada:\n{path}",
        "rebuild_error_title": "Erro durante rebuild",

        # exceptions (traduzidas)
        "error_json_invalid": "JSON inválido - esperado lista de entradas",
        "error_entry_off_missing": "ENTRY_OFF ausente na entrada INDEX {index}",
        "error_file_not_found": "Arquivo não encontrado: {path}",
        "error_rel_offset_invalid": "Rel offset inválido para ENTRY_OFF {entry_off} (rel={rel})",
    },
    "en_US": {
        "plugin_name": "DAT TT Games TOOL",
        "plugin_description": "Extracts and reinserts .DAT TT Games files",
        "extract_file": "Extract files",
        "reinsert_file": "Reinsert files (select JSON)",
        "select_dat_file": "Select DAT file",
        "select_json_file": "Select JSON file",

        # logs
        "log_extracting": "EXTRACTING: {filename}",
        "log_parse_error_short": "File too short to contain valid header.",
        "log_info_off_invalid": "INFO_OFF invalid.",
        "log_unsupported_new_format": "New format (CC40TAD) not supported",
        "log_failed_old_header": "Failed reading old-format header.",
        "log_entry_invalid": "Entry #{i} invalid.",
        "log_written_json": "JSON saved at: {json_path}",
        "log_extracted_folder": "Files extracted to: {folder}",
        "log_rebuild_started": "Starting rebuild from JSON: {json_path}",
        "log_inserting": "Inserting: {filename} -> {path}",
        "log_rebuild_completed": "Rebuild finished: {out_path}",
        "log_rebuild_updated_json": "JSON updated: {json_path}",
        "log_wrote_info_block": "Wrote modified INFO block in new DAT (NEW_INFO_OFF={off}).",

        # messagebox titles / messages
        "message_title_error": "Error",
        "message_title_success": "Success",
        "message_extraction_complete": "Files extracted to:\n{folder}\nJSON saved at:\n{json_path}",
        "message_dat_not_found": "Original DAT file not found:\n{path}",
        "message_extracted_folder_missing": "Extracted folder not found:\n{path}",
        "rebuild_error_title": "Error during rebuild",

        # exceptions (translated)
        "error_json_invalid": "Invalid JSON - expected list of entries",
        "error_entry_off_missing": "ENTRY_OFF missing in entry INDEX {index}",
        "error_file_not_found": "File not found: {path}",
        "error_rel_offset_invalid": "Invalid relative offset for ENTRY_OFF {entry_off} (rel={rel})",
    },
    "es_ES": {
        "plugin_name": "DAT TT Games TOOL",
        "plugin_description": "Extrae y reimporta archivos .DAT TT Games",
        "extract_file": "Extraer archivos",
        "reinsert_file": "Reinsertar archivos (seleccionar JSON)",
        "select_dat_file": "Seleccionar archivo DAT",
        "select_json_file": "Seleccionar JSON",

        # logs
        "log_extracting": "EXTRAÍENDO: {filename}",
        "log_parse_error_short": "Archivo demasiado corto para contener un header válido.",
        "log_info_off_invalid": "INFO_OFF inválido.",
        "log_unsupported_new_format": "Formato nuevo (CC40TAD) no soportado",
        "log_failed_old_header": "Error al leer el header del formato antiguo.",
        "log_entry_invalid": "Entrada #{i} inválida.",
        "log_written_json": "JSON guardado en: {json_path}",
        "log_extracted_folder": "Archivos extraídos en: {folder}",
        "log_rebuild_started": "Iniciando reconstrucción desde JSON: {json_path}",
        "log_inserting": "Insertando: {filename} -> {path}",
        "log_rebuild_completed": "Reconstrucción finalizada: {out_path}",
        "log_rebuild_updated_json": "JSON actualizado: {json_path}",
        "log_wrote_info_block": "Escribió el bloque INFO modificado en el nuevo DAT (NEW_INFO_OFF={off}).",

        # messagebox titles / messages
        "message_title_error": "Error",
        "message_title_success": "Éxito",
        "message_extraction_complete": "Archivos extraídos en:\n{folder}\nJSON guardado en:\n{json_path}",
        "message_dat_not_found": "Archivo DAT original no encontrado:\n{path}",
        "message_extracted_folder_missing": "Carpeta extraída no encontrada:\n{path}",
        "rebuild_error_title": "Error durante reconstrucción",

        # exceptions (translated)
        "error_json_invalid": "JSON inválido - se esperaba una lista de entradas",
        "error_entry_off_missing": "ENTRY_OFF ausente en la entrada INDEX {index}",
        "error_file_not_found": "Archivo no encontrado: {path}",
        "error_rel_offset_invalid": "Offset relativo inválido para ENTRY_OFF {entry_off} (rel={rel})",
    }
}

# ==========================
# Globais do plugin
# ==========================
global ALIGN
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
    Padrão: register_plugin(log_func, option_getter, host_language="pt_BR")
    Retorna get_plugin_info() utilizado pelo host (ALL FOR ONE).
    """
    global logger, current_language
    logger = log_func or print
    current_language = host_language

    def get_plugin_info():
        return {
            "name": translate("plugin_name"),
            "description": translate("plugin_description"),
            "commands": [
                {"label": translate("extract_file"), "action": select_dat_file},
                {"label": translate("reinsert_file"), "action": select_json_file},
            ]
        }
    return get_plugin_info

# ==========================
# Código convertido (lógica intacta, sem interface)
# ==========================
ALIGN = 0x200  # 512 bytes

def align_up(x, a):
    return (x + (a - 1)) & ~(a - 1)

def parse_old_format_names(data, INFO_OFF, FILES, name_field_size):
    names_offset_table = INFO_OFF + 8 + FILES * 16
    NAMES = struct.unpack_from("<I", data, names_offset_table)[0]
    name_info_offset = names_offset_table + 4
    names_offset = name_info_offset + NAMES * name_field_size
    names_crc_offset = struct.unpack_from("<I", data, names_offset)[0]
    names_offset_current = names_offset + 4
    names_crc_offset += names_offset_current

    temp_array = [""] * 65536
    names_list = [""] * FILES
    name_index = 0

    for i in range(FILES):
        next_val = 1
        name = ""
        full_path = ""
        while next_val > 0:
            next_val = struct.unpack_from("<h", data, name_info_offset)[0]
            prev = struct.unpack_from("<h", data, name_info_offset + 2)[0]
            name_offset = struct.unpack_from("<i", data, name_info_offset + 4)[0]
            if name_field_size == 12:
                _ = struct.unpack_from("<I", data, name_info_offset + 8)[0]
            name_info_offset += name_field_size

            if name_offset > 0:
                real_offset = names_offset_current + name_offset
                name_bytes = bytearray()
                while real_offset < len(data) and data[real_offset] != 0:
                    name_bytes.append(data[real_offset])
                    real_offset += 1
                name = name_bytes.decode('utf-8', errors='ignore')
                if name and ord(name[0]) >= 0xF0:
                    name = ""

            if prev != 0:
                full_path = temp_array[prev]

            temp_array[name_index] = full_path
            if next_val > 0 and name:
                full_path = full_path + name + "\\"
            name_index += 1

        full_name = full_path + name
        names_list[i] = "\\" + full_name.lower()

    return names_list

def extract_dat(filepath):
    # preserved original logic; filepath must be provided (no GUI)
    if not filepath:
        return

    with open(filepath, "rb") as f:
        data = f.read()

    try:
        INFO_OFF, INFO_SIZE = struct.unpack_from("<II", data, 0)
    except struct.error:
        messagebox.showerror(translate("message_title_error"), translate("log_parse_error_short"))
        return

    if INFO_OFF & 0x80000000:
        INFO_OFF ^= 0xFFFFFFFF
        INFO_OFF <<= 8
        INFO_OFF += 0x100

    try:
        version_type1 = struct.unpack_from("<I", data, INFO_OFF)[0]
    except Exception:
        messagebox.showerror(translate("message_title_error"), translate("log_info_off_invalid"))
        return

    version_str = version_type1.to_bytes(4, 'little').decode('ascii', errors='ignore')
    if version_str in ['4CC.', '.CC4']:
        messagebox.showerror(translate("message_title_error"), translate("log_unsupported_new_format"))
        return

    try:
        format_byte_order = struct.unpack_from("<I", data, INFO_OFF)[0]
        FILES = struct.unpack_from("<I", data, INFO_OFF + 4)[0]
    except Exception:
        messagebox.showerror(translate("message_title_error"), translate("log_failed_old_header"))
        return

    name_field_size = 12 if format_byte_order <= -5 else 8

    files_info = []
    for i in range(FILES):
        entry_off = INFO_OFF + 8 + i * 16
        try:
            OFFSET_raw, ZSIZE, SIZE = struct.unpack_from("<III", data, entry_off)
        except Exception:
            messagebox.showerror(translate("message_title_error"), translate("log_entry_invalid", i=i))
            return
        OFFSET = OFFSET_raw << 8
        PACKED = data[entry_off + 12]
        files_info.append({
            "INDEX": i,
            "ENTRY_OFF": entry_off,
            "OFFSET": OFFSET,
            "ZSIZE": ZSIZE,
            "SIZE": SIZE,
            "PACKED": PACKED
        })

    names_list = parse_old_format_names(data, INFO_OFF, FILES, name_field_size)

    base_dir = os.path.dirname(filepath)
    dat_name = os.path.splitext(os.path.basename(filepath))[0]
    extracted_folder = os.path.join(base_dir, f"{dat_name}_extracted")
    os.makedirs(extracted_folder, exist_ok=True)

    json_path = os.path.join(base_dir, f"{dat_name}.json")

    extracted_data = []
    for i, entry in enumerate(files_info):
        filename = names_list[i].lstrip("\\").replace("\\", os.sep).upper()
        logger(translate("log_extracting", filename=filename))
        file_data = data[entry['OFFSET']:entry['OFFSET'] + entry['ZSIZE']]
        out_path = os.path.join(extracted_folder, filename)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "wb") as f_out:
            f_out.write(file_data)

        extracted_data.append({
            "INDEX": entry["INDEX"],
            "ENTRY_OFF": entry["ENTRY_OFF"],
            "OFFSET": entry["OFFSET"],
            "ZSIZE": entry["ZSIZE"],
            "SIZE": entry["SIZE"],
            "PACKED": entry["PACKED"],
            "FILENAME": filename
        })

    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(extracted_data, jf, indent=4, ensure_ascii=False)

    logger(translate("log_extracted_folder", folder=extracted_folder))
    logger(translate("log_written_json", json_path=json_path))
    messagebox.showinfo(translate("message_title_success"), translate("message_extraction_complete", folder=extracted_folder, json_path=json_path))

def rebuild_dat(original_dat_name, extracted_folder, json_path, out_path):
    # Lê cabeçalho e bloco INFO original
    FILE_TYPE = 0
    with open(original_dat_name, "rb") as ori_dat:
        ORIGINAL_HEADER = ori_dat.read(512)                 # preserva os 512 bytes iniciais
        ori_dat.seek(0)
        OLD_INFO_OFF, OLD_INFO_SIZE = struct.unpack("<II", ori_dat.read(8))
        if OLD_INFO_OFF & 0x80000000:
            OLD_INFO_OFF ^= 0xFFFFFFFF
            OLD_INFO_OFF <<= 8
            OLD_INFO_OFF += 0x100
            FILE_TYPE = 1
        ori_dat.seek(OLD_INFO_OFF)
        ORIGINAL_FILE_INFO = ori_dat.read(OLD_INFO_SIZE)   # bloco inteiro (inclui tabela + names + crc etc.)

    # Carrega JSON (a lista com entradas)
    with open(json_path, "r", encoding="utf-8") as jf:
        file_entries = json.load(jf)

    if not isinstance(file_entries, list):
        raise ValueError(translate("error_json_invalid"))

    # Ordena pela posição original (OFFSET) para reescrever na ordem original
    file_entries.sort(key=lambda x: x["OFFSET"])

    offsets_table = []  # guarda (offset_written, len)
    # converte ORIGINAL_FILE_INFO em bytearray mutável para sobrescrever apenas os campos
    info_bytes = bytearray(ORIGINAL_FILE_INFO)

    # Abre novo arquivo e escreve header original
    with open(out_path, "wb") as f:
        f.write(ORIGINAL_HEADER)
        if FILE_TYPE == 1:
            f.seek(2048)

        # Escreve os arquivos na ordem
        for i, entry in enumerate(file_entries):
            in_file = os.path.join(extracted_folder, entry["FILENAME"])
            logger(translate("log_inserting", filename=entry["FILENAME"], path=in_file))
            
            if not os.path.exists(in_file):
                raise FileNotFoundError(translate("error_file_not_found", path=in_file))

            with open(in_file, "rb") as fin:
                data = fin.read()

            # Detecta compressão via magic LZ2K
            if data.startswith(b"LZ2K"):
                entry["PACKED"] = 2
                entry["ZSIZE"] = len(data)   # tamanho comprimido atual (salva o real)
                # mantemos entry["SIZE"] (descomprimido) como estava no JSON original
            else:
                entry["PACKED"] = 0
                entry["SIZE"] = len(data)
                entry["ZSIZE"] = len(data)

            # Offset absoluto onde o arquivo será escrito no novo DAT
            offset_now = f.tell()
            entry["OFFSET"] = offset_now
            f.write(data)
            offsets_table.append((offset_now, len(data)))

            
            if FILE_TYPE == 0:
                if i < len(file_entries) - 1:
                    pad = (ALIGN - (f.tell() % ALIGN)) % ALIGN
                    if pad:
                        f.write(b"\x00" * pad)
                        
            else:
                ALIGN = 0x800
                pad = (ALIGN - (f.tell() % ALIGN)) % ALIGN
                if pad:
                    f.write(b"\x00" * pad)

            # --- Atualiza também os bytes na cópia ORIGINAL_FILE_INFO (em memória) ---
            # ENTRY_OFF no JSON é o offset absoluto original da entrada (entry_off)
            entry_off_abs = entry.get("ENTRY_OFF")
            if entry_off_abs is None:
                # se ENTRY_OFF não existir no JSON, não conseguimos atualizar a tabela in-place
                raise ValueError(translate("error_entry_off_missing", index=entry.get("INDEX")))

            # relativo dentro do bloco ORIGINAL_FILE_INFO
            rel = entry_off_abs - OLD_INFO_OFF
            if rel < 0 or rel + 16 > len(info_bytes):
                raise IndexError(translate("error_rel_offset_invalid", entry_off=entry_off_abs, rel=rel))

            OFFSET_raw = entry["OFFSET"] >> 8
            ZSIZE = entry["ZSIZE"]
            SIZE = entry["SIZE"]
            PACKED = entry["PACKED"] & 0xFF

            # escreve os 3 uint32 (12 bytes) no lugar correto
            info_bytes[rel:rel+12] = struct.pack("<III", OFFSET_raw, ZSIZE, SIZE)
            # escreve o byte PACKED na posição rel+12 (o quarto byte dentro dos 16 bytes da entrada)
            info_bytes[rel+12] = PACKED
            # os 3 bytes restantes (rel+13..rel+15) mantemos como estavam (não tocar)

        # Agora que todos os arquivos foram escritos e info_bytes atualizado,
        # vamos escrever o bloco info modificado no novo local
        NEW_INFO_OFF = f.tell()
        f.write(info_bytes)   # escreve o bloco completo (todas as entradas + nomes + crc etc.)

        NEW_INFO_SIZE = len(info_bytes)

        # Atualiza header (INFO_OFF e INFO_SIZE) na posição 0 do novo DAT
        f.seek(0)
        if FILE_TYPE == 1:
            NEW_INFO_OFF = NEW_INFO_OFF - 0x100
            NEW_INFO_OFF >>= 8
            NEW_INFO_OFF = NEW_INFO_OFF ^ 0xFFFFFFFF
            f.write(struct.pack("<II", NEW_INFO_OFF, NEW_INFO_SIZE))
        
        else:
            f.write(struct.pack("<II", NEW_INFO_OFF, NEW_INFO_SIZE))
            f.seek(132)
            f.write(struct.pack("<I", NEW_INFO_OFF))

    logger(translate("log_wrote_info_block", off=NEW_INFO_OFF))

    # Salva JSON atualizado com novos offsets/tamanhos/packed
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(file_entries, jf, indent=4, ensure_ascii=False)

def do_rebuild(json_path):
    # wrapper para reconstrução (json_path obrigatório)
    base_dir = os.path.dirname(json_path)
    dat_name = os.path.splitext(os.path.basename(json_path))[0]  # ex: GAME
    original_dat_name = os.path.join(base_dir, f"{dat_name}.dat")
    extracted_folder = os.path.join(base_dir, f"{dat_name}_extracted")
    out_path = os.path.join(base_dir, f"{dat_name}_rebuild.dat")

    # Verificações simples
    if not os.path.exists(original_dat_name):
        messagebox.showerror(translate("message_title_error"), translate("message_dat_not_found", path=original_dat_name))
        return
    if not os.path.isdir(extracted_folder):
        messagebox.showerror(translate("message_title_error"), translate("message_extracted_folder_missing", path=extracted_folder))
        return

    logger(translate("log_rebuild_started", json_path=json_path))

    try:
        rebuild_dat(original_dat_name, extracted_folder, json_path, out_path)
        logger(translate("log_rebuild_completed", out_path=out_path))
        logger(translate("log_rebuild_updated_json", json_path=json_path))
        messagebox.showinfo(translate("message_title_success"), translate("log_rebuild_completed", out_path=out_path))
    except Exception as e:
        # mantém exceção técnica mas mostra diálogo traduzido
        messagebox.showerror(translate("rebuild_error_title"), str(e))

# ==========================
# Funções de seleção integradas ao host via register_plugin
# ==========================
def select_dat_file():
    file_path = filedialog.askopenfilename(title=translate("select_dat_file"), filetypes=[("DAT files", "*.dat"), ("All files", "*.*")])
    if file_path:
        threading.Thread(target=extract_dat, args=(file_path,), daemon=True).start()

def select_json_file():
    json_path = filedialog.askopenfilename(title=translate("select_json_file"), filetypes=[("JSON Files", "*.json"), ("All files", "*.*")])
    if json_path:
        threading.Thread(target=do_rebuild, args=(json_path,), daemon=True).start()
