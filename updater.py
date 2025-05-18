import os
import sys
import requests
import tkinter as tk
from tkinter import messagebox

# Configuração do repositório GitHub
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/TicoDoido/all_for_one/main"

# Arquivos principais e plugins a serem verificados
FILES = ["ALL_FOR_ONE.py"]
PLUGIN_DIR = "plugins"

# Baixa conteúdo bruto (bytes) do GitHub raw
def baixar_arquivo_bytes(url):
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return r.content
    except Exception:
        pass
    return None

# Atualiza um arquivo local se o conteúdo for diferente do remoto
def atualizar_arquivo(local_path, remote_path):
    url = f"{GITHUB_RAW_BASE}/{remote_path}"
    conteudo_remoto = baixar_arquivo_bytes(url)
    if conteudo_remoto is None:
        return False
    # Lê conteúdo local como bytes, se existir
    conteudo_local = None
    if os.path.exists(local_path):
        with open(local_path, 'rb') as f:
            conteudo_local = f.read()
    # Compara bytes diretamente
    if conteudo_local != conteudo_remoto:
        os.makedirs(os.path.dirname(local_path) or '.', exist_ok=True)
        # Escreve novo conteúdo em modo binário para preservar quebras
        with open(local_path, 'wb') as f:
            f.write(conteudo_remoto)
        print(f"Atualizado: {local_path}")
        return True
    return False

# Verifica e atualiza todos os arquivos e plugins

def verificar_atualizacoes():
    atualizados = []
    # Arquivos principais
    for f in FILES:
        if atualizar_arquivo(f, f):
            atualizados.append(f)
    # Plugins
    if os.path.isdir(PLUGIN_DIR):
        for fn in os.listdir(PLUGIN_DIR):
            if fn.endswith('.py'):
                local = os.path.join(PLUGIN_DIR, fn)
                remote = f"{PLUGIN_DIR}/{fn}"
                if atualizar_arquivo(local, remote):
                    atualizados.append(local)
    return atualizados

# Ponto de partida: executa atualização e depois o programa principal
if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()
    atualizados = verificar_atualizacoes()
    if atualizados:
        messagebox.showinfo("Atualização", "Os seguintes arquivos foram atualizados:\n" +
                            "\n".join(atualizados) + "\nReinicie o programa.")
        sys.exit(0)
    root.destroy()
    # Se não houve atualizações, executa o main
    os.execv(sys.executable, [sys.executable, "ALL_FOR_ONE.py"])