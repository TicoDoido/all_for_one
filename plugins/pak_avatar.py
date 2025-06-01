import os
import struct
from tkinter import filedialog, messagebox
import zlib

# no topo do seu plugin.py
logger = print
get_option = lambda name: None  # stub até receber do host

def register_plugin(log_func, option_getter):
    global logger, get_option
    # atribui o logger e a função de consulta de opções vindos do host
    logger     = log_func or print
    get_option = option_getter or (lambda name: None)
            
    return {
        "name": "PAK|STR Avatar The Last Airbender, The Burning Earth(PS2)",
        "description": "Extrai e recria arquivos PAK|STR do jogo Avatar The Last Airbender|The Burning Earth|Into the Inferno de PS2. Alguns arquivos .STR tem alguns dados no final do mesmo e esses não podem ficar maiores que seu tamanho original ainda...",
        "commands": [
            {"label": "Extrair Arquivo", "action": selecionar_arquivo},
            {"label": "Recriar Arquivo", "action": selecionar_arquivo_txt},
            {"label": "Extrair Texto(.str)", "action": select_file_textout},
            {"label": "Remontar texto(.str)", "action": select_file_textin},
        ]
    }


def ler_little_endian(arquivo, tamanho):
    return int.from_bytes(arquivo.read(tamanho), 'little')

def extrair_pak(arquivo_pak):
    # Obter o diretório do arquivo .pak
    diretorio_arquivo = os.path.dirname(arquivo_pak)
    # Nome da pasta de saída será o nome do arquivo .pak sem a extensão
    nome_pasta_saida = os.path.join(diretorio_arquivo, os.path.splitext(os.path.basename(arquivo_pak))[0])
    nome_pasta_saida = os.path.normpath(nome_pasta_saida)

    # Criar uma lista para armazenar os nomes dos arquivos extraídos
    lista_arquivos_extraidos = []

    with open(arquivo_pak, 'rb') as arquivo:
        # Ler magic
        magic = arquivo.read(8)
        if magic == b'kcap\x01\x00\x01\x00':

            # Ler o tamanho do cabeçalho
            tamanho_cabecalho = ler_little_endian(arquivo, 4)

            # Ler o tamanho total do container
            tamanho_total = ler_little_endian(arquivo, 4)

            # Ler a posição inicial dos nomes dos arquivos
            posicao_nomes = ler_little_endian(arquivo, 4)

            # Calcular o tamanho do bloco de nomes
            tamanho_nomes = tamanho_cabecalho - posicao_nomes

            # Ler o número de itens no container
            numero_itens = ler_little_endian(arquivo, 4)

            # Ler ponteiros e informações dos itens
            itens = []
            for _ in range(numero_itens):
                arquivo.seek(4, 1)  # Pular 4 bytes
                ponteiro = ler_little_endian(arquivo, 4)
                tamanho_comp = ler_little_endian(arquivo, 4)
                tamanho_descomp = ler_little_endian(arquivo, 4)
                itens.append((ponteiro, tamanho_comp, tamanho_descomp))

            # Ler e dividir nomes dos arquivos
            arquivo.seek(posicao_nomes)
            blocos_nomes = arquivo.read(tamanho_nomes)
            nomes_arquivos = blocos_nomes.split(b'\x00')[:numero_itens]

            # Convertendo para strings e extraindo arquivos
            nomes_arquivos = [nome.decode('utf-8').lstrip("//") for nome in nomes_arquivos if nome]
            
        elif magic == b'kcap\x01\x00\x02\x00':
            
            # Ler o tamanho do cabeçalho
            cabecalho_inicio = ler_little_endian(arquivo, 4)

            # Ler o tamanho total do container
            tamanho_cabecalho_total = ler_little_endian(arquivo, 4)

            # Ler a posição inicial dos nomes dos arquivos
            tamanho_cabecalho_ponteiros = ler_little_endian(arquivo, 4)

            # Calcular o tamanho do bloco de nomes
            tamanho_nomes = tamanho_cabecalho_total - tamanho_cabecalho_ponteiros

            # Ler o número de itens no container
            numero_itens = ler_little_endian(arquivo, 4)
            
            arquivo.seek(cabecalho_inicio)

            # Ler ponteiros e informações dos itens
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

            # Convertendo para strings e extraindo arquivos
            nomes_arquivos = [nome.decode('utf-8').lstrip("//") for nome in nomes_arquivos if nome]
            
            
        else:
            raise ValueError("Arquivo não tem o magic esperado!")

        if magic == b'kcap\x01\x00\x01\x00':
            for i, (ponteiro, tamanho_comp, tamanho_descomp) in enumerate(itens):
                arquivo.seek(ponteiro)
                dados = arquivo.read(tamanho_comp)

                # Descomprimir se necessário
                if tamanho_descomp > 0:
                    dados = zlib.decompress(dados)
                    # Adicionar "_descomprimido" ao nome do arquivo
                    nome_arquivo = nomes_arquivos[i]
                    nome_arquivo_descomprimido = os.path.splitext(nome_arquivo)[0] + "_descomprimido" + os.path.splitext(nome_arquivo)[1]
                else:
                    nome_arquivo_descomprimido = nomes_arquivos[i]  # Usar o nome original se não houver descompressão
                
                
                # Criar diretórios para o arquivo no local correto
                nome_arquivo_descomprimido = os.path.normpath(nome_arquivo_descomprimido)
                caminho_completo = os.path.join(nome_pasta_saida, nome_arquivo_descomprimido)
                caminho_completo = os.path.normpath(caminho_completo)  # Normalizar o caminho
                os.makedirs(os.path.dirname(caminho_completo), exist_ok=True)

                # Salvar arquivo extraído
                with open(caminho_completo, 'wb') as saida:
                    saida.write(dados)

                # Adicionar o nome do arquivo à lista
                lista_arquivos_extraidos.append(nome_arquivo_descomprimido)

                print(f"Arquivo '{caminho_completo}' extraído com sucesso.")
        
        else:
            for i, (ponteiro, tamanho_descomp, tamanho_comp) in enumerate(itens):
                arquivo.seek(ponteiro)
                dados = arquivo.read(tamanho_comp)

                # Descomprimir se necessário
                if tamanho_descomp > tamanho_comp:
                    dados = zlib.decompress(dados)
                    # Adicionar "_descomprimido" ao nome do arquivo
                    nome_arquivo = nomes_arquivos[i]
                    nome_arquivo_descomprimido = os.path.splitext(nome_arquivo)[0] + "_descomprimido" + os.path.splitext(nome_arquivo)[1]
                else:
                    nome_arquivo_descomprimido = nomes_arquivos[i]  # Usar o nome original se não houver descompressão
                    
                nome_arquivo_descomprimido = os.path.normpath(nome_arquivo_descomprimido)

                # Criar diretórios para o arquivo no local correto
                caminho_completo = os.path.join(nome_pasta_saida, nome_arquivo_descomprimido)
                caminho_completo = os.path.normpath(caminho_completo)  # Normalizar o caminho
                os.makedirs(os.path.dirname(caminho_completo), exist_ok=True)

                # Salvar arquivo extraído
                with open(caminho_completo, 'wb') as saida:
                    saida.write(dados)

                # Adicionar o nome do arquivo à lista
                lista_arquivos_extraidos.append(nome_arquivo_descomprimido)

                logger(f"Arquivo '{caminho_completo}' extraído com sucesso.")

    # Salvar a lista de arquivos extraídos em um arquivo .txt
    lista_txt = os.path.join(diretorio_arquivo, os.path.splitext(os.path.basename(arquivo_pak))[0] + '.txt')
    lista_txt = os.path.normpath(lista_txt)  # Normalizar o caminho

    with open(lista_txt, 'w') as arquivo_lista:
        for nome in lista_arquivos_extraidos:
            arquivo_lista.write(nome + '\n')

    logger(f"Lista de arquivos extraídos salva em '{lista_txt}'.")

def escrever_little_endian(arquivo, valor):
    """Escreve um valor em formato little endian no arquivo."""
    arquivo.write(valor.to_bytes(4, 'little'))
    return valor

def recreate_file(arquivo_txt):
    # Obter o nome do arquivo .pak e o diretório com base no arquivo .txt
    diretorio_txt = os.path.dirname(arquivo_txt)
    nome_pak = os.path.splitext(os.path.basename(arquivo_txt))[0]
    nome_pasta = os.path.join(diretorio_txt, nome_pak)

    # Verificar se a pasta com os arquivos existe
    if not os.path.exists(nome_pasta):
        raise FileNotFoundError(f"A pasta '{nome_pasta}' não foi encontrada!")

    # Ler a lista de arquivos do .txt
    with open(arquivo_txt, 'r') as arquivo:
        lista_arquivos = [linha.strip() for linha in arquivo.readlines()]

    # Abrir o arquivo .pak original para leitura e escrita
    arquivo_pak = os.path.join(diretorio_txt, nome_pak + '.pak')
    if not os.path.exists(arquivo_pak):
        raise FileNotFoundError(f"O arquivo .pak '{arquivo_pak}' não foi encontrado!")

    # Variáveis para armazenar os dados dos arquivos
    ponteiros = []
    tamanhos_normais = []
    tamanhos_comprimidos = []

    with open(arquivo_pak, 'r+b') as pak:
        
        magic = pak.read(8)
        if magic == b'kcap\x01\x00\x01\x00':
            # Ir até a posição 28 e ler o ponteiro de onde começar a inserção
            pak.seek(28)
            posicao_insercao = ler_little_endian(pak, 4)
            logger(f"Iniciando inserção a partir da posição: 0x{posicao_insercao:08X}")

            # Ir até a posição de inserção
            pak.seek(posicao_insercao)

            for nome_arquivo in lista_arquivos:
                caminho_arquivo = os.path.join(nome_pasta, nome_arquivo)
                if not os.path.exists(caminho_arquivo):
                    raise FileNotFoundError(f"O arquivo '{caminho_arquivo}' não foi encontrado!")

                # Ler o conteúdo do arquivo
                with open(caminho_arquivo, 'rb') as f:
                    dados = f.read()

                # Salvar o tamanho normal do arquivo
                tamanho_normal = len(dados)
                tamanhos_normais.append(tamanho_normal)

                # Se o arquivo tiver '_descomprimido' no nome, comprimir os dados
                if '_descomprimido' in nome_arquivo:
                    dados = zlib.compress(dados)

                # Salvar o tamanho comprimido
                tamanho_comprimido = len(dados)
                tamanhos_comprimidos.append(tamanho_comprimido)

                # Verificar o tamanho e adicionar padding se necessário
                if tamanho_comprimido % 2048 != 0:
                    padding = 2048 - (tamanho_comprimido % 2048)
                    dados += b'\x00' * padding

                # Salvar o ponteiro de onde o arquivo será escrito
                ponteiro_atual = pak.tell()
                ponteiros.append(ponteiro_atual)

                # Escrever os dados no .pak
                pak.write(dados)

                # Atualizar a posição de inserção para o próximo arquivo
                posicao_insercao += len(dados)
                logger(f"Arquivo '{nome_arquivo}' inserido com sucesso na posição 0x{ponteiro_atual:08X}.")
            
            pak.truncate()

            # Escrever a nova posição e tamanhos na posição correta
            pak.seek(24)  # Pular para a posição 28

            for i in range(len(ponteiros)):
                # Pular 4 bytes
                pak.seek(4, 1)

                # Escrever o ponteiro da posição atual
                escrever_little_endian(pak, ponteiros[i])

                # Se o arquivo não foi comprimido, escrever 4 bytes zero
                if tamanhos_normais[i] == tamanhos_comprimidos[i]:
                    # Escrever o tamanho normal do arquivo
                    escrever_little_endian(pak, tamanhos_normais[i])
                    pak.write(b'\x00\x00\x00\x00')
                
                else:
                    # Se o arquivo foi comprimido, escrever o tamanho comprimido
                    escrever_little_endian(pak, tamanhos_comprimidos[i])
                    # Escrever o tamanho normal do arquivo
                    escrever_little_endian(pak, tamanhos_normais[i])
                    
        elif magic == b'kcap\x01\x00\x02\x00':
            
            inicio_ponteiros = ler_little_endian(pak, 4)
            pak.seek(inicio_ponteiros)
            
            posicao_insercao = ler_little_endian(pak, 4)
            logger(f"Iniciando inserção a partir da posição: 0x{posicao_insercao:08X}")

            # Ir até a posição de inserção
            pak.seek(posicao_insercao)
            
            for nome_arquivo in lista_arquivos:
                caminho_arquivo = os.path.join(nome_pasta, nome_arquivo)
                if not os.path.exists(caminho_arquivo):
                    raise FileNotFoundError(f"O arquivo '{caminho_arquivo}' não foi encontrado!")

                # Ler o conteúdo do arquivo
                with open(caminho_arquivo, 'rb') as f:
                    dados = f.read()

                # Salvar o tamanho normal do arquivo
                tamanho_normal = len(dados)
                tamanhos_normais.append(tamanho_normal)

                # Se o arquivo tiver '_descomprimido' no nome, comprimir os dados
                if '_descomprimido' in nome_arquivo:
                    dados = zlib.compress(dados, level=9)

                # Salvar o tamanho comprimido
                tamanho_comprimido = len(dados)
                tamanhos_comprimidos.append(tamanho_comprimido)

                # Verificar o tamanho e adicionar padding se necessário
                if tamanho_comprimido % 2048 != 0:
                    padding = 2048 - (tamanho_comprimido % 2048)
                    dados += b'\x00' * padding

                # Salvar o ponteiro de onde o arquivo será escrito
                ponteiro_atual = pak.tell()
                ponteiros.append(ponteiro_atual)

                # Escrever os dados no .pak
                pak.write(dados)

                # Atualizar a posição de inserção para o próximo arquivo
                posicao_insercao += len(dados)
                logger(f"Arquivo '{nome_arquivo}' inserido com sucesso na posição 0x{ponteiro_atual:08X}.")
                
            pak.truncate()
            
            # Escrever a nova posição e tamanhos na posição correta
            pak.seek(inicio_ponteiros)  # Pular para a posição 28

            for i in range(len(ponteiros)):

                # Escrever o ponteiro da posição atual
                escrever_little_endian(pak, ponteiros[i])

                # Se o arquivo não foi comprimido, escrever 4 bytes zero
                if tamanhos_normais[i] == tamanhos_comprimidos[i]:
                    # Escrever o tamanho normal do arquivo
                    escrever_little_endian(pak, tamanhos_normais[i])
                    escrever_little_endian(pak, tamanhos_normais[i])
                
                else:

                    # Escrever o tamanho normal do arquivo
                    escrever_little_endian(pak, tamanhos_normais[i])
                    # Se o arquivo foi comprimido, escrever o tamanho comprimido
                    escrever_little_endian(pak, tamanhos_comprimidos[i])
                
                pak.seek(12, 1)

        logger("Todos os arquivos foram reinseridos com sucesso.")


def selecionar_arquivo():
    arquivo_pak = filedialog.askopenfilename(filetypes=[("PAK Files", "*.pak")])
    if arquivo_pak:
        try:
            extrair_pak(arquivo_pak)
            messagebox.showinfo("Sucesso", "Extração concluída com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro: {str(e)}")

def selecionar_arquivo_txt():
    arquivo_txt = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
    if arquivo_txt:
        try:
            recreate_file(arquivo_txt)
            messagebox.showinfo("Sucesso", "Reinserção concluída com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro: {str(e)}")

# Extrator de textos embutido
def read_little_endian_int(file):
    """Lê 4 bytes e retorna um inteiro little endian"""
    return struct.unpack('<I', file.read(4))[0]

def extract_texts_from_binary(file_path):
    with open(file_path, 'rb') as file:
        file.seek(8)
        # Ler o total de textos (total de ponteiros) - 4 bytes little endian
        total_texts = read_little_endian_int(file)
        
        # Lista para armazenar os ponteiros reais
        pointers = []
        
        # Ponteiros começam na posição 12
        file.seek(12)

        for _ in range(total_texts):
            # Pular 4 bytes
            file.seek(4, 1)
            # Ler 4 bytes para o ponteiro real
            pointer = read_little_endian_int(file)
            pointers.append(pointer)
            # Pular 4 bytes
            file.seek(4, 1)
        
        # Extrair os textos
        texts = []
        text_start_position = 20 + (total_texts * 12)  # Posição de onde os textos começam

        for pointer in pointers:
            # Calcular a posição real do texto no arquivo
            text_position = pointer + text_start_position
            file.seek(text_position)

            # Ler o texto até encontrar um byte nulo (indica fim da string)
            text = b""
            while True:
                byte = file.read(1)
                if byte == b'\x00':  # String null-terminated
                    break
                text += byte
            
            # Adicionar o texto à lista (decodificar de bytes para string)
            texts.append(text.decode('utf8', errors='ignore'))
    
    return texts

def save_texts_to_file(texts, file_path):
    # Criar o nome do arquivo de saída com o nome original + .txt
    output_file = f"{os.path.splitext(file_path)[0]}.txt"
    
    # Salvar os textos no arquivo .txt
    with open(output_file, 'w', encoding='utf8') as f:
        for text in texts:
            f.write(f"{text}[fim]\n")
    
    messagebox.showinfo("Sucesso", f"Os textos foram extraídos e salvos em {output_file}")

def insert_texts_into_binary(file_path):
    # Criar o nome do arquivo de texto correspondente
    txt_file_path = f"{os.path.splitext(file_path)[0]}.txt"
    
    if not os.path.exists(txt_file_path):
        messagebox.showerror("Erro", f"O arquivo {txt_file_path} não existe.")
        return

    with open(txt_file_path, 'r', encoding='utf8') as f:
        # Ler os textos do arquivo de texto
        texts = f.read().split("[fim]\n")
        if texts[-1] == "":  # Remover último item vazio se existir
            texts.pop()

    with open(file_path, 'r+b') as file:
        file.seek(8)
        # Ler o total de textos (total de ponteiros) - 4 bytes little endian
        total_texts = read_little_endian_int(file)
        text_start_position = 20 + (total_texts * 12)  # Posição de onde os textos começam
        
        # Salvar os offsets para cada texto
        offsets = []
        
        file.seek(text_start_position)
        
        # Reinserir os textos no arquivo binário e salvar os novos offsets
        for idx, text in enumerate(texts):
            # Capturar o offset (posição atual no arquivo) antes de escrever o texto
            offset = file.tell()
            offsets.append(offset - text_start_position)
            
            # Converter texto para bytes e adicionar byte nulo ao final
            text_bytes = text.encode('utf8') + b'\x00'
            file.write(text_bytes)
        
        size = file.tell() - text_start_position


        # Voltar para o início da área de ponteiros para escrever os novos valores
        file.seek(12)  # Ponteiros começam na posição 8
        for offset in offsets:
            # Pular 4 bytes
            file.seek(4, 1)
            # Escrever o offset em little endian
            file.write(struct.pack('<I', offset))
            # Pular 4 bytes
            file.seek(4, 1)
            
        file.seek(text_start_position - 4)
        file.write(struct.pack('<I', size))

    messagebox.showinfo("Sucesso", "Os textos foram reinseridos no arquivo binário.")


def select_file_textout():
    # Abrir diálogo para escolher o arquivo .str
    file_path = filedialog.askopenfilename(
        title="Selecione o arquivo STR",
        filetypes=(("Arquivos STR", "*.str"), ("Todos os arquivos", "*.*"))
    )
    
    if file_path:
        try:
            texts = extract_texts_from_binary(file_path)
            save_texts_to_file(texts, file_path)
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao processar o arquivo: {e}")
            
def select_file_textin():
    # Abrir diálogo para escolher o arquivo .str
    file_path = filedialog.askopenfilename(
        title="Selecione o arquivo STR",
        filetypes=(("Arquivos STR", "*.str"), ("Todos os arquivos", "*.*"))
    )
    
    if file_path:
        try:
            texts = insert_texts_into_binary(file_path)
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao processar o arquivo: {e}")