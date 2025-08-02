import struct
import os
import threading
from tkinter import filedialog, messagebox
from pathlib import Path

# ===================== TRADUÇÕES =====================
plugin_translations = {
    "pt_BR": {
        "plugin_name": "COALESCED Arquivo Unreal Engine 3 PS3/XBOX 360/N. Switch",
        "plugin_description": "Extrai e recria arquivos COALESCED de jogos feitos na Unreal Engine 3 PS360/Switch",
        "extract_file": "Extrair Arquivo",
        "rebuild_file": "Reconstruir Arquivo",
        "select_coalesced_file": "Selecione arquivo COALESCED",
        "coalesced_files": "Arquivos COALESCED",
        "all_files": "Todos os arquivos",
        "success": "Sucesso",
        "extraction_success": "Extração concluída com sucesso!",
        "recreation_success": "Arquivo reconstruído com sucesso!",
        "error": "Erro",
        "extraction_error": "Erro durante extração: {error}",
        "recreation_error": "Erro durante reconstrução: {error}",
        "file_not_found": "Arquivo não encontrado: {file}",
        "processing_file": "Processando arquivo: {file}",
        "extracting_to": "Extraindo para: {path}",
        "recreating_to": "Reconstruindo para: {path}",
        "version_warning": "Versão - ANSI (1.0/2.0) ou UTF-8 (3.0)",
        "empty_file": "Arquivo vazio ou inválido",
        "invalid_structure": "Estrutura do arquivo inválida",
        "missing_extracted": "Arquivos extraídos não encontrados",
        "version_options": {
            "1.0": "Versão 1.0 (ANSI - Texto simples)",
            "2.0": "Versão 2.0 (ANSI - Estrutura INI simples)",
            "3.0": "Versão 3.0 (UTF-16 - Estrutura complexa)"
        }
    },
    "en_US": {
        "plugin_name": "COALESCED Unreal Engine 3 PS3/XBOX 360/N. Switch File",
        "plugin_description": "Extracts and rebuilds COALESCED files from Unreal Engine 3 PS360/Switch games",
        "extract_file": "Extract File",
        "rebuild_file": "Rebuild File",
        "select_coalesced_file": "Select COALESCED file",
        "coalesced_files": "COALESCED Files",
        "all_files": "All files",
        "success": "Success",
        "extraction_success": "Extraction completed successfully!",
        "recreation_success": "File rebuilt successfully!",
        "error": "Error",
        "extraction_error": "Error during extraction: {error}",
        "recreation_error": "Error during rebuilding: {error}",
        "file_not_found": "File not found: {file}",
        "processing_file": "Processing file: {file}",
        "extracting_to": "Extracting to: {path}",
        "recreating_to": "Rebuilding to: {path}",
        "version_warning": "Version {version} - ANSI (1.0/2.0) or UTF-8 (3.0)",
        "empty_file": "Empty or invalid file",
        "invalid_structure": "Invalid file structure",
        "missing_extracted": "Extracted files not found",
        "version_options": {
            "1.0": "Version 1.0 (ANSI - Simple text)",
            "2.0": "Version 2.0 (ANSI - INI structure)",
            "3.0": "Version 3.0 (UTF-16 - Full structure)"
        }
    },
    "es_ES": {
        "plugin_name": "COALESCED Archivo Unreal Engine 3 PS3/XBOX 360/N. Switch",
        "plugin_description": "Extrae y recrea archivos COALESCED de juegos Unreal Engine 3 PS360/Switch",
        "extract_file": "Extraer Archivo",
        "rebuild_file": "Reconstruir Archivo",
        "select_coalesced_file": "Seleccionar archivo COALESCED",
        "coalesced_files": "Archivos COALESCED",
        "all_files": "Todos los archivos",
        "success": "Éxito",
        "extraction_success": "¡Extracción completada con éxito!",
        "recreation_success": "¡Archivo reconstruido con éxito!",
        "error": "Error",
        "extraction_error": "Error durante extracción: {error}",
        "recreation_error": "Error durante reconstrucción: {error}",
        "file_not_found": "Archivo no encontrado: {file}",
        "processing_file": "Procesando archivo: {file}",
        "extracting_to": "Extrayendo a: {path}",
        "recreating_to": "Reconstruyendo a: {path}",
        "version_warning": "Versión - ANSI (1.0/2.0) o UTF-8 (3.0)",
        "empty_file": "Archivo vacío o inválido",
        "invalid_structure": "Estructura de archivo inválida",
        "missing_extracted": "Archivos extraídos no encontrados",
        "1.0": "Versión 1.0 (ANSI - Texto simple)",
        "2.0": "Versión 2.0 (ANSI - Estructura INI)",
        "3.0": "Versión 3.0 (UTF-16 - Estructura completa)"
    }
}

# ===================== VARIÁVEIS GLOBAIS =====================
logger = print
current_language = "pt_BR"
get_option = lambda name: None

# ===================== FUNÇÃO DE TRADUÇÃO =====================
def translate(key, **kwargs):
    """Função de tradução interna do plugin"""
    lang_dict = plugin_translations.get(current_language, plugin_translations["pt_BR"])
    translation = lang_dict.get(key, key)
    
    if kwargs:
        try:
            return translation.format(**kwargs)
        except:
            return translation
    return translation

# ===================== REGISTRO DO PLUGIN =====================
def register_plugin(log_func, option_getter, host_language="pt_BR"):
    global logger, get_option, current_language
    logger = log_func or print
    get_option = option_getter or (lambda name: None)
    current_language = host_language
    
    def get_plugin_info():

        return {
            "name": translate("plugin_name"),
            "description": translate("plugin_description"),
            "options":[
                {
                    "name": "tipo_arquivo",
                    "label": translate("version_warning"),
                    "values": [translate("1.0"), translate("2.0"), translate("3.0")]}
                
            ],
            "commands": [
                {"label": translate("extract_file"), "action": process_file},
                {"label": translate("rebuild_file"), "action": reprocess_file},
            ]
        }
    
    return get_plugin_info

# ===================== FUNÇÕES AUXILIARES =====================
def read_utf16_name(file, endianess):
    """Lê um nome de arquivo no formato UTF-16 com tratamento de endianness"""
    char_count_bytes = file.read(4)
    if not char_count_bytes:
        return None
        
    raw_value = struct.unpack(f'{endianess}I', char_count_bytes)[0]
    char_count = 0xFFFFFFFF - raw_value  # 4294967295 = FF FF FF FF
    name_length = char_count * 2 + 2  # UTF-16LE + terminador nulo
    name_data = file.read(name_length)
    return name_data.decode('utf-16le').rstrip('\x00')

# ===================== FUNÇÕES PRINCIPAIS =====================
def read_binary_file(file_path):
    """Extrai conteúdo de arquivo COALESCED conforme versão selecionada"""
    try:
        version = get_option("tipo_arquivo") or "3.0"
        logger(translate("version_warning", version=version))
        
        if version == "2.0":
            return extract_version_2(file_path)
        elif version == "1.0":
            return extract_version_1(file_path)
        else:
            return extract_version_3(file_path)
            
    except Exception as e:
        messagebox.showerror(
            translate("error"),
            translate("extraction_error", error=str(e))
        )
        return False

def extract_version_1(file_path):
    """Estrutura INI em ANSI mais simplificada..."""
    try:
        input_path = Path(file_path)
        output_folder = input_path.parent / input_path.stem
        output_folder.mkdir(exist_ok=True)

        logger(translate("extracting_to", path=output_folder))

        with open(file_path, 'rb') as f:
            f.seek(4)

            while True:
                name_len_data = f.read(4)
                if not name_len_data:
                    break  # Fim do arquivo

                name_len = struct.unpack('>I', name_len_data)[0]
                name = f.read(name_len).strip(b'\x00').decode('ansi').replace('..\\', '').replace('../', '')
                
                content_len_data = f.read(4)
                if not content_len_data:
                    break  # Fim do arquivo
                content_len = struct.unpack('>I', content_len_data)[0]
                content = f.read(content_len).strip(b'\x00')

                output_path = output_folder / name
                output_path.parent.mkdir(parents=True, exist_ok=True)

                with open(output_path, 'wb') as out_file:
                    out_file.write(content)

        messagebox.showinfo(
            translate("success"),
            translate("extraction_success")
        )
        return True

    except Exception as e:
        raise Exception(translate("extraction_error", error=str(e)))

def extract_version_2(file_path):
    """Extrai versão 2.0 (estrutura INI ANSI um pouco mais complexa"""
    try:
        output_dir = Path(file_path).with_suffix('')
        output_dir.mkdir(exist_ok=True)
        logger(translate("extracting_to", path=output_dir))
        
        with open(file_path, 'rb') as f:
            f.seek(4)
            
            while True:
                # Lê nome do arquivo
                name_length_data = f.read(4)
                if not name_length_data:
                    break
                    
                name_length = struct.unpack('>I', name_length_data)[0]
                name_data = f.read(name_length)
                filename = name_data.strip(b'\x00').decode('ansi')
                safe_path = output_dir / filename.lstrip('..\\')
                safe_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Processa conteúdo do arquivo
                num_items = struct.unpack('>I', f.read(4))[0]
                with open(safe_path, 'w', encoding='ansi') as out_file:
                    for i in range(num_items):
                        # Nome do item
                        item_name_length = struct.unpack('>I', f.read(4))[0]
                        item_name = f.read(item_name_length).strip(b'\x00').decode('ansi')
                        out_file.write(f"[{item_name}]\n")
                        
                        # Subitens
                        num_subitems = struct.unpack('>I', f.read(4))[0]
                        for _ in range(num_subitems):
                            # Chave
                            key_length = struct.unpack('>I', f.read(4))[0]
                            key = f.read(key_length).strip(b'\x00').decode('ansi')
                            
                            # Valor
                            value_length = struct.unpack('>I', f.read(4))[0]
                            value = f.read(value_length).strip(b'\x00').decode('ansi')
                            
                            out_file.write(f"{key}={value}\n")
                            
                        if i + 1 < num_items:
                            out_file.write("\n")
                
                logger(translate("processing_file", file=filename))
                
        messagebox.showinfo(
            translate("success"),
            translate("extraction_success")
        )
        return True
        
    except Exception as e:
        raise Exception(translate("extraction_error", error=str(e)))

def extract_version_3(file_path):
    """Extrai versão 3.0 (estrutura completa UTF-16)"""
    try:
        output_dir = Path(file_path).with_suffix('')
        output_dir.mkdir(exist_ok=True)
        logger(translate("extracting_to", path=output_dir))
        
        with open(file_path, 'rb') as f:
            # Detecta endianness
            endian_check = f.read(2)
            endianess = '>' if endian_check == b'\x00\x00' else '<'
            f.seek(0)
            
            # Número total de arquivos
            total_files = struct.unpack(f'{endianess}I', f.read(4))[0]
            
            for _ in range(total_files):
                # Lê nome do arquivo
                filename = read_utf16_name(f, endianess)
                if not filename:
                    raise Exception(translate("empty_file"))
                    
                safe_path = output_dir / filename.replace("..\\", "")
                safe_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Número de itens
                num_items = struct.unpack(f'{endianess}I', f.read(4))[0]
                items = []
                
                for _ in range(num_items):
                    # Nome do item
                    item_name = read_utf16_name(f, endianess)
                    
                    # Subitens
                    num_subitems = struct.unpack(f'{endianess}I', f.read(4))[0]
                    subitems = []
                    
                    for _ in range(num_subitems):
                        # Chave
                        key = read_utf16_name(f, endianess) or ""
                        
                        # Valor
                        value = read_utf16_name(f, endianess) or ""
                        value = value.replace("\n", "\\n").replace("\r", "\\r")
                        
                        subitems.append((key, value))
                    
                    items.append((item_name, subitems))
                
                # Escreve arquivo extraído
                with open(safe_path, 'w', encoding='utf-8') as out_file:
                    for i, (item_name, subitems) in enumerate(items):
                        if item_name:
                            out_file.write(f"[{item_name}]\n")
                            
                        for j, (key, value) in enumerate(subitems):
                            out_file.write(f"{key}={value}")
                            if j + 1 < len(subitems) or i + 1 < len(items):
                                out_file.write("\n")
                                
                        if i + 1 < len(items) and subitems:
                            out_file.write("\n")
                
                logger(translate("processing_file", file=filename))
                
        messagebox.showinfo(
            translate("success"),
            translate("extraction_success")
        )
        return True
        
    except Exception as e:
        raise Exception(translate("extraction_error", error=str(e)))

def rebuild_binary_file(original_file_path, output_file_path, extracted_folder):
    """Reconstrói arquivo COALESCED conforme versão selecionada"""
    try:
        version = get_option("tipo_arquivo") or "3.0"
        logger(translate("version_warning", version=version))
        
        if version == "2.0":
            return rebuild_version_2(original_file_path, output_file_path, extracted_folder)
        elif version == "1.0":
            return rebuild_version_1(original_file_path, output_file_path, extracted_folder)
        else:
            return rebuild_version_3(original_file_path, output_file_path, extracted_folder)
            
    except Exception as e:
        messagebox.showerror(
            translate("error"),
            translate("recreation_error", error=str(e))
        )
        return False

def rebuild_version_1(original_path, output_path, extracted_folder):
    """Reconstrói container versão 1.0 com base nos caminhos do arquivo original."""
    try:
        extracted_folder = Path(extracted_folder)
        original_path = Path(original_path)
        output_path = Path(output_path)

        logger(translate("recreating_to", path=output_path))

        file_entries = []
        num_files = []

        # Primeiro: extrai apenas a lista de caminhos do arquivo original
        with open(original_path, 'rb') as orig:
            num_files_data = orig.read(4)
            if len(num_files_data) != 4:
                raise Exception("Cabeçalho inválido.")

            num_files = struct.unpack('>I', num_files_data)[0]

            while True:
                name_len_data = orig.read(4)
                if not name_len_data:
                    break
                name_len = struct.unpack('>I', name_len_data)[0]

                name = orig.read(name_len).strip(b'\x00').decode('ansi')
                logger(f"{name}")

                content_len_data = orig.read(4)
                if not content_len_data:
                    break
                content_len = struct.unpack('>I', content_len_data)[0]

                # pula o conteúdo original (não vamos reutilizar)
                orig.seek(content_len, 1)

                file_entries.append(name)

        # Segundo: escreve novo arquivo com os conteúdos da pasta extraída
        with open(output_path, 'wb') as out:
            out.write(struct.pack('>I', num_files))

            for name in file_entries:
                cleaned_name = name.replace('..\\', '').replace('../', '')
                file_path = extracted_folder / cleaned_name

                if not file_path.exists():
                    raise FileNotFoundError(translate("file_not_found", file=str(file_path)))

                encoded_name = name.encode('ansi') + b'\x00'
                encoded_content = file_path.read_bytes() + b'\x00'

                out.write(struct.pack('>I', len(encoded_name)))
                out.write(encoded_name)
                out.write(struct.pack('>I', len(encoded_content)))
                out.write(encoded_content)

        messagebox.showinfo(
            translate("success"),
            translate("recreation_success")
        )
        return True

    except Exception as e:
        raise Exception(translate("recreation_error", error=str(e)))

def rebuild_version_2(original_path, output_path, extracted_folder):
    """Reconstrói versão 2.0 (estrutura INI ANSI)"""
    try:
        extracted_folder = Path(extracted_folder)
        output_path = Path(output_path)
        
        # Primeiro passagem: coleta nomes dos arquivos originais
        file_names = []
        with open(original_path, 'rb') as orig:
            orig.seek(4)  # Pula cabeçalho
            
            while True:
                name_length_data = orig.read(4)
                if not name_length_data:
                    break
                    
                name_length = struct.unpack('>I', name_length_data)[0]
                name_data = orig.read(name_length)
                file_names.append(name_data)
                
                # Pula o conteúdo do arquivo
                num_items = struct.unpack('>I', orig.read(4))[0]
                for _ in range(num_items):
                    item_name_len = struct.unpack('>I', orig.read(4))[0]
                    orig.seek(item_name_len, 1)
                    sub_count = struct.unpack('>I', orig.read(4))[0]
                    for __ in range(sub_count):
                        key_len = struct.unpack('>I', orig.read(4))[0]
                        orig.seek(key_len, 1)
                        val_len = struct.unpack('>I', orig.read(4))[0]
                        orig.seek(val_len, 1)
        
        # Segunda passagem: reconstrói com os arquivos modificados
        with open(output_path, 'wb') as out:
            out.write(struct.pack('>I', len(file_names)))
            
            for name_data in file_names:
                out.write(struct.pack('>I', len(name_data)))
                out.write(name_data)
                
                filename = name_data.rstrip(b'\x00').decode('ansi').lstrip('..\\')
                file_path = extracted_folder / filename
                
                if not file_path.exists():
                    raise FileNotFoundError(translate("file_not_found", file=file_path))
                    
                # Processa arquivo INI
                with open(file_path, 'r', encoding='ansi') as f:
                    blocks = [b.strip() for b in f.read().split('\n\n') if b.strip()]
                
                out.write(struct.pack('>I', len(blocks)))
                
                for block in blocks:
                    lines = [l.strip() for l in block.split('\n') if l.strip()]
                    if not lines:
                        continue
                        
                    # Escreve nome do item
                    item_name = lines[0][1:-1]  # Remove []
                    item_name_enc = item_name.encode('ansi') + b'\x00'
                    out.write(struct.pack('>I', len(item_name_enc)))
                    out.write(item_name_enc)
                    
                    # Escreve subitens
                    subitems = lines[1:]
                    out.write(struct.pack('>I', len(subitems)))
                    
                    for line in subitems:
                        if '=' not in line:
                            continue
                            
                        key, value = line.split('=', 1)
                        key_enc = key.encode('ansi') + b'\x00'
                        value_enc = value.encode('ansi') + b'\x00'
                        
                        out.write(struct.pack('>I', len(key_enc)))
                        out.write(key_enc)
                        out.write(struct.pack('>I', len(value_enc)))
                        out.write(value_enc)
        
        messagebox.showinfo(
            translate("success"),
            translate("recreation_success")
        )
        return True
        
    except Exception as e:
        raise Exception(translate("recreation_error", error=str(e)))

def rebuild_version_3(original_path, output_path, extracted_folder):
    """Reconstrói versão 3.0 (estrutura completa UTF-16)"""
    try:
        extracted_folder = Path(extracted_folder)
        output_path = Path(output_path)
        
        # Detecta endianness do original
        with open(original_path, 'rb') as f:
            endian_check = f.read(2)
            endianess = '>' if endian_check == b'\x00\x00' else '<'
            f.seek(0)
            
            # Coleta nomes dos arquivos originais
            total_files = struct.unpack(f'{endianess}I', f.read(4))[0]
            file_names = []
            
            for _ in range(total_files):
                filename = read_utf16_name(f, endianess)
                if not filename:
                    break
                    
                file_names.append(filename)
                
                # Pula conteúdo do arquivo
                num_items = struct.unpack(f'{endianess}I', f.read(4))[0]
                for _ in range(num_items):
                    read_utf16_name(f, endianess)  # Nome do item
                    num_subitems = struct.unpack(f'{endianess}I', f.read(4))[0]
                    for __ in range(num_subitems):
                        read_utf16_name(f, endianess)  # Chave
                        read_utf16_name(f, endianess)  # Valor
        
        # Reconstrói arquivo
        with open(output_path, 'wb') as out:
            out.write(struct.pack(f'{endianess}I', len(file_names)))
            
            for filename in file_names:
                file_path = extracted_folder / filename.replace("..\\", "")
                if not file_path.exists():
                    raise FileNotFoundError(translate("file_not_found", file=file_path))
                    
                # Processa conteúdo do arquivo
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Escreve nome do arquivo
                filename_utf16 = filename.encode('utf-16le')
                char_count = len(filename)
                char_count_enc = 0xFFFFFFFF - char_count
                out.write(struct.pack(f'{endianess}I', char_count_enc))
                out.write(filename_utf16 + b'\x00\x00')
                
                if not content.strip():
                    out.write(struct.pack(f'{endianess}I', 0))
                    continue
                    
                # Processa itens
                items = [i.strip() for i in content.split('\n\n') if i.strip()]
                out.write(struct.pack(f'{endianess}I', len(items)))
                
                for item in items:
                    lines = [l.strip() for l in item.split('\n') if l.strip()]
                    if not lines:
                        continue
                        
                    # Nome do item
                    item_name = lines[0][1:-1]  # Remove []
                    item_name_utf16 = item_name.encode('utf-16le')
                    char_count_item = len(item_name)
                    char_count_item_enc = 0xFFFFFFFF - char_count_item
                    out.write(struct.pack(f'{endianess}I', char_count_item_enc))
                    out.write(item_name_utf16 + b'\x00\x00')
                    
                    # Subitens
                    subitems = lines[1:]
                    out.write(struct.pack(f'{endianess}I', len(subitems)))
                    
                    for subitem in subitems:
                        if '=' not in subitem:
                            continue
                            
                        key, value = subitem.split('=', 1)
                        value = value.replace("\\n", "\n").replace("\\r", "\r")
                        
                        # Chave
                        key_utf16 = key.encode('utf-16le')
                        char_count_key = len(key)
                        if char_count_key > 0:
                            char_count_key_enc = 0xFFFFFFFF - char_count_key
                            out.write(struct.pack(f'{endianess}I', char_count_key_enc))
                            out.write(key_utf16 + b'\x00\x00')
                        else:
                            out.write(struct.pack(f'{endianess}I', 0))
                            
                        # Valor
                        value_utf16 = value.encode('utf-16le')
                        char_count_value = len(value)
                        if char_count_value > 0:
                            char_count_value_enc = 0xFFFFFFFF - char_count_value
                            out.write(struct.pack(f'{endianess}I', char_count_value_enc))
                            out.write(value_utf16 + b'\x00\x00')
                        else:
                            out.write(struct.pack(f'{endianess}I', 0))
        
        messagebox.showinfo(
            translate("success"),
            translate("recreation_success")
        )
        return True
        
    except Exception as e:
        raise Exception(translate("recreation_error", error=str(e)))

# ===================== HANDLERS DE COMANDOS =====================
def process_file():
    """Handler para extração de arquivos"""
    file_path = filedialog.askopenfilename(
        title=translate("select_coalesced_file"),
        filetypes=[
            (translate("coalesced_files"), "*.bin *.ini *.int"),
            (translate("all_files"), "*.*")
        ]
    )
    if not file_path:
        return
        
    def run_extraction():
        try:
            if read_binary_file(file_path):
                logger(translate("extraction_success"))
        except Exception as e:
            logger(translate("extraction_error", error=str(e)))
    
    threading.Thread(target=run_extraction, daemon=True).start()

def reprocess_file():
    """Handler para reconstrução de arquivos"""
    original_path = filedialog.askopenfilename(
        title=translate("select_coalesced_file"),
        filetypes=[
            (translate("coalesced_files"), "*.bin *.ini *.int"),
            (translate("all_files"), "*.*")
        ]
    )
    if not original_path:
        return
        
    extracted_folder = Path(original_path).with_suffix('')
    output_path = Path(original_path).with_name(f"NEW_{Path(original_path).name}")
    
    def run_rebuild():
        try:
            if rebuild_binary_file(original_path, output_path, extracted_folder):
                logger(translate("recreation_success"))
        except Exception as e:
            logger(translate("recreation_error", error=str(e)))
    
    threading.Thread(target=run_rebuild, daemon=True).start()