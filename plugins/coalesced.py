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
        "description": "Extrai e recria arquivos COALESCEDde jogos feitos na Unreal Engine 3 PS360/Switch.\nAltere o numero de linhas nos arquivos .ini ou .int por sua conta e risco...\nRecomendo apenas a sua edição, versão 1.0 usa ANSI e o restante UTF-8",
        "options": [
            {
                "name": "tipo_arquivo",
                "label": "Versão",
                "values": ["1.0", "2.0/3.0"]
            }
        ],
        "commands": [
            {"label": "Extrair Arquivo", "action": process_file},
            {"label": "Reconstruir Arquivo", "action": reprocess_file},
        ]
    }

def read_binary_file(file_path):
    
    tipo = get_option("tipo_arquivo")
    
    if tipo == "1.0":
        
            with open(file_path, 'rb') as f:
                output_base_dir = os.path.splitext(file_path)[0]
                f.seek(4)  # Posição inicial dos arquivos
                print(output_base_dir)
        
                while True:
                    # Ler tamanho do nome do arquivo
                    filename_length_data = f.read(4)
                    if not filename_length_data:
                        break  # Fim do arquivo
                    
                    filename_length = struct.unpack('>I', filename_length_data)[0]
                    filename_data = f.read(filename_length)
                    filename = filename_data.strip(b'\x00').decode('ansi')
                
                    # Criar estrutura de diretórios segura
                    safe_path = os.path.join(output_base_dir, filename.lstrip('..\\'))
                    full_path = os.path.abspath(safe_path)
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                    # Processar itens do arquivo
                    num_items = struct.unpack('>I', f.read(4))[0]
                    file_content = []
                
                    # Escrever arquivo extraído
                    with open(full_path, 'w', encoding='ansi') as out_file:
                
                        for _ in range(num_items):
                            # Item name
                            item_name_length = struct.unpack('>I', f.read(4))[0]
                            item_name = f.read(item_name_length).strip(b'\x00').decode('ansi')
                            out_file.write(f"[{item_name}]\n")
                    
                            # Subitens
                            num_subitems = struct.unpack('>I', f.read(4))[0]
                            subitems = []
                        
                            for i in range(num_subitems):
                                # Subitem title
                                subitem_title_length = struct.unpack('>I', f.read(4))[0]
                                subitem_title = f.read(subitem_title_length).strip(b'\x00').decode('ansi')
                            
                                # Subitem value
                                subitem_value_length = struct.unpack('>I', f.read(4))[0]
                                subitem_value = f.read(subitem_value_length).strip(b'\x00').decode('ansi')
                            
                                
                                out_file.write(f"{subitem_title}={subitem_value}\n")
                                
                            if _ + 1 < (num_items):
                                out_file.write(f"\n")
                    
                    
                    logger(f"Arquivo extraído: {full_path}")
            messagebox.showinfo("PRONTO !!!", f"Extração bem sucedida")
                
                
    else:           
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

    tipo = get_option("tipo_arquivo")
    if tipo == "1.0":
        try:
            # === 1) Abre original e lê só os nomes, na ordem ===
            file_names = []
            with open(original_file_path, 'rb') as orig:
                # pula os 4 bytes do contador
                orig.seek(4)
                while True:
                    # lê tamanho do nome
                    data = orig.read(4)
                    if not data:
                        break
                    name_len = struct.unpack('>I', data)[0]
                    # lê o nome em si (inclui zeros finais)
                    name_data = orig.read(name_len)
                    file_names.append(name_data)   # guarda o raw bytes
                    
                    # agora pula o resto do bloco: num_items + todos os subblocos
                    num_items = struct.unpack('>I', orig.read(4))[0]
                    for _ in range(num_items):
                        # item_name
                        item_name_len = struct.unpack('>I', orig.read(4))[0]
                        orig.seek(item_name_len, os.SEEK_CUR)
                        # subitems
                        sub_count = struct.unpack('>I', orig.read(4))[0]
                        for __ in range(sub_count):
                            # key + value
                            key_len = struct.unpack('>I', orig.read(4))[0]
                            orig.seek(key_len, os.SEEK_CUR)
                            val_len = struct.unpack('>I', orig.read(4))[0]
                            orig.seek(val_len, os.SEEK_CUR)
            
            # === 2) Recomeça a reconstrução, agora com a lista exata de nomes ===
            with open(output_file_path, 'wb') as out_bin:
                # escreve o número de arquivos
                out_bin.write(struct.pack('>I', len(file_names)))
                
                # para cada nome capturado, busca o .txt correspondente e reescreve
                for name_data in file_names:
                    # 2.1) copia nome (comprimento + bytes)
                    out_bin.write(struct.pack('>I', len(name_data)))
                    out_bin.write(name_data)
                    
                    # extrai o caminho relativo sem o prefixo ..\\ e sem zeros finais
                    decoded = name_data.rstrip(b'\x00').decode('ansi')
                    relative = decoded.lstrip('..\\').replace('\\','/')
                    txt_path = os.path.join(extracted_folder, relative)
                    if not os.path.isfile(txt_path):
                        raise FileNotFoundError(f"Falta: {txt_path}")
                    
                    # 2.2) lê o conteúdo extraído e separa por blocos \n\n
                    with open(txt_path, 'r', encoding='ansi') as f:
                        blocks = f.read().strip().split('\n\n')
                    
                    # 2.3) escreve número de blocos (itens)
                    out_bin.write(struct.pack('>I', len(blocks)))
                    
                    # 2.4) para cada bloco, escreve título + subitens
                    for block in blocks:
                        if not block:
                            continue
                        # separa em linhas e já remove as vazias
                        lines = [line for line in block.splitlines() if line.strip()]
                        title = lines[0][1:-1]  # retira [ e ]
                        subitems = lines[1:]
                        
                        if title == "":
                            out_bin.write(struct.pack('>I', 0))
                        else:
                            title_b = title.encode('ansi') + b'\x00'
                            out_bin.write(struct.pack('>I', len(title_b)))
                            out_bin.write(title_b)
                        
                            out_bin.write(struct.pack('>I', len(subitems)))
                            for line in subitems:
                                k, v = line.split('=', 1)
                                
                                if k == "":
                                    out_bin.write(struct.pack('>I', 0))
                                else:
                                    kb = k.encode('ansi') + b'\x00'
                                    out_bin.write(struct.pack('>I', len(kb)))
                                    out_bin.write(kb)
                                if v == "":
                                    out_bin.write(struct.pack('>I', 0))
                                else:
                                    vb = v.encode('ansi') + b'\x00'
                                    out_bin.write(struct.pack('>I', len(vb)))
                                    out_bin.write(vb)
    
            messagebox.showinfo("SUCESSO", f"Binário reconstruído em:\n{output_file_path}")
    
        except Exception as e:
            messagebox.showerror("ERRO", f"Falha ao reconstruir:\n{e}")


    else:
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
