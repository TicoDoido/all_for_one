from tkinter import filedialog, messagebox
import struct
import xml.etree.ElementTree as ET
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
        "name": "XUS Arquivos de texto Xbox 360",
        "description": "Converte arquivos .xus para XML e faz reconversão. Util para localização de jogos.",
        "commands": [
            {"label": "Extrair Texto em XML", "action": select_file_for_xus},
            {"label": "Recriar XUS com XML", "action": select_file_for_xml},
        ]
    }

def get_magic_number_from_xus(file_path):
    with open(file_path, 'rb') as file:
        # Ler o magic number
        magic_number = file.read(6)
    return magic_number

def convert_xus_to_xml(file_path, output_xml_path):
    try:
        with open(file_path, 'rb') as file:
            
            # Verificar o magic number
            magic_number = file.read(6)
            # Lista ou tupla de magic numbers permitidos
            valid_magic_numbers = [b'XUIS\x01\x02', b'XUIS\x01\x00']

            # Verificar se o magic number do arquivo está em uma das opções válidas
            if magic_number not in valid_magic_numbers:
                raise ValueError("Arquivo não tem o magic number esperado.")
            
            # Ler o número de itens
            file.seek(10)
            num_items_bytes = file.read(2)
            num_items = struct.unpack('>H', num_items_bytes)[0]  # Big-endian 2 bytes para número de itens

            # Se o magic number for b'XUIS\x01\x00', dobrar o número de itens
            if magic_number == b'XUIS\x01\x00':
                num_items *= 2
            
            root = ET.Element("Root")  # Elemento raiz que conterá todos os itens
            
            for i in range(num_items):
                # Ler o count char
                count_char_bytes = file.read(2)
                count_char = struct.unpack('>H', count_char_bytes)[0]  # Big-endian 2 bytes para count char
                
                # Ler o texto
                text_bytes = file.read(count_char * 2)  # UTF-16BE usa 2 bytes por caractere
                text = text_bytes.decode('utf-16-be')
                
                # Substituir os caracteres de nova linha por marcadores
                text = text.replace('\r\n', '[0D0A]')
                
                # Criar um elemento pai para cada item
                item_element = ET.Element(f"Item_{i+1}")  # Use i+1 para que o índice comece de 1
                item_element.text = text
                root.append(item_element)
            
            # Criar a árvore XML
            tree = ET.ElementTree(root)
            
            # Converter a árvore XML para uma string
            xml_str = ET.tostring(root, encoding='unicode', method='xml')
            
            # Adicionar quebras de linha entre elementos
            xml_str = xml_str.replace('><', '>\n<')

            # Adicionar uma quebra de linha no início e no fim
            xml_str = '\n' + xml_str.strip() + '\n'
            
            # Salvar a string XML formatada em um arquivo
            with open(output_xml_path, 'w', encoding='utf-8') as output_file:
                output_file.write(xml_str)
        
        messagebox.showinfo("Sucesso", f"Arquivo XML salvo em: {output_xml_path}")
    except Exception as e:
        messagebox.showerror("Erro", str(e))

def xml_to_xus(xml_path, output_xus_path):
    try:
        # Determinar o magic number do arquivo original .xus
        original_xus_path = xml_path.rsplit('.', 1)[0] + '.xus'
        original_magic_number = get_magic_number_from_xus(original_xus_path)
        
        # Escolher o magic number do novo arquivo com base no original
        if original_magic_number == b'XUIS\x01\x00':
            new_magic_number = b'XUIS\x01\x00'
        else:
            new_magic_number = b'XUIS\x01\x02'

        tree = ET.parse(xml_path)
        root = tree.getroot()

        with open(output_xus_path, 'wb+') as file:
            # Escrever o magic number
            file.write(new_magic_number)

            # Criar uma lista para armazenar os dados dos itens
            items_data = []

            for item in root:
                text = item.text
                
                if text is not None:
                    # Substituir de volta os marcadores para os caracteres originais
                    text = text.replace('[0D0A]', '\r\n')

                    # Codificar o texto em UTF-16BE
                    text_bytes = text.encode('utf-16-be')
                else:
                    # Se o texto for None (vazio), cria um array vazio de bytes
                    text_bytes = b''

                # Calcular o número de caracteres (não bytes) e escrever o count_char
                count_char = len(text_bytes) // 2  # Cada caractere em UTF-16BE ocupa 2 bytes
                count_char_bytes = struct.pack('>H', count_char)  # 2 bytes big-endian para o count_char

                # Adicionar o count_char e o texto (ou vazio) à lista de dados
                items_data.append(count_char_bytes + text_bytes)

            num_items = len(items_data)
            num_items_bytes = struct.pack('>H', num_items)
            
            # Se o magic number original for b'XUIS\x01\x00', dividir o número de itens por 2
            if original_magic_number == b'XUIS\x01\x00':
                num_items_bytes = struct.pack('>H', num_items // 2)
            
            # Escrever o número de itens na posição 10
            file.seek(10)
            file.write(num_items_bytes)

            # Escrever os itens
            for item_data in items_data:
                file.write(item_data)

            # Capturar o tamanho total do arquivo
            file_size = file.tell()

            # Voltar para a posição 6 e escrever o tamanho do arquivo em 4 bytes big-endian
            file.seek(6)
            file_size_bytes = struct.pack('>I', file_size)  # 4 bytes big-endian
            file.write(file_size_bytes)

        messagebox.showinfo("Sucesso", f"Arquivo XUS salvo em: {output_xus_path}")
    except Exception as e:
        messagebox.showerror("Erro", str(e))

def select_file_for_xml():
    file_path = filedialog.askopenfilename(filetypes=[("XML files", "*.xml")])
    if file_path:
        output_xus_path = file_path.rsplit('.', 1)[0] + '_novo.xus'
        xml_to_xus(file_path, output_xus_path)

def select_file_for_xus():
    file_path = filedialog.askopenfilename(filetypes=[("XUS files", "*.xus")])
    if file_path:
        output_xml_path = file_path.rsplit('.', 1)[0] + '.xml'
        convert_xus_to_xml(file_path, output_xml_path)

