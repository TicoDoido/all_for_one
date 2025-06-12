import struct
import os
import zlib
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Label, Button

logger = print
get_option = lambda name: None

def register_plugin(log_func, option_getter):
    global logger, get_option
    logger = log_func or print
    get_option = option_getter or (lambda name: None)
            
    return {
        "name": "PACKED arquivos do jogo Clive Barker's Jericho...",
        "description": "Extrai e reinsere arquivos de containers .packed com threads e progresso",
        "commands": [
            {"label": "Extrair Container", "action": start_extraction},
            {"label": "Reinserir Arquivos", "action": start_reinsertion},
        ]
    }

class ProgressWindow:
    def __init__(self, parent, title, total):
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("400x120")
        self.window.resizable(False, False)
        self.window.grab_set()
        
        self.progress_var = tk.DoubleVar()  # Corrigido: tk.DoubleVar em vez de ttk.DoubleVar
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
            text="Cancelar", 
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
            raise ValueError("Arquivo não é um container .packed válido.")
        
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
                progress_window.update(i + 1, f"{percent}% - {i+1}/{num_files} arquivos")
                if progress_window.canceled:
                    return None

    return output_dir

def start_extraction():
    container_path = filedialog.askopenfilename(
        title="Selecione o arquivo .packed", 
        filetypes=[("Packed Files", "*.packed")]
    )
    if not container_path:
        return
    
    try:
        with open(container_path, 'rb') as f:
            if f.read(4) != b'BFPK':
                raise ValueError("Arquivo inválido")
            f.seek(8)
            num_files = struct.unpack('<I', f.read(4))[0]
    except Exception as e:
        messagebox.showerror("Erro", str(e))
        return

    progress_window = ProgressWindow(None, "Extraindo Container", num_files)
    
    def extraction_thread():
        try:
            output_dir = extract_packed_container(container_path, progress_window)
            if output_dir is None:
                messagebox.showinfo("Cancelado", "Extração cancelada pelo usuário")
            else:
                messagebox.showinfo("Concluído", f"Extração concluída!\n{output_dir}")
        except Exception as e:
            messagebox.showerror("Erro", str(e))
        finally:
            progress_window.destroy()
    
    threading.Thread(target=extraction_thread, daemon=True).start()

def get_file_list(container_path):
    with open(container_path, 'rb') as f:
        if f.read(4) != b'BFPK':
            raise ValueError("Arquivo inválido")
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
                raise FileNotFoundError(f"Arquivo não encontrado: {input_file}")
            
            with open(input_file, 'rb') as fin:
                original_data = fin.read()
                compressed_data = zlib.compress(original_data)
                pointer = out.tell()
                out.write(struct.pack('<I', len(compressed_data)))
                out.write(compressed_data)
                novos_dados.append((pointer, len(original_data)))
                
            if progress_window:
                percent = int((i + 1) / total_files * 100)
                progress_window.update(i + 1, f"{percent}% - {i+1}/{total_files} arquivos")
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
        title="Selecione o arquivo .packed",
        filetypes=[("Packed Files", "*.packed")]
    )
    if not container_path:
        return

    input_dir = os.path.splitext(container_path)[0]
    if not os.path.exists(input_dir):
        messagebox.showerror("Erro", f"Diretório não encontrado: {input_dir}")
        return

    try:
        file_list, _ = get_file_list(container_path)
        total_files = len(file_list)
        progress_window = ProgressWindow(None, "Reinserindo Arquivos", total_files)
    except Exception as e:
        messagebox.showerror("Erro", str(e))
        return

    def reinsertion_thread():
        try:
            success = reinsert_files(container_path, input_dir, progress_window)
            if progress_window.canceled:
                messagebox.showinfo("Cancelado", "Reinserção cancelada pelo usuário")
            elif success:
                messagebox.showinfo("Concluído", "Reinserção concluída com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", str(e))
        finally:
            progress_window.destroy()
    
    threading.Thread(target=reinsertion_thread, daemon=True).start()