import struct
import os
import threading
from tkinter import filedialog, messagebox, scrolledtext

# Translation dictionaries for the plugin
plugin_translations = {
    "pt_BR": {
        "plugin_name": "RCF - Radcore Cement Library VER:1.2/2.1",
        "plugin_description": "Extrai e recria arquivos RCF de jogos da Radical Entertainment",
        "extract_file": "Extrair Arquivo",
        "rebuild_file": "Recriar Arquivo",
        "select_rcf_file": "Selecione o arquivo .rcf",
        "select_txt_file": "Selecione o arquivo .txt",
        "rcf_files": "Arquivos RCF",
        "text_files": "Arquivos de Texto",
        "all_files": "Todos os arquivos",
        "unsupported_file": "Arquivo não suportado!",
        "extraction_completed": "Arquivos extraídos com sucesso para:\n{path}",
        "recreation_completed": "Novo arquivo RCF criado em:\n{path}",
        "folder_not_found": "Pasta não encontrada: {folder}",
        "file_not_found": "Arquivo não encontrado: {file}",
        "error_creating_dir": "Erro ao criar diretório: {error}",
        "version_21_le": "Versão é 2.1\nMODO LITTLE ENDIAN",
        "version_21_be": "Versão é 2.1\nMODO BIG ENDIAN",
        "version_12_le": "Versão é 1.2\nMODO LITTLE ENDIAN",
        "progress_title": "Processando Arquivo RCF",
        "cancel_button": "Cancelar"
    },
    "en_US": {
        "plugin_name": "RCF - Radcore Cement Library VER:1.2/2.1",
        "plugin_description": "Extracts and recreates RCF files from Radical Entertainment games",
        "extract_file": "Extract File",
        "rebuild_file": "Rebuild File",
        "select_rcf_file": "Select .rcf file",
        "select_txt_file": "Select .txt file",
        "rcf_files": "RCF Files",
        "text_files": "Text Files",
        "all_files": "All files",
        "unsupported_file": "Unsupported file!",
        "extraction_completed": "Files successfully extracted to:\n{path}",
        "recreation_completed": "New RCF file created at:\n{path}",
        "folder_not_found": "Folder not found: {folder}",
        "file_not_found": "File not found: {file}",
        "error_creating_dir": "Error creating directory: {error}",
        "version_21_le": "Version is 2.1\nLITTLE ENDIAN MODE",
        "version_21_be": "Version is 2.1\nBIG ENDIAN MODE",
        "version_12_le": "Version is 1.2\nLITTLE ENDIAN MODE",
        "progress_title": "Processing RCF File",
        "cancel_button": "Cancel"
    },
    "es_ES": {
        "plugin_name": "RCF - Radcore Cement Library VER:1.2/2.1",
        "plugin_description": "Extrae y recrea archivos RCF de juegos de Radical Entertainment",
        "extract_file": "Extraer Archivo",
        "rebuild_file": "Recrear Archivo",
        "select_rcf_file": "Seleccionar archivo .rcf",
        "select_txt_file": "Seleccionar archivo .txt",
        "rcf_files": "Archivos RCF",
        "text_files": "Archivos de Texto",
        "all_files": "Todos los archivos",
        "unsupported_file": "¡Archivo no soportado!",
        "extraction_completed": "Archivos extraídos exitosamente a:\n{path}",
        "recreation_completed": "Nuevo archivo RCF creado en:\n{path}",
        "folder_not_found": "Carpeta no encontrada: {folder}",
        "file_not_found": "Archivo no encontrado: {file}",
        "error_creating_dir": "Error al crear directorio: {error}",
        "version_21_le": "Versión es 2.1\nMODO LITTLE ENDIAN",
        "version_21_be": "Versión es 2.1\nMODO BIG ENDIAN",
        "version_12_le": "Versión es 1.2\nMODO LITTLE ENDIAN",
        "progress_title": "Procesando Archivo RCF",
        "cancel_button": "Cancelar"
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
                {"label": translate("extract_file"), "action": select_file},
                {"label": translate("rebuild_file"), "action": start_rcf_recreation},
            ]
        }
    
    return get_plugin_info

class ProgressWindow:
    def __init__(self, parent, title, total):
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("400x120")
        self.window.resizable(False, False)
        self.window.grab_set()
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.window, 
            variable=self.progress_var, 
            maximum=total,
            length=380
        )
        self.progress_bar.pack(pady=15, padx=10, fill="x")
        
        self.status_label = Label(self.window, text="0%")
        self.status_label.pack(pady=5)
        
        self.cancel_button = Button(
            self.window, 
            text=translate("cancel_button"), 
            command=self.cancel,
            width=10
        )
        self.cancel_button.pack(pady=5)
        
        self.canceled = False
        self.window.protocol("WM_DELETE_WINDOW", self.cancel)
        
    def cancel(self):
        self.canceled = True
        self.cancel_button.config(state="disabled")
        
    def update(self, value, text):
        self.progress_var.set(value)
        self.status_label.config(text=text)
        
    def destroy(self):
        self.window.grab_release()
        self.window.destroy()

def calculate_padding(size, allocation=512):
    if size % allocation == 0:
        return size
    return ((size // allocation) + 1) * allocation

def select_file():
    file_path = filedialog.askopenfilename(
        title=translate("select_rcf_file"),
        filetypes=[(translate("rcf_files"), "*.rcf"), (translate("all_files"), "*.*")]
    )
    if file_path:
        threading.Thread(target=extract_files, args=(file_path,), daemon=True).start()

def start_rcf_recreation():
    rcf_path = filedialog.askopenfilename(
        title=translate("select_rcf_file"),
        filetypes=[(translate("rcf_files"), "*.rcf")]
    )
    if not rcf_path:
        return

    base_filename = os.path.splitext(os.path.basename(rcf_path))[0]
    txt_path = filedialog.askopenfilename(
        title=translate("select_txt_file"),
        filetypes=[(translate("text_files"), "*.txt")],
        initialfile=f"{base_filename}.txt"
    )
    if not txt_path:
        return

    threading.Thread(target=recreate_rcf, args=(rcf_path, txt_path), daemon=True).start()

def recreate_rcf(original_file_path, txt_names_path):
    base_filename = os.path.splitext(os.path.basename(original_file_path))[0]
    base_directory = os.path.dirname(original_file_path)
    new_rcf_path = os.path.join(base_directory, f"new_{base_filename}.rcf")
    extracted_files_directory = os.path.join(base_directory, base_filename)

    if not os.path.exists(extracted_files_directory):
        messagebox.showerror(
            translate("error"),
            translate("folder_not_found", folder=extracted_files_directory)
        )
        return

    if not os.path.exists(txt_names_path):
        messagebox.showerror(
            translate("error"),
            translate("file_not_found", file=txt_names_path)
        )
        return

    logger(translate("progress_title"))
    
    with open(original_file_path, 'rb') as original_file:
        original_file.seek(32)
        file_version = original_file.read(4)

        if file_version in [b'\x02\x01\x00\x01', b'\x02\x01\x01\x01']:
            endian_format = '<' if file_version == b'\x02\x01\x00\x01' else '>'
            logger(translate("version_21_le") if endian_format == '<' else translate("version_21_be"))

            original_file.seek(44)
            offset_value = struct.unpack(f'{endian_format}I', original_file.read(4))[0]
            original_file.seek(48)
            size_value = struct.unpack(f'{endian_format}I', original_file.read(4))[0]

            header_size = offset_value + size_value
            adjusted_header_size = calculate_padding(header_size)

            original_file.seek(0)
            header = original_file.read(adjusted_header_size)

        elif file_version == b'\x01\x02\x00\x01':
            logger(translate("version_12_le"))
            endian_format = '<'
            
            original_file.seek(2048)
            total_items = struct.unpack('<I', original_file.read(4))[0]
            names_offset = struct.unpack('<I', original_file.read(4))[0]
            
            original_file.seek(names_offset + 4)
            
            for _ in range(total_items):
                original_file.seek(4, os.SEEK_CUR)
                name_size = struct.unpack('<I', original_file.read(4))[0]
                original_file.read(name_size)
                
            header_size = original_file.tell()
            adjusted_header_size = calculate_padding(header_size)
            
            original_file.seek(0)
            header = original_file.read(adjusted_header_size)

        else:
            messagebox.showerror(translate("error"), translate("unsupported_file"))
            return

    with open(new_rcf_path, 'w+b') as new_rcf:
        new_rcf.write(header)
        pointers = []
        current_position = adjusted_header_size
    
        with open(txt_names_path, 'r', encoding='utf-8') as txt_names:
            for line in txt_names:
                file_name = line.lstrip("/\\").strip()
                file_path = os.path.join(extracted_files_directory, file_name)

                if not os.path.exists(file_path):
                    logger(translate("file_not_found", file=file_path))
                    continue

                with open(file_path, 'rb') as f_file:
                    file_data = f_file.read()

                original_size = len(file_data)
                size_with_padding = calculate_padding(original_size)

                new_rcf.write(file_data)
                new_rcf.write(b'\x00' * (size_with_padding - original_size))
    
                pointers.append((current_position, original_size))
                current_position += size_with_padding

        new_rcf.seek(32)
        file_version = new_rcf.read(4)
        
        if file_version in [b'\x02\x01\x00\x01', b'\x02\x01\x01\x01']:
            endian_format = '<' if file_version == b'\x02\x01\x00\x01' else '>'
            new_rcf.seek(60)
            for pointer, original_size in pointers:
                new_rcf.seek(4, os.SEEK_CUR)
                new_rcf.write(struct.pack(f'{endian_format}I', pointer))
                new_rcf.write(struct.pack(f'{endian_format}I', original_size))
        else:
            new_rcf.seek(2064)
            for pointer, original_size in pointers:
                new_rcf.seek(4, os.SEEK_CUR)
                new_rcf.write(struct.pack('<I', pointer))
                new_rcf.write(struct.pack('<I', original_size))
    
    messagebox.showinfo(
        translate("completed"),
        translate("recreation_completed", path=new_rcf_path)
    )

def extract_files(file_path):
    base_directory = os.path.dirname(file_path)
    base_filename = os.path.splitext(os.path.basename(file_path))[0]
    extraction_directory = os.path.join(base_directory, base_filename)

    if not os.path.exists(extraction_directory):
        try:
            os.makedirs(extraction_directory)
        except Exception as e:
            messagebox.showerror(
                translate("error"),
                translate("error_creating_dir", error=str(e))
            )
            return

    with open(file_path, 'rb') as file:
        file.seek(32)
        file_version = file.read(4)
        
        if file_version in [b'\x02\x01\x00\x01', b'\x02\x01\x01\x01']:
            endian_format = '<' if file_version == b'\x02\x01\x00\x01' else '>'
            logger(translate("version_21_le") if endian_format == '<' else translate("version_21_be"))

            file.seek(36)
            pointers_offset = struct.unpack(f'{endian_format}I', file.read(4))[0]
            file.seek(4, os.SEEK_CUR)
            names_offset = struct.unpack(f'{endian_format}I', file.read(4))[0]
            file.seek(4, os.SEEK_CUR)

            file.seek(56)
            total_items = struct.unpack(f'{endian_format}I', file.read(4))[0]

            pointers = []
            file.seek(pointers_offset)
            for _ in range(total_items):
                file.seek(4, os.SEEK_CUR)
                file_offset = struct.unpack(f'{endian_format}I', file.read(4))[0]
                file_size = struct.unpack(f'{endian_format}I', file.read(4))[0]
                pointers.append((file_offset, file_size))

            names = []
            file.seek(names_offset + 8)
            for _ in range(total_items):
                file.seek(12, os.SEEK_CUR)
                name_size = struct.unpack('<I', file.read(4))[0]
                name_bytes = file.read(name_size)
                try:
                    name = name_bytes.decode('utf-8').strip('\x00')
                    names.append(name)
                except UnicodeDecodeError:
                    names.append(f"unknown_{len(names)}")

            for i, (file_offset, file_size) in enumerate(pointers):
                if i >= len(names):
                    break
                    
                file.seek(file_offset)
                data = file.read(file_size)
                file_name = names[i].strip()
                complete_path = os.path.join(extraction_directory, file_name.lstrip("/\\"))
                
                os.makedirs(os.path.dirname(complete_path), exist_ok=True)
                with open(complete_path, 'wb') as f:
                    f.write(data)
                
                logger(f"File {complete_path} extracted successfully.")

            names_list_path = os.path.join(base_directory, f"{base_filename}.txt")
            with open(names_list_path, 'w', encoding='utf-8') as names_list:
                for name in names:
                    names_list.write(name + '\n')

        elif file_version == b'\x01\x02\x00\x01':
            logger(translate("version_12_le"))
            
            file.seek(2048)
            total_items = struct.unpack('<I', file.read(4))[0]
            names_offset = struct.unpack('<I', file.read(4))[0]
            file.seek(8, os.SEEK_CUR)
            
            pointers = []
            for _ in range(total_items):
                file.seek(4, os.SEEK_CUR)
                file_offset = struct.unpack('<I', file.read(4))[0]
                file_size = struct.unpack('<I', file.read(4))[0]
                pointers.append((file_offset, file_size))
                
            names = []
            file.seek(names_offset +4)
            for _ in range(total_items):
                file.seek(4, os.SEEK_CUR)
                name_size = struct.unpack('<I', file.read(4))[0]
                name_bytes = file.read(name_size)
                try:
                    name = name_bytes.decode('utf-8').strip('\x00')
                    names.append(name)
                except UnicodeDecodeError:
                    names.append(f"unknown_{len(names)}")

            for i, (file_offset, file_size) in enumerate(pointers):
                if i >= len(names):
                    break
                    
                file.seek(file_offset)
                data = file.read(file_size)
                file_name = names[i].strip()
                complete_path = os.path.join(extraction_directory, file_name.lstrip("/\\"))
                
                os.makedirs(os.path.dirname(complete_path), exist_ok=True)
                with open(complete_path, 'wb') as f:
                    f.write(data)
                
                logger(f"File {complete_path} extracted successfully.")

            names_list_path = os.path.join(base_directory, f"{base_filename}.txt")
            with open(names_list_path, 'w', encoding='utf-8') as names_list:
                for name in names:
                    names_list.write(name + '\n')

        else:
            messagebox.showerror(translate("error"), translate("unsupported_file"))
            return

    messagebox.showinfo(
        translate("completed"),
        translate("extraction_completed", path=extraction_directory)
    )