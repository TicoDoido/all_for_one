import struct
import os
import threading
from tkinter import filedialog, messagebox
from pathlib import Path

# ===================== TRANSLATIONS =====================
plugin_translations = {
    "pt_BR": {
        "plugin_name": "GMD Arquivos de texto MT Framework (RE6)",
        "plugin_description": "Extrai e reinsere textos dos arquivos GMD da MT Framework, testado com Resident Evil 6",
        "extract_texts": "Extrair Textos",
        "insert_texts": "Reinserir Textos",
        "select_gmd_file": "Selecione arquivo GMD",
        "gmd_files": "Arquivos GMD",
        "all_files": "Todos os arquivos",
        "success": "Sucesso",
        "extraction_success": "Textos extraídos e salvos em:\n{path}",
        "insertion_success": "Textos reinseridos com sucesso no arquivo binário",
        "error": "Erro",
        "extraction_error": "Erro durante extração: {error}",
        "insertion_error": "Erro durante reinserção: {error}",
        "file_not_found": "Arquivo não encontrado: {file}",
        "processing_file": "Processando arquivo: {file}",
        "extracting_texts": "Extraindo {count} textos...",
        "saving_to": "Salvando em: {path}",
        "invalid_utf8": "Texto[{index}] contém bytes UTF-8 inválidos",
        "pointer_update": "Pointer[{index}] atualizado com offset {offset}",
        "skipped_pointer": "Pointer[{index}] ignorado (0xFFFFFFFF)",
        "text_count_mismatch": "Mais textos ({text_count}) que ponteiros válidos ({pointer_count})",
        "text_file_not_found": "Arquivo de texto não encontrado para reinserção",
        "decoding_error": "<ERRO DE DECODIFICAÇÃO>"
    },
    "en_US": {
        "plugin_name": "GMD Text Files MT Framework (RE6)",
        "plugin_description": "Extracts and reinserts texts from GMD files in MT Framework, tested with Resident Evil 6",
        "extract_texts": "Extract Texts",
        "insert_texts": "Insert Texts",
        "select_gmd_file": "Select GMD File",
        "gmd_files": "GMD Files",
        "all_files": "All Files",
        "success": "Success",
        "extraction_success": "Texts extracted and saved to:\n{path}",
        "insertion_success": "Texts successfully reinserted into binary file",
        "error": "Error",
        "extraction_error": "Error during extraction: {error}",
        "insertion_error": "Error during insertion: {error}",
        "file_not_found": "File not found: {file}",
        "processing_file": "Processing file: {file}",
        "extracting_texts": "Extracting {count} texts...",
        "saving_to": "Saving to: {path}",
        "invalid_utf8": "Text[{index}] contains invalid UTF-8 bytes",
        "pointer_update": "Pointer[{index}] updated with offset {offset}",
        "skipped_pointer": "Pointer[{index}] skipped (0xFFFFFFFF)",
        "text_count_mismatch": "More texts ({text_count}) than valid pointers ({pointer_count})",
        "text_file_not_found": "Text file not found for insertion",
        "decoding_error": "<DECODING ERROR>"
    },
    "es_ES": {
        "plugin_name": "GMD Archivos de texto MT Framework (RE6)",
        "plugin_description": "Extrae y reinserta textos de archivos GMD de MT Framework, probado con Resident Evil 6",
        "extract_texts": "Extraer Textos",
        "insert_texts": "Reinsertar Textos",
        "select_gmd_file": "Seleccionar archivo GMD",
        "gmd_files": "Archivos GMD",
        "all_files": "Todos los archivos",
        "success": "Éxito",
        "extraction_success": "Textos extraídos y guardados en:\n{path}",
        "insertion_success": "Textos reinsertados exitosamente en el archivo binario",
        "error": "Error",
        "extraction_error": "Error durante extracción: {error}",
        "insertion_error": "Error durante reinserción: {error}",
        "file_not_found": "Archivo no encontrado: {file}",
        "processing_file": "Procesando archivo: {file}",
        "extracting_texts": "Extrayendo {count} textos...",
        "saving_to": "Guardando en: {path}",
        "invalid_utf8": "Texto[{index}] contiene bytes UTF-8 inválidos",
        "pointer_update": "Pointer[{index}] actualizado con offset {offset}",
        "skipped_pointer": "Pointer[{index}] ignorado (0xFFFFFFFF)",
        "text_count_mismatch": "Más textos ({text_count}) que punteros válidos ({pointer_count})",
        "text_file_not_found": "Archivo de texto no encontrado para reinserción",
        "decoding_error": "<ERROR DE DECODIFICACIÓN>"
    }
}

# ===================== GLOBAL VARIABLES =====================
logger = print
current_language = "pt_BR"
get_option = lambda name: None

# ===================== TRANSLATION FUNCTION =====================
def translate(key, **kwargs):
    """Plugin's internal translation function"""
    lang_dict = plugin_translations.get(current_language, plugin_translations["pt_BR"])
    translation = lang_dict.get(key, key)
    
    if kwargs:
        try:
            return translation.format(**kwargs)
        except:
            return translation
    return translation

# ===================== PLUGIN REGISTRATION =====================
def register_plugin(log_func, option_getter, host_language="pt_BR"):
    global logger, get_option, current_language
    logger = log_func or print
    get_option = option_getter or (lambda name: None)
    current_language = host_language
    
    return {
        "name": translate("plugin_name"),
        "description": translate("plugin_description"),
        "commands": [
            {"label": translate("extract_texts"), "action": extract_texts_handler},
            {"label": translate("insert_texts"), "action": insert_texts_handler},
        ]
    }

# ===================== UTILITY FUNCTIONS =====================
def read_little_endian_int(file):
    """Read 4-byte little-endian integer from file"""
    return struct.unpack('<I', file.read(4))[0]

def decode_text(text_bytes):
    """Decode text bytes with UTF-8, fallback to error message"""
    try:
        return text_bytes.decode('utf-8')
    except UnicodeDecodeError:
        return translate("decoding_error")

# ===================== MAIN FUNCTIONS =====================
def extract_texts_from_gmd(gmd_path):
    """Extract texts from GMD binary file"""
    try:
        gmd_path = Path(gmd_path)
        logger(translate("processing_file", file=gmd_path.name))
        
        with gmd_path.open('rb') as file:
            file.seek(20)
            pointer_count = read_little_endian_int(file)
            pointer_block_size = pointer_count * 4
            pointer_table_end = pointer_block_size + 28

            # Read valid pointers
            valid_pointers = []
            for _ in range(pointer_count):
                pointer_data = file.read(4)
                if pointer_data != b'\xFF\xFF\xFF\xFF':
                    valid_pointers.append(struct.unpack('<I', pointer_data)[0])

            logger(translate("extracting_texts", count=len(valid_pointers)))
            texts = []

            for i, pointer in enumerate(valid_pointers):
                file.seek(pointer_table_end + pointer)
                
                # Read null-terminated string
                text_bytes = bytearray()
                while True:
                    byte = file.read(1)
                    if byte == b'\x00' or not byte:
                        break
                    text_bytes += byte

                text = decode_text(text_bytes)
                if text == translate("decoding_error"):
                    logger(translate("invalid_utf8", index=i))
                texts.append(text)

        return texts
        
    except Exception as e:
        raise Exception(translate("extraction_error", error=str(e)))

def save_extracted_texts(texts, gmd_path):
    """Save extracted texts to output file"""
    try:
        output_path = gmd_path.with_suffix('.txt')
        logger(translate("saving_to", path=output_path))
        
        with output_path.open('w', encoding='utf-8') as f:
            for text in texts:
                processed_text = text.replace("\r\n", "[BR]")
                f.write(f"{processed_text}[END]\n")
                
        return output_path
        
    except Exception as e:
        raise Exception(translate("extraction_error", error=str(e)))

def insert_texts_into_gmd(gmd_path):
    """Insert texts from TXT file back into GMD binary"""
    try:
        gmd_path = Path(gmd_path)
        txt_path = gmd_path.with_suffix('.txt')
        
        if not txt_path.exists():
            raise FileNotFoundError(translate("text_file_not_found"))
            
        logger(translate("processing_file", file=gmd_path.name))

        # Read texts from TXT file
        with txt_path.open('r', encoding='utf-8') as f:
            texts = [t.replace("[BR]", "\r\n") for t in f.read().split("[END]\n") if t]

        with gmd_path.open('r+b') as file:
            # Read pointer information
            file.seek(20)
            pointer_count = read_little_endian_int(file)
            pointer_block_size = pointer_count * 4
            pointer_table_end = pointer_block_size + 28

            # Find all valid pointers (skip 0xFFFFFFFF)
            file.seek(24)
            valid_pointer_positions = []
            for _ in range(pointer_count):
                pos = file.tell()
                if file.read(4) != b'\xFF\xFF\xFF\xFF':
                    valid_pointer_positions.append(pos)
                else:
                    file.seek(pos + 4)  # Skip invalid pointer

            # Write new texts and collect offsets
            file.seek(pointer_table_end)
            text_offsets = []
            
            for text in texts:
                offset = file.tell() - pointer_table_end
                text_offsets.append(offset)
                file.write(text.encode('utf-8') + b'\x00')

            # Update file size in header
            file_size = file.tell()
            file.seek(pointer_table_end - 4)
            file.write(struct.pack('<I', file_size - pointer_table_end))

            # Update valid pointers with new offsets
            text_index = 0
            for pos in valid_pointer_positions:
                if text_index < len(text_offsets):
                    file.seek(pos)
                    file.write(struct.pack('<I', text_offsets[text_index]))
                    logger(translate("pointer_update", index=text_index, offset=text_offsets[text_index]))
                    text_index += 1
                else:
                    break

            # Warn if there are more texts than pointers
            if text_index < len(texts):
                warning = translate("text_count_mismatch", 
                    text_count=len(texts), 
                    pointer_count=text_index)
                logger(f"Warning: {warning}")
                return warning

        return True
        
    except Exception as e:
        raise Exception(translate("insertion_error", error=str(e)))

# ===================== COMMAND HANDLERS =====================
def extract_texts_handler():
    """Handle text extraction command"""
    gmd_path = filedialog.askopenfilename(
        title=translate("select_gmd_file"),
        filetypes=[
            (translate("gmd_files"), "*.gmd"),
            (translate("all_files"), "*.*")
        ]
    )
    if not gmd_path:
        return

    def run_extraction():
        try:
            texts = extract_texts_from_gmd(gmd_path)
            output_path = save_extracted_texts(texts, Path(gmd_path))
            messagebox.showinfo(
                translate("success"),
                translate("extraction_success", path=output_path)
            )
        except Exception as e:
            messagebox.showerror(
                translate("error"),
                str(e)
            )

    threading.Thread(target=run_extraction, daemon=True).start()

def insert_texts_handler():
    """Handle text insertion command"""
    gmd_path = filedialog.askopenfilename(
        title=translate("select_gmd_file"),
        filetypes=[
            (translate("gmd_files"), "*.gmd"),
            (translate("all_files"), "*.*")
        ]
    )
    if not gmd_path:
        return

    def run_insertion():
        try:
            result = insert_texts_into_gmd(gmd_path)
            if result is True:
                messagebox.showinfo(
                    translate("success"),
                    translate("insertion_success")
                )
            else:
                messagebox.showwarning(
                    translate("warning"),
                    result
                )
        except Exception as e:
            messagebox.showerror(
                translate("error"),
                str(e)
            )

    threading.Thread(target=run_insertion, daemon=True).start()