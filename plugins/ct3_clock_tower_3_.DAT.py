import os
import threading
from tkinter import filedialog, messagebox

# Translation dictionaries for the plugin
plugin_translations = {
    "pt_BR": {
        "plugin_name": "CT3PACK - Clock Tower 3 (PS2)",
        "plugin_description": "Extrai e recria arquivos ct3pack.dat do jogo Clock Tower 3 (PS2)",
        "extract_file": "Extrair Arquivo",
        "rebuild_file": "Recriar Arquivo",
        "select_ct3_file": "Selecione o arquivo *.dat",
        "select_txt_file": "Selecione o arquivo *_filelist.txt",
        "ct3_files": "Arquivos CT3",
        "text_files": "Arquivos de Texto",
        "all_files": "Todos os arquivos",
        "extraction_completed": "Extração concluída com sucesso!\nArquivos salvos em: {path}",
        "recreation_completed": "Arquivo reconstruído com sucesso!\nSalvo em: {path}",
        "file_not_found": "Arquivo não encontrado: {file}",
        "folder_not_found": "Pasta não encontrada: {folder}",
        "empty_file_list": "A lista de arquivos está vazia",
        "name_decode_error": "Erro ao decodificar nome: {error}\nBytes lidos: {bytes}",
        "unexpected_error": "Ocorreu um erro inesperado: {error}",
        "success": "Sucesso"
    },
    "en_US": {
        "plugin_name": "CT3PACK - Clock Tower 3 (PS2)",
        "plugin_description": "Extracts and rebuilds ct3pack.dat files from Clock Tower 3 (PS2)",
        "extract_file": "Extract File",
        "rebuild_file": "Rebuild File",
        "select_ct3_file": "Select *.dat file",
        "select_txt_file": "Select *_filelist.txt file",
        "ct3_files": "CT3 Files",
        "text_files": "Text Files",
        "all_files": "All files",
        "extraction_completed": "Extraction completed successfully!\nFiles saved to: {path}",
        "recreation_completed": "File rebuilt successfully!\nSaved to: {path}",
        "file_not_found": "File not found: {file}",
        "folder_not_found": "Folder not found: {folder}",
        "empty_file_list": "File list is empty",
        "name_decode_error": "Error decoding name: {error}\nBytes read: {bytes}",
        "unexpected_error": "An unexpected error occurred: {error}",
        "success": "Success"
    },
    "es_ES": {
        "plugin_name": "CT3PACK - Clock Tower 3 (PS2)",
        "plugin_description": "Extrae y reconstruye archivos ct3pack.dat del juego Clock Tower 3 (PS2)",
        "extract_file": "Extraer Archivo",
        "rebuild_file": "Reconstruir Archivo",
        "select_ct3_file": "Seleccionar archivo *.dat",
        "select_txt_file": "Seleccionar archivo *_filelist.txt",
        "ct3_files": "Archivos CT3",
        "text_files": "Archivos de Texto",
        "all_files": "Todos los archivos",
        "extraction_completed": "¡Extracción completada con éxito!\nArchivos guardados en: {path}",
        "recreation_completed": "¡Archivo reconstruido con éxito!\nGuardado en: {path}",
        "file_not_found": "Archivo no encontrado: {file}",
        "folder_not_found": "Carpeta no encontrada: {folder}",
        "empty_file_list": "La lista de archivos está vacía",
        "name_decode_error": "Error al decodificar nombre: {error}\nBytes leídos: {bytes}",
        "unexpected_error": "Ocurrió un error inesperado: {error}",
        "success": "Éxito"
    }
}

# Plugin global variables
logger = print
current_language = "pt_BR"
get_option = lambda name: None

def translate(key, **kwargs):
    """Internal plugin translation function"""
    lang_dict = plugin_translations.get(current_language, plugin_translations["pt_BR"])
    translation = lang_dict.get(key, key)
    
    if kwargs:
        try:
            return translation.format(**kwargs)
        except:
            return translation
    return translation

def register_plugin(log_func, option_getter, host_language="pt_BR"):
    global logger, current_language, get_option
    logger = log_func or print
    current_language = host_language
    get_option = option_getter or (lambda name: None)
    
    def get_plugin_info():
        return {
            "name": translate("plugin_name"),
            "description": translate("plugin_description"),
            "commands": [
                {"label": translate("extract_file"), "action": extract_file},
                {"label": translate("rebuild_file"), "action": recreate_file}
            ]
        }
    
    return get_plugin_info

def extract_file():
    file_path = filedialog.askopenfilename(
        title=translate("select_ct3_file"),
        filetypes=[(translate("ct3_files"), "*.dat"), (translate("all_files"), "*.*")]
    )
    if not file_path:
        return

    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(translate("file_not_found", file=file_path))
        
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_dir = os.path.join(os.path.dirname(file_path), base_name)
        os.makedirs(output_dir, exist_ok=True)
        
        filelist_path = os.path.join(os.path.dirname(file_path), f"{base_name}_filelist.txt")
        
        with open(file_path, 'rb') as f:
            file_names = []
            pointers = []
            sizes = []
            extracted_files = []
            
            total_items = f.read(4)
            total_items_int = int.from_bytes(total_items, byteorder='little')
            
            f.seek(2048)

            for _ in range(total_items_int):
                name_bytes = f.read(16)
                try:
                    name = name_bytes.decode('utf-8').strip('\x00')
                    file_names.append(name)
                except UnicodeDecodeError as e:
                    logger(translate("name_decode_error", error=str(e), bytes=name_bytes))
                    file_names.append(f"unknown_{len(file_names)}")
                
                f.seek(4, 1)
                size = f.read(4)
                size_int = int.from_bytes(size, byteorder='little')
                sizes.append(size_int)
                
                offset = f.read(4)
                offset_int = int.from_bytes(offset, byteorder='little')
                pointers.append(offset_int * 2048)
                f.seek(4, 1)

            for i, (pointer, size, name) in enumerate(zip(pointers, sizes, file_names)):
                output_file_path = os.path.join(output_dir, name)
                
                f.seek(pointer)
                file_data = f.read(size)
                
                os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
                with open(output_file_path, 'wb') as output_file:
                    output_file.write(file_data)
                
                extracted_files.append(name)
                logger(f"Arquivo extraído: {output_file_path}")
            
            with open(filelist_path, 'w', encoding='utf-8') as filelist_file:
                filelist_file.write("\n".join(extracted_files))
                
        messagebox.showinfo(
            translate("success"),
            translate("extraction_completed", path=output_dir)
        )
    
    except Exception as e:
        messagebox.showerror(
            translate("error"),
            translate("unexpected_error", error=str(e))
        )

def recreate_file():
    filelist_path = filedialog.askopenfilename(
        title=translate("select_txt_file"),
        filetypes=[(translate("text_files"), "*.txt"), (translate("all_files"), "*.*")]
    )
    if not filelist_path:
        return

    try:
        base_name = os.path.splitext(os.path.basename(filelist_path))[0].replace("_filelist", "")
        output_dir = os.path.join(os.path.dirname(filelist_path), base_name)
        recreated_file = os.path.join(os.path.dirname(filelist_path), f"{base_name}_new.dat")
        original_file = os.path.join(os.path.dirname(filelist_path), f"{base_name}.dat")

        if not os.path.exists(output_dir):
            raise FileNotFoundError(translate("folder_not_found", folder=output_dir))

        with open(filelist_path, 'r', encoding='utf-8') as fl:
            file_names = fl.read().splitlines()
        
        if not file_names:
            raise ValueError(translate("empty_file_list"))

        file_pointers = []
        file_sizes = []
        tamanhos_com_pad = []

        with open(original_file, 'rb') as arquivo_original:
            arquivo_original.seek(4)
            header_size = arquivo_original.read(4)
            header_size_int = int.from_bytes(header_size, byteorder='little')
            arquivo_original.seek(0)
            header = arquivo_original.read(header_size_int)

        with open(recreated_file, 'w+b') as new_file:
            new_file.write(header)
            
            for file_name in file_names:
                file_path = os.path.join(output_dir, file_name)
                if not os.path.exists(file_path):
                    logger(translate("file_not_found", file=file_path))
                    continue

                pointer = new_file.tell()
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                    new_file.write(file_data)
                
                file_pointers.append(pointer)
                file_sizes.append(len(file_data))
                
                tamanho_atual = new_file.tell()
                padding = (2048 - (tamanho_atual % 2048)) % 2048
                new_file.write(b'\x00' * padding)
                tamanho_com_pad = len(file_data) + padding
                tamanhos_com_pad.append(tamanho_com_pad)
                
            new_file.seek(2048)

            for pointer, size, size_pad in zip(file_pointers, file_sizes, tamanhos_com_pad):
                new_file.seek(20, 1)
                new_file.write(size.to_bytes(4, byteorder='little'))
                new_file.write((pointer // 2048).to_bytes(4, byteorder='little'))
                new_file.write((size_pad // 2048).to_bytes(4, byteorder='little'))
                
        messagebox.showinfo(
            translate("success"),
            translate("recreation_completed", path=recreated_file)
        )

    except Exception as e:
        messagebox.showerror(
            translate("error"),
            translate("unexpected_error", error=str(e))
        )