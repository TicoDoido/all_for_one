import os
import struct
import threading
from tkinter import filedialog, messagebox
from pathlib import Path

# Função de tradução dummy
def translate(key, **kwargs):
    translations = {
        "extracting_to": "Extraindo para: {path}",
        "success": "Sucesso",
        "extraction_success": "Extração concluída com sucesso!",
        "extraction_error": "Erro na extração: {error}",
        "recreation_success": "Arquivo recriado com sucesso!",
        "recreation_error": "Erro na recriação: {error}",
        "file_not_found": "Arquivo não encontrado: {file}",
        "select_original_file": "Selecione o arquivo binário original",
        "select_extracted_folder": "Selecione a pasta extraída",
        "select_output_file": "Selecione onde salvar o novo arquivo"
    }
    return translations.get(key, key).format(**kwargs)

# Variáveis globais
logger = print
get_option = lambda name: None

def register_plugin(log_func, option_getter, host_language="pt_BR"):
    global logger, get_option
    logger = log_func or print
    get_option = option_getter or (lambda name: None)
    return {
        "name": "COALESCED Arquivo Unreal Engine 3 PS3/XBOX 360/N. Switch",
        "description": "Extrai e recria arquivos COALESCED de jogos feitos na Unreal Engine 3 PS360/Switch.",
        "options": [
            {
                "name": "tipo_arquivo",
                "label": "Versão",
                "values": ["1.0", "2.0", "3.0"]  # Corrigido para 3 valores distintos
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
        try:
            input_path = Path(file_path)
            output_folder = input_path.parent / input_path.stem
            output_folder.mkdir(exist_ok=True)

            logger(translate("extracting_to", path=output_folder))

            with open(file_path, 'rb') as f:
                f.seek(4)

                while True:
                    name_len_data = f.read(4)
                    if not name_len_data:
                        break

                    name_len = struct.unpack('>I', name_len_data)[0]
                    name = f.read(name_len).strip(b'\x00').decode('ansi').replace('..\\', '').replace('../', '')
                
                    content_len_data = f.read(4)
                    if not content_len_data:
                        break
                    content_len = struct.unpack('>I', content_len_data)[0]
                    content = f.read(content_len).strip(b'\x00')

                    output_path = output_folder / name
                    output_path.parent.mkdir(parents=True, exist_ok=True)

                    with open(output_path, 'wb') as out_file:
                        out_file.write(content)

            messagebox.showinfo(
                translate("success"),
                translate("extraction_success")
            )
            return True

        except Exception as e:
            messagebox.showerror(
                translate("error"),
                translate("extraction_error", error=str(e))
            )
            return False
    
    elif tipo == "2.0":
        try:
            output_base_dir = os.path.splitext(file_path)[0]
            os.makedirs(output_base_dir, exist_ok=True)
            
            with open(file_path, 'rb') as f:
                f.seek(4)  # Pula o header

                while True:
                    filename_length_data = f.read(4)
                    if not filename_length_data:
                        break
                    
                    filename_length = struct.unpack('>I', filename_length_data)[0]
                    filename_data = f.read(filename_length)
                    filename = filename_data.strip(b'\x00').decode('utf-8')
                
                    safe_path = os.path.join(output_base_dir, filename.lstrip('..\\'))
                    full_path = os.path.abspath(safe_path)
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                    num_items = struct.unpack('>I', f.read(4))[0]
                
                    with open(full_path, 'w', encoding='utf-8') as out_file:
                        for _ in range(num_items):
                            item_name_length = struct.unpack('>I', f.read(4))[0]
                            item_name = f.read(item_name_length).strip(b'\x00').decode('utf-8')
                            out_file.write(f"[{item_name}]\n")
                    
                            num_subitems = struct.unpack('>I', f.read(4))[0]
                            for i in range(num_subitems):
                                subitem_title_length = struct.unpack('>I', f.read(4))[0]
                                subitem_title = f.read(subitem_title_length).strip(b'\x00').decode('utf-8')
                            
                                subitem_value_length = struct.unpack('>I', f.read(4))[0]
                                subitem_value = f.read(subitem_value_length).strip(b'\x00').decode('utf-8', errors='ignore')
                            
                                out_file.write(f"{subitem_title}={subitem_value}\n")
                                
                            if _ + 1 < num_items:
                                out_file.write("\n")
                    
                    logger(f"Arquivo extraído: {full_path}")
            
            messagebox.showinfo(
                translate("success"),
                translate("extraction_success")
            )
            return True
                
        except Exception as e:
            messagebox.showerror(
                translate("error"),
                translate("extraction_error", error=str(e))
            )
            return False
                
    else:  # Versão 3.0
        try:
            def read_name(file, char_count):
                name_length = char_count * 2 + 2
                name_data = file.read(name_length)
                return name_data.decode('utf-16le', ).rstrip('\x00')
    
            output_dir = os.path.splitext(file_path)[0]
            os.makedirs(output_dir, exist_ok=True)
    
            with open(file_path, 'rb') as f:
                endiam_check = f.read(2)
                if endiam_check == b'\x00\x00':
                    endianess = '>'
                    byte_order = 'big'
                else:
                    endianess = '<'
                    byte_order = 'little'
                f.seek(-2, 1)
                
                total_files = struct.unpack(f'{endianess}I', f.read(4))[0]
    
                for _ in range(total_files):
                    char_count_bytes = f.read(4)
                    raw_value = int.from_bytes(char_count_bytes, byteorder=byte_order)
                    char_count = 4294967295 - raw_value
                    file_name = read_name(f, char_count)
                    file_name = os.path.normpath(file_name.replace("..\\", ""))
                    
                    file_path_out = os.path.join(output_dir, file_name)
                    os.makedirs(os.path.dirname(file_path_out), exist_ok=True)
    
                    num_items = struct.unpack(f'{endianess}I', f.read(4))[0]
    
                    items = []
                    for _ in range(num_items):
                        char_count_bytes_item = f.read(4)
                        raw_value_item = int.from_bytes(char_count_bytes_item, byteorder=byte_order)
                        if raw_value_item == 0:
                            item_name = ""
                        else:
                            char_count_item = 4294967295 - raw_value_item
                            item_name = read_name(f, char_count_item)
    
                        num_subitems = struct.unpack(f'{endianess}I', f.read(4))[0]
    
                        subitems = []
                        for _ in range(num_subitems):
                            char_count_bytes_sub_item1 = f.read(4)
                            raw_value_sub_item1 = int.from_bytes(char_count_bytes_sub_item1, byteorder=byte_order)
                            if raw_value_sub_item1 == 0:
                                sub_item_1 = ""
                            else:
                                char_count_sub_item1 = 4294967295 - raw_value_sub_item1
                                sub_item_1 = read_name(f, char_count_sub_item1)
    
                            char_count_bytes_sub_item2 = f.read(4)
                            raw_value_sub_item2 = int.from_bytes(char_count_bytes_sub_item2, byteorder=byte_order)
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

            messagebox.showinfo(
                translate("success"),
                translate("extraction_success")
            )
            return True

        except Exception as e:
            messagebox.showerror(
                translate("error"),
                translate("extraction_error", error=str(e))
            )
            return False

def rebuild_binary_file(original_file_path, output_file_path, extracted_folder):
    tipo = get_option("tipo_arquivo")  # Obter o tipo aqui
    
    if tipo == "1.0":
        try:
            extracted_folder = Path(extracted_folder)
            output_file_path = Path(output_file_path)
    
            logger(translate("recreating_to", path=output_file_path))
    
            file_entries = []
            num_files = 0
    
            with open(original_file_path, 'rb') as orig:
                num_files_data = orig.read(4)
                if len(num_files_data) == 4:
                    num_files = struct.unpack('>I', num_files_data)[0]
    
                while True:
                    name_len_data = orig.read(4)
                    if not name_len_data or len(name_len_data) < 4:
                        break
                    name_len = struct.unpack('>I', name_len_data)[0]
    
                    name = orig.read(name_len).strip(b'\x00').decode('ansi')
    
                    content_len_data = orig.read(4)
                    if not content_len_data or len(content_len_data) < 4:
                        break
                    content_len = struct.unpack('>I', content_len_data)[0]
    
                    orig.seek(content_len, 1)
                    file_entries.append(name)
    
            with open(output_file_path, 'wb') as out:
                out.write(struct.pack('>I', num_files))
    
                for name in file_entries:
                    cleaned_name = name.replace('..\\', '').replace('../', '')
                    file_path = extracted_folder / cleaned_name
    
                    if not file_path.exists():
                        raise FileNotFoundError(translate("file_not_found", file=str(file_path)))
    
                    encoded_name = name.encode('ansi') + b'\x00'
                    encoded_content = file_path.read_bytes() + b'\x00'
    
                    out.write(struct.pack('>I', len(encoded_name)))
                    out.write(encoded_name)
                    out.write(struct.pack('>I', len(encoded_content)))
                    out.write(encoded_content)
    
            messagebox.showinfo(
                translate("success"),
                translate("recreation_success")
            )
            return True
    
        except Exception as e:
            messagebox.showerror(
                translate("error"),
                translate("recreation_error", error=str(e))
            )
            return False

    elif tipo == "2.0":
        try:
            extracted_folder = Path(extracted_folder)
            output_file_path = Path(output_file_path)
            
            file_names = []
            with open(original_file_path, 'rb') as orig:
                orig.seek(4)
                
                while True:
                    name_length_data = orig.read(4)
                    if not name_length_data:
                        break
                        
                    name_length = struct.unpack('>I', name_length_data)[0]
                    name_data = orig.read(name_length)
                    file_names.append(name_data)
                    
                    num_items = struct.unpack('>I', orig.read(4))[0]
                    for _ in range(num_items):
                        item_name_len = struct.unpack('>I', orig.read(4))[0]
                        orig.seek(item_name_len, 1)
                        sub_count = struct.unpack('>I', orig.read(4))[0]
                        for __ in range(sub_count):
                            key_len = struct.unpack('>I', orig.read(4))[0]
                            orig.seek(key_len, 1)
                            val_len = struct.unpack('>I', orig.read(4))[0]
                            orig.seek(val_len, 1)
            
            with open(output_file_path, 'wb') as out:
                out.write(struct.pack('>I', len(file_names)))
                
                for name_data in file_names:
                    out.write(struct.pack('>I', len(name_data)))
                    out.write(name_data)
                    
                    filename = name_data.rstrip(b'\x00').decode('ansi').lstrip('..\\')
                    file_path = extracted_folder / filename
                    
                    if not file_path.exists():
                        raise FileNotFoundError(translate("file_not_found", file=str(file_path)))
                        
                # Processa arquivo INI
                with open(file_path, 'r', encoding='ansi') as f:
                    blocks = [b.strip() for b in f.read().split('\n\n') if b.strip()]
                
                out.write(struct.pack('>I', len(blocks)))
                
                for block in blocks:
                    lines = [l.strip() for l in block.split('\n') if l.strip()]
                    if not lines:
                        continue
                        
                    item_name = lines[0][1:-1]  # Remove []
                    item_name_enc = item_name.encode('ansi') + b'\x00'
                    out.write(struct.pack('>I', len(item_name_enc)))
                    out.write(item_name_enc)
                    
                    subitems = lines[1:]
                    out.write(struct.pack('>I', len(subitems)))
                    
                    for line in subitems:
                        if '=' not in line:
                            continue
                            
                        key, value = line.split('=', 1)
                        key_enc = key.encode('ansi') + b'\x00'
                        value_enc = value.encode('ansi') + b'\x00'
                        
                        out.write(struct.pack('>I', len(key_enc)))
                        out.write(key_enc)
                        out.write(struct.pack('>I', len(value_enc)))
                        out.write(value_enc)
            
            messagebox.showinfo(
                translate("success"),
                translate("recreation_success")
            )
            return True
            
        except Exception as e:
            messagebox.showerror(
                translate("error"),
                translate("recreation_error", error=str(e))
            )
            return False

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
                        if raw_value_item == 0:
                            char_count_item = ""
                        else:
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
                                if len(item_name) > 0:
                                    char_count_item = len(item_name)
                                    char_count_item_encoded = 4294967295 - char_count_item
                                    bin_file.write(struct.pack(endianess + 'I', char_count_item_encoded))
                                    bin_file.write(item_name.encode('utf-16le') + b'\x00\x00')
                                else:
                                    bin_file.write(struct.pack(endianess + 'I', 0))
        
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
            
            messagebox.showinfo(
                translate("success"),
                translate("recreation_success")
            )
            return True
            
        except Exception as e:
            messagebox.showerror(
                translate("error"),
                translate("recreation_error", error=str(e))
            )
            return False

def process_file():
    file_path = filedialog.askopenfilename()
    if file_path:
        read_binary_file(file_path)

def reprocess_file():
    # Selecionar arquivo original
    original_file_path = filedialog.askopenfilename(
        title=translate("select_original_file")
    )
    if not original_file_path:
        return
    
    extracted_folder, file_extension = os.path.splitext(original_file_path)
    
    # Selecionar local para salvar
    output_file_path = extracted_folder + "_MOD" + file_extension
    if not output_file_path:
        return

    rebuild_binary_file(original_file_path, output_file_path, extracted_folder)
