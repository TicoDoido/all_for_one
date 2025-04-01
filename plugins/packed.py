import struct
import os
import zlib
from tkinter import filedialog, messagebox

def register_plugin():
    return {
        "name": "PACKED arquivos do jogo Clive Barker's Jericho...",
        "description": "Extrai e reinsere arquivos de containers .packed do jogo Clive Barker's Jericho.\nOs arquivos de texto desse jogo são apenas txt simples e a codificação é ANSI. \nO magic do arquivo é BFPK... versão 1.0 e talvez funcione em algum outro jogo.",
        "commands": [
            {"label": "Extrair Container", "action": start_extraction},
            {"label": "Reinserir Arquivos", "action": start_reinsertion},
        ]
    }

def extract_packed_container(container_path):
    # Obter o nome base do arquivo sem extensão e seu diretório
    base_name = os.path.splitext(os.path.basename(container_path))[0]
    output_dir = os.path.join(os.path.dirname(container_path), base_name)
    
    # Criar a pasta de saída
    os.makedirs(output_dir, exist_ok=True)

    with open(container_path, 'rb') as f:
        # Verificar o Magic Number
        magic = f.read(4)
        if magic != b'BFPK':
            raise ValueError("Arquivo não é um container .packed válido.")
        
        # Ler a versão
        version = struct.unpack('<I', f.read(4))[0]
        
        # Ler o número total de arquivos
        num_files = struct.unpack('<I', f.read(4))[0]
        
        # Percorrer o cabeçalho
        for _ in range(num_files):
            # Ler o tamanho do nome
            name_size = struct.unpack('<I', f.read(4))[0]
            
            # Ler o nome do arquivo (e substituir '/' por separadores do sistema)
            name = f.read(name_size).decode('utf-8').replace('/', os.sep)
            
            # Ler o tamanho descomprimido do arquivo (conforme cabeçalho)
            decompressed_size = struct.unpack('<I', f.read(4))[0]
            
            # Ler a posição inicial do arquivo no container
            file_offset = struct.unpack('<I', f.read(4))[0]
            
            # Salvar a posição atual no arquivo (para voltar ao cabeçalho depois)
            current_pos = f.tell()
            
            print(f"Extraindo: {name}")
            
            # Ir para a posição do arquivo no container
            f.seek(file_offset)
            
            # Ler os primeiros 4 bytes que indicam o tamanho dos dados comprimidos
            compressed_size = struct.unpack('<I', f.read(4))[0]
            
            # Ler os dados comprimidos
            compressed_data = f.read(compressed_size)
            
            # Tentar descomprimir os dados lidos
            try:
                decompressed_data = zlib.decompress(compressed_data)
            except zlib.error:
                # Se ocorrer erro, manter os dados brutos (incluindo os 4 bytes iniciais do tamanho)
                f.seek(file_offset)
                decompressed_data = f.read(compressed_size + 4)
            
            # Criar o caminho de saída normalizado
            output_path = os.path.join(output_dir, name)
            output_path = os.path.normpath(output_path)

            # Criar o diretório de saída, se não existir
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Abrir o arquivo de saída para escrita
            with open(output_path, 'wb') as out_file:
                out_file.write(decompressed_data)
            
            # Voltar para a posição anterior no cabeçalho
            f.seek(current_pos)

    return output_dir


def start_extraction():
    container_path = filedialog.askopenfilename(
        title="Selecione o arquivo .packed", 
        filetypes=[("Packed Files", "*.packed"), ("Todos os Arquivos", "*.*")]
    )
    if not container_path:
        return
    
    try:
        output_dir = extract_packed_container(container_path)
        messagebox.showinfo("Concluído", f"Extração concluída com sucesso!\nArquivos salvos em:\n{output_dir}")
    except Exception as e:
        messagebox.showerror("Erro", str(e))
        
def get_file_list(container_path):
    with open(container_path, 'rb') as f:
        if f.read(4) != b'BFPK':
            raise ValueError("Arquivo não é um container .packed válido.")
        
        version = struct.unpack('<I', f.read(4))[0]
        num_files = struct.unpack('<I', f.read(4))[0]
        
        file_list = []
        for _ in range(num_files):
            name_size = struct.unpack('<I', f.read(4))[0]
            name = f.read(name_size).decode('utf-8').replace('/', os.sep)
            f.seek(4, 1)
            f.seek(4, 1)
            file_list.append(name)
        
        header_end = f.tell()
    
    return file_list, header_end

def reinsert_files(container_path, input_dir):
    file_list, header_end = get_file_list(container_path)
    
    temp_path = container_path + ".new"
    
    with open(container_path, 'rb') as f, open(temp_path, 'w+b') as out:
        out.write(f.read(header_end))  # Copiar cabeçalho original
        
        novos_dados = []
        
        for name in file_list:
            pointer = out.tell()
            input_file = os.path.join(input_dir, name)
            input_file = os.path.normpath(input_file)
            if not os.path.exists(input_file):
                raise FileNotFoundError(f"Arquivo não encontrado: {input_file}")
            
            print(f"Remontando arquivo: {input_file}")
            with open(input_file, 'rb') as fin:
                original_data = fin.read()
                this_file_size = len(original_data)
                compressed_data = zlib.compress(original_data)
                out.write(struct.pack('<I', len(compressed_data)))
                out.write(compressed_data)
                novos_dados.append((pointer, this_file_size))
                
        out.seek(12)
        
        for pointer, this_file_size in novos_dados:
            name_size = struct.unpack('<I', out.read(4))[0]
            out.read(name_size)
            out.write(struct.pack('<I', this_file_size))
            out.write(struct.pack('<I', pointer))
            
    os.replace(temp_path, container_path)

def start_reinsertion():
    container_path = filedialog.askopenfilename(
        title="Selecione o arquivo .packed",
        filetypes=[("Packed Files", "*.packed"), ("Todos os Arquivos", "*.*")]
    )
    if not container_path:
        return

    # Obtém o diretório de entrada removendo a extensão do container_path
    input_dir = os.path.splitext(container_path)[0]
    if not os.path.exists(input_dir):
        messagebox.showerror("Erro", f"Diretório não encontrado: {input_dir}")
        return

    try:
        reinsert_files(container_path, input_dir)
        messagebox.showinfo("Concluído", "Reinserção concluída com sucesso!")
    except Exception as e:
        messagebox.showerror("Erro", str(e))