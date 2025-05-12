import os
import struct
from tkinter import filedialog, messagebox

# no topo do seu plugin.py
logger = print
get_option = lambda name: None  # stub até receber do host

def register_plugin(log_func, option_getter):
    global logger, get_option
    # atribui o logger e a função de consulta de opções vindos do host
    logger     = log_func or print
    get_option = option_getter or (lambda name: None)
            
    return {
        "name": "FILES arquivos (Eternal Sonata PS3)",
        "description": "Extrai e recria textos de arquivos do jogo Eternal Sonata",
        "commands": [
            {"label": "Extrair Arquivo", "action": select_container},
        ]
    }

def extract_files_from_container(container_path):
    # Obtém o nome base do arquivo (sem extensão)
    container_name = os.path.splitext(os.path.basename(container_path))[0]
    # Define o diretório de saída como o mesmo local do arquivo
    file_dir = os.path.dirname(container_path)
    # Cria uma pasta com o nome do arquivo no mesmo diretório
    container_output_dir = os.path.join(file_dir, container_name)
    os.makedirs(container_output_dir, exist_ok=True)
    
    try:
        with open(container_path, 'rb') as container:
            container.seek(8)
            num_files = struct.unpack('>I', container.read(4))[0]
            
            header_offset = 16
            
            for _ in range(num_files):
                container.seek(header_offset)
                
                filename = container.read(32).decode('utf-8').strip('\x00')
                file_start = struct.unpack('>I', container.read(4))[0]
                file_size = struct.unpack('>I', container.read(4))[0]
                
                header_offset += 48
                
                container.seek(file_start)
                file_data = container.read(file_size)
                
                full_output_path = os.path.join(container_output_dir, filename)
                os.makedirs(os.path.dirname(full_output_path), exist_ok=True)
                
                with open(full_output_path, 'wb') as output_file:
                    output_file.write(file_data)
                
                logger(f'Extraiu {filename} para {full_output_path}')
        
        messagebox.showinfo("Sucesso", "Arquivos extraídos com sucesso!")
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro: {e}")

def select_container():
    file_path = filedialog.askopenfilename(
        title="Selecione o arquivo", 
        filetypes=[("Arquivos .files", "*.files"), ("Todos os Arquivos", "*.*")]
    )
    if file_path:
        extract_files_from_container(file_path)
