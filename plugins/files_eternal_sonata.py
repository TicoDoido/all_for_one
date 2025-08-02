import os
import struct
import threading
from tkinter import filedialog, messagebox
from pathlib import Path

# ===================== TRANSLATIONS =====================
plugin_translations = {
    "pt_BR": {
        "plugin_name": "FILES arquivos (Eternal Sonata PS3)",
        "plugin_description": "Extrai e recria textos de arquivos do jogo Eternal Sonata",
        "extract_file": "Extrair Arquivo",
        "select_files_file": "Selecione arquivo .FILES",
        "files_files": "Arquivos FILES",
        "all_files": "Todos os arquivos",
        "success": "Sucesso",
        "extraction_success": "Arquivos extraídos com sucesso!",
        "error": "Erro",
        "extraction_error": "Erro durante extração: {error}",
        "file_not_found": "Arquivo não encontrado: {file}",
        "processing_file": "Processando arquivo: {file}",
        "extracting_to": "Extraindo para: {path}",
        "invalid_structure": "Estrutura do arquivo inválida",
        "file_extracted": "Arquivo extraído: {filename} -> {output_path}"
    },
    "en_US": {
        "plugin_name": "FILES files (Eternal Sonata PS3)",
        "plugin_description": "Extracts and rebuilds text files from Eternal Sonata game",
        "extract_file": "Extract File",
        "select_files_file": "Select .FILES file",
        "files_files": "FILES Files",
        "all_files": "All files",
        "success": "Success",
        "extraction_success": "Files extracted successfully!",
        "error": "Error",
        "extraction_error": "Error during extraction: {error}",
        "file_not_found": "File not found: {file}",
        "processing_file": "Processing file: {file}",
        "extracting_to": "Extracting to: {path}",
        "invalid_structure": "Invalid file structure",
        "file_extracted": "File extracted: {filename} -> {output_path}"
    },
    "es_ES": {
        "plugin_name": "FILES archivos (Eternal Sonata PS3)",
        "plugin_description": "Extrae y recrea archivos de texto del juego Eternal Sonata",
        "extract_file": "Extraer Archivo",
        "select_files_file": "Seleccionar archivo .FILES",
        "files_files": "Archivos FILES",
        "all_files": "Todos los archivos",
        "success": "Éxito",
        "extraction_success": "¡Archivos extraídos con éxito!",
        "error": "Error",
        "extraction_error": "Error durante extracción: {error}",
        "file_not_found": "Archivo no encontrado: {file}",
        "processing_file": "Procesando archivo: {file}",
        "extracting_to": "Extrayendo a: {path}",
        "invalid_structure": "Estructura de archivo inválida",
        "file_extracted": "Archivo extraído: {filename} -> {output_path}"
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
            {"label": translate("extract_file"), "action": select_container},
        ]
    }

# ===================== MAIN FUNCTIONS =====================
def extract_files_from_container(container_path):
    """Extract files from Eternal Sonata FILES container"""
    try:
        container_path = Path(container_path)
        output_dir = container_path.with_name(container_path.stem)
        output_dir.mkdir(exist_ok=True)
        
        logger(translate("extracting_to", path=output_dir))

        with container_path.open('rb') as container:
            # Read header information
            container.seek(8)
            num_files = struct.unpack('>I', container.read(4))[0]
            
            if num_files == 0 or num_files > 10000:  # Sanity check
                raise ValueError(translate("invalid_structure"))
            
            header_offset = 16  # Start of file entries
            
            for _ in range(num_files):
                container.seek(header_offset)
                
                # Read file entry
                filename = container.read(32).decode('utf-8').strip('\x00')
                file_start = struct.unpack('>I', container.read(4))[0]
                file_size = struct.unpack('>I', container.read(4))[0]
                
                header_offset += 48  # Move to next entry
                
                # Validate file position
                if file_start == 0 or file_size == 0:
                    continue
                
                logger(translate("processing_file", file=filename))
                
                # Read file data
                container.seek(file_start)
                file_data = container.read(file_size)
                
                # Create output path and write file
                output_path = output_dir / filename
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(file_data)
                
                logger(translate("file_extracted", 
                    filename=filename, 
                    output_path=output_path))

        messagebox.showinfo(
            translate("success"),
            translate("extraction_success")
        )
        return True
        
    except Exception as e:
        messagebox.showerror(
            translate("error"),
            translate("extraction_error", error=str(e))
        )
        return False

# ===================== COMMAND HANDLERS =====================
def select_container():
    """Handle file selection and start extraction"""
    file_path = filedialog.askopenfilename(
        title=translate("select_files_file"),
        filetypes=[
            (translate("files_files"), "*.files"),
            (translate("all_files"), "*.*")
        ]
    )
    if not file_path:
        return
    
    def run_extraction():
        extract_files_from_container(file_path)
    
    # Run extraction in separate thread to prevent UI freezing
    threading.Thread(target=run_extraction, daemon=True).start()