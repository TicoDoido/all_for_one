import os
import struct
import zlib

def register_plugin():
    return {
        "name": "CAT/MATCAT Arquivo FEAR 1 PS3/XBOX 360",
        "description": "Extrai e recria contêineres (.CAT/.MATCAT) FEAR 1",
        "commands": [
            {"label": "Extrair Arquivo", "action": choose_file},
            {"label": "Reconstruir Arquivo", "action": choose_file_to_recreate},
        ]
    }

def read_file_info(file_path):
    try:
        with open(file_path, 'rb') as f:
            f.seek(4)
            start_pointers = struct.unpack('>I', f.read(4))[0]
            f.seek(8)
            num_pointers = struct.unpack('>I', f.read(4))[0]
            f.seek(12)
            start_block_names = struct.unpack('>I', f.read(4))[0]
            f.seek(16)
            size_block_names = struct.unpack('>I', f.read(4))[0]

            f.seek(start_block_names)
            names_block = f.read(size_block_names)

            # Substitui b'MSF\x01' por b'.wav' nos bytes lidos
            file_names = names_block.replace(b'MSF\x01', b'wav')

            # Divide nos bytes nulos para obter uma lista de nomes de arquivos
            file_names = file_names.split(b'\x00')
             
         

            file_list_name = f"{os.path.splitext(file_path)[0]}_filelist.txt"
            extract_folder = os.path.splitext(file_path)[0]

            if not os.path.exists(extract_folder):
                os.makedirs(extract_folder)

            with open(file_list_name, 'w') as file_list:
                for i in range(num_pointers):
                    f.seek(start_pointers + i * 16)
                    f.read(4)
                    pointer = struct.unpack('>I', f.read(4))[0]
                    uncompressed_size = struct.unpack('>I', f.read(4))[0]
                    compressed_size = struct.unpack('>I', f.read(4))[0]

                    f.seek(pointer)
                    compressed_data = f.read(compressed_size)

                    file_name = file_names[i].decode('utf-8')
                    file_path = os.path.join(extract_folder, file_name)

                    try:
                        decompressed_data = zlib.decompress(compressed_data)
                        data_to_write = decompressed_data
                        file_list.write(f"{file_name}\n")
                    except zlib.error:
                        data_to_write = compressed_data
                        file_list.write(f"{file_name},uncompressed\n")

                    os.makedirs(os.path.dirname(file_path), exist_ok=True)

                    with open(file_path, 'wb') as out_file:
                        out_file.write(data_to_write)

                    print(f"Processado: {file_name}, Ponteiro: {hex(pointer).upper()}")

        messagebox.showinfo("Sucesso", "Arquivos extraídos com sucesso!")
    except Exception as e:
        messagebox.showerror("Erro", str(e))

def pad_to_32_bytes(data):
    padding_length = (32 - (len(data) % 32)) % 32
    return data + b'\x00' * padding_length

def recreate_file(file_path):
    try:
        base_name = os.path.splitext(file_path)[0]
        folder_name = base_name
        new_file_path = f"{base_name}_mod.cat"
        file_list_path = f"{base_name}_filelist.txt"

        if not os.path.exists(file_list_path):
            messagebox.showerror("Erro", "Arquivo de lista de arquivos não encontrado.")
            return

        with open(file_path, 'rb') as original_file:
            original_file.seek(20)
            data_start_offset = struct.unpack('>I', original_file.read(4))[0]
            original_file.seek(0)
            header = original_file.read(data_start_offset)

        file_infos = []

        with open(new_file_path, 'wb') as new_file:
            new_file.write(header)
            current_pointer = data_start_offset

            with open(file_list_path, 'r') as file_list:
                for line in file_list:
                    line = line.strip()
                    if ',' in line:
                        file_name, uncompressed = line.split(',')
                        uncompressed = True
                    else:
                        file_name = line
                        uncompressed = False

                    file_name = file_name.strip()
                    file_path = os.path.join(folder_name, file_name)

                    with open(file_path, 'rb') as f:
                        data = f.read()
                        uncompressed_size = len(data)
                        if not uncompressed:
                            data = zlib.compress(data)
                            print(f"Adicionando {file_name} comprimido.")

                    compressed_size = len(data)  # Tamanho comprimido sem o padding
                    compressed_data = pad_to_32_bytes(data)

                    file_infos.append((current_pointer, uncompressed_size, compressed_size))
                    new_file.write(compressed_data)
                    current_pointer += len(compressed_data)

        with open(new_file_path, 'r+b') as new_file:
            new_file.seek(32)
            for file_info in file_infos:
                #esses 4 bytes pulados são identificadores usados pelo jogo
                new_file.read(4)
                new_file.write(struct.pack('>I', file_info[0]))
                new_file.write(struct.pack('>I', file_info[1]))
                new_file.write(struct.pack('>I', file_info[2]))

        messagebox.showinfo("Sucesso", "Arquivo recriado com sucesso!")
    except Exception as e:
        messagebox.showerror("Erro", str(e))

def choose_file_to_recreate():
    file_path = filedialog.askopenfilename(filetypes=[("Arquivos FEAR", "*.cat *.matcat")])
    if file_path:
        recreate_file(file_path)

def choose_file():
    file_path = filedialog.askopenfilename(filetypes=[("Arquivos FEAR", "*.cat *.matcat")])
    if file_path:
        read_file_info(file_path)

