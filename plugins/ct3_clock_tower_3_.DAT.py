import os
from tkinter import filedialog, messagebox

def register_plugin():
    return {
        "name": "CT3PACK Clock Tower 3(PS2)",
        "description": "Extrai e recria arquivo ct3pack.dat do jogo Clock Tower 3(PS2)",
        "commands": [
            {"label": "Extrair Arquivo", "action": extract_file},
            {"label": "Recriar Arquivo", "action": recreate_file}
        ]
    }

def extract_file():
    file_path = filedialog.askopenfilename(title="Selecione o arquivo *ct3", filetypes=[("CT3 Files", "*.dat")])
    if not file_path:
        return

    try:
        # Verifica se o arquivo existe
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"O arquivo {file_path} não foi encontrado.")
        
        # Cria uma pasta com o nome do arquivo original (sem extensão)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_dir = os.path.join(os.path.dirname(file_path), base_name)
        os.makedirs(output_dir, exist_ok=True)
        
        # Caminho do arquivo de lista
        filelist_path = os.path.join(os.path.dirname(file_path), f"{base_name}_filelist.txt")
        
        # Abre o arquivo em modo binário para leitura
        with open(file_path, 'rb') as f:
            
            file_names = []
            pointers = []
            sizes = []
            extracted_files = []  # Lista para manter os nomes de arquivos extraídos
            
            # Lê os primeiros 4 bytes (quantidade de itens)
            total_items = f.read(4)
            
            # Converte os valores para inteiros para processar posições e tamanhos
            total_items_int = int.from_bytes(total_items, byteorder='little')
            
            f.seek(2048)

            # Lê informações para cada item no total_items
            for _ in range(total_items_int):
                name_bytes = f.read(16)
                try:
                    name = name_bytes.decode('utf-8').strip('\x00')
                    file_names.append(name)
                except UnicodeDecodeError as e:
                    print(f"Erro ao decodificar nome: {e} - Bytes lidos: {name_bytes}")
                f.seek(4, 1)
                
                size = f.read(4)
                size_int = int.from_bytes(size, byteorder='little')
                sizes.append(size_int)
                
                offset = f.read(4)
                offset_int = int.from_bytes(offset, byteorder='little')
                pointers.append(offset_int * 2048)
                f.seek(4, 1)

            for i, (pointer, size, name) in enumerate(zip(pointers, sizes, file_names)):
                # Caminho do arquivo extraído
                output_file_path = os.path.join(output_dir, name)

                # Lê o conteúdo do arquivo original
                f.seek(pointer)
                file_data = f.read(size)
                
                # Salva o arquivo extraído
                with open(output_file_path, 'wb') as output_file:
                    output_file.write(file_data)
                
                # Adiciona o nome do arquivo extraído à lista
                extracted_files.append(name)
                
                print(f"Arquivo extraído: {output_file_path}")
            
            # Salva a lista de nomes no mesmo local do arquivo original
            with open(filelist_path, 'w', encoding='utf-8') as filelist_file:
                filelist_file.write("\n".join(extracted_files))
                
            messagebox.showinfo("Sucesso", (f"Lista de arquivos extraídos salvo em: {filelist_path}"))
    
    except Exception as e:
        print(f"Ocorreu um erro: {e}")


def recreate_file():
    import os
    from tkinter import filedialog
    
    # Função para recriar o arquivo original
    filelist_path = filedialog.askopenfilename(title="Selecione o arquivo *_filelist.txt", filetypes=[("TXT Files", "*.txt")])
    if not filelist_path:
        return

    try:
        # Determina a pasta de saída e o nome do arquivo original
        base_name = os.path.splitext(os.path.basename(filelist_path))[0].replace("_filelist", "")
        output_dir = os.path.join(os.path.dirname(filelist_path), base_name)
        recreated_file = os.path.join(os.path.dirname(filelist_path), f"{base_name}_new.dat")
        original_file = os.path.join(os.path.dirname(filelist_path), f"{base_name}.dat")

        # Lê arquivos na lista
        with open(filelist_path, 'r', encoding='utf-8') as fl:
            file_names = fl.read().splitlines()
        
        if not file_names:
            raise ValueError("A lista de arquivos está vazia.")

        # Lista para armazenar ponteiros e tamanhos
        file_pointers = []
        file_sizes = []
        tamanhos_com_pad = []

        # Cria o novo arquivo
        with open(original_file, 'rb') as arquivo_original:
            # Lê o header original
            arquivo_original.seek(4)
            header_size = arquivo_original.read(4)
            header_size_int = int.from_bytes(header_size, byteorder='little')
            arquivo_original.seek(0)
            header = arquivo_original.read(header_size_int)

        with open(recreated_file, 'w+b') as new_file:
            new_file.write(header)
            
            # Escreve os arquivos na ordem da lista
            for file_name in file_names:
                file_path = os.path.join(output_dir, file_name)
                if os.path.exists(file_path):
                    # Obtém o ponteiro antes de escrever o arquivo
                    pointer = new_file.tell()
                    with open(file_path, 'rb') as f:
                        file_data = f.read()
                        new_file.write(file_data)
                    # Salva o ponteiro e o tamanho
                    file_pointers.append(pointer)
                    file_sizes.append(len(file_data))
                    
                    # Adiciona padding
                    tamanho_atual = new_file.tell()
                    padding = (2048 - (tamanho_atual % 2048)) % 2048
                    new_file.write(b'\x00' * padding)
                    tamanho_com_pad = len(file_data) + padding
                    tamanhos_com_pad.append(tamanho_com_pad)
                    
            new_file.seek(2048)

            # Escreve os ponteiros e tamanhos no subheader
            for pointer, size, size_pad in zip(file_pointers, file_sizes, tamanhos_com_pad):
                new_file.seek(20, 1)
                new_file.write(size.to_bytes(4, byteorder='little'))  # Escreve o ponteiro
                new_file.write((pointer // 2048).to_bytes(4, byteorder='little'))      # Escreve o tamanho
                new_file.write((size_pad // 2048).to_bytes(4, byteorder='little'))
                
        messagebox.showinfo("Sucesso", (f"Arquivo reconstruído salvo em: {recreated_file}"))

    except Exception as e:
        print(f"Erro ao recriar arquivo: {e}")
