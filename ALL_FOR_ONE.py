import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
import importlib.util
import sys

# Verifica e instala automaticamente o módulo 'requests' se não estiver disponível
try:
    import requests
except ImportError:
    import subprocess
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests'])
        import requests
        messagebox.showinfo("Instalação", "Dependência 'requests' instalada com sucesso.")
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao instalar 'requests': {e}")
        sys.exit(1)

# Configuração para atualização automática
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/TicoDoido/all_for_one/main"

def baixar_arquivo(url):
    """Baixa o conteúdo de um arquivo no GitHub raw."""
    try:
        resposta = requests.get(url)
        if resposta.status_code == 200:
            return resposta.text
    except Exception as e:
        print(f"Erro ao baixar {url}: {e}")
    return None


def atualizar_arquivo_if_needed(local_path, github_url):
    """Compara e atualiza o arquivo local se houver diferença no repositório."""
    conteudo_remoto = baixar_arquivo(github_url)
    if conteudo_remoto is None:
        return False

    # Se o arquivo existir, compara
    if os.path.exists(local_path):
        with open(local_path, 'r', encoding='utf-8') as f:
            conteudo_local = f.read()
        if conteudo_local == conteudo_remoto:
            return False  # Sem mudanças
    else:
        # Cria diretórios necessários
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

    # Escreve nova versão
    with open(local_path, 'w', encoding='utf-8') as f:
        f.write(conteudo_remoto)
    print(f"Arquivo atualizado: {local_path}")
    return True


def verificar_e_atualizar_arquivos():
    """Verifica todos os arquivos principais e plugins e atualiza automaticamente."""
    arquivos = ["ALL_FOR_ONE.py"]
    plugin_dir = "plugins"
    if os.path.isdir(plugin_dir):
        for file in os.listdir(plugin_dir):
            if file.endswith(".py"):
                arquivos.append(os.path.join(plugin_dir, file))

    atualizou = False
    for caminho in arquivos:
        url = f"{GITHUB_RAW_BASE}/{caminho}"
        if atualizar_arquivo_if_needed(caminho, url):
            atualizou = True

    if atualizou:
        messagebox.showinfo("Atualização", "Arquivos atualizados! Reinicie o programa.")
        sys.exit(0)

# Variáveis globais para armazenar opções de radio
global radio_vars
radio_vars = {}


def load_plugin(plugin_name, plugin_dir="plugins"):
    """Carrega ou recarrega um plugin específico no momento da seleção."""
    original_dont_write_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True

    plugin_path = os.path.join(plugin_dir, f"{plugin_name}.py")
    if not os.path.exists(plugin_path):
        messagebox.showerror("Erro", f"Plugin '{plugin_name}' não encontrado.")
        return None

    try:
        if plugin_name in sys.modules:
            del sys.modules[plugin_name]

        spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        sys.dont_write_bytecode = original_dont_write_bytecode

        if hasattr(module, "register_plugin"):
            def get_option(name):
                var = radio_vars.get(name)
                return var.get() if var else None

            plugin = module.register_plugin(log_message, get_option)

            # Inicializa variáveis de radio se fornecidas pelo plugin
            for opt in plugin.get("options", []):
                name = opt["name"]
                values = opt.get("values", [])
                var = tk.StringVar(value=values[0] if values else "")
                radio_vars[name] = var
            return plugin
        else:
            messagebox.showerror("Erro", f"O plugin '{plugin_name}' não possui register_plugin.")
            return None
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao carregar plugin '{plugin_name}': {e}")
        return None


def get_plugins_mapping(plugin_dir="plugins"):
    mapping = {}
    if not os.path.exists(plugin_dir):
        os.makedirs(plugin_dir)
    for filename in os.listdir(plugin_dir):
        if filename.endswith(".py"):
            data = load_plugin(filename[:-3], plugin_dir)
            if data and "name" in data:
                mapping[data["name"]] = filename[:-3]
    return mapping


def log_message(message):
    global text_log
    if text_log:
        text_log.config(state=tk.NORMAL)
        text_log.insert(tk.END, message + '\n')
        text_log.config(state=tk.DISABLED)
        text_log.see(tk.END)
    else:
        print(message)


def main():
    # Verifica e atualiza antes de iniciar a interface
    verificar_e_atualizar_arquivos()

    global text_log
    root = tk.Tk()
    root.title("All For One - Gerenciador de PLUGINS para JOGOS")
    root.geometry("700x600")
    root.configure(bg="#2c3e50")

    style = ttk.Style()
    style.configure("TButton", font=("Arial", 12), padding=6)
    style.configure("TLabel", font=("Arial", 12), background="#2c3e50", foreground="white")

    plugins_mapping = get_plugins_mapping()
    plugin_names = list(plugins_mapping.keys())

    ttk.Label(root, text="Selecione um Plugin", font=("Arial", 16, "bold"), background="#2c3e50", foreground="white").pack(pady=10)

    plugin_selector = ttk.Combobox(root, values=plugin_names, state="readonly", width=60)
    plugin_selector.set("Selecione um plugin")
    plugin_selector.pack(pady=10)

    commands_frame = tk.Frame(root, bg="#34495e", padx=10, pady=10)
    commands_frame.pack(fill="both", expand=True, pady=10)

    text_log = scrolledtext.ScrolledText(root, wrap=tk.WORD, state=tk.DISABLED, height=10,
                                        bg="#ecf0f1", font=("Arial", 10))
    text_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def load_selected_plugin():
        sel = plugin_selector.get()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um plugin.")
            return
        plugin_file = plugins_mapping.get(sel)
        log_message(f"Carregando '{sel}'...\n")

        radio_vars.clear()
        for w in commands_frame.winfo_children():
            w.destroy()

        plugin = load_plugin(plugin_file)
        if not plugin:
            log_message(f"Falha ao carregar '{sel}'.\n")
            return

        log_message(f"Plugin '{sel}' carregado!\n")

        ttk.Label(commands_frame, text=plugin["description"], font=("Arial", 12, "bold"),
                  background="#34495e", foreground="white", wraplength=660).pack(pady=10)

        # Opções horizontais
        for opt in plugin.get("options", []):
            frame_opt = tk.Frame(commands_frame, bg="#34495e")
            frame_opt.pack(anchor='w', pady=(5,10), padx=10)
            ttk.Label(frame_opt, text=opt["label"], font=("Arial", 10, "bold"),
                      background="#34495e", foreground="white").pack(side=tk.LEFT)
            var = radio_vars[opt["name"]]
            for val in opt.get("values", []):
                ttk.Radiobutton(frame_opt, text=val, variable=var, value=val,
                                style="TRadiobutton").pack(side=tk.LEFT, padx=10)

        # Comandos
        for cmd in plugin.get("commands", []):
            ttk.Button(commands_frame, text=cmd["label"], command=cmd["action"]).pack(pady=5)

    ttk.Button(root, text="Carregar Plugin", command=load_selected_plugin).pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()
