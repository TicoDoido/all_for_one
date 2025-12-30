import os
import struct
import threading
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import List, Optional, Tuple

# ===================== TRANSLATIONS =====================
plugin_translations = {
    "pt_BR": {
        "plugin_name": "FILES|TEX|P3TEX... (Eternal Sonata PS3)",
        "plugin_description": "Extrai e recria textos de arquivos do jogo Eternal Sonata",
        "extract_file": "Extrair Arquivo(.FILES)",
        "import_files": "Reimportar Arquivos(.FILES)",
        "select_files_file": "Selecione arquivo .FILES",
        "select_import_dir": "Selecione pasta com arquivos para reimportar",
        "files_files": "Arquivos FILES",
        "all_files": "Todos os arquivos",
        "log_magic_invalid": "Magic FILE não encontrado no início do arquivo.",
        "success": "Sucesso",
        "extraction_success": "Arquivos extraídos com sucesso!",
        "import_success": "Arquivos reimportados com sucesso!",
        "error": "Erro",
        "extraction_error": "Erro durante extração: {error}",
        "import_error": "Erro durante reimportação: {error}",
        "file_not_found": "Arquivo não encontrado: {file}",
        "processing_file": "Processando arquivo: {file}",
        "extracting_to": "Extraindo para: {path}",
        "invalid_structure": "Estrutura do arquivo inválida",
        "file_extracted": "Arquivo extraído: {filename} -> {output_path}",
        "file_reimported": "Arquivo reimportado: {filename} -> offset {offset} size {size}",
        "file_not_in_header": "Arquivo não encontrado no header, pulando: {filename}",
        "reading_header": "Lendo header do container...",
        "found_num_files": "Número de entradas no header: {num}",
        "starting_insert_at": "Iniciando inserção em offset alinhado: {offset}",
        "skipping_nonfiles": "Pulando: {name} (não é arquivo)",
        "extract_ntx": "Extrair NTX3 -> DDS",
        "import_dds": "Importar DDS -> NTX3",
        "select_ntx_files": "Escolha o(s) arquivo(s) binário(s)",
        "select_ntx_file": "Escolha o arquivo NTX3 original para receber os DDS",
        "select_dds_files": "Selecione os arquivos .dds a importar",
        "msg_title_error": "Erro",
        "msg_title_done": "Concluído",
        "msg_no_offsets": "Nenhum offset NTX3 encontrado no arquivo.",
        "msg_invalid_magic": "Magic inválido: {magic} (esperado {file_magic} ou 'NTX3').",
        "msg_offsets_found": "Offsets encontrados: {n}",
        "msg_extracted_count": "Texturas extraídas: {n} (pasta: {out})",
        "msg_import_success": "Importação concluída. Arquivos gravados com sucesso: {n}",
        "msg_import_fail": "Falha durante importação: {err}",

        # mensagens de log (formatadas com translate e passadas ao logger)
        "warn_offset_negative": "[WARN] offset negativo {off} — pulando",
        "warn_offset_beyond_file": "[WARN] offset {off} está além do tamanho do arquivo ({file_size}) — pulando",
        "warn_cant_read_header_size": "[WARN] offset {off}: não foi possível ler header_size — pulando",
        "warn_invalid_header_size": "[WARN] offset {off}: header_size inválido ({header_size}) — pulando",
        "warn_pixel_format": "[WARN] Pixel Format Não implementado {b} em: {off}",
        "warn_cant_read_wh": "[WARN] offset {off}: não foi possível ler width/height — pulando",
        "warn_invalid_dimensions": "[WARN] offset {off}: dimensão inválida ({width}x{height}) — pulando",
        "warn_data_exceeds_file": "[WARN] offset {off}: dados esperados ({data_size} bytes) excedem arquivo ({available} disponíveis). Tentando ler parcial.",
        "warn_no_data_read": "[WARN] offset {off}: nenhum dado lido — pulando",
        "info_ok_written": "[OK] {path} ({width}x{height}) fmt={fmt} read={read}/{expected} bytes",
        "error_processing_offset": "[ERROR] ao processar offset {off}: {err}",

        "warn_index_mismatch": "Arquivo {name}: índice {idx} não corresponde a nenhum offset (offsets: {count}). Pulando.",
        "warn_cant_read_block": "Não foi possível ler informações do bloco NTX3 em 0x{off:08X}. Pulando {name}",
        "warn_unknown_pixel_byte": "Offset 0x{off:08X}: pixel format byte desconhecido {pixel}. Pulando {name}",
        "error_read_dds": "Falha lendo {name}: {err}",
        "warn_dds_small": "{name}: DDS parece pequeno (<128 bytes). Pulando.",
        "warn_size_mismatch": "{name}: tamanho de imagem DDS ({have}) não corresponde a {width}x{height} (esperado {expect}).",
        "error_convert": "Falha convertendo ARGB->RGBA em {name}: {err}",
        "warn_cant_determine_expected": "cannot determine expected data size for offset 0x{off:08X}. Pulando {name}",
        "warn_final_img_too_big": "{name}: dados a escrever ({have}) maiores que espaço original ({expected}) em 0x{off:08X}. Pulando.",
        "info_padding": "{name}: dados menores; serão preenchidos com {pad} zeros.",
        "info_written": "[OK] Gravado {name} em 0x{off:08X} (tamanho {expected})."
    },
    "en_US": {
        "plugin_name": "FILES|TEX|P3TEX... (Eternal Sonata PS3)",
        "plugin_description": "Extracts and rebuilds text files from Eternal Sonata game",
        "extract_file": "Extract File(.FILES)",
        "import_files": "Reimport Files(.FILES)",
        "select_files_file": "Select .FILES file",
        "select_import_dir": "Select folder with files to reimport",
        "files_files": "FILES Files",
        "all_files": "All files",
        "log_magic_invalid": "FILE magic not found at file start.",
        "success": "Success",
        "extraction_success": "Files extracted successfully!",
        "import_success": "Files reimported successfully!",
        "error": "Error",
        "extraction_error": "Error during extraction: {error}",
        "import_error": "Error during reimport: {error}",
        "file_not_found": "File not found: {file}",
        "processing_file": "Processing file: {file}",
        "extracting_to": "Extracting to: {path}",
        "invalid_structure": "Invalid file structure",
        "file_extracted": "File extracted: {filename} -> {output_path}",
        "file_reimported": "File reimported: {filename} -> offset {offset} size {size}",
        "file_not_in_header": "File not found in header, skipping: {filename}",
        "reading_header": "Reading container header...",
        "found_num_files": "Number of header entries: {num}",
        "starting_insert_at": "Starting insertion at aligned offset: {offset}",
        "skipping_nonfiles": "Skipping: {name} (not a file)",
        "extract_ntx": "Extract NTX3 -> DDS",
        "import_dds": "Import DDS -> NTX3",
        "select_ntx_files": "Choose binary file(s)",
        "select_ntx_file": "Choose the NTX3 original file to receive DDSs",
        "select_dds_files": "Select .dds files to import",
        "msg_title_error": "Error",
        "msg_title_done": "Done",
        "msg_no_offsets": "No NTX3 offsets found in the file.",
        "msg_invalid_magic": "Invalid magic: {magic} (expected {file_magic} or 'NTX3').",
        "msg_offsets_found": "Offsets found: {n}",
        "msg_extracted_count": "Textures extracted: {n} (folder: {out})",
        "msg_import_success": "Import finished. Files written successfully: {n}",
        "msg_import_fail": "Import failed: {err}",

        "warn_offset_negative": "[WARN] offset negative {off} — skipping",
        "warn_offset_beyond_file": "[WARN] offset {off} is beyond file size ({file_size}) — skipping",
        "warn_cant_read_header_size": "[WARN] offset {off}: cannot read header_size — skipping",
        "warn_invalid_header_size": "[WARN] offset {off}: invalid header_size ({header_size}) — skipping",
        "warn_pixel_format": "[WARN] Pixel Format not implemented {b} at: {off}",
        "warn_cant_read_wh": "[WARN] offset {off}: cannot read width/height — skipping",
        "warn_invalid_dimensions": "[WARN] offset {off}: invalid dimensions ({width}x{height}) — skipping",
        "warn_data_exceeds_file": "[WARN] offset {off}: expected data ({data_size} bytes) exceeds file ({available} available). Trying partial read.",
        "warn_no_data_read": "[WARN] offset {off}: no data read — skipping",
        "info_ok_written": "[OK] {path} ({width}x{height}) fmt={fmt} read={read}/{expected} bytes",
        "error_processing_offset": "[ERROR] processing offset {off}: {err}",

        "warn_index_mismatch": "File {name}: index {idx} does not match any offset (offsets: {count}). Skipping.",
        "warn_cant_read_block": "Cannot read NTX3 block info at 0x{off:08X}. Skipping {name}",
        "warn_unknown_pixel_byte": "Offset 0x{off:08X}: unknown pixel format byte {pixel}. Skipping {name}",
        "error_read_dds": "Failed reading {name}: {err}",
        "warn_dds_small": "{name}: DDS seems small (<128 bytes). Skipping.",
        "warn_size_mismatch": "{name}: DDS image size ({have}) does not match {width}x{height} (expected {expect}).",
        "error_convert": "Failed converting ARGB->RGBA in {name}: {err}",
        "warn_cant_determine_expected": "cannot determine expected data size for offset 0x{off:08X}. Skipping {name}",
        "warn_final_img_too_big": "{name}: data to write ({have}) larger than original space ({expected}) at 0x{off:08X}. Skipping.",
        "info_padding": "{name}: data smaller than original; will be padded with {pad} zeros.",
        "info_written": "[OK] Written {name} at 0x{off:08X} (size {expected})."
    },
    "es_ES": {
        "plugin_name": "FILES|TEX|P3TEX... (Eternal Sonata PS3)",
        "plugin_description": "Extrae y recrea archivos de texto del juego Eternal Sonata",
        "extract_file": "Extraer Archivo(.FILES)",
        "import_files": "Reimportar Archivos(.FILES)",
        "select_files_file": "Seleccionar archivo .FILES",
        "select_import_dir": "Seleccionar carpeta con archivos para reimportar",
        "files_files": "Archivos FILES",
        "all_files": "Todos los archivos",
        "log_magic_invalid": "Magic FILE no encontrada al inicio del archivo.",
        "success": "Éxito",
        "extraction_success": "¡Archivos extraídos con éxito!",
        "import_success": "¡Archivos reimportados con éxito!",
        "error": "Error",
        "extraction_error": "Error durante extracción: {error}",
        "import_error": "Error durante reimportación: {error}",
        "file_not_found": "Archivo no encontrado: {file}",
        "processing_file": "Procesando archivo: {file}",
        "extracting_to": "Extrayendo a: {path}",
        "invalid_structure": "Estructura de archivo inválida",
        "file_extracted": "Archivo extraído: {filename} -> {output_path}",
        "file_reimported": "Archivo reimportado: {filename} -> offset {offset} size {size}",
        "file_not_in_header": "Archivo no encontrado en el header, saltando: {filename}",
        "reading_header": "Leyendo header del contenedor...",
        "found_num_files": "Número de entradas en el header: {num}",
        "starting_insert_at": "Iniciando inserción en offset alineado: {offset}",
        "skipping_nonfiles": "Saltando: {name} (no es archivo)",
        "extract_ntx": "Extraer NTX3 -> DDS",
        "import_dds": "Importar DDS -> NTX3",
        "select_ntx_files": "Elija archivo(s) binario(s)",
        "select_ntx_file": "Elija el archivo NTX3 original para recibir los DDS",
        "select_dds_files": "Seleccione los archivos .dds a importar",
        "msg_title_error": "Error",
        "msg_title_done": "Listo",
        "msg_no_offsets": "No se encontraron offsets NTX3 en el archivo.",
        "msg_invalid_magic": "Magic inválido: {magic} (se esperaba {file_magic} o 'NTX3').",
        "msg_offsets_found": "Offsets encontrados: {n}",
        "msg_extracted_count": "Texturas extraídas: {n} (carpeta: {out})",
        "msg_import_success": "Importación finalizada. Archivos escritos con éxito: {n}",
        "msg_import_fail": "Fallo durante la importación: {err}",

        "warn_offset_negative": "[WARN] offset negativo {off} — omitiendo",
        "warn_offset_beyond_file": "[WARN] offset {off} está más allá del tamaño del archivo ({file_size}) — omitiendo",
        "warn_cant_read_header_size": "[WARN] offset {off}: no se pudo leer header_size — omitiendo",
        "warn_invalid_header_size": "[WARN] offset {off}: header_size inválido ({header_size}) — omitiendo",
        "warn_pixel_format": "[WARN] Pixel Format no implementado {b} en: {off}",
        "warn_cant_read_wh": "[WARN] offset {off}: no se pudo leer width/height — omitiendo",
        "warn_invalid_dimensions": "[WARN] offset {off}: dimensión inválida ({width}x{height}) — omitiendo",
        "warn_data_exceeds_file": "[WARN] offset {off}: datos esperados ({data_size} bytes) exceden archivo ({available} disponibles). Intentando lectura parcial.",
        "warn_no_data_read": "[WARN] offset {off}: no se leyeron datos — omitiendo",
        "info_ok_written": "[OK] {path} ({width}x{height}) fmt={fmt} read={read}/{expected} bytes",
        "error_processing_offset": "[ERROR] al procesar offset {off}: {err}",

        "warn_index_mismatch": "Archivo {name}: índice {idx} no corresponde a ningún offset (offsets: {count}). Omite.",
        "warn_cant_read_block": "No se pudo leer información del bloque NTX3 en 0x{off:08X}. Omite {name}",
        "warn_unknown_pixel_byte": "Offset 0x{off:08X}: byte de formato de píxel desconocido {pixel}. Omite {name}",
        "error_read_dds": "Fallo leyendo {name}: {err}",
        "warn_dds_small": "{name}: DDS parece pequeño (<128 bytes). Omite.",
        "warn_size_mismatch": "{name}: tamaño de imagen DDS ({have}) no coincide con {width}x{height} (esperado {expect}).",
        "error_convert": "Fallo al convertir ARGB->RGBA en {name}: {err}",
        "warn_cant_determine_expected": "cannot determine expected data size for offset 0x{off:08X}. Omite {name}",
        "warn_final_img_too_big": "{name}: datos a escribir ({have}) mayores que el espacio original ({expected}) en 0x{off:08X}. Omite.",
        "info_padding": "{name}: datos menores; serán rellenados con {pad} ceros.",
        "info_written": "[OK] Grabado {name} en 0x{off:08X} (tamaño {expected})."
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
            {"label": translate("import_files"), "action": select_container_for_import},
            {"label": translate("extract_ntx"), "action": selecionar_extrair_ntx},
            {"label": translate("import_dds"), "action": selecionar_import_dds_auto},
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
            
            magic = container.read(4)
            if magic != b'FILE':
                logger(translate("log_magic_invalid"))
                raise ValueError(translate("log_magic_invalid"))
                
            # Read header information
            container.seek(8)
            num_files = struct.unpack('>I', container.read(4))[0]
            
            if num_files == 0 or num_files > 10000:  # Sanity check
                raise ValueError(translate("invalid_structure"))
            
            header_offset = 16  # Start of file entries
            entry_size = 32 + 4 + 4  # filename(32) + start(4) + size(4) = 40 bytes
            
            for i in range(num_files):
                container.seek(header_offset + i * entry_size)
                
                # Read file entry
                filename = container.read(32).decode('utf-8').rstrip('\x00')
                file_start = struct.unpack('>I', container.read(4))[0]
                file_size = struct.unpack('>I', container.read(4))[0]
                
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


def align_up(x: int, alignment: int) -> int:
    return ((x + alignment - 1) // alignment) * alignment

def reimport_files_to_container(container_path, import_dir):
    """
    Reimport files from import_dir into the container using header ordering,
    without making a temporary copy. Abort if ANY header file is missing.
    Writes files sequentially after the header, aligned to 2048 bytes,
    with zero padding between header and first file and between files.
    """
    try:
        container_path = Path(container_path)
        import_dir = Path(import_dir)

        logger(translate("reading_header"))

        # --- READ HEADER (only read, no modifications yet) ---
        with container_path.open('rb') as orig:
            orig.seek(0)
            magic = orig.read(4)
            if magic != b'FILE':
                logger(translate("log_magic_invalid"))
                raise ValueError(translate("log_magic_invalid"))

            orig.seek(8)
            num_files = struct.unpack('>I', orig.read(4))[0]
            logger(translate("found_num_files", num=num_files))
            if num_files == 0 or num_files > 10000:
                raise ValueError(translate("invalid_structure"))

            entries_start = 16
            entry_size = 48
            header_entries = []

            for i in range(num_files):
                entry_offset = entries_start + i * entry_size
                orig.seek(entry_offset)
                raw_name = orig.read(32)
                filename = raw_name.split(b'\x00', 1)[0].decode('utf-8', errors='ignore')
                header_entries.append({
                    "filename": filename,
                    "entry_offset": entry_offset
                })

            header_end = entries_start + num_files * entry_size

        # --- VERIFY all files exist BEFORE modifying container ---
        missing = []
        for e in header_entries:
            src = import_dir / e['filename']
            if not src.exists() or not src.is_file():
                missing.append(e['filename'])

        if missing:
            for m in missing:
                logger(translate("file_not_in_header", filename=m))
            messagebox.showerror(translate("error"), translate("missing_files_abort", files=", ".join(missing)))
            return False

        # --- ALL FILES PRESENT: open original container for writing directly ---
        with container_path.open('r+b') as container:
            insert_ptr = align_up(header_end, 2048)
            logger(translate("starting_insert_at", offset=insert_ptr))

            # write zeros from header_end up to insert_ptr (if any)
            if insert_ptr > header_end:
                container.seek(header_end)
                to_write = insert_ptr - header_end
                chunk = 65536
                while to_write > 0:
                    write_now = min(chunk, to_write)
                    container.write(b'\x00' * write_now)
                    to_write -= write_now

            # iterate entries in header order, write each file and update header
            for e in header_entries:
                fname = e['filename']
                src_path = import_dir / fname
                data = src_path.read_bytes()
                file_len = len(data)

                # ensure file start aligned
                insert_ptr = align_up(insert_ptr, 2048)

                # write file data
                container.seek(insert_ptr)
                container.write(data)

                # write padding zeros so next file starts at 2048 boundary
                end_after_write = insert_ptr + file_len
                next_aligned = align_up(end_after_write, 2048)
                padding = next_aligned - end_after_write
                if padding > 0:
                    # write padding in one go (padding <= 2047)
                    container.write(b'\x00' * padding)

                # update header start and size fields (big-endian '>I')
                container.seek(e['entry_offset'] + 32)
                container.write(struct.pack('>I', insert_ptr))
                container.write(struct.pack('>I', file_len))

                logger(translate("file_reimported", filename=fname, offset=insert_ptr, size=file_len))

                # advance insert_ptr
                insert_ptr = next_aligned
            
            container.truncate()
            total_size = container.tell()
            container.seek(4)
            container.write(struct.pack('>I', total_size))


        messagebox.showinfo(translate("success"), translate("import_success"))
        return True

    except Exception as ex:
        # Any failure will leave the container possibly partially updated;
        # you mentioned you keep backups, so inform and return False.
        logger(translate("import_error", error=str(ex)))
        messagebox.showerror(translate("error"), translate("import_error", error=str(ex)))
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

def select_container_for_import():
    """Select .FILES and then select folder with files to reimport"""
    file_path = filedialog.askopenfilename(
        title=translate("select_files_file"),
        filetypes=[
            (translate("files_files"), "*.files"),
            (translate("all_files"), "*.*")
        ]
    )
    if not file_path:
        return

    file_path = Path(file_path)
    import_dir = file_path.with_name(file_path.stem)
    if not import_dir:
        return

    def run_import():
        reimport_files_to_container(file_path, import_dir)

    threading.Thread(target=run_import, daemon=True).start()


# constantes do formato
FILE_MAGIC = bytes.fromhex("03 33 90 10")
NTX_MAGIC = b"NTX3"

DDS_MAGIC = b"DDS "
DDS_HEADER_SIZE = 124
DDSD_CAPS = 0x1
DDSD_HEIGHT = 0x2
DDSD_WIDTH = 0x4
DDSD_PITCH = 0x8
DDSD_PIXELFORMAT = 0x1000
DDSD_LINEARSIZE = 0x80000
DDSCAPS_TEXTURE = 0x1000
DDPF_FOURCC = 0x4
DDPF_RGB = 0x40
DDPF_ALPHAPIXELS = 0x1

# -------------------------
# Conversões e header DDS
# -------------------------
def rgba_to_argb(data: bytes) -> bytes:
    out = bytearray(len(data))
    for i in range(0, len(data), 4):
        r = data[i]
        g = data[i + 1]
        b = data[i + 2]
        a = data[i + 3]
        out[i]     = a
        out[i + 1] = r
        out[i + 2] = g
        out[i + 3] = b
    return bytes(out)

def argb_to_rgba(data: bytes) -> bytes:
    out = bytearray(len(data))
    for i in range(0, len(data), 4):
        a = data[i]
        r = data[i + 1]
        g = data[i + 2]
        b = data[i + 3]
        out[i]     = r
        out[i + 1] = g
        out[i + 2] = b
        out[i + 3] = a
    return bytes(out)

def build_dds_header(width: int, height: int, fmt: str = "DXT5") -> bytes:
    if fmt not in ("DXT5", "DXT1", "RGBA"):
        raise ValueError("fmt must be 'DXT5', 'DXT1' or 'RGBA'")
    if fmt in ("DXT5", "DXT1"):
        flags = DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT | DDSD_LINEARSIZE
    else:
        flags = DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT | DDSD_PITCH
    header = bytearray()
    header += DDS_MAGIC
    header += struct.pack("<I", DDS_HEADER_SIZE)
    header += struct.pack("<I", flags)
    header += struct.pack("<I", height)
    header += struct.pack("<I", width)
    if fmt == "DXT5":
        blocks_w = max(1, (width + 3) // 4)
        blocks_h = max(1, (height + 3) // 4)
        linear_size = blocks_w * blocks_h * 16
        header += struct.pack("<I", linear_size)
    elif fmt == "DXT1":
        blocks_w = max(1, (width + 3) // 4)
        blocks_h = max(1, (height + 3) // 4)
        linear_size = blocks_w * blocks_h * 8
        header += struct.pack("<I", linear_size)
    else:
        header += struct.pack("<I", width * 4)
    header += struct.pack("<I", 0)
    header += struct.pack("<I", 0)
    for _ in range(11):
        header += struct.pack("<I", 0)
    header += struct.pack("<I", 32)
    if fmt in ("DXT5", "DXT1"):
        header += struct.pack("<I", DDPF_FOURCC)
        header += (b"DXT5" if fmt == "DXT5" else b"DXT1")
        header += struct.pack("<I", 0)
        header += struct.pack("<I", 0)
        header += struct.pack("<I", 0)
        header += struct.pack("<I", 0)
        header += struct.pack("<I", 0)
    else:
        header += struct.pack("<I", DDPF_RGB | DDPF_ALPHAPIXELS)
        header += struct.pack("<4s", b"\x00\x00\x00\x00")
        header += struct.pack("<I", 32)
        header += struct.pack("<I", 0x00FF0000)
        header += struct.pack("<I", 0x0000FF00)
        header += struct.pack("<I", 0x000000FF)
        header += struct.pack("<I", 0xFF000000)
    header += struct.pack("<I", DDSCAPS_TEXTURE)
    header += struct.pack("<I", 0)
    header += struct.pack("<I", 0)
    header += struct.pack("<I", 0)
    header += struct.pack("<I", 0)
    if len(header) != 128:
        raise RuntimeError(f"DDS header inesperado: {len(header)} bytes (esperado 128)")
    return bytes(header)

# -------------------------
# Detecção de offsets
# -------------------------
def collect_offsets_from_file(f) -> List[int]:
    offsets: List[int] = []
    try:
        f.seek(8)
    except Exception:
        return offsets
    while True:
        marker_bytes = f.read(4)
        if len(marker_bytes) < 4:
            break
        marker = int.from_bytes(marker_bytes, byteorder="little", signed=False)
        if marker == 1:
            off_bytes = f.read(4)
            if len(off_bytes) < 4:
                break
            offset = int.from_bytes(off_bytes, byteorder="big", signed=False)
            offsets.append(offset)
            continue
        else:
            break
    return offsets

def find_ntx_offsets_by_scanning(path: Path) -> List[int]:
    offsets: List[int] = []
    data = path.read_bytes()
    start = 0
    while True:
        idx = data.find(NTX_MAGIC, start)
        if idx == -1:
            break
        offsets.append(idx)
        start = idx + 1
    offsets = sorted(set(offsets))
    return offsets

# -------------------------
# Extração
# -------------------------
def extract_textures(path: Path, offsets: List[int]) -> List[Path]:
    out_files: List[Path] = []
    base = path.stem
    out_dir = path.parent
    with path.open("rb") as f:
        counter = 1
        for off in offsets:
            try:
                if off < 0:
                    logger(translate("warn_offset_negative", off=off))
                    continue
                f.seek(0, 2)
                file_size = f.tell()
                if off + 16 > file_size:
                    logger(translate("warn_offset_beyond_file", off=off, file_size=file_size))
                    continue
                f.seek(off)
                magic = f.read(4)
                if magic != NTX_MAGIC:
                    logger(translate("warn_pixel_format", b=magic.hex(), off=off))
                    continue
                f.seek(off + 16)
                header_size_b = f.read(4)
                if len(header_size_b) < 4:
                    logger(translate("warn_cant_read_header_size", off=off))
                    continue
                header_size = int.from_bytes(header_size_b, byteorder="big", signed=False)
                if header_size <= 0:
                    logger(translate("warn_invalid_header_size", off=off, header_size=header_size))
                    continue

                f.seek(off + 24)
                b = f.read(1)
                if b == b'\x86' or b == b'\xA6':
                    fmt = "DXT1"
                elif b == b'\x88' or b == b'\xA8':
                    fmt = "DXT5"
                elif b == b'\xA5':
                    fmt = "RGBA"
                else:
                    logger(translate("warn_pixel_format", b=b.hex(), off=off))
                    fmt = "DXT5"

                f.seek(off + 32)
                wh = f.read(4)
                if len(wh) < 4:
                    logger(translate("warn_cant_read_wh", off=off))
                    continue
                width = int.from_bytes(wh[0:2], byteorder="big", signed=False)
                height = int.from_bytes(wh[2:4], byteorder="big", signed=False)
                if width == 0 or height == 0:
                    logger(translate("warn_invalid_dimensions", off=off, width=width, height=height))
                    continue

                blocks_w = max(1, (width + 3) // 4)
                blocks_h = max(1, (height + 3) // 4)
                dxt1_size = blocks_w * blocks_h * 8
                dxt5_size = blocks_w * blocks_h * 16
                rgba_size = width * height * 4

                if fmt == "RGBA":
                    data_size = rgba_size
                elif fmt == "DXT1":
                    data_size = dxt1_size
                else:
                    data_size = dxt5_size

                data_offset = off + header_size

                if data_offset + data_size > file_size:
                    available = max(0, file_size - data_offset)
                    logger(translate("warn_data_exceeds_file", off=off, data_size=data_size, available=available))
                    f.seek(data_offset)
                    img_data = f.read(data_size)
                    if not img_data:
                        logger(translate("warn_no_data_read", off=off))
                        continue
                else:
                    f.seek(data_offset)
                    img_data = f.read(data_size)

                dds_fmt_for_header = fmt if fmt in ("DXT5", "DXT1") else "RGBA"
                dds_hdr = build_dds_header(width, height, dds_fmt_for_header)
                
                if dds_fmt_for_header == "RGBA":
                    img_data = rgba_to_argb(img_data)

                filename = f"{base}_{counter:04d}.dds"
                out_path = out_dir / filename
                with out_path.open("wb") as out_f:
                    out_f.write(dds_hdr)
                    out_f.write(img_data)

                logger(translate("info_ok_written", path=out_path, width=width, height=height, fmt=fmt, read=len(img_data), expected=data_size))
                out_files.append(out_path)
                counter += 1
            except Exception as e:
                logger(translate("error_processing_offset", off=off, err=str(e)))
                continue
    return out_files

# -------------------------
# Leitura de bloco NTX3 e parsing DDS
# -------------------------
def read_ntx3_block_info(f, off: int) -> Optional[Tuple[int,int,int,bytes,int]]:
    try:
        f.seek(0, 2)
        file_size = f.tell()
        if off + 40 > file_size:
            return None
        f.seek(off)
        magic = f.read(4)
        if magic != NTX_MAGIC:
            return None
        f.seek(off + 16)
        header_size_b = f.read(4)
        if len(header_size_b) < 4:
            return None
        header_size = int.from_bytes(header_size_b, byteorder="big", signed=False)
        f.seek(off + 24)
        pixel_byte = f.read(1)
        f.seek(off + 32)
        wh = f.read(4)
        if len(wh) < 4:
            return None
        width = int.from_bytes(wh[0:2], byteorder="big", signed=False)
        height = int.from_bytes(wh[2:4], byteorder="big", signed=False)
        if width == 0 or height == 0:
            return None
        blocks_w = max(1, (width + 3) // 4)
        blocks_h = max(1, (height + 3) // 4)
        dxt1_size = blocks_w * blocks_h * 8
        dxt5_size = blocks_w * blocks_h * 16
        rgba_size = width * height * 4
        if pixel_byte == b'\xA5':
            expected = rgba_size
        elif pixel_byte in (b'\x86', b'\xA6'):
            expected = dxt1_size
        elif pixel_byte in (b'\x88', b'\xA8'):
            expected = dxt5_size
        else:
            expected = 0
        return (header_size, width, height, pixel_byte, expected)
    except Exception:
        return None

def parse_dds_header(header: bytes) -> Tuple[str, int]:
    if len(header) < 128:
        raise ValueError("Header DDS muito pequeno")
    if b"DXT1" in header:
        return ("DXT1", 128)
    if b"DXT5" in header:
        return ("DXT5", 128)
    m1 = struct.pack("<I", 0x00FF0000)
    m2 = struct.pack("<I", 0x0000FF00)
    m3 = struct.pack("<I", 0x000000FF)
    m4 = struct.pack("<I", 0xFF000000)
    if m1 in header and m2 in header and m3 in header and m4 in header:
        return ("ARGB", 128)
    return ("ARGB", 128)

# -------------------------
# Importar DDS de volta
# -------------------------
def import_dds_back_to_ntx3(ntx_path: Path, dds_paths: List[Path]) -> int:
    success_count = 0
    with ntx_path.open("rb") as f:
        start4 = f.read(4)
        f.seek(0)
        if start4 == FILE_MAGIC:
            offsets = collect_offsets_from_file(f)
        else:
            whole = f.read()
            if whole.startswith(NTX_MAGIC) or NTX_MAGIC in whole:
                offsets = find_ntx_offsets_by_scanning(ntx_path)
            else:
                raise RuntimeError(translate("msg_invalid_magic", magic=start4.hex(), file_magic=FILE_MAGIC.hex()))
    if not offsets:
        raise RuntimeError(translate("msg_no_offsets"))

    regex_idx = re.compile(r"_(\d{1,4})\.dds$", re.IGNORECASE)
    mapped: List[Tuple[int, Path]] = []
    for p in dds_paths:
        m = regex_idx.search(p.name)
        if m:
            idx = int(m.group(1))
            mapped.append((idx, p))
        else:
            mapped.append((0, p))
    has_indices = any(idx > 0 for idx, _ in mapped)
    if has_indices:
        mapped = [pair for pair in mapped if pair[0] > 0]
        mapped.sort(key=lambda x: x[0])
    else:
        dds_paths_sorted = sorted([p for _, p in mapped], key=lambda p: p.name)
        mapped = [(i+1, p) for i, p in enumerate(dds_paths_sorted)]

    with ntx_path.open("r+b") as f:
        for idx, dds_path in mapped:
            if idx - 1 < 0 or idx - 1 >= len(offsets):
                logger(translate("warn_index_mismatch", name=dds_path.name, idx=idx, count=len(offsets)))
                continue
            off = offsets[idx - 1]
            block_info = read_ntx3_block_info(f, off)
            if block_info is None:
                logger(translate("warn_cant_read_block", off=off, name=dds_path.name))
                continue
            header_size, width, height, pixel_byte, expected_size = block_info
            if pixel_byte == b'\xA5':
                orig_fmt = "RGBA"
            elif pixel_byte in (b'\x86', b'\xA6'):
                orig_fmt = "DXT1"
            elif pixel_byte in (b'\x88', b'\xA8'):
                orig_fmt = "DXT5"
            else:
                logger(translate("warn_unknown_pixel_byte", off=off, pixel=pixel_byte.hex(), name=dds_path.name))
                continue

            try:
                with dds_path.open("rb") as df:
                    dds_all = df.read()
            except Exception as e:
                logger(translate("error_read_dds", name=dds_path.name, err=str(e)))
                continue
            if len(dds_all) < 128:
                logger(translate("warn_dds_small", name=dds_path.name))
                continue
            dds_header = dds_all[:128]
            dds_fmt, dds_data_offset = parse_dds_header(dds_header)
            dds_img = dds_all[dds_data_offset:]

            if dds_fmt in ("DXT1", "DXT5"):
                dds_type = dds_fmt
            else:
                dds_type = "RGBA"

            if orig_fmt != dds_type:
                logger(translate("warn_final_img_too_big", name=dds_path.name, have=len(dds_img), expected=expected_size, off=off))
                logger(translate("warn_size_mismatch", name=dds_path.name, have=len(dds_img), width=width, expect=width*height*4))
                continue

            if dds_type == "RGBA":
                if len(dds_img) != width * height * 4:
                    logger(translate("warn_size_mismatch", name=dds_path.name, have=len(dds_img), width=width, expect=width*height*4))
                try:
                    final_img = argb_to_rgba(dds_img)
                except Exception as e:
                    logger(translate("error_convert", name=dds_path.name, err=str(e)))
                    continue
            else:
                final_img = dds_img

            if expected_size == 0:
                logger(translate("warn_cant_determine_expected", off=off, name=dds_path.name))
                continue

            if len(final_img) > expected_size:
                logger(translate("warn_final_img_too_big", name=dds_path.name, have=len(final_img), expected=expected_size, off=off))
                continue
            if len(final_img) < expected_size:
                pad_len = expected_size - len(final_img)
                final_img = final_img + (b"\x00" * pad_len)
                logger(translate("info_padding", name=dds_path.name, pad=pad_len))

            data_offset = off + header_size
            try:
                f.seek(data_offset)
                f.write(final_img[:expected_size])
                f.flush()
                logger(translate("info_written", name=dds_path.name, off=off, expected=expected_size))
                success_count += 1
            except Exception as e:
                logger(translate("error_processing_offset", off=off, err=str(e)))
                continue

    return success_count

# ==========================
# Selecionadores / comandos expostos pelo plugin
# ==========================

def selecionar_extrair_ntx():
    files = filedialog.askopenfilenames(title=translate("select_ntx_files"), filetypes=[("Textura (.tex/.p3tex)", "*.tex;*.p3tex"), ("All files", "*.*")])
    if not files:
        return
    def job():
        for file_path in files:
            path = Path(file_path)
            logger(translate("info_ok_written", path=path, width=0, height=0, fmt="", read=0, expected=0))
            try:
                with path.open("rb") as f:
                    start = f.read(4)
                    f.seek(0)
                    if start == FILE_MAGIC:
                        logger(translate("info_ok_written", path=path, width=0, height=0, fmt="FILE_MAGIC", read=0, expected=0))
                        offsets = collect_offsets_from_file(f)
                    else:
                        whole = f.read()
                        if whole.startswith(NTX_MAGIC) or NTX_MAGIC in whole:
                            logger(translate("info_ok_written", path=path, width=0, height=0, fmt="NTX_SCAN", read=0, expected=0))
                            offsets = find_ntx_offsets_by_scanning(path)
                        else:
                            messagebox.showerror(translate("msg_title_error"), translate("msg_invalid_magic", magic=start.hex(), file_magic=FILE_MAGIC.hex()))
                            continue
            except Exception as e:
                logger(translate("error_processing_offset", off=0, err=str(e)))
                continue

            logger(translate("msg_offsets_found", n=len(offsets)))
            for i, off in enumerate(offsets, start=1):
                logger(translate("info_written", name=f"offset_{i}", off=off, expected=0))

            if not offsets:
                logger(translate("msg_no_offsets"))
                continue

            logger(translate("info_ok_written", path=path, width=0, height=0, fmt="start_extract", read=0, expected=0))
            out_files = extract_textures(path, offsets)
            messagebox.showinfo("OK", translate("msg_extracted_count", n=len(out_files), out=path.parent))

    threading.Thread(target=job, daemon=True).start()


def selecionar_import_dds_auto():
    ntx_file = filedialog.askopenfilename(title=translate("select_ntx_file"), filetypes=[("Textura (.tex/.p3tex)", "*.tex;*.p3tex"), ("All files", "*.*")])
    if not ntx_file:
        return
    ntx_path = Path(ntx_file)
    base = ntx_path.stem
    dirp = ntx_path.parent
    pattern = f"{base}_*.dds"
    found = sorted(dirp.glob(pattern), key=lambda p: p.name)
    if found:
        dds_paths = found
    else:
        resp = messagebox.askyesno(translate("import_dds"), "Nenhum DDS automático encontrado na mesma pasta. Selecionar arquivos manualmente?")
        if not resp:
            return
        sel = filedialog.askopenfilenames(title=translate("select_dds_files"), initialdir=str(dirp), filetypes=[("DDS files", "*.dds"), ("All files", "*.*")])
        if not sel:
            return
        dds_paths = [Path(p) for p in sel]

    def job():
        try:
            written = import_dds_back_to_ntx3(ntx_path, dds_paths)
            messagebox.showinfo("OK", translate("msg_import_success", n=written))
        except Exception as e:
            logger(translate("msg_import_fail", err=str(e)))

    threading.Thread(target=job, daemon=True).start()
