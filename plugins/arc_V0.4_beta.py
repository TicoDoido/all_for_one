import os
import struct
import zlib
import threading
from tkinter import filedialog, messagebox
from pathlib import Path

# ===================== TRANSLATIONS =====================
plugin_translations = {
    "pt_BR": {
        "plugin_name": "ARC de Dead Rising V 0.4 XBOX 360/PC",
        "plugin_description": "Extrai e recria .arc Dead Rising Xbox 360/PC",
        "extract_file": "Extrair Arquivo",
        "rebuild_file": "Reconstruir Arquivo",
        "select_arc_file": "Selecione arquivo .ARC",
        "arc_files": "Arquivos ARC",
        "all_files": "Todos os arquivos",
        "success": "Sucesso",
        "extraction_success": "{count} arquivos extraídos para:\n{path}",
        "recreation_success": "Arquivo {file} remontado com sucesso",
        "error": "Erro",
        "extraction_error": "Erro durante extração: {error}",
        "recreation_error": "Erro durante reconstrução: {error}",
        "file_not_found": "Arquivo não encontrado: {file}",
        "invalid_magic": "Magic inválido. Esperado \\x00CRA ou ARC\\x00",
        "version_warning": "Feito para versão 0.4\nEncontrado: 0.{version}",
        "processing_file": "Processando: {file}",
        "writing_file": "Gravando: {file}",
        "file_error": "Erro no arquivo '{file}': {error}",
        "compression_mode": "Modo de Compactação",
        "compression_options": {
            "zlib": "ZLIB (padrão)",
            "deflate": "DEFLATE (raw)",
            "N/A": "Sem compressão"
        },
        "compression_attempt": "Tentando {method} em '{file}'",
        "compression_failed": "Falha ao comprimir '{file}': {error}",
        "rebuilding_at": "Reinserindo em offset: {offset}",
        "header_update": "Atualizando cabeçalhos"
    },
    "en_US": {
        "plugin_name": "Dead Rising V 0.4 XBOX 360/PC ARC",
        "plugin_description": "Extracts and rebuilds Dead Rising .arc files for Xbox 360/PC",
        "extract_file": "Extract File",
        "rebuild_file": "Rebuild File",
        "select_arc_file": "Select .ARC file",
        "arc_files": "ARC Files",
        "all_files": "All files",
        "success": "Success",
        "extraction_success": "{count} files extracted to:\n{path}",
        "recreation_success": "File {file} rebuilt successfully",
        "error": "Error",
        "extraction_error": "Error during extraction: {error}",
        "recreation_error": "Error during rebuilding: {error}",
        "file_not_found": "File not found: {file}",
        "invalid_magic": "Invalid magic. Expected \\x00CRA or ARC\\x00",
        "version_warning": "Made for version 0.4\nFound: 0.{version}",
        "processing_file": "Processing: {file}",
        "writing_file": "Writing: {file}",
        "file_error": "File error '{file}': {error}",
        "compression_mode": "Compression Mode",
        "compression_options": {
            "zlib": "ZLIB (standard)",
            "deflate": "DEFLATE (raw)",
            "N/A": "No compression"
        },
        "compression_attempt": "Trying {method} on '{file}'",
        "compression_failed": "Compression failed '{file}': {error}",
        "rebuilding_at": "Rebuilding at offset: {offset}",
        "header_update": "Updating headers"
    },
    "es_ES": {
        "plugin_name": "ARC Dead Rising V 0.4 XBOX 360/PC",
        "plugin_description": "Extrae y recrea archivos .arc Dead Rising Xbox 360/PC",
        "extract_file": "Extraer Archivo",
        "rebuild_file": "Reconstruir Archivo",
        "select_arc_file": "Seleccionar archivo .ARC",
        "arc_files": "Archivos ARC",
        "all_files": "Todos los archivos",
        "success": "Éxito",
        "extraction_success": "{count} archivos extraídos en:\n{path}",
        "recreation_success": "Archivo {file} recreado con éxito",
        "error": "Error",
        "extraction_error": "Error durante extracción: {error}",
        "recreation_error": "Error durante reconstrucción: {error}",
        "file_not_found": "Archivo no encontrado: {file}",
        "invalid_magic": "Magic inválido. Se esperaba \\x00CRA o ARC\\x00",
        "version_warning": "Hecho para versión 0.4\nEncontrado: 0.{version}",
        "processing_file": "Procesando: {file}",
        "writing_file": "Escribiendo: {file}",
        "file_error": "Error en archivo '{file}': {error}",
        "compression_mode": "Modo de Compresión",
        "zlib": "ZLIB (estándar)",
        "deflate": "DEFLATE (raw)",
        "N/A": "Sin compresión",
        "compression_attempt": "Intentando {method} en '{file}'",
        "compression_failed": "Fallo al comprimir '{file}': {error}",
        "rebuilding_at": "Reinsertando en offset: {offset}",
        "header_update": "Actualizando cabeceras"
    }
}


logger = print
current_language = "pt_BR"
get_option = lambda name: None

# ===================== TRANSLATION FUNCTION =====================
def translate(key, **kwargs):
    """Plugin's internal translation function with nested key support"""
    lang_dict = plugin_translations.get(current_language, plugin_translations["pt_BR"])
    parts = key.split('.')
    translation = lang_dict
    for part in parts:
        if isinstance(translation, dict) and part in translation:
            translation = translation[part]
        else:
            translation = key
            break
    if isinstance(translation, str) and kwargs:
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

    def get_plugin_info():
        return {
            "name": translate("plugin_name"),
            "description": translate("plugin_description"),
            "options": [
                {   "name": "modo_compactacao",
                    "label": translate("compression_mode"),
                    "values": [translate("zlib"), translate("deflate"), translate("N/A")]}
            ],
            "commands": [
            {"label": translate("extract_file"), "action": choose_file},
            {"label": translate("rebuild_file"), "action": choose_file_to_rebuild},
            ]
        }

    return get_plugin_info

# ===================== UTILITY FUNCTIONS =====================
def determine_endian(magic):
    """Determine endianness based on magic bytes"""
    if magic == b'\x00CRA':
        return '>'  # Big-endian
    elif magic == b'ARC\x00':
        return '<'  # Little-endian
    return None

def try_decompression(data, original_size, compressed_size, filename):
    """Attempt different decompression methods"""
    if original_size <= compressed_size:
        return data  # No compression
    
    # Try standard ZLIB first
    try:
        return zlib.decompress(data)
    except zlib.error as err_zlib:
        logger(translate("compression_attempt", method="ZLIB", file=filename))
        logger(translate("compression_failed", file=filename, error=str(err_zlib)))
        
        # Try raw DEFLATE if standard fails
        try:
            return zlib.decompress(data, -zlib.MAX_WBITS)
        except zlib.error as err_deflate:
            logger(translate("compression_attempt", method="DEFLATE", file=filename))
            logger(translate("compression_failed", file=filename, error=str(err_deflate)))
            return data  # Return original data if all decompression fails

def apply_compression(data, mode):
    """Apply compression based on selected mode"""
    if mode == "N/A" or not data:
        return data
    
    try:
        if mode == "deflate":
            compress_obj = zlib.compressobj(wbits=-15)
            return compress_obj.compress(data) + compress_obj.flush()
        else:  # Default to standard ZLIB
            return zlib.compress(data)
    except Exception as e:
        logger(translate("compression_failed", file="", error=str(e)))
        return data

# ===================== MAIN FUNCTIONS =====================
def extract_arc(arc_path):
    """Extract contents from ARC file"""
    try:
        arc_path = Path(arc_path)
        with arc_path.open('rb') as f:
            # Read and validate header
            magic = f.read(4)
            endian = determine_endian(magic)
            if not endian:
                messagebox.showerror(
                    translate("error"),
                    translate("invalid_magic")
                )
                return False

            version = struct.unpack(endian + 'H', f.read(2))[0]
            if version != 4:
                messagebox.showinfo(
                    translate("warning"),
                    translate("version_warning", version=version)
                )

            file_count = struct.unpack(endian + 'H', f.read(2))[0]
            entries = []
            
            # Read file entries
            for _ in range(file_count):
                name_bytes = f.read(64)
                name_str = name_bytes.split(b'\x00', 1)[0].decode('utf-8', errors='ignore')
                file_id = f.read(4).hex().upper()
                full_name = f"{name_str}_{file_id}"
                
                compressed_size = struct.unpack(endian + 'I', f.read(4))[0]
                original_size = struct.unpack(endian + 'I', f.read(4))[0]
                offset = struct.unpack(endian + 'I', f.read(4))[0]
                
                entries.append((full_name, compressed_size, original_size, offset))

        # Prepare output directory
        output_dir = arc_path.with_name(arc_path.stem)
        output_dir.mkdir(exist_ok=True)
        
        # Process each file
        with arc_path.open('rb') as f:
            for name, compressed_size, original_size, offset in entries:
                try:
                    logger(translate("processing_file", file=name))
                    output_path = output_dir / name
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    f.seek(offset)
                    file_data = f.read(compressed_size)
                    
                    # Handle compression if needed
                    file_data = try_decompression(
                        file_data, 
                        original_size, 
                        compressed_size, 
                        name
                    )
                    
                    output_path.write_bytes(file_data)
                    logger(translate("writing_file", file=name))
                    
                except Exception as file_error:
                    logger(translate("file_error", file=name, error=str(file_error)))
                    continue

        messagebox.showinfo(
            translate("success"),
            translate("extraction_success", count=file_count, path=output_dir)
        )
        return True
        
    except Exception as e:
        messagebox.showerror(
            translate("error"),
            translate("extraction_error", error=str(e))
        )
        return False

def rebuild_arc(arc_path):
    """Rebuild ARC file from extracted files"""
    try:
        arc_path = Path(arc_path)
        compression_mode = get_option("modo_compactacao") or "zlib"
        
        with arc_path.open('r+b') as f:
            # Read header info
            magic = f.read(4)
            endian = determine_endian(magic)
            if not endian:
                messagebox.showerror(
                    translate("error"), 
                    translate("invalid_magic")
                )
                return False

            f.seek(4)
            version = struct.unpack(endian + 'H', f.read(2))[0]
            if version != 4:
                messagebox.showinfo(
                    translate("warning"),
                    translate("version_warning", version=version)
                )

            file_count = struct.unpack(endian + 'H', f.read(2))[0]
            logger(f"Total files: {file_count}")
            
            # Calculate data start position
            header_size = 8 + (80 * file_count)
            f.seek(header_size)
            data_start = f.tell()
            logger(translate("rebuilding_at", offset=data_start))

            # Read original entries
            entries = []
            f.seek(8)  # Start of entries
            for _ in range(file_count):
                name_bytes = f.read(64)
                name_str = name_bytes.split(b'\x00', 1)[0].decode('utf-8', errors='ignore')
                file_id = f.read(4).hex().upper()
                full_name = f"{name_str}_{file_id}"
                
                compressed_size = struct.unpack(endian + 'I', f.read(4))[0]
                original_size = struct.unpack(endian + 'I', f.read(4))[0]
                offset = struct.unpack(endian + 'I', f.read(4))[0]
                
                entries.append((full_name, compressed_size, original_size))

            # Process files and write new data
            new_data = []
            f.seek(data_start)
            extracted_dir = arc_path.with_name(arc_path.stem)
            
            for name, original_compressed, original_size in entries:
                file_path = extracted_dir / name
                if not file_path.exists():
                    messagebox.showerror(
                        translate("error"),
                        translate("file_not_found", file=file_path)
                    )
                    return False

                file_data = file_path.read_bytes()
                current_offset = f.tell()
                logger(translate("rebuilding_at", offset=current_offset))

                # Apply compression if needed
                if original_size > original_compressed:
                    compressed_data = apply_compression(file_data, compression_mode)
                    f.write(compressed_data)
                    new_compressed = len(compressed_data)
                    logger(f"[OK] {translate('compression_options.'+compression_mode)}: {name}")
                else:
                    f.write(file_data)
                    new_compressed = len(file_data)
                    logger(f"[OK] No compression: {name}")

                new_data.append((current_offset, len(file_data), new_compressed))

            # Update headers
            logger(translate("header_update"))
            f.seek(8)
            for idx in range(file_count):
                f.seek(68, 1)  # Skip name and ID
                f.write(struct.pack(endian + 'I', new_data[idx][2]))  # New compressed size
                if compression_mode != "N/A":
                    f.write(struct.pack(endian + 'I', new_data[idx][1]))  # Original size
                else:
                    f.seek(4, 1)
                f.write(struct.pack(endian + 'I', new_data[idx][0]))  # New offset

        messagebox.showinfo(
            translate("success"),
            translate("recreation_success", file=arc_path.name)
        )
        return True
        
    except Exception as e:
        messagebox.showerror(
            translate("error"),
            translate("recreation_error", error=str(e))
        )
        return False

# ===================== COMMAND HANDLERS =====================
def choose_file():
    """Handler for file extraction"""
    arc_path = filedialog.askopenfilename(
        title=translate("select_arc_file"),
        filetypes=[
            (translate("arc_files"), "*.arc"),
            (translate("all_files"), "*.*")
        ]
    )
    if not arc_path:
        return
    
    def run_extraction():
        extract_arc(arc_path)
    
    threading.Thread(target=run_extraction, daemon=True).start()

def choose_file_to_rebuild():
    """Handler for file rebuilding"""
    arc_path = filedialog.askopenfilename(
        title=translate("select_arc_file"),
        filetypes=[
            (translate("arc_files"), "*.arc"),
            (translate("all_files"), "*.*")
        ]
    )
    if not arc_path:
        return
    
    def run_rebuild():
        rebuild_arc(arc_path)
    
    threading.Thread(target=run_rebuild, daemon=True).start()