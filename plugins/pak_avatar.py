import os
import struct
import zlib
import threading
from tkinter import filedialog, messagebox, ttk, Label, Button
from collections import defaultdict

# Dicionários de tradução do plugin
plugin_translations = {
    "pt_BR": {
        "plugin_name": "PAK|STR - Avatar The Last Airbender (PS2)",
        "plugin_description": "Extrai e recria arquivos PAK|STR dos jogos Avatar The Last Airbender/The Burning Earth/Into the Inferno para PS2",
        "extract_file": "Extrair Arquivo",
        "rebuild_file": "Recriar Arquivo",
        "extract_text": "Extrair Texto (.str)",
        "reinsert_text": "Remontar texto (.str)",
        "select_pak_file": "Selecione o arquivo .pak",
        "select_txt_file": "Selecione o arquivo .txt",
        "select_str_file": "Selecione o arquivo .str",
        "pak_files": "Arquivos PAK",
        "str_files": "Arquivos STR",
        "text_files": "Arquivos de Texto",
        "all_files": "Todos os arquivos",
        "invalid_magic": "Arquivo não tem o magic esperado!",
        "extraction_completed": "Extração concluída com sucesso!",
        "reinsertion_completed": "Reinserção concluída com sucesso!",
        "text_extraction_completed": "Textos extraídos e salvos em:\n{path}",
        "text_reinsertion_completed": "Textos reinseridos no arquivo binário.",
        "folder_not_found": "Pasta não encontrada: {folder}",
        "file_not_found": "Arquivo não encontrado: {file}",
        "unexpected_error": "Ocorreu um erro inesperado: {error}",
        "progress_title_extract": "Extraindo Arquivos",
        "progress_title_reinsert": "Reinserindo Arquivos",
        "cancel_button": "Cancelar"
    },
    "en_US": {
        "plugin_name": "PAK|STR - Avatar The Last Airbender (PS2)",
        "plugin_description": "Extracts and rebuilds PAK|STR files from Avatar The Last Airbender/The Burning Earth/Into the Inferno PS2 games",
        "extract_file": "Extract File",
        "rebuild_file": "Rebuild File",
        "extract_text": "Extract Text (.str)",
        "reinsert_text": "Reinsert Text (.str)",
        "select_pak_file": "Select .pak file",
        "select_txt_file": "Select .txt file",
        "select_str_file": "Select .str file",
        "pak_files": "PAK Files",
        "str_files": "STR Files",
        "text_files": "Text Files",
        "all_files": "All files",
        "invalid_magic": "File does not have expected magic!",
        "extraction_completed": "Extraction completed successfully!",
        "reinsertion_completed": "Reinsertion completed successfully!",
        "text_extraction_completed": "Texts extracted and saved to:\n{path}",
        "text_reinsertion_completed": "Texts reinserted into binary file.",
        "folder_not_found": "Folder not found: {folder}",
        "file_not_found": "File not found: {file}",
        "unexpected_error": "An unexpected error occurred: {error}",
        "progress_title_extract": "Extracting Files",
        "progress_title_reinsert": "Reinserting Files",
        "cancel_button": "Cancel"
    },
    "es_ES": {
        "plugin_name": "PAK|STR - Avatar The Last Airbender (PS2)",
        "plugin_description": "Extrae y reconstruye archivos PAK|STR de los juegos Avatar The Last Airbender/The Burning Earth/Into the Inferno para PS2",
        "extract_file": "Extraer Archivo",
        "rebuild_file": "Reconstruir Archivo",
        "extract_text": "Extraer Texto (.str)",
        "reinsert_text": "Reinsertar Texto (.str)",
        "select_pak_file": "Seleccionar archivo .pak",
        "select_txt_file": "Seleccionar archivo .txt",
        "select_str_file": "Seleccionar archivo .str",
        "pak_files": "Archivos PAK",
        "str_files": "Archivos STR",
        "text_files": "Archivos de Texto",
        "all_files": "Todos los archivos",
        "invalid_magic": "¡El archivo no tiene el magic esperado!",
        "extraction_completed": "¡Extracción completada con éxito!",
        "reinsertion_completed": "¡Reinserción completada con éxito!",
        "text_extraction_completed": "Textos extraídos y guardados en:\n{path}",
        "text_reinsertion_completed": "Textos reinsertados en el archivo binario.",
        "folder_not_found": "Carpeta no encontrada: {folder}",
        "file_not_found": "Archivo no encontrado: {file}",
        "unexpected_error": "Ocurrió un error inesperado: {error}",
        "progress_title_extract": "Extrayendo Archivos",
        "progress_title_reinsert": "Reinsertando Archivos",
        "cancel_button": "Cancelar"
    }
}

# Variáveis globais do plugin
logger = print
current_language = "pt_BR"
get_option = lambda name: None

def translate(key, **kwargs):
    """Função de tradução interna do plugin"""
    lang_dict = plugin_translations.get(current_language, plugin_translations["pt_BR"])
    translation = lang_dict.get(key, key)
    
    if kwargs:
        try:
            return translation.format(**kwargs)
        except:
            return translation
    return translation

def register_plugin(log_func, option_getter, host_language="pt_BR"):
    global logger, current_language, get_option
    logger = log_func or print
    current_language = host_language
    get_option = option_getter or (lambda name: None)
    
    def get_plugin_info():
        return {
            "name": translate("plugin_name"),
            "description": translate("plugin_description"),
            "commands": [
                {"label": translate("extract_file"), "action": selecionar_arquivo},
                {"label": translate("rebuild_file"), "action": selecionar_arquivo_txt},
                {"label": translate("extract_text"), "action": select_file_textout},
                {"label": translate("reinsert_text"), "action": select_file_textin},
            ]
        }
    
    return get_plugin_info

class ProgressWindow:
    def __init__(self, parent, title, total):
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("400x120")
        self.window.resizable(False, False)
        self.window.grab_set()
        
        self.progress_var = tk.DoubleVar()
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
            text=translate("cancel_button"), 
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

def ler_little_endian(arquivo, tamanho):
    return int.from_bytes(arquivo.read(tamanho), 'little')

def extrair_pak(arquivo_pak):
    diretorio_arquivo = os.path.dirname(arquivo_pak)
    nome_pasta_saida = os.path.join(diretorio_arquivo, os.path.splitext(os.path.basename(arquivo_pak))[0])
    nome_pasta_saida = os.path.normpath(nome_pasta_saida)

    lista_arquivos_extraidos = []

    with open(arquivo_pak, 'rb') as arquivo:
        magic = arquivo.read(8)
        if magic == b'kcap\x01\x00\x01\x00':
            tamanho_cabecalho = ler_little_endian(arquivo, 4)
            tamanho_total = ler_little_endian(arquivo, 4)
            posicao_nomes = ler_little_endian(arquivo, 4)
            tamanho_nomes = tamanho_cabecalho - posicao_nomes
            numero_itens = ler_little_endian(arquivo, 4)

            itens = []
            for _ in range(numero_itens):
                arquivo.seek(4, 1)
                ponteiro = ler_little_endian(arquivo, 4)
                tamanho_comp = ler_little_endian(arquivo, 4)
                tamanho_descomp = ler_little_endian(arquivo, 4)
                itens.append((ponteiro, tamanho_comp, tamanho_descomp))

            arquivo.seek(posicao_nomes)
            blocos_nomes = arquivo.read(tamanho_nomes)
            nomes_arquivos = blocos_nomes.split(b'\x00')[:numero_itens]
            nomes_arquivos = [nome.decode('utf-8').lstrip("//") for nome in nomes_arquivos if nome]
            
        elif magic == b'kcap\x01\x00\x02\x00':
            cabecalho_inicio = ler_little_endian(arquivo, 4)
            tamanho_cabecalho_total = ler_little_endian(arquivo, 4)
            tamanho_cabecalho_ponteiros = ler_little_endian(arquivo, 4)
            tamanho_nomes = tamanho_cabecalho_total - tamanho_cabecalho_ponteiros
            numero_itens = ler_little_endian(arquivo, 4)
            
            arquivo.seek(cabecalho_inicio)
            itens = []
            for _ in range(numero_itens):
                ponteiro = ler_little_endian(arquivo, 4)
                tamanho_descomp = ler_little_endian(arquivo, 4)
                tamanho_comp = ler_little_endian(arquivo, 4)
                itens.append((ponteiro, tamanho_descomp, tamanho_comp))
                arquivo.seek(12, 1)
                
            posicao_nomes = arquivo.tell()
            blocos_nomes = arquivo.read(tamanho_nomes)
            nomes_arquivos = blocos_nomes.split(b'\x00')[:numero_itens]
            nomes_arquivos = [nome.decode('utf-8').lstrip("//") for nome in nomes_arquivos if nome]
            
        else:
            raise ValueError(translate("invalid_magic"))

        if magic == b'kcap\x01\x00\x01\x00':
            for i, (ponteiro, tamanho_comp, tamanho_descomp) in enumerate(itens):
                arquivo.seek(ponteiro)
                dados = arquivo.read(tamanho_comp)

                if tamanho_descomp > 0:
                    dados = zlib.decompress(dados)
                    nome_arquivo = nomes_arquivos[i]
                    nome_arquivo_descomprimido = os.path.splitext(nome_arquivo)[0] + "_descomprimido" + os.path.splitext(nome_arquivo)[1]
                else:
                    nome_arquivo_descomprimido = nomes_arquivos[i]
                
                nome_arquivo_descomprimido = os.path.normpath(nome_arquivo_descomprimido)
                caminho_completo = os.path.join(nome_pasta_saida, nome_arquivo_descomprimido)
                caminho_completo = os.path.normpath(caminho_completo)
                os.makedirs(os.path.dirname(caminho_completo), exist_ok=True)

                with open(caminho_completo, 'wb') as saida:
                    saida.write(dados)

                lista_arquivos_extraidos.append(nome_arquivo_descomprimido)
                logger(f"Arquivo '{caminho_completo}' extraído com sucesso.")
        
        else:
            for i, (ponteiro, tamanho_descomp, tamanho_comp) in enumerate(itens):
                arquivo.seek(ponteiro)
                dados = arquivo.read(tamanho_comp)

                if tamanho_descomp > tamanho_comp:
                    dados = zlib.decompress(dados)
                    nome_arquivo = nomes_arquivos[i]
                    nome_arquivo_descomprimido = os.path.splitext(nome_arquivo)[0] + "_descomprimido" + os.path.splitext(nome_arquivo)[1]
                else:
                    nome_arquivo_descomprimido = nomes_arquivos[i]
                    
                nome_arquivo_descomprimido = os.path.normpath(nome_arquivo_descomprimido)
                caminho_completo = os.path.join(nome_pasta_saida, nome_arquivo_descomprimido)
                caminho_completo = os.path.normpath(caminho_completo)
                os.makedirs(os.path.dirname(caminho_completo), exist_ok=True)

                with open(caminho_completo, 'wb') as saida:
                    saida.write(dados)

                lista_arquivos_extraidos.append(nome_arquivo_descomprimido)
                logger(f"Arquivo '{caminho_completo}' extraído com sucesso.")

    lista_txt = os.path.join(diretorio_arquivo, os.path.splitext(os.path.basename(arquivo_pak))[0] + '.txt')
    lista_txt = os.path.normpath(lista_txt)

    with open(lista_txt, 'w') as arquivo_lista:
        for nome in lista_arquivos_extraidos:
            arquivo_lista.write(nome + '\n')

    logger(f"Lista de arquivos extraídos salva em '{lista_txt}'.")

def escrever_little_endian(arquivo, valor):
    arquivo.write(valor.to_bytes(4, 'little'))
    return valor

def recreate_file(arquivo_txt):
    diretorio_txt = os.path.dirname(arquivo_txt)
    nome_pak = os.path.splitext(os.path.basename(arquivo_txt))[0]
    nome_pasta = os.path.join(diretorio_txt, nome_pak)

    if not os.path.exists(nome_pasta):
        raise FileNotFoundError(translate("folder_not_found", folder=nome_pasta))

    with open(arquivo_txt, 'r') as arquivo:
        lista_arquivos = [linha.strip() for linha in arquivo.readlines()]

    arquivo_pak = os.path.join(diretorio_txt, nome_pak + '.pak')
    if not os.path.exists(arquivo_pak):
        raise FileNotFoundError(translate("file_not_found", file=arquivo_pak))

    ponteiros = []
    tamanhos_normais = []
    tamanhos_comprimidos = []

    with open(arquivo_pak, 'r+b') as pak:
        magic = pak.read(8)
        if magic == b'kcap\x01\x00\x01\x00':
            pak.seek(28)
            posicao_insercao = ler_little_endian(pak, 4)
            logger(f"Iniciando inserção a partir da posição: 0x{posicao_insercao:08X}")
            pak.seek(posicao_insercao)

            for nome_arquivo in lista_arquivos:
                caminho_arquivo = os.path.join(nome_pasta, nome_arquivo)
                if not os.path.exists(caminho_arquivo):
                    raise FileNotFoundError(translate("file_not_found", file=caminho_arquivo))

                with open(caminho_arquivo, 'rb') as f:
                    dados = f.read()

                tamanho_normal = len(dados)
                tamanhos_normais.append(tamanho_normal)

                if '_descomprimido' in nome_arquivo:
                    dados = zlib.compress(dados)

                tamanho_comprimido = len(dados)
                tamanhos_comprimidos.append(tamanho_comprimido)

                if tamanho_comprimido % 2048 != 0:
                    padding = 2048 - (tamanho_comprimido % 2048)
                    dados += b'\x00' * padding

                ponteiro_atual = pak.tell()
                ponteiros.append(ponteiro_atual)
                pak.write(dados)
                posicao_insercao += len(dados)
                logger(f"Arquivo '{nome_arquivo}' inserido com sucesso na posição 0x{ponteiro_atual:08X}.")
            
            pak.truncate()
            pak.seek(24)

            for i in range(len(ponteiros)):
                pak.seek(4, 1)
                escrever_little_endian(pak, ponteiros[i])

                if tamanhos_normais[i] == tamanhos_comprimidos[i]:
                    escrever_little_endian(pak, tamanhos_normais[i])
                    pak.write(b'\x00\x00\x00\x00')
                else:
                    escrever_little_endian(pak, tamanhos_comprimidos[i])
                    escrever_little_endian(pak, tamanhos_normais[i])
                    
        elif magic == b'kcap\x01\x00\x02\x00':
            inicio_ponteiros = ler_little_endian(pak, 4)
            pak.seek(inicio_ponteiros)
            posicao_insercao = ler_little_endian(pak, 4)
            logger(f"Iniciando inserção a partir da posição: 0x{posicao_insercao:08X}")
            pak.seek(posicao_insercao)
            
            for nome_arquivo in lista_arquivos:
                caminho_arquivo = os.path.join(nome_pasta, nome_arquivo)
                if not os.path.exists(caminho_arquivo):
                    raise FileNotFoundError(translate("file_not_found", file=caminho_arquivo))

                with open(caminho_arquivo, 'rb') as f:
                    dados = f.read()

                tamanho_normal = len(dados)
                tamanhos_normais.append(tamanho_normal)

                if '_descomprimido' in nome_arquivo:
                    dados = zlib.compress(dados, level=9)

                tamanho_comprimido = len(dados)
                tamanhos_comprimidos.append(tamanho_comprimido)

                if tamanho_comprimido % 2048 != 0:
                    padding = 2048 - (tamanho_comprimido % 2048)
                    dados += b'\x00' * padding

                ponteiro_atual = pak.tell()
                ponteiros.append(ponteiro_atual)
                pak.write(dados)
                posicao_insercao += len(dados)
                logger(f"Arquivo '{nome_arquivo}' inserido com sucesso na posição 0x{ponteiro_atual:08X}.")
                
            pak.truncate()
            pak.seek(inicio_ponteiros)

            for i in range(len(ponteiros)):
                escrever_little_endian(pak, ponteiros[i])

                if tamanhos_normais[i] == tamanhos_comprimidos[i]:
                    escrever_little_endian(pak, tamanhos_normais[i])
                    escrever_little_endian(pak, tamanhos_normais[i])
                else:
                    escrever_little_endian(pak, tamanhos_normais[i])
                    escrever_little_endian(pak, tamanhos_comprimidos[i])
                
                pak.seek(12, 1)

        logger(translate("reinsertion_completed"))

def read_little_endian_int(file):
    return struct.unpack('<I', file.read(4))[0]

def extract_texts_from_binary(file_path):
    with open(file_path, 'rb') as file:
        file.seek(8)
        total_texts = read_little_endian_int(file)
        pointers = []
        file.seek(12)

        for _ in range(total_texts):
            file.seek(4, 1)
            pointer = read_little_endian_int(file)
            pointers.append(pointer)
            file.seek(4, 1)
        
        texts = []
        text_start_position = 20 + (total_texts * 12)

        for pointer in pointers:
            text_position = pointer + text_start_position
            file.seek(text_position)
            text = b""
            while True:
                byte = file.read(1)
                if byte == b'\x00':
                    break
                text += byte
            texts.append(text.decode('utf8', errors='ignore'))
    
    return texts

def save_texts_to_file(texts, file_path):
    output_file = f"{os.path.splitext(file_path)[0]}.txt"
    with open(output_file, 'w', encoding='utf8') as f:
        for text in texts:
            f.write(f"{text}[fim]\n")
    messagebox.showinfo(translate("completed"), translate("text_extraction_completed", path=output_file))

def insert_texts_into_binary(file_path):
    txt_file_path = f"{os.path.splitext(file_path)[0]}.txt"
    if not os.path.exists(txt_file_path):
        messagebox.showerror(translate("invalid_file"), translate("file_not_found", file=txt_file_path))
        return

    with open(txt_file_path, 'r', encoding='utf8') as f:
        texts = f.read().split("[fim]\n")
        if texts[-1] == "":
            texts.pop()

    with open(file_path, 'r+b') as file:
        file.seek(8)
        total_texts = read_little_endian_int(file)
        text_start_position = 20 + (total_texts * 12)
        offsets = []
        file.seek(text_start_position)
        
        for idx, text in enumerate(texts):
            offset = file.tell()
            offsets.append(offset - text_start_position)
            text_bytes = text.encode('utf8') + b'\x00'
            file.write(text_bytes)
        
        size = file.tell() - text_start_position
        file.seek(12)
        
        for offset in offsets:
            file.seek(4, 1)
            file.write(struct.pack('<I', offset))
            file.seek(4, 1)
            
        file.seek(text_start_position - 4)
        file.write(struct.pack('<I', size))

    messagebox.showinfo(translate("completed"), translate("text_reinsertion_completed"))

def selecionar_arquivo():
    arquivo_pak = filedialog.askopenfilename(
        title=translate("select_pak_file"),
        filetypes=[(translate("pak_files"), "*.pak"), (translate("all_files"), "*.*")]
    )
    if arquivo_pak:
        try:
            extrair_pak(arquivo_pak)
            messagebox.showinfo(translate("completed"), translate("extraction_completed"))
        except Exception as e:
            messagebox.showerror(translate("invalid_file"), translate("unexpected_error", error=str(e)))

def selecionar_arquivo_txt():
    arquivo_txt = filedialog.askopenfilename(
        title=translate("select_txt_file"),
        filetypes=[(translate("text_files"), "*.txt"), (translate("all_files"), "*.*")]
    )
    if arquivo_txt:
        try:
            recreate_file(arquivo_txt)
            messagebox.showinfo(translate("completed"), translate("reinsertion_completed"))
        except Exception as e:
            messagebox.showerror(translate("invalid_file"), translate("unexpected_error", error=str(e)))

def select_file_textout():
    file_path = filedialog.askopenfilename(
        title=translate("select_str_file"),
        filetypes=[(translate("str_files"), "*.str"), (translate("all_files"), "*.*")]
    )
    if file_path:
        try:
            texts = extract_texts_from_binary(file_path)
            save_texts_to_file(texts, file_path)
        except Exception as e:
            messagebox.showerror(translate("invalid_file"), translate("unexpected_error", error=str(e)))
            
def select_file_textin():
    file_path = filedialog.askopenfilename(
        title=translate("select_str_file"),
        filetypes=[(translate("str_files"), "*.str"), (translate("all_files"), "*.*")]
    )
    if file_path:
        try:
            insert_texts_into_binary(file_path)
        except Exception as e:
            messagebox.showerror(translate("invalid_file"), translate("unexpected_error", error=str(e)))