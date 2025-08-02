import os
import struct
import zlib
import threading
from tkinter import filedialog, messagebox

# ===================== TRADUÇÕES =====================
plugin_translations = {
    "pt_BR": {
        "plugin_name": "CAT/MATCAT Arquivo FEAR 1 PS3/XBOX 360",
        "plugin_description": "Extrai e recria contêineres (.CAT/.MATCAT) FEAR 1",
        "extract_file": "Extrair Arquivo",
        "rebuild_file": "Reconstruir Arquivo",
        "select_fear_file": "Selecione arquivo .CAT ou .MATCAT",
        "fear_files": "Arquivos FEAR (.cat, .matcat)",
        "all_files": "Todos os arquivos",
        "success": "Sucesso",
        "extraction_success": "Arquivos extraídos com sucesso!",
        "recreation_success": "Arquivo recriado com sucesso!",
        "error": "Erro",
        "extraction_error": "Erro durante extração: {error}",
        "recreation_error": "Erro durante reconstrução: {error}",
        "file_not_found": "Arquivo não encontrado: {file}",
        "filelist_not_found": "Arquivo de lista de arquivos não encontrado.",
        "processing_file": "Processado: {file}, Posição: {position}",
        "adding_compressed": "Adicionando {file} comprimido.",
        "extracting_to": "Extraindo para: {path}",
        "recreating_to": "Recriando arquivo: {path}"
    },
    "en_US": {
        "plugin_name": "CAT/MATCAT FEAR 1 PS3/XBOX 360 File",
        "plugin_description": "Extracts and recreates FEAR 1 containers (.CAT/.MATCAT)",
        "extract_file": "Extract File",
        "rebuild_file": "Rebuild File",
        "select_fear_file": "Select .CAT or .MATCAT file",
        "fear_files": "FEAR Files (.cat, .matcat)",
        "all_files": "All files",
        "success": "Success",
        "extraction_success": "Files extracted successfully!",
        "recreation_success": "File recreated successfully!",
        "error": "Error",
        "extraction_error": "Error during extraction: {error}",
        "recreation_error": "Error during recreation: {error}",
        "file_not_found": "File not found: {file}",
        "filelist_not_found": "File list not found.",
        "processing_file": "Processed: {file}, Position: {position}",
        "adding_compressed": "Adding compressed: {file}",
        "extracting_to": "Extracting to: {path}",
        "recreating_to": "Recreating file: {path}"
    },
    "es_ES": {
        "plugin_name": "CAT/MATCAT Archivo FEAR 1 PS3/XBOX 360",
        "plugin_description": "Extrae y recrea contenedores (.CAT/.MATCAT) FEAR 1",
        "extract_file": "Extraer Archivo",
        "rebuild_file": "Reconstruir Archivo",
        "select_fear_file": "Seleccionar archivo .CAT o .MATCAT",
        "fear_files": "Archivos FEAR (.cat, .matcat)",
        "all_files": "Todos los archivos",
        "success": "Éxito",
        "extraction_success": "¡Archivos extraídos con éxito!",
        "recreation_success": "¡Archivo recreado con éxito!",
        "error": "Error",
        "extraction_error": "Error durante extracción: {error}",
        "recreation_error": "Error durante reconstrucción: {error}",
        "file_not_found": "Archivo no encontrado: {file}",
        "filelist_not_found": "Archivo de lista no encontrado.",
        "processing_file": "Procesado: {file}, Posición: {position}",
        "adding_compressed": "Añadiendo comprimido: {file}",
        "extracting_to": "Extrayendo a: {path}",
        "recreating_to": "Recreando archivo: {path}"
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
            "commands": [
                {"label": translate("extract_file"), "action": choose_file},
                {"label": translate("rebuild_file"), "action": choose_file_to_recreate},
            ]
        }
    
    return get_plugin_info

# ===================== FUNÇÕES AUXILIARES =====================
def pad_to_32_bytes(data):
    """Adiciona padding para alinhar dados em 32 bytes"""
    padding_length = (32 - (len(data) % 32)) % 32
    return data + b'\x00' * padding_length

# ===================== FUNÇÕES PRINCIPAIS =====================
def read_file_info(file_path):
    """Extrai arquivos de um contêiner .CAT/.MATCAT"""
    try:
        base_path = Path(file_path)
        extract_folder = base_path.with_suffix('')
        
        with open(file_path, 'rb') as f:
            # Leitura do cabeçalho
            f.seek(4)
            start_pointers = struct.unpack('>I', f.read(4))[0]
            f.seek(8)
            num_pointers = struct.unpack('>I', f.read(4))[0]
            f.seek(12)
            start_block_names = struct.unpack('>I', f.read(4))[0]
            f.seek(16)
            size_block_names = struct.unpack('>I', f.read(4))[0]

            # Leitura dos nomes dos arquivos
            f.seek(start_block_names)
            names_block = f.read(size_block_names)
            names_block = names_block.replace(b'MSF\x01', b'wav')  # Correção de extensão
            file_names = names_block.split(b'\x00')
            
            # Preparar arquivo de lista
            file_list_name = base_path.with_name(f"{base_path.stem}_filelist.txt")
            extract_folder.mkdir(parents=True, exist_ok=True)
            
            # Processar cada arquivo
            with open(file_list_name, 'w', encoding='utf-8') as file_list:
                for i in range(num_pointers):
                    f.seek(start_pointers + i * 16)
                    f.read(4)  # Ignorar identificador
                    pointer = struct.unpack('>I', f.read(4))[0]
                    uncompressed_size = struct.unpack('>I', f.read(4))[0]
                    compressed_size = struct.unpack('>I', f.read(4))[0]

                    # Ler e processar dados
                    f.seek(pointer)
                    compressed_data = f.read(compressed_size)
                    
                    file_name = file_names[i].decode('utf-8')
                    output_path = extract_folder / file_name
                    
                    # Tentar descomprimir ou usar dados brutos
                    try:
                        decompressed_data = zlib.decompress(compressed_data)
                        data_to_write = decompressed_data
                        file_list.write(f"{file_name}\n")
                    except zlib.error:
                        data_to_write = compressed_data
                        file_list.write(f"{file_name},uncompressed\n")
                    
                    # Escrever arquivo
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_bytes(data_to_write)
                    
                    logger(translate(
                        "processing_file", 
                        file=file_name, 
                        position=hex(pointer).upper()
                    ))
        
        logger(translate("extracting_to", path=extract_folder))
        return True
    except Exception as e:
        logger(translate("extraction_error", error=str(e)))
        return False

def recreate_file(file_path):
    """Reconstrói um contêiner .CAT/.MATCAT"""
    try:
        base_path = Path(file_path)
        folder_name = base_path.with_suffix('')
        new_file_path = base_path.with_name(f"{base_path.stem}_mod{base_path.suffix}")
        file_list_path = base_path.with_name(f"{base_path.stem}_filelist.txt")

        # Verificar existência da lista de arquivos
        if not file_list_path.exists():
            raise FileNotFoundError(translate("filelist_not_found"))

        # Ler cabeçalho original
        with open(file_path, 'rb') as original_file:
            original_file.seek(20)
            data_start_offset = struct.unpack('>I', original_file.read(4))[0]
            original_file.seek(0)
            header = original_file.read(data_start_offset)

        file_infos = []
        logger(translate("recreating_to", path=new_file_path))

        # Construir novo arquivo
        with open(new_file_path, 'wb') as new_file:
            new_file.write(header)
            current_pointer = data_start_offset

            with open(file_list_path, 'r', encoding='utf-8') as file_list:
                for line in file_list:
                    line = line.strip()
                    uncompressed = ',uncompressed' in line
                    file_name = line.replace(',uncompressed', '')
                    file_path = folder_name / file_name
                    
                    # Verificar existência do arquivo
                    if not file_path.exists():
                        raise FileNotFoundError(translate(
                            "file_not_found", 
                            file=file_path
                        ))
                    
                    # Ler e processar dados
                    data = file_path.read_bytes()
                    if not uncompressed:
                        logger(translate("adding_compressed", file=file_name))
                        data = zlib.compress(data)
                    
                    # Adicionar padding e escrever
                    compressed_size = len(data)
                    compressed_data = pad_to_32_bytes(data)
                    file_infos.append((current_pointer, len(data), compressed_size))
                    new_file.write(compressed_data)
                    current_pointer += len(compressed_data)

        # Atualizar tabela de ponteiros
        with open(new_file_path, 'r+b') as new_file:
            new_file.seek(32)  # Início da tabela de ponteiros
            for file_info in file_infos:
                new_file.read(4)  # Ignorar identificador
                new_file.write(struct.pack('>I', file_info[0]))  # Offset
                new_file.write(struct.pack('>I', file_info[1]))  # Tamanho descomprimido
                new_file.write(struct.pack('>I', file_info[2]))  # Tamanho comprimido
        
        return True
    except Exception as e:
        logger(translate("recreation_error", error=str(e)))
        return False

# ===================== HANDLERS DE COMANDOS =====================
def choose_file():
    """Seleciona arquivo para extração"""
    file_path = filedialog.askopenfilename(
        title=translate("select_fear_file"),
        filetypes=[
            (translate("fear_files"), "*.cat *.matcat"),
            (translate("all_files"), "*.*")
        ]
    )
    if not file_path:
        return
    
    def run_extraction():
        try:
            if read_file_info(file_path):
                messagebox.showinfo(
                    translate("success"),
                    translate("extraction_success")
                )
        except Exception as e:
            messagebox.showerror(
                translate("error"),
                translate("extraction_error", error=str(e))
            )
    
    threading.Thread(target=run_extraction, daemon=True).start()

def choose_file_to_recreate():
    """Seleciona arquivo para reconstrução"""
    file_path = filedialog.askopenfilename(
        title=translate("select_fear_file"),
        filetypes=[
            (translate("fear_files"), "*.cat *.matcat"),
            (translate("all_files"), "*.*")
        ]
    )
    if not file_path:
        return
    
    def run_recreation():
        try:
            if recreate_file(file_path):
                messagebox.showinfo(
                    translate("success"),
                    translate("recreation_success")
                )
        except Exception as e:
            messagebox.showerror(
                translate("error"),
                translate("recreation_error", error=str(e))
            )
    
    threading.Thread(target=run_recreation, daemon=True).start()