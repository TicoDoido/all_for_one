from tkinter import filedialog, messagebox
import struct
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
        "name": "LXB de texto de alguns jogos da DreamWorks(PS2, PS3, PC, Wii...)",
        "description": "Extrai e recria textos de arquivos .LXB de texto de alguns jogos DreamWorks como Kung Foo Panda ou Shrek Forever After",
        "commands": [
            {"label": "Extrair Arquivo", "action": selecionar_arquivo_lxb_auto},
            {"label": "Recriar Arquivo", "action": selecionar_arquivo_txt_auto}
        ]
    }

def determinar_endianess(caminho_arquivo):
    try:
        with open(caminho_arquivo, 'rb') as file:
            # Ler os primeiros 4 bytes do arquivo
            cabecalho = file.read(4)
            
            # Verificar os valores em ambos os endianness
            valor_be = struct.unpack('>I', cabecalho)[0]  # Big-endian
            valor_le = struct.unpack('<I', cabecalho)[0]  # Little-endian
            
            # Determinar o endianness com base no valor esperado (5 para big-endian)
            if valor_be == 5:
                logger("Endianness detectado: Big-endian")
                return '>'
            elif valor_le == 5:
                logger("Endianness detectado: Little-endian")
                return '<'
            else:
                raise ValueError("Cabeçalho do arquivo inválido ou desconhecido.")
    except Exception as e:
        raise ValueError(f"Erro ao determinar o endianness: {e}")

def selecionar_arquivo_lxb_auto():
    arquivos = filedialog.askopenfilenames(
        title="Selecione os arquivos",
        filetypes=(("Arquivos LXB", "*.lxb"), ("Todos os arquivos", "*.*"))
    )
    if arquivos:
        for arquivo in arquivos:
            try:
                endianess = determinar_endianess(arquivo)
                extrair_dados(arquivo, endianess)
            except ValueError as e:
                messagebox.showerror("Erro", f"Erro ao processar o arquivo {arquivo}:\n{str(e)}")

def selecionar_arquivo_txt_auto():
    arquivos = filedialog.askopenfilenames(
        title="Selecione o arquivo",
        filetypes=(("Arquivos TXT", "*.txt"), ("Todos os arquivos", "*.*"))
    )
    if arquivos:
        for arquivo in arquivos:  # Itera sobre cada arquivo selecionado
            try:
                nome_arquivo, _ = os.path.splitext(os.path.basename(arquivo))
                caminho_arquivo_lxb = os.path.join(os.path.dirname(arquivo), f"{nome_arquivo}.lxb")
                endianess = determinar_endianess(caminho_arquivo_lxb)
                reinserir_dados(arquivo, endianess)
            except ValueError as e:
                messagebox.showerror("Erro", f"Erro ao processar o arquivo {arquivo}:\n{str(e)}")
                
        messagebox.showinfo("Pronto", f"Textos inseridos com sucesso ")

def extrair_dados(caminho_arquivo, endianess):
    try:
        with open(caminho_arquivo, 'rb') as file:
            file.seek(124)
            quantidade_ponteiros = struct.unpack(endianess + 'I', file.read(4))[0]
            
            ponteiros = []
            file.seek(128)
            for i in range(quantidade_ponteiros):
                file.seek(4, os.SEEK_CUR)  
                posicao_atual = file.tell()
                ponteiro = struct.unpack(endianess + 'I', file.read(4))[0]
                novo_valor = posicao_atual + ponteiro
                
                if novo_valor >= os.path.getsize(caminho_arquivo):
                    logger(f"Ponteiro inválido: 0x{novo_valor:X} fora do tamanho do arquivo.")
                    continue
                
                ponteiros.append(novo_valor)

            dados_extraidos = []
            for i, novo_valor in enumerate(ponteiros):
                file.seek(novo_valor)
                bloco_dados = []
                while True:
                    byte = file.read(1)
                    if byte == b'\x00' or byte == b'':
                        break
                    bloco_dados.append(byte)
                
                bloco_dados = b''.join(bloco_dados)
                dados_extraidos.append(bloco_dados)

            dados_modificados = b'[FIM]\n'.join(dados_extraidos) + b'[FIM]\n'
            nome_arquivo, _ = os.path.splitext(os.path.basename(caminho_arquivo))
            novo_caminho = os.path.join(os.path.dirname(caminho_arquivo), f"{nome_arquivo}.txt")
            novo_caminho = os.path.normpath(novo_caminho)
            with open(novo_caminho, 'wb') as novo_arquivo:
                novo_arquivo.write(dados_modificados)
            
            messagebox.showinfo("Pronto", f"Textos extraídos e salvos em:\n {novo_caminho}")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao processar o arquivo: {e}")

def reinserir_dados(caminho_arquivo_txt, endianess):
    try:
        nome_arquivo, _ = os.path.splitext(os.path.basename(caminho_arquivo_txt))
        caminho_arquivo_lxb = os.path.join(os.path.dirname(caminho_arquivo_txt), f"{nome_arquivo}.lxb")
        
        if not os.path.exists(caminho_arquivo_lxb):
            logger(f"Erro: Arquivo LXB correspondente não encontrado: {caminho_arquivo_lxb}")
            return
        
        logger(f"Processando arquivo TXT: {caminho_arquivo_txt}")
        with open(caminho_arquivo_txt, 'rb') as file_txt:
            dados_modificados = file_txt.read()
        
        dados_extraidos = dados_modificados.replace(b'[FIM]\n', b'\x00')
        blocos_dados = dados_extraidos.split(b'\x00')
        if blocos_dados[-1] == b'':
            blocos_dados.pop()
        
        with open(caminho_arquivo_lxb, 'r+b') as file_lxb:
            file_lxb.seek(4)
            bytes_dados_restantes = file_lxb.read(4)
            dados_restantes = struct.unpack(endianess + 'I', bytes_dados_restantes)[0]
            if dados_restantes != 0:
                nova_posicao = dados_restantes - 4
                file_lxb.seek(nova_posicao)
                dados_finais = file_lxb.read()
            else:
                dados_finais = b''
            
            file_lxb.seek(124)
            bytes_lidos = file_lxb.read(4)
            valor_lido = struct.unpack(endianess + 'I', bytes_lidos)[0]
            posicao_escrita = 128 + 8 * valor_lido
            
            posicoes_blocos = []
            posicao_atual = posicao_escrita
            for i, bloco in enumerate(blocos_dados):
                file_lxb.seek(posicao_atual)
                file_lxb.write(bloco)
                posicoes_blocos.append(posicao_atual)
                posicao_atual += len(bloco) + 1
                file_lxb.seek(posicao_atual - 1)
                file_lxb.write(b'\x00')
            
            pos_dados_finais = file_lxb.tell()
            pos_final_real = pos_dados_finais - 4
            file_lxb.write(dados_finais)
            file_lxb.truncate()
            
            file_lxb.seek(4)
            file_lxb.write(struct.pack(endianess + 'I', pos_final_real))
            
            file_lxb.seek(128)
            for posicao_atual in posicoes_blocos:
                file_lxb.seek(4, os.SEEK_CUR)
                posicao_atual_2 = file_lxb.tell()
                novo_valor = posicao_atual - posicao_atual_2
                file_lxb.write(struct.pack(endianess + 'I', novo_valor))

    except Exception as e:
        logger(f"Erro: {str(e)}")
