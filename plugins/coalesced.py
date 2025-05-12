import struct
from tkinter import filedialog, messagebox
import os

# no topo do seu plugin.py
logger = print
get_option = lambda name: None  # stub até receber do host

def register_plugin(log_func, option_getter):
    global logger, get_option
    # atribui o logger e a função de consulta de opções vindos do host
    logger     = log_func or print
    get_option = option_getter or (lambda name: None)
            
    return {
        "name": "COALESCED Arquivo Unreal Engine 3 PS3/XBOX 360/N. Switch",
        "description": "Extrai e recria arquivos COALESCED de jogos feitos na Unreal Engine 3 PS360/Switch. Altere o numero de linhas nos arquivos .ini ou .int por sua conta e risco...Recomendo apenas a sua edição",
        "commands": [
            {"label": "Extrair Arquivo", "action": process_file},
            {"label": "Reconstruir Arquivo", "action": reprocess_file},
        ]
    }

def read_binary_file(file_path):
    try:
        def read_name(file, char_count):
            name_length = char_count * 2 + 2  # Multiplicar por 2 para UTF-16LE + 2 pelo endstring
            name_data = file.read(name_length)
            return name_data.decode('utf-16le').rstrip('\x00')

        output_dir = os.path.splitext(file_path)[0]
        os.makedirs(output_dir, exist_ok=True)

        with open(file_path, 'rb') as f:
            
            endiam_check = f.read(2)
            if endiam_check == b'\x00\x00':
                endianess = '>'
                ordem_dos_bytes = 'big'
            else:
                endianess = '<'
                ordem_dos_bytes = 'little'
            f.seek(-2, 1)
            
            
            # Ler os primeiros 4 bytes para o número total de arquivos
            total_files = struct.unpack(endianess + 'I', f.read(4))[0]

            for _ in range(total_files):
                # Ler o número de caracteres do nome do arquivo
                char_count_bytes = f.read(4)
                raw_value = int.from_bytes(char_count_bytes, byteorder=ordem_dos_bytes)
                char_count = 4294967295 - raw_value # 4294967295 = FF FF FF FF
                file_name = read_name(f, char_count)

                # Corrigir o caminho do arquivo, removendo componentes "..\..\" e padronizando
                file_name = os.path.normpath(file_name.replace("..\\", "").replace("..\\", ""))
                logger(f"Extraindo arquivo: {file_name}")

                # Criar caminho do arquivo para salvar
                file_path_out = os.path.join(output_dir, file_name)
                os.makedirs(os.path.dirname(file_path_out), exist_ok=True)  # Garantir diretório

                # Ler o número de itens no arquivo de texto
                num_items = struct.unpack(endianess + 'I', f.read(4))[0]

                items = []
                for _ in range(num_items):
                    # Ler o número de caracteres do nome do item
                    char_count_bytes_item = f.read(4)
                    raw_value_item = int.from_bytes(char_count_bytes_item, byteorder=ordem_dos_bytes)
                    char_count_item = 4294967295 - raw_value_item
                    item_name = read_name(f, char_count_item)

                    # Ler o número de subitens no item
                    num_subitems = struct.unpack(endianess + 'I', f.read(4))[0]  # Big endian

                    subitems = []
                    for _ in range(num_subitems):
                        # Ler o número de caracteres do nome do subitem 1
                        char_count_bytes_sub_item1 = f.read(4)
                        raw_value_sub_item1 = int.from_bytes(char_count_bytes_sub_item1, byteorder=ordem_dos_bytes)
                        if raw_value_sub_item1 == 0:
                            sub_item_1 = ""
                        else:
                            char_count_sub_item1 = 4294967295 - raw_value_sub_item1
                            sub_item_1 = read_name(f, char_count_sub_item1)

                        # Ler o número de caracteres do nome do subitem 2
                        char_count_bytes_sub_item2 = f.read(4)
                        raw_value_sub_item2 = int.from_bytes(char_count_bytes_sub_item2, byteorder=ordem_dos_bytes)
                        if raw_value_sub_item2 == 0:
                            sub_item_2 = ""
                        else:
                            char_count_sub_item2 = 4294967295 - raw_value_sub_item2
                            sub_item_2 = read_name(f, char_count_sub_item2)

                        subitems.append((sub_item_1, sub_item_2))

                    items.append((item_name, subitems))

                # Salvar conteúdo em arquivos
                with open(file_path_out, 'w', encoding='utf-8') as out_file:
                    total_items = len(items)
                   
                    for index, (item_name, subitems) in enumerate(items):
                        total_subitems = len(subitems)
                        if index > 0:
                            out_file.write(f"[{item_name}]\n")
                            for i, (sub_item_1, sub_item_2) in enumerate(subitems):
                            
                                sub_item_2 = sub_item_2.replace("\n", "\\n")
                                sub_item_2 = sub_item_2.replace("\r", "\\r")
                                total_items_subitems = len(subitems)
                                out_file.write(f"{sub_item_1}=")
                                if index < total_items -1:
                                    out_file.write(f"{sub_item_2}\n")
                                else:
                                    if i < total_items_subitems -1:
                                        out_file.write(f"{sub_item_2}\n")
                                    else:
                                        out_file.write(f"{sub_item_2}")
                        
                            # Apenas adicione a quebra de linha se não for o último item
                            if index < total_items -1:
                                out_file.write(f"\n")
                                    
                        else:
                            if total_subitems > 0:
                                out_file.write(f"[{item_name}]\n")
                                for i, (sub_item_1, sub_item_2) in enumerate(subitems):
                            
                                    sub_item_2 = sub_item_2.replace("\n", "\\n") # Trocar quebra de linha 
                                    sub_item_2 = sub_item_2.replace("\r", "\\r") # por algum simbolo ?
                                    total_items_subitems = len(subitems)
                                    out_file.write(f"{sub_item_1}=")
                                    if index < total_items -1:
                                        out_file.write(f"{sub_item_2}\n")
                                    else:
                                        if i < total_items_subitems -1:
                                            out_file.write(f"{sub_item_2}\n")
                                        else:
                                            out_file.write(f"{sub_item_2}")
                                # Apenas adicione a quebra de linha se não for o último item
                                if index < total_items -1:
                                    out_file.write(f"\n")


                            else:
                                if total_items > 1:
                                    out_file.write(f"[{item_name}]\n\n")
                                else:
                                    out_file.write(f"[{item_name}]")
                            
                                


        messagebox.showinfo("PRONTO !!!", f"Extração bem sucedida")

    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro ao processar o arquivo: {e}")
        return None
        
def rebuild_binary_file(original_file_path, output_file_path, extracted_folder):
    try:
        def read_name(file, char_count):
            name_length = char_count * 2 + 2  # Multiplicar por 2 para UTF-16LE + 2 pelo endstring
            name_data = file.read(name_length)
            return name_data.decode('utf-16le').rstrip('\x00')

        # Abrir o arquivo binário original para leitura dos nomes
        file_names = []
        with open(original_file_path, 'rb') as f:
            
            endiam_check = f.read(2)
            if endiam_check == b'\x00\x00':
                endianess = '>'
                ordem_dos_bytes = 'big'
            else:
                endianess = '<'
                ordem_dos_bytes = 'little'
            f.seek(-2, 1)
            # Isso é pura suposição de endiam... o numero total de arquivos tem 4 bytes 
            # Se for algo como 00 00 00 09 podemos imaginar ser big endiam se começar com 00 00
            # Dificilmente um arquivo COALESCED vai ter mais de 65.535 itens... ou seja, mais de 
            # 00 00 FF FF itens marcados no cabeçalho, e se for litle endiam vai marcar pelo menos 1 item
            # e seria 01 00 00 00, então se começar com 2 bytes nulos é big endiam...
            
            
            # Aqui vamos refazer o processo de ler os nomes dos arquivos para reimportar eles de volta
            # Evitando importar arquivos que não existem no arquivo original...
            # Ler o número total de arquivos
            total_files = struct.unpack(endianess + 'I', f.read(4))[0]

            for _ in range(total_files):
                # Ler o número de caracteres do nome do arquivo
                char_count_bytes = f.read(4)
                raw_value = int.from_bytes(char_count_bytes, byteorder=ordem_dos_bytes)
                char_count = 4294967295 - raw_value  # 4294967295 = FF FF FF FF
                file_name = read_name(f, char_count)
                file_names.append(file_name)

                # Pular a leitura dos dados dos itens (não necessário para esta etapa)
                num_items = struct.unpack(endianess + 'I', f.read(4))[0]
                for _ in range(num_items):
                    # Ler o número de caracteres do nome do item
                    char_count_bytes_item = f.read(4)
                    raw_value_item = int.from_bytes(char_count_bytes_item, byteorder=ordem_dos_bytes)
                    char_count_item = 4294967295 - raw_value_item
                    read_name(f, char_count_item)  # Nome do item

                    # Ler o número de subitens
                    num_subitems = struct.unpack(endianess + 'I', f.read(4))[0]
                    for _ in range(num_subitems):
                        # Ler os subitens
                        char_count_bytes_sub_item1 = f.read(4)
                        raw_value_sub_item1 = int.from_bytes(char_count_bytes_sub_item1, byteorder=ordem_dos_bytes)
                        if raw_value_sub_item1 != 0: # Se o valor for diferente de zero...
                            char_count_sub_item1 = 4294967295 - raw_value_sub_item1
                            read_name(f, char_count_sub_item1)  # Subitem 1, item antes do sinal de =

                        char_count_bytes_sub_item2 = f.read(4)
                        raw_value_sub_item2 = int.from_bytes(char_count_bytes_sub_item2, byteorder=ordem_dos_bytes)
                        if raw_value_sub_item2 != 0:
                            char_count_sub_item2 = 4294967295 - raw_value_sub_item2
                            read_name(f, char_count_sub_item2)  # Subitem 2, item depois do sinal de =


        # Abrir o arquivo binário para escrita
        with open(output_file_path, 'wb') as bin_file:
            # Escrever o número total de arquivos
            bin_file.write(struct.pack(endianess + 'I', len(file_names)))

            for file_name in file_names:
                file_path = os.path.join(extracted_folder, os.path.normpath(file_name.replace("..\\", "")))
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Arquivo extraído não encontrado: {file_path}")

                with open(file_path, 'r', encoding='utf-8') as f:
                    logger(f"Remontando arquivo: {file_path}")
                    # Ler e processar os itens do arquivo extraído
                    content = f.read()
                    
                    items = [item for item in content.split('\n\n') if item]

                    # Preparar e escrever o nome do arquivo
                    char_count = len(file_name)
                    char_count_encoded = 4294967295 - char_count
                    bin_file.write(struct.pack(endianess + 'I', char_count_encoded))
                    bin_file.write(file_name.encode('utf-16le') + b'\x00\x00')

                    # Escrever o número de itens
                    if content:
                        bin_file.write(struct.pack(endianess + 'I', len(items)))
                        for item in items:
                            # Processar cada item
                            lines = [line for line in item.split('\n') if line]
                            item_name = lines[0].strip('[]')
                            subitems = lines[1:]
    
                            # Preparar e escrever o nome do item
                            char_count_item = len(item_name)
                            char_count_item_encoded = 4294967295 - char_count_item
                            bin_file.write(struct.pack(endianess + 'I', char_count_item_encoded))
                            bin_file.write(item_name.encode('utf-16le') + b'\x00\x00')
    
                            # Escrever o número de subitens
                            bin_file.write(struct.pack(endianess + 'I', len(subitems)))
    
                            for subitem in subitems:
                                # Processar subitem
                                sub_item_1, sub_item_2 = subitem.split('=', 1)
                                sub_item_2 = sub_item_2.replace('\\n', '\n')  # Restaurar quebras de linha
                                sub_item_2 = sub_item_2.replace('\\r', '\r')
    
                                # Escrever o primeiro subitem
                                char_count_sub_item1 = len(sub_item_1)
                                if char_count_sub_item1 > 0:
                                    char_count_sub_item1_encoded = 4294967295 - char_count_sub_item1
                                    bin_file.write(struct.pack(endianess + 'I', char_count_sub_item1_encoded))  
                                    bin_file.write(sub_item_1.encode('utf-16le') + b'\x00\x00')
                                else:
                                    bin_file.write(struct.pack(endianess + 'I', 0))  # Subitem 1 vazio
    
                                # Escrever o segundo subitem
                                char_count_sub_item2 = len(sub_item_2)
                                if char_count_sub_item2 > 0:
                                    char_count_sub_item2_encoded = 4294967295 - char_count_sub_item2
                                    bin_file.write(struct.pack(endianess + 'I', char_count_sub_item2_encoded))
                                    bin_file.write(sub_item_2.encode('utf-16le') + b'\x00\x00')
                                else:
                                    bin_file.write(struct.pack(endianess + 'I', 0))  # Subitem 2 vazio
                    else:
                        bin_file.write(struct.pack(endianess + 'I', 0))



        messagebox.showinfo("PRONTO !!!", "Arquivo binário reconstruído com sucesso")

    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro ao reconstruir o arquivo binário: {e}")
        return None


def process_file():
    file_path = filedialog.askopenfilename()
    if file_path:
        result = read_binary_file(file_path)
        if result:
            messagebox.showinfo("Sucesso", "Processamento concluído com sucesso!")

def reprocess_file():
    original_file_path = filedialog.askopenfilename(title="Selecione o arquivo binário original")
    if not original_file_path:
        return
    
    extracted_folder = os.path.splitext(original_file_path)[0]
    if not extracted_folder:
        return
    
    base_filename = os.path.splitext(os.path.basename(original_file_path))[0]
    base_filename = os.path.normpath(base_filename)
    base_directory = os.path.dirname(original_file_path)
    base_directory = os.path.normpath(base_directory)
    output_file_path = os.path.join(base_directory, f"NOVO_{base_filename}.BIN")
    if not output_file_path:
        return

    rebuild_binary_file(original_file_path, output_file_path, extracted_folder)
