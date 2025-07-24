import struct
import os
import threading
from tkinter import filedialog, messagebox, Button, Label

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

            total_itens = struct.unpack('<I', f.read(4))[0]
            total_itens = total_itens + 1
            posicoes = []
            tamanhos = []

            for _ in range(total_itens):
                pos, tamanho = struct.unpack('<II', f.read(8))
                posicoes.append(pos)
                tamanhos.append(tamanho)

            # Criar pasta de extração
            pasta_saida = os.path.join(os.path.dirname(arquivo_afs), os.path.splitext(os.path.basename(arquivo_afs))[0])
            os.makedirs(pasta_saida, exist_ok=True)

            for i, (pos, tamanho) in enumerate(zip(posicoes, tamanhos), 1):
                f.seek(pos)
                dados = f.read(tamanho)
                nome_arquivo = f"arquivo_{i:05d}.bin"
                logger(f"Extraindo {nome_arquivo}")
                caminho_saida = os.path.join(pasta_saida, nome_arquivo)
                with open(caminho_saida, 'wb') as saida:
                    saida.write(dados)

            messagebox.showinfo("Concluído", f"{total_itens} arquivos extraídos em:\n{pasta_saida}")
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro: {e}")

def selecionar_arquivo():
    caminho = filedialog.askopenfilename(
        title="Selecione um arquivo AFS",
        filetypes=[("Arquivos AFS", "*.afs"), ("Todos os arquivos", "*.*")]
    )
    if caminho:
        # Executa a extração em uma nova thread
        threading.Thread(target=extrair_afs, args=(caminho,), daemon=True).start()


