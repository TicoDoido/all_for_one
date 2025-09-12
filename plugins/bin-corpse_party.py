import os
import struct
import json
import threading
from tkinter import filedialog, messagebox

# importa unlzss diretamente
from plugins.DECOMP_CODE.lzss_codec import unlzss

# ==========================
# Traduções
# ==========================
plugin_translations = {
    "pt_BR": {
        "plugin_name": "BIN Corpse Party Extrator",
        "plugin_description": "Extrai arquivos de image.bin (formato PACK do PSP)",
        "extract_file": "Extrair image.bin (PACK)",
        "select_image_file": "Selecione o image.bin (PACK)",
        "image_bin": "image.bin",
        "all_files": "Todos os arquivos",

        # logs / mensagens
        "log_detected_magic": "Magic detectado: {magic} no offset {offset}",
        "log_invalid_magic": "Magic inválido (esperado 'PACK') — abortando.",
        "error_invalid_magic": "Arquivo não é um PACK válido",
        "log_read_count": "Total de arquivos: {count}",
        "log_entry_found": "Entrada {i} encontrada em {entry_pos}: name='{name}' offset={offset} size={size}",
        "log_extracting": "Extraindo: {name} (offset={offset}, size={size})",
        "log_lzss_detected": "Arquivo {name} detectado como LZSS — descompactando.",
        "log_saved": "Arquivo salvo em: {path}",
        "log_json_written": "JSON salvo em: {json_path}",
        "log_extracted_folder": "Arquivos extraídos em: {folder}",

        # UI
        "msg_title_error": "Erro",
        "msg_title_done": "Concluído",
        "err_file_not_found": "Arquivo não encontrado: {path}",
        "err_unexpected": "Erro inesperado: {error}",
    },
    "en_US": {
        "plugin_name": "BIN Corpse Party Extractor",
        "plugin_description": "Extract files from image.bin (PSP PACK format)",
        "extract_file": "Extract image.bin (PACK)",
        "select_image_file": "Select image.bin (PACK)",
        "image_bin": "image.bin",
        "all_files": "All files",

        # logs / messages
        "log_detected_magic": "Detected magic: {magic} at offset {offset}",
        "log_invalid_magic": "Invalid magic (expected 'PACK') — aborting.",
        "error_invalid_magic": "File is not a valid PACK",
        "log_read_count": "Total files: {count}",
        "log_entry_found": "Entry {i} at {entry_pos}: name='{name}' offset={offset} size={size}",
        "log_extracting": "Extracting: {name} (offset={offset}, size={size})",
        "log_lzss_detected": "File {name} detected as LZSS — decompressing.",
        "log_saved": "File saved to: {path}",
        "log_json_written": "JSON saved at: {json_path}",
        "log_extracted_folder": "Files extracted to: {folder}",

        # UI
        "msg_title_error": "Error",
        "msg_title_done": "Done",
        "err_file_not_found": "File not found: {path}",
        "err_unexpected": "Unexpected error: {error}",
    },
    "es_ES": {
        "plugin_name": "BIN Corpse Party Extractor",
        "plugin_description": "Extrae archivos de image.bin (formato PACK PSP)",
        "extract_file": "Extraer image.bin (PACK)",
        "select_image_file": "Seleccionar image.bin (PACK)",
        "image_bin": "image.bin",
        "all_files": "Todos los archivos",

        # logs / mensajes
        "log_detected_magic": "Magic detectado: {magic} en offset {offset}",
        "log_invalid_magic": "Magic inválido (se esperaba 'PACK') — abortando.",
        "error_invalid_magic": "El archivo no es un PACK válido",
        "log_read_count": "Total de archivos: {count}",
        "log_entry_found": "Entrada {i} en {entry_pos}: name='{name}' offset={offset} size={size}",
        "log_extracting": "Extrayendo: {name} (offset={offset}, size={size})",
        "log_lzss_detected": "Archivo {name} detectado como LZSS — descomprimiendo.",
        "log_saved": "Archivo guardado en: {path}",
        "log_json_written": "JSON guardado en: {json_path}",
        "log_extracted_folder": "Archivos extraídos en: {folder}",

        # UI
        "msg_title_error": "Error",
        "msg_title_done": "Completado",
        "err_file_not_found": "Archivo no encontrado: {path}",
        "err_unexpected": "Error inesperado: {error}",
    }
}

# ==========================
# Globais do plugin
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
    global logger, current_language
    logger = log_func or print
    current_language = host_language

    def get_plugin_info():
        return {
            "name": translate("plugin_name"),
            "description": translate("plugin_description"),
            "commands": [
                {"label": translate("extract_file"), "action": selecionar_extrair},
            ]
        }
    return get_plugin_info

def selecionar_extrair():
    filepath = filedialog.askopenfilename(
        title=translate("select_image_file"),
        filetypes=[(translate("image_bin"), "*.bin"), (translate("all_files"), "*.*")]
    )
    if filepath:
        threading.Thread(target=extract_pack, args=(filepath,), daemon=True).start()

# ==========================
# Função principal de extração
# ==========================
def extract_pack(filepath):
    try:
        if not os.path.exists(filepath):
            messagebox.showerror(translate("msg_title_error"), translate("err_file_not_found", path=filepath))
            return

        with open(filepath, "rb") as f:
            magic_offset = f.tell()
            magic = f.read(4)
            magic_str = magic.decode("ascii", errors="ignore")
            logger(translate("log_detected_magic", magic=magic_str, offset=magic_offset))

            if magic != b"PACK":
                messagebox.showerror(translate("msg_title_error"), translate("log_invalid_magic"))
                raise ValueError(translate("error_invalid_magic"))

            total_files = struct.unpack("<I", f.read(4))[0]
            _ = f.read(4)  # CRC ignorado
            logger(translate("log_read_count", count=total_files))

            entries = []
            for i in range(total_files):
                entry_pos = f.tell()
                _ = f.read(8)  # CRC-like
                offset = struct.unpack("<I", f.read(4))[0]
                size = struct.unpack("<I", f.read(4))[0]
                name_bytes = f.read(128)
                name = name_bytes.split(b"\x00", 1)[0].decode("utf-8", errors="ignore")
                if not name:
                    name = name_bytes.split(b"\x00", 1)[0].decode("cp1252", errors="ignore")
                if not name:
                    name = f"file_{i:05d}.bin"

                logger(translate("log_entry_found", i=i, entry_pos=entry_pos, name=name, offset=offset, size=size))

                entries.append({"ENTRY_OFF": entry_pos, "NAME": name, "OFFSET": offset, "SIZE": size})

        # Pasta de saída
        base_dir = os.path.dirname(filepath)
        base_name = os.path.splitext(os.path.basename(filepath))[0]
        extracted_dir = os.path.join(base_dir, f"{base_name}_extracted")
        os.makedirs(extracted_dir, exist_ok=True)

        with open(filepath, "rb") as f:
            for e in entries:
                f.seek(e["OFFSET"])
                data = f.read(e["SIZE"])
                logger(translate("log_extracting", name=e["NAME"], offset=e["OFFSET"], size=e["SIZE"]))

                out_path = os.path.join(extracted_dir, e["NAME"])
                os.makedirs(os.path.dirname(out_path), exist_ok=True)

                # Se for LZSS, tenta descomprimir
                if data.startswith(b"LZSS"):
                    logger(translate("log_lzss_detected", name=e["NAME"]))
                    try:
                        expected_size = struct.unpack("<I", data[4:8])[0] if len(data) >= 8 else 0
                        decomp = unlzss(data[8:])
                        with open(out_path, "wb") as df:
                            df.write(decomp)
                        logger(translate("log_saved", path=out_path))
                        if expected_size and len(decomp) != expected_size:
                            logger(f"[WARN] tamanho esperado={expected_size}, obtido={len(decomp)}")
                        continue  # não salvar raw se já descompactou
                    except Exception as dex:
                        logger(translate("err_unexpected", error=str(dex)))

                # Salvar raw
                with open(out_path, "wb") as fout:
                    fout.write(data)
                logger(translate("log_saved", path=out_path))

        # JSON com metadados
        json_path = os.path.join(base_dir, f"{base_name}.json")
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(entries, jf, indent=4, ensure_ascii=False)

        logger(translate("log_json_written", json_path=json_path))
        logger(translate("log_extracted_folder", folder=extracted_dir))
        messagebox.showinfo(translate("msg_title_done"), translate("log_extracted_folder", folder=extracted_dir))

        return extracted_dir, json_path

    except Exception as e_all:
        messagebox.showerror(translate("msg_title_error"), translate("err_unexpected", error=str(e_all)))
        logger(translate("err_unexpected", error=str(e_all)))
        return None, None
