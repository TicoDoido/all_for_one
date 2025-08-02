import struct
import os
import zlib
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Label, Button
from collections import defaultdict

# Dicionários de tradução do plugin
plugin_translations = {
    "pt_BR": {
        "plugin_name": "PACKED - Clive Barker's Jericho",
        "plugin_description": "Extrai e reinsere arquivos de containers .packed",
        "extract_container": "Extrair Container",
        "reinsert_files": "Reinserir Arquivos",
        "select_packed_file": "Selecione o arquivo .packed",
        "packed_files": "Arquivos Packed",
        "all_files": "Todos os arquivos",
        "invalid_file": "Arquivo inválido",
        "invalid_packed_file": "Arquivo não é um container .packed válido.",
        "extraction_completed": "Extração concluída!\n{path}",
        "reinsertion_completed": "Reinserção concluída com sucesso!",
        "cancelled": "Cancelado",
        "extraction_cancelled": "Extração cancelada pelo usuário",
        "reinsertion_cancelled": "Reinserção cancelada pelo usuário",
        "file_not_found": "Arquivo não encontrado: {file}",
        "dir_not_found": "Diretório não encontrado: {dir}",
        "progress_title_extract": "Extraindo Container",
        "progress_title_reinsert": "Reinserindo Arquivos",
        "progress_status": "{percent}% - {current}/{total} arquivos",
        "cancel_button": "Cancelar"
    },
    "en_US": {
        "plugin_name": "PACKED - Clive Barker's Jericho",
        "plugin_description": "Extracts and reinserts files from .packed containers",
        "extract_container": "Extract Container",
        "reinsert_files": "Reinsert Files",
        "select_packed_file": "Select .packed file",
        "packed_files": "Packed Files",
        "all_files": "All files",
        "invalid_file": "Invalid file",
        "invalid_packed_file": "File is not a valid .packed container.",
        "extraction_completed": "Extraction completed!\n{path}",
        "reinsertion_completed": "Reinsertion completed successfully!",
        "cancelled": "Cancelled",
        "extraction_cancelled": "Extraction cancelled by user",
        "reinsertion_cancelled": "Reinsertion cancelled by user",
        "file_not_found": "File not found: {file}",
        "dir_not_found": "Directory not found: {dir}",
        "progress_title_extract": "Extracting Container",
        "progress_title_reinsert": "Reinserting Files",
        "progress_status": "{percent}% - {current}/{total} files",
        "cancel_button": "Cancel"
    },
    "es_ES": {
        "plugin_name": "PACKED - Clive Barker's Jericho",
        "plugin_description": "Extrae y reinserta archivos de contenedores .packed",
        "extract_container": "Extraer Contenedor",
        "reinsert_files": "Reinsertar Archivos",
        "select_packed_file": "Seleccionar archivo .packed",
        "packed_files": "Archivos Packed",
        "all_files": "Todos los archivos",
        "invalid_file": "Archivo inválido",
        "invalid_packed_file": "El archivo no es un contenedor .packed válido.",
        "extraction_completed": "¡Extracción completada!\n{path}",
        "reinsertion_completed": "¡Reinserción completada con éxito!",
        "cancelled": "Cancelado",
        "extraction_cancelled": "Extracción cancelada por el usuario",
        "reinsertion_cancelled": "Reinserción cancelada por el usuario",
        "file_not_found": "Archivo no encontrado: {file}",
        "dir_not_found": "Directorio no encontrado: {dir}",
        "progress_title_extract": "Extrayendo Contenedor",
        "progress_title_reinsert": "Reinsertando Archivos",
        "progress_status": "{percent}% - {current}/{total} archivos",
        "cancel_button": "Cancelar"
    }
}

# Variáveis globais do plugin
logger = print
current_language = "pt_BR"
get_option = lambda name: None

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
                {"label": translate("extract_container"), "action": start_extraction},
                {"label": translate("reinsert_files"), "action": start_reinsertion},
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

def extract_packed_container(container_path, progress_window=None):
    base_name = os.path.splitext(os.path.basename(container_path))[0]
    output_dir = os.path.join(os.path.dirname(container_path), base_name)
    os.makedirs(output_dir, exist_ok=True)

    with open(container_path, 'rb') as f:
        if f.read(4) != b'BFPK':
            raise ValueError(translate("invalid_packed_file"))
        
        version = struct.unpack('<I', f.read(4))[0]
        num_files = struct.unpack('<I', f.read(4))[0]
        
        for i in range(num_files):
            name_size = struct.unpack('<I', f.read(4))[0]
            name = f.read(name_size).decode('utf-8').replace('/', os.sep)
            decompressed_size = struct.unpack('<I', f.read(4))[0]
            file_offset = struct.unpack('<I', f.read(4))[0]
            
            current_pos = f.tell()
            f.seek(file_offset)
            compressed_size = struct.unpack('<I', f.read(4))[0]
            compressed_data = f.read(compressed_size)
            f.seek(current_pos)
            
            output_path = os.path.join(output_dir, name)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            try:
                decompressed_data = zlib.decompress(compressed_data)
            except zlib.error:
                f.seek(file_offset)
                decompressed_data = f.read(compressed_size + 4)
            
            with open(output_path, 'wb') as out_file:
                out_file.write(decompressed_data)
                
            if progress_window:
                percent = int((i + 1) / num_files * 100)
                progress_window.update(
                    i + 1,
                    translate("progress_status",
                        percent=percent,
                        current=i+1,
                        total=num_files
                    )
                )
                if progress_window.canceled:
                    return None

    return output_dir

def start_extraction():
    container_path = filedialog.askopenfilename(
        title=translate("select_packed_file"),
        filetypes=[(translate("packed_files"), "*.packed"), (translate("all_files"), "*.*")]
    )
    if not container_path:
        return
    
    try:
        with open(container_path, 'rb') as f:
            if f.read(4) != b'BFPK':
                raise ValueError(translate("invalid_packed_file"))
            f.seek(8)
            num_files = struct.unpack('<I', f.read(4))[0]
    except Exception as e:
        messagebox.showerror(translate("invalid_file"), str(e))
        return

    progress_window = ProgressWindow(None, translate("progress_title_extract"), num_files)
    
    def extraction_thread():
        try:
            output_dir = extract_packed_container(container_path, progress_window)
            if output_dir is None:
                messagebox.showinfo(translate("cancelled"), translate("extraction_cancelled"))
            else:
                messagebox.showinfo(translate("completed"), translate("extraction_completed", path=output_dir))
        except Exception as e:
            messagebox.showerror(translate("invalid_file"), str(e))
        finally:
            progress_window.destroy()
    
    threading.Thread(target=extraction_thread, daemon=True).start()

def get_file_list(container_path):
    with open(container_path, 'rb') as f:
        if f.read(4) != b'BFPK':
            raise ValueError(translate("invalid_packed_file"))
        f.seek(8)
        num_files = struct.unpack('<I', f.read(4))[0]
        
        file_list = []
        for _ in range(num_files):
            name_size = struct.unpack('<I', f.read(4))[0]
            name = f.read(name_size).decode('utf-8').replace('/', os.sep)
            f.seek(8, 1)
            file_list.append(name)
        
        header_end = f.tell()
    
    return file_list, header_end

def reinsert_files(container_path, input_dir, progress_window=None):
    file_list, header_end = get_file_list(container_path)
    total_files = len(file_list)
    temp_path = container_path + ".new"
    
    with open(container_path, 'rb') as f, open(temp_path, 'w+b') as out:
        out.write(f.read(header_end))
        novos_dados = []
        
        for i, name in enumerate(file_list):
            input_file = os.path.join(input_dir, name)
            if not os.path.exists(input_file):
                raise FileNotFoundError(translate("file_not_found", file=input_file))
            
            with open(input_file, 'rb') as fin:
                original_data = fin.read()
                compressed_data = zlib.compress(original_data)
                pointer = out.tell()
                out.write(struct.pack('<I', len(compressed_data)))
                out.write(compressed_data)
                novos_dados.append((pointer, len(original_data)))
                
            if progress_window:
                percent = int((i + 1) / total_files * 100)
                progress_window.update(
                    i + 1,
                    translate("progress_status",
                        percent=percent,
                        current=i+1,
                        total=total_files
                    )
                )
                if progress_window.canceled:
                    os.remove(temp_path)
                    return False
                    
        out.seek(12)
        for (pointer, size) in novos_dados:
            name_size = struct.unpack('<I', out.read(4))[0]
            out.seek(name_size, 1)
            out.write(struct.pack('<I', size))
            out.write(struct.pack('<I', pointer))
            
    os.replace(temp_path, container_path)
    return True

def start_reinsertion():
    container_path = filedialog.askopenfilename(
        title=translate("select_packed_file"),
        filetypes=[(translate("packed_files"), "*.packed"), (translate("all_files"), "*.*")]
    )
    if not container_path:
        return

    input_dir = os.path.splitext(container_path)[0]
    if not os.path.exists(input_dir):
        messagebox.showerror(translate("invalid_file"), translate("dir_not_found", dir=input_dir))
        return

    try:
        file_list, _ = get_file_list(container_path)
        total_files = len(file_list)
        progress_window = ProgressWindow(None, translate("progress_title_reinsert"), total_files)
    except Exception as e:
        messagebox.showerror(translate("invalid_file"), str(e))
        return

    def reinsertion_thread():
        try:
            success = reinsert_files(container_path, input_dir, progress_window)
            if progress_window.canceled:
                messagebox.showinfo(translate("cancelled"), translate("reinsertion_cancelled"))
            elif success:
                messagebox.showinfo(translate("completed"), translate("reinsertion_completed"))
        except Exception as e:
            messagebox.showerror(translate("invalid_file"), str(e))
        finally:
            progress_window.destroy()
    
    threading.Thread(target=reinsertion_thread, daemon=True).start()