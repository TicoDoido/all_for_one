import struct
import os
from tkinter import filedialog, messagebox, scrolledtext

# no topo do seu plugin.py
logger = print
get_option = lambda name: None  # stub até receber do host

def register_plugin(log_func, option_getter):
    global logger, get_option
    # atribui o logger e a função de consulta de opções vindos do host
    logger     = log_func or print
    get_option = option_getter or (lambda name: None)

    return {
        "name": "RCF Radcore Cement Library VER:1.2/2.1",
        "description": "Extrai e recria arquivos RCF de jogos da Radical Entertainment",
        "commands": [
            {"label": "Extrair Arquivo", "action": select_file},
            {"label": "Recriar Arquivo", "action": select_rcf_file}
        ]
    }



def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("RCF Files", "*.rcf"), ("All Files", "*.*")])
    if file_path:
        extract_files(file_path)
        
def calculate_padding(size, allocation=512):
    if size % allocation == 0:
        return size
    return ((size // allocation) + 1) * allocation

def select_rcf_file():
    rcf_path = filedialog.askopenfilename(filetypes=[("RCF Files", "*.rcf")])
    if rcf_path:
        select_txt_file(rcf_path)

def select_txt_file(rcf_path):
    base_filename = os.path.splitext(os.path.basename(rcf_path))[0]
    txt_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")], initialfile=f"{base_filename}.txt")
    if txt_path:
        recreate_rcf(rcf_path, txt_path)

def recreate_rcf(original_file_path, txt_names_path):
    base_filename = os.path.splitext(os.path.basename(original_file_path))[0]
    base_filename = os.path.normpath(base_filename)
    base_directory = os.path.dirname(original_file_path)
    base_directory = os.path.normpath(base_directory)
    new_rcf_path = os.path.join(base_directory, f"new_{base_filename}.rcf")

    # Normalize extracted_files_directory to ensure it contains the correct path
    extracted_files_directory = os.path.normpath(os.path.join(base_directory, base_filename))
    extracted_files_directory = os.path.normpath(extracted_files_directory)

    # Check if the directory exists
    if not os.path.exists(extracted_files_directory):
        messagebox.showerror("Error", f"Folder {extracted_files_directory} not found!")
        return

    # Check if txt_names_path exists
    if not os.path.exists(txt_names_path):
        messagebox.showerror("Error", f"File {txt_names_path} not found!")
        return

    logger("Starting RCF file recreation...")
    
    with open(original_file_path, 'rb') as original_file:
        original_file.seek(32)
        file_version = original_file.read(4)

        # Process versions 2.1 (Little and Big Endian)
        if file_version in [b'\x02\x01\x00\x01', b'\x02\x01\x01\x01']:
            endian_format = '<' if file_version == b'\x02\x01\x00\x01' else '>'
            endian_type = "LITTLE ENDIAN" if endian_format == '<' else "BIG ENDIAN"
            log_message(f"Version is 2.1\n{endian_type} MODE")

            original_file.seek(44)
            offset_value = struct.unpack(f'{endian_format}I', original_file.read(4))[0]
            original_file.seek(48)
            size_value = struct.unpack(f'{endian_format}I', original_file.read(4))[0]

            header_size = offset_value + size_value
            adjusted_header_size = calculate_padding(header_size)

            original_file.seek(0)
            header = original_file.read(adjusted_header_size)

        # Process version 1.2
        elif file_version == b'\x01\x02\x00\x01':
            logger("Version is 1.2\nLITTLE ENDIAN MODE.")
            
            endian_format = '<'  # Define the endian format for version 1.2
            
            original_file.seek(2048)
            total_items = struct.unpack('<I', original_file.read(4))[0]
            names_offset = struct.unpack('<I', original_file.read(4))[0]
            
            original_file.seek(names_offset + 4)
            
            for i in range(total_items):
                original_file.seek(4, os.SEEK_CUR)
                name_size = struct.unpack('<I', original_file.read(4))[0]
                name_bytes = original_file.read(name_size)
                
            header_size = original_file.tell()
            adjusted_header_size = calculate_padding(header_size)
            
            original_file.seek(0)
            header = original_file.read(adjusted_header_size)

        else:
            messagebox.showerror("Error", "Unsupported file!")
            return

    with open(new_rcf_path, 'w+b') as new_rcf:
        # Escrever o cabeçalho
        new_rcf.write(header)
    
        pointers = []
        current_position = adjusted_header_size
    
        # Abrir o arquivo de texto contendo os nomes
        # Open the file containing the names
        with open(txt_names_path, 'r', encoding='utf-8') as txt_names:
            for line in txt_names:
                file_name = line.lstrip("/\\").strip()  # Remove barras e espaços adicionais
                logger(f"Processed file name: {file_name}")


                # Construct the full file path
                file_path = os.path.normpath(os.path.join(extracted_files_directory, file_name))


                # Check if the file exists
                if os.path.exists(file_path):
                    logger(f"File exists: {file_path}")
                else:
                    logger(f"File does not exist: {file_path}. Directory contents: {os.listdir(extracted_files_directory)}")


                # Process the file
                with open(file_path, 'rb') as f_file:
                    file_data = f_file.read()
    
                original_size = len(file_data)
                size_with_padding = calculate_padding(original_size)

                new_rcf.write(file_data)
                new_rcf.write(b'\x00' * (size_with_padding - original_size))
    
                # Armazenar o ponteiro e o tamanho original
                pointers.append((current_position, original_size))
                current_position += size_with_padding
    
                logger(f"File {file_name} added successfully.")
    
        # Voltar e escrever os ponteiros e os tamanhos
        new_rcf.seek(32)
        file_version = new_rcf.read(4)
        
        if file_version in [b'\x02\x01\x00\x01', b'\x02\x01\x01\x01']:
            endian_format = '<' if file_version == b'\x02\x01\x00\x01' else '>'
            
            new_rcf.seek(60)
            for pointer, original_size in pointers:
                new_rcf.seek(4, os.SEEK_CUR)  # Skip 4 bytes
                new_rcf.write(struct.pack(f'{endian_format}I', pointer))
                new_rcf.write(struct.pack(f'{endian_format}I', original_size))
                
        else:
            # Version 1.2 (LITTLE ENDIAN) -- EXISTS A BIG ENDIAN VERSION ?
            new_rcf.seek(2064)
            for pointer, original_size in pointers:
                new_rcf.seek(4, os.SEEK_CUR)  # Skip 4 bytes
                new_rcf.write(struct.pack('<I', pointer))
                new_rcf.write(struct.pack('<I', original_size))
    
    logger(f"New RCF file successfully created at: {new_rcf_path}")
    messagebox.showinfo("DONE", f"New RCF file created at: {new_rcf_path}")

def extract_files(file_path):
    # Resolva o caminho do diretório base
    base_directory = os.path.realpath(os.path.dirname(file_path))
    
    # Nome base para o diretório de extração
    base_filename = os.path.splitext(os.path.basename(file_path))[0]
    
    # Diretório de extração
    extraction_directory = os.path.join(base_directory, base_filename)

    # Criação do diretório de extração
    if not os.path.exists(extraction_directory):
        try:
            os.makedirs(extraction_directory)
            logger(f"Extraction directory created: {extraction_directory}")
        except Exception as e:
            logger(f"Error creating extraction directory: {e}")

    with open(file_path, 'rb') as file:
        file.seek(32)
        file_version = file.read(4)
        
        if file_version in [b'\x02\x01\x00\x01', b'\x02\x01\x01\x01']:
            if file_version == b'\x02\x01\x00\x01':
                logger("Version is 2.1\nLITTLE ENDIAN MODE")
            else:
                logger("Version is 2.1\nBIG ENDIAN MODE")

            file.seek(36)  # Move to the initial position of the pointers
            if file_version == b'\x02\x01\x00\x01':
                pointers_offset = struct.unpack('<I', file.read(4))[0]
                file.seek(4, os.SEEK_CUR)
                names_offset = struct.unpack('<I', file.read(4))[0]
                file.seek(4, os.SEEK_CUR)
            else:
                pointers_offset = struct.unpack('>I', file.read(4))[0]
                file.seek(4, os.SEEK_CUR)
                names_offset = struct.unpack('>I', file.read(4))[0]
                file.seek(4, os.SEEK_CUR)

            file.seek(56)
            
            if file_version == b'\x02\x01\x00\x01':
                total_items = struct.unpack('<I', file.read(4))[0]
            else:
                total_items = struct.unpack('>I', file.read(4))[0]

            pointers = []

            file.seek(pointers_offset)
            for i in range(total_items):
                file.seek(4, os.SEEK_CUR)  # Skip the first 4 bytes
                if file_version == b'\x02\x01\x00\x01':
                    file_offset = struct.unpack('<I', file.read(4))[0]
                    file_size = struct.unpack('<I', file.read(4))[0]
                else:
                    file_offset = struct.unpack('>I', file.read(4))[0]
                    file_size = struct.unpack('>I', file.read(4))[0]
                pointers.append((file_offset, file_size))

            names = []
            file.seek(names_offset + 8)

            for i in range(total_items):
                file.seek(12, os.SEEK_CUR)
                name_size = struct.unpack('<I', file.read(4))[0]

                name_bytes = file.read(name_size)

                try:
                    name = name_bytes.decode('utf-8').strip('\x00')
                    names.append(name)
                except UnicodeDecodeError as e:
                    logger(f"Error decoding name: {e} - Bytes read: {name_bytes}")

                file.seek(3, os.SEEK_CUR)

            for i, (file_offset, file_size) in enumerate(pointers):
                file.seek(file_offset)
                data = file.read(file_size)
                
                # Certifique-se de que o nome do arquivo seja válido
                if i >= len(names) or not names[i].strip():
                    logger(f"Skipping unnamed file at index {i}.")
                    continue
                
                # Corrigir o nome do arquivo para remover caminhos absolutos e normalizar
                file_name = names[i].strip()
                
                # Caminho relativo completo preservado
                complete_path = os.path.join(extraction_directory, file_name.lstrip("/\\"))

                
                # Criar todos os subdiretórios necessários
                file_directory = os.path.dirname(complete_path)
                if not os.path.exists(file_directory):
                    os.makedirs(file_directory)

                # Escrever o arquivo no caminho final
                with open(complete_path, 'wb') as f:
                    f.write(data)
                
                logger(f"File {complete_path} extracted successfully.")


            names_list_path = os.path.join(base_directory, f"{base_filename}.txt")
            with open(names_list_path, 'w', encoding='utf-8') as names_list:
                for name in names:
                    names_list.write(name + '\n')

            logger(f"File list saved at: {names_list_path}")

        # Processo específico para a versão 01 02 00 01
        elif file_version == b'\x01\x02\x00\x01':
            log_message("Version is 1.2\nLITTLE ENDIAN MODE.")
            
            file.seek(2048)
            total_items = struct.unpack('<I', file.read(4))[0]
            
            names_offset = struct.unpack('<I', file.read(4))[0]
            
            file.seek(8, os.SEEK_CUR)
            
            pointers = []
            
            for i in range(total_items):
                file.seek(4, os.SEEK_CUR)  # Skip the first 4 bytes
                file_offset = struct.unpack('<I', file.read(4))[0]
                file_size = struct.unpack('<I', file.read(4))[0]
                pointers.append((file_offset, file_size))
                
            names = []
            
            file.seek(names_offset +4)
            
            for i in range(total_items):
                file.seek(4, os.SEEK_CUR)
                
                name_size = struct.unpack('<I', file.read(4))[0]

                name_bytes = file.read(name_size)

                try:
                    name = name_bytes.decode('utf-8').strip('\x00')
                    names.append(name)
                except UnicodeDecodeError as e:
                    logger(f"Error decoding name: {e} - Bytes read: {name_bytes}")
            
                for i, (file_offset, file_size) in enumerate(pointers):
                    file.seek(file_offset)
                    data = file.read(file_size)
                
                    # Certifique-se de que o nome do arquivo seja válido
                    if i >= len(names) or not names[i].strip():
                        logger(f"Skipping unnamed file at index {i}.")
                        continue
                
                    # Corrigir o nome do arquivo para remover caminhos absolutos e normalizar
                    file_name = names[i].strip()
                
                    # Caminho relativo completo preservado
                    complete_path = os.path.join(extraction_directory, file_name.lstrip("/\\"))

                
                    # Criar todos os subdiretórios necessários
                    file_directory = os.path.dirname(complete_path)
                    if not os.path.exists(file_directory):
                        os.makedirs(file_directory)

                    # Escrever o arquivo no caminho final
                    with open(complete_path, 'wb') as f:
                        f.write(data)
                
                    logger(f"File {complete_path} extracted successfully.")


            names_list_path = os.path.join(base_directory, f"{base_filename}.txt")
            names_list_path = names_list_path.replace('\\', '/')
            with open(names_list_path, 'w', encoding='utf-8') as names_list:
                for name in names:
                    names_list.write(name + '\n')

            logger(f"File list saved at: {names_list_path}")

        else:
            messagebox.showerror("Error", "Unsupported file!")
            return  

    messagebox.showinfo("DONE", f"Files successfully extracted to: {extraction_directory}")