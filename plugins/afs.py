import struct
import os
import threading
from tkinter import filedialog, messagebox
from collections import defaultdict

# Funções injetadas pelo host
logger = print
get_option = lambda name: None

def register_plugin(log_func, option_getter):
    global logger, get_option
    # Recebe do host a função de log e o getter de opções
    logger = log_func or print
    get_option = option_getter or (lambda name: None)

    return {
        "name": "AFS (PS2) Extrai e remonta arquivos",
        "description": "Extrai e recria arquivos AFS de Playstation 2",
        "commands": [
            {"label": "Extrair Arquivo", "action": selecionar_arquivo},
        ]
    }

def extrair_afs(arquivo_afs):
    try:
        with open(arquivo_afs, 'rb') as f:
            magic = f.read(4)
            if magic != b'AFS\x00':
                messagebox.showerror("Erro", "Arquivo inválido: Magic incorreto (esperado 'AFS\\x00').")
                return

            total_itens = struct.unpack('<I', f.read(4))[0] + 1

            posicoes = []
            tamanhos = []
            for _ in range(total_itens):
                pos, tamanho = struct.unpack('<II', f.read(8))
                posicoes.append(pos)
                tamanhos.append(tamanho)

            ponteiro_meta = f.read(8)
            nomes_grupos = []

            if len(ponteiro_meta) == 8:
                meta_offset, meta_size = struct.unpack('<II', ponteiro_meta)
                logger(f"Ponteiro da tabela de metadados encontrado: Offset={meta_offset}, Tamanho={meta_size}")

                if meta_offset > 0 and meta_size > 0:
                    f.seek(meta_offset)
                    for _ in range(total_itens):
                        meta_bloco = f.read(0x30) # Cada entrada tem 48 bytes
                        if len(meta_bloco) < 16:
                            nomes_grupos.append("")
                            continue
                        
                        nome_bytes = meta_bloco[:16]
                        try:
                            nome_limpo = nome_bytes.split(b'\x00', 1)[0].decode('shift_jis', errors='ignore').strip()
                        except:
                            nome_limpo = ""
                        nomes_grupos.append(nome_limpo)
                else:
                    logger("Ponteiro de metadados inválido ou nulo. Extraindo sem nomes de grupo.")
                    nomes_grupos = [""] * total_itens # Preenche com nomes vazios
            else:
                messagebox.showwarning("Aviso", "Não foi possível encontrar o ponteiro para a tabela de metadados. Extraindo sem nomes de grupo.")
                nomes_grupos = [""] * total_itens

            pasta_saida = os.path.join(os.path.dirname(arquivo_afs), os.path.splitext(os.path.basename(arquivo_afs))[0])
            os.makedirs(pasta_saida, exist_ok=True)
            
            contagem_sufixos = defaultdict(int)
            base_nome_afs = os.path.splitext(os.path.basename(arquivo_afs))[0]

            for i, (pos, tamanho, grupo) in enumerate(zip(posicoes, tamanhos, nomes_grupos)):
                if tamanho == 0:
                    continue

                f.seek(pos)
                dados = f.read(tamanho)
                
                if grupo:
                    pasta_grupo = os.path.join(pasta_saida, grupo)
                    os.makedirs(pasta_grupo, exist_ok=True)
                    
                    contagem_sufixos[grupo] += 1
                    nome_arquivo = f"{grupo}_{contagem_sufixos[grupo]:04d}.bin"
                    caminho_saida = os.path.join(pasta_grupo, nome_arquivo)
                    logger(f"Extraindo para o grupo '{grupo}': {nome_arquivo}")
                else:
                    contagem_sufixos['__root__'] += 1
                    nome_arquivo = f"{base_nome_afs}_{contagem_sufixos['__root__']:05d}.bin"
                    caminho_saida = os.path.join(pasta_saida, nome_arquivo)
                    logger(f"Extraindo para a raiz: {nome_arquivo}")

                with open(caminho_saida, 'wb') as saida:
                    saida.write(dados)

            messagebox.showinfo("Concluído", f"Extração de {total_itens} arquivos concluída em:\n{pasta_saida}")
    except FileNotFoundError:
        messagebox.showerror("Erro", f"Arquivo não encontrado: {arquivo_afs}")
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro inesperado: {e}")
        logger(f"Erro detalhado: {e}")


def selecionar_arquivo():
    caminho = filedialog.askopenfilename(
        title="Selecione um arquivo AFS",
        filetypes=[("Arquivos AFS", "*.afs"), ("Todos os arquivos", "*.*")]
    )
    if caminho:
        # Executa a extração em uma nova thread
        threading.Thread(target=extrair_afs, args=(caminho,), daemon=True).start()
        