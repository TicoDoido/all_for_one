import os
import struct
import zlib
from tkinter import filedialog, messagebox

# Funções injetadas pelo host
logger = print
get_option = lambda name: None

def register_plugin(log_func, option_getter):
    global logger, get_option
    # Recebe do host a função de log e o getter de opções
    logger = log_func or print
    get_option = option_getter or (lambda name: None)

    return {
        "name": "ARC de Dead Rising V 0.4 XBOX 360/PC",
        "description": "Extrai e recria .arc Dead Rising Xbox 360/PC",
        "options": [
            {
                "name": "modo_compactacao",
                "label": "Modo de Compactação",
                "values": ["zlib", "deflate", "N/A"]
            }
        ],
        "commands": [
            {"label": "Extrair Arquivo",     "action": escolher_arquivo},
            {"label": "Reconstruir Arquivo", "action": escolher_arquivo_remontar},
        ]
    }


def determinar_endian(magic):
    if magic == b'\x00CRA':
        return '>'  # Big-endian
    elif magic == b'ARC\x00':
        return '<'  # Little-endian
    else:
        return None


def extrair_arc(arquivo_arc):
    try:
        with open(arquivo_arc, 'rb') as f:
            magic = f.read(4)
            endian = determinar_endian(magic)
            if not endian:
                messagebox.showerror("Erro", "Magic inválido. Esperado \\x00CRA ou ARC\\x00")
                return

            versao = struct.unpack(endian + 'H', f.read(2))[0]
            if versao != 4:
                messagebox.showinfo("Atenção", f"Feito para a versão 0.4\nEsse é: 0.{versao}")

            num_arquivos = struct.unpack(endian + 'H', f.read(2))[0]

            entradas = []
            for _ in range(num_arquivos):
                nome_bytes = f.read(64)
                nome_str = nome_bytes.split(b'\x00', 1)[0].decode('utf-8', errors='ignore')
                id_bytes = f.read(4)
                id_hex = id_bytes.hex().upper()
                nome_completo = f"{nome_str}_{id_hex}"

                tamanho = struct.unpack(endian + 'I', f.read(4))[0]
                tamanho_descomprimido = struct.unpack(endian + 'I', f.read(4))[0]
                offset = struct.unpack(endian + 'I', f.read(4))[0]

                entradas.append((nome_completo, tamanho, tamanho_descomprimido, offset))

            pasta_saida = os.path.splitext(os.path.basename(arquivo_arc))[0]
            dir_saida = os.path.join(os.path.dirname(arquivo_arc), pasta_saida)
            os.makedirs(dir_saida, exist_ok=True)

            for nome, tamanho, tamanho_descomprimido, offset in entradas:
                try:
                    logger(f"Processando: {nome}")
                    caminho_arquivo = os.path.join(dir_saida, nome)
                    os.makedirs(os.path.dirname(caminho_arquivo), exist_ok=True)

                    f.seek(offset)
                    dados = f.read(tamanho)

                    # Se houver compressão esperada
                    if tamanho_descomprimido > tamanho:
                        # 1) Tenta ZLIB padrão
                        try:
                            dados = zlib.decompress(dados)
                        except Exception as err_zlib:
                            logger(f"Aviso (ZLIB): erro ao descomprimir '{nome}': {err_zlib}")
                            # 2) Tenta raw DEFLATE (wbits negativo)
                            try:
                                dados = zlib.decompress(dados, -zlib.MAX_WBITS)
                            except Exception as err_deflate:
                                logger(f"Aviso (DEFLATE): erro ao descomprimir '{nome}': {err_deflate}")
                                # 3) Se ainda falhar, dados permanecem brutos

                    # gravação ocorre sempre, dentro do try individual
                    with open(caminho_arquivo, 'wb') as out:
                        out.write(dados)
                    logger(f"Gravado: {caminho_arquivo}")

                except Exception as err_arquivo:
                    logger(f"Erro ao processar '{nome}': {err_arquivo}")
                    continue

    except Exception as err_global:
        messagebox.showerror("Erro crítico", f"Não foi possível abrir/processar o ARC:\n{err_global}")
        return

    messagebox.showinfo("Sucesso", f"{num_arquivos} arquivos extraídos para:\n{dir_saida}")




def recriar_arc(arquivo_arc):
    with open(arquivo_arc, 'r+b') as f:
        modo = get_option("modo_compactacao")
        
        magic = f.read(4)
        endian = determinar_endian(magic)
        if not endian:
            messagebox.showerror("Erro", "Magic inválido!")
            return

        f.seek(4)
        versao = struct.unpack(endian + 'H', f.read(2))[0]
        if versao != 4:
            messagebox.showinfo("Atenção", f"Feito para a versão 0.4 \nEsse é: 0.{versao}")

        num_arquivos = struct.unpack(endian + 'H', f.read(2))[0]
        logger(f"Total de arquivos: {num_arquivos}")
        
        # Calcula posição correta dos dados
        header_size = 8 + (80 * num_arquivos)
        f.seek(header_size)
        insercao = f.tell()
        logger(f"Posição inicial: {insercao}")

        entradas = []
        f.seek(8)  # Início das entradas
        for _ in range(num_arquivos):
            nome_bytes = f.read(64)
            nome_str = nome_bytes.split(b'\x00', 1)[0].decode('utf-8', errors='ignore')

            id_bytes = f.read(4)
            id_hex = id_bytes.hex().upper()
            nome_completo = f"{nome_str}_{id_hex}"

            tamanho = struct.unpack(endian + 'I', f.read(4))[0]
            tamanho_descomprimido = struct.unpack(endian + 'I', f.read(4))[0]
            offset = struct.unpack(endian + 'I', f.read(4))[0]

            entradas.append((nome_completo, tamanho, tamanho_descomprimido))

        pasta_saida = os.path.splitext(os.path.basename(arquivo_arc))[0]
        dir_saida = os.path.join(os.path.dirname(arquivo_arc), pasta_saida)

        f.seek(insercao)
        dados_novos = []

        for idx, (nome, tamanho_original, tamanho_descomprimido) in enumerate(entradas):
            caminho_arquivo = os.path.join(dir_saida, nome)
            
            if not os.path.exists(caminho_arquivo):
                messagebox.showerror("Erro", f"Arquivo não encontrado: {caminho_arquivo}")
                return

            with open(caminho_arquivo, 'rb') as arq:
                dados = arq.read()

            offset_novo = f.tell()
            logger(f"Inserindo em: {offset_novo}")
            tamanho_total_novo = len(dados)

            if tamanho_descomprimido > tamanho_original:
                
                if modo == "deflate":
                    compress_obj = zlib.compressobj(wbits=-15)
                    dados_comp = compress_obj.compress(dados) + compress_obj.flush()
                    
                elif modo == "N/A":
                    dados_comp = dados
                    
                else:
                    dados_comp = zlib.compress(dados)
                
                f.write(dados_comp)
                tamanho_novo = len(dados_comp)
                logger(f"[OK] Recompressão ({modo}) e reinserção: {nome}")
            else:
                f.write(dados)
                tamanho_novo = len(dados)
                logger(f"[OK] Reescreveu sem compressão: {nome}")

            dados_novos.append((offset_novo, tamanho_total_novo, tamanho_novo))

        # Atualiza headers
        f.seek(8)
        for idx in range(num_arquivos):
            f.seek(68, 1)  # Posiciona após nome e id
            f.write(struct.pack(endian + 'I', dados_novos[idx][2]))  # Tamanho comprimido
            if modo == "N/A":
                f.seek(4, 1)
            else:
                f.write(struct.pack(endian + 'I', dados_novos[idx][1]))  # Tamanho original
            f.write(struct.pack(endian + 'I', dados_novos[idx][0]))  # Offset

    messagebox.showinfo("Sucesso", f"{arquivo_arc} remontado com sucesso")


def escolher_arquivo():
    caminho = filedialog.askopenfilename(filetypes=[("Arquivos ARC", "*.arc")])
    if caminho:
        extrair_arc(caminho)

def escolher_arquivo_remontar():
    caminho = filedialog.askopenfilename(filetypes=[("Arquivos ARC", "*.arc")])
    if caminho:
        recriar_arc(caminho)
