import os
import struct
import threading
from tkinter import filedialog, messagebox
from pathlib import Path

# ===================== TRANSLATIONS =====================
plugin_translations = {
    "pt_BR": {
        "plugin_name": "LXB de texto DreamWorks (PS2/PS3/PC/Wii)",
        "plugin_description": "Extrai e recria textos de arquivos .LXB de jogos DreamWorks como Kung Fu Panda e Shrek",
        "extract_file": "Extrair Arquivo",
        "rebuild_file": "Recriar Arquivo",
        "select_lxb_file": "Selecione arquivos LXB",
        "select_txt_file": "Selecione arquivos TXT",
        "lxb_files": "Arquivos LXB",
        "txt_files": "Arquivos TXT",
        "all_files": "Todos os arquivos",
        "success": "Sucesso",
        "extraction_success": "Textos extraídos e salvos em:\n{path}",
        "recreation_success": "Textos reinseridos com sucesso",
        "error": "Erro",
        "extraction_error": "Erro durante extração: {error}",
        "recreation_error": "Erro durante reconstrução: {error}",
        "file_not_found": "Arquivo não encontrado: {file}",
        "invalid_pointer": "Ponteiro inválido: 0x{pointer:X} fora do arquivo",
        "processing_file": "Processando arquivo: {file}",
        "detected_endian": "Endianness detectado: {endian}",
        "invalid_header": "Cabeçalho do arquivo inválido",
        "writing_to": "Escrevendo em: {path}",
        "tab_replacement": "[TAB]",
        "end_marker": "[FIM]"
    },
    "en_US": {
        "plugin_name": "DreamWorks LXB Text (PS2/PS3/PC/Wii)",
        "plugin_description": "Extracts and rebuilds text from .LXB files in DreamWorks games like Kung Fu Panda and Shrek",
        "extract_file": "Extract File",
        "rebuild_file": "Rebuild File",
        "select_lxb_file": "Select LXB Files",
        "select_txt_file": "Select TXT Files",
        "lxb_files": "LXB Files",
        "txt_files": "TXT Files",
        "all_files": "All Files",
        "success": "Success",
        "extraction_success": "Texts extracted and saved to:\n{path}",
        "recreation_success": "Texts reinserted successfully",
        "error": "Error",
        "extraction_error": "Error during extraction: {error}",
        "recreation_error": "Error during rebuilding: {error}",
        "file_not_found": "File not found: {file}",
        "invalid_pointer": "Invalid pointer: 0x{pointer:X} outside file",
        "processing_file": "Processing file: {file}",
        "detected_endian": "Detected endianness: {endian}",
        "invalid_header": "Invalid file header",
        "writing_to": "Writing to: {path}",
        "tab_replacement": "[TAB]",
        "end_marker": "[END]"
    },
    "es_ES": {
        "plugin_name": "LXB de texto DreamWorks (PS2/PS3/PC/Wii)",
        "plugin_description": "Extrae y recrea textos de archivos .LXB de juegos DreamWorks como Kung Fu Panda y Shrek",
        "extract_file": "Extraer Archivo",
        "rebuild_file": "Recrear Archivo",
        "select_lxb_file": "Seleccionar archivos LXB",
        "select_txt_file": "Seleccionar archivos TXT",
        "lxb_files": "Archivos LXB",
        "txt_files": "Archivos TXT",
        "all_files": "Todos los archivos",
        "success": "Éxito",
        "extraction_success": "Textos extraídos y guardados en:\n{path}",
        "recreation_success": "Textos reinsertados con éxito",
        "error": "Error",
        "extraction_error": "Error durante extracción: {error}",
        "recreation_error": "Error durante reconstrucción: {error}",
        "file_not_found": "Archivo no encontrado: {file}",
        "invalid_pointer": "Puntero inválido: 0x{pointer:X} fuera del archivo",
        "processing_file": "Procesando archivo: {file}",
        "detected_endian": "Endianness detectado: {endian}",
        "invalid_header": "Cabecera de archivo inválida",
        "writing_to": "Escribiendo en: {path}",
        "tab_replacement": "[TAB]",
        "end_marker": "[FIN]"
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
            {"label": translate("extract_file"), "action": extract_lxb_files},
            {"label": translate("rebuild_file"), "action": rebuild_from_txt}
        ]
    }

# ===================== UTILITY FUNCTIONS =====================
def determine_endianness(file_path):
    """Determine file endianness by checking header"""
    try:
        with file_path.open('rb') as file:
            header = file.read(4)
            big_endian = struct.unpack('>I', header)[0] == 5
            little_endian = struct.unpack('<I', header)[0] == 5
            
            if big_endian:
                logger(translate("detected_endian", endian="Big-endian"))
                return '>'
            elif little_endian:
                logger(translate("detected_endian", endian="Little-endian"))
                return '<'
            else:
                raise ValueError(translate("invalid_header"))
    except Exception as e:
        raise ValueError(f"{translate('error')}: {str(e)}")

# ===================== MAIN FUNCTIONS =====================
def extract_lxb_text(file_path, endian):
    """Extract text from LXB file"""
    try:
        logger(translate("processing_file", file=file_path.name))
        
        with file_path.open('rb') as file:
            file.seek(124)
            pointer_count = struct.unpack(endian + 'I', file.read(4))[0]
            
            # Read pointers
            pointers = []
            file.seek(128)
            for _ in range(pointer_count):
                file.seek(4, os.SEEK_CUR)  # Skip unknown bytes
                pointer = struct.unpack(endian + 'I', file.read(4))[0]
                pointer_pos = file.tell()
                absolute_pos = pointer_pos + pointer
                
                if absolute_pos >= file_path.stat().st_size:
                    logger(translate("invalid_pointer", pointer=absolute_pos))
                    continue
                
                pointers.append(absolute_pos)

            # Extract text blocks
            text_blocks = []
            for pos in pointers:
                file.seek(pos)
                text_bytes = bytearray()
                
                while True:
                    byte = file.read(1)
                    if byte == b'\x00' or not byte:
                        break
                    text_bytes += byte
                
                # Replace tabs with marker
                text_bytes = text_bytes.replace(b'\x09', translate("tab_replacement").encode('utf-8'))
                text_blocks.append(text_bytes)

        # Join blocks with end markers
        joined_text = translate("end_marker").encode('utf-8') + b'\n'.join(text_blocks) + \
                     translate("end_marker").encode('utf-8') + b'\n'
        
        # Save to TXT file
        output_path = file_path.with_suffix('.txt')
        logger(translate("writing_to", path=output_path))
        output_path.write_bytes(joined_text)
        
        return output_path
        
    except Exception as e:
        raise Exception(translate("extraction_error", error=str(e)))

def rebuild_lxb_from_txt(txt_path, endian):
    """Rebuild LXB file from TXT"""
    try:
        lxb_path = txt_path.with_suffix('.lxb')
        if not lxb_path.exists():
            raise FileNotFoundError(translate("file_not_found", file=lxb_path))
        
        logger(translate("processing_file", file=txt_path.name))
        
        # Read and parse TXT file
        text_data = txt_path.read_bytes()
        text_blocks = text_data.split(
            translate("end_marker").encode('utf-8') + b'\n'
        )
        text_blocks = [block for block in text_blocks if block.strip()]
        
        # Process text blocks
        processed_blocks = []
        for block in text_blocks:
            block = block.replace(
                translate("tab_replacement").encode('utf-8'), 
                b'\x09'
            )
            processed_blocks.append(block)
        
        with lxb_path.open('r+b') as file:
            # Read original structure
            file.seek(4)
            remaining_data_pos = struct.unpack(endian + 'I', file.read(4))[0]
            
            if remaining_data_pos != 0:
                file.seek(remaining_data_pos - 4)
                remaining_data = file.read()
            else:
                remaining_data = b''
            
            # Get pointer info
            file.seek(124)
            pointer_count = struct.unpack(endian + 'I', file.read(4))[0]
            text_start_pos = 128 + 8 * pointer_count
            
            # Write new text blocks
            block_positions = []
            current_pos = text_start_pos
            for block in processed_blocks:
                file.seek(current_pos)
                file.write(block)
                file.write(b'\x00')
                block_positions.append(current_pos)
                current_pos += len(block) + 1
            
            # Write remaining data
            remaining_pos = file.tell()
            file.write(remaining_data)
            file.truncate()
            
            # Update header
            file.seek(4)
            file.write(struct.pack(endian + 'I', remaining_pos - 4))
            
            # Update pointers
            file.seek(128)
            for pos in block_positions:
                file.seek(4, os.SEEK_CUR)  # Skip unknown bytes
                pointer_pos = file.tell()
                relative_pos = pos - pointer_pos
                file.write(struct.pack(endian + 'I', relative_pos))
        
        return True
        
    except Exception as e:
        raise Exception(translate("recreation_error", error=str(e)))

# ===================== COMMAND HANDLERS =====================
def extract_lxb_files():
    """Handle LXB file extraction"""
    file_paths = filedialog.askopenfilenames(
        title=translate("select_lxb_file"),
        filetypes=[
            (translate("lxb_files"), "*.lxb"),
            (translate("all_files"), "*.*")
        ]
    )
    if not file_paths:
        return
    
    def process_files():
        for path in file_paths:
            try:
                path = Path(path)
                endian = determine_endianness(path)
                output_path = extract_lxb_text(path, endian)
                messagebox.showinfo(
                    translate("success"),
                    translate("extraction_success", path=output_path)
                )
            except Exception as e:
                messagebox.showerror(
                    translate("error"),
                    f"{path.name}: {str(e)}"
                )
    
    threading.Thread(target=process_files, daemon=True).start()

def rebuild_from_txt():
    """Handle TXT file rebuilding"""
    file_paths = filedialog.askopenfilenames(
        title=translate("select_txt_file"),
        filetypes=[
            (translate("txt_files"), "*.txt"),
            (translate("all_files"), "*.*")
        ]
    )
    if not file_paths:
        return
    
    def process_files():
        for path in file_paths:
            try:
                path = Path(path)
                lxb_path = path.with_suffix('.lxb')
                endian = determine_endianness(lxb_path)
                rebuild_lxb_from_txt(path, endian)
                messagebox.showinfo(
                    translate("success"),
                    translate("recreation_success")
                )
            except Exception as e:
                messagebox.showerror(
                    translate("error"),
                    f"{path.name}: {str(e)}"
                )
    
    threading.Thread(target=process_files, daemon=True).start()