import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
import importlib.util
import importlib
import sys

# Variáveis globais para armazenar opções de radio
global radio_vars
radio_vars = {}

# Função de registro de logs
def log_message(message):
    global text_log
    if text_log:
        text_log.config(state=tk.NORMAL)
        text_log.insert(tk.END, message + '\n')
        text_log.config(state=tk.DISABLED)
        text_log.see(tk.END)
    else:
        print(message)


def load_plugin(plugin_name, plugin_dir="plugins"):
    original_write = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    plugin_path = os.path.join(plugin_dir, f"{plugin_name}.py")

    if not os.path.exists(plugin_path):
        messagebox.showerror("Erro", f"Plugin '{plugin_name}' não encontrado.")
        sys.dont_write_bytecode = original_write
        return None

    try:
        if plugin_name in sys.modules:
            del sys.modules[plugin_name]

        spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        sys.dont_write_bytecode = original_write

        if hasattr(module, "register_plugin"):
            def get_option(name):
                var = radio_vars.get(name)
                return var.get() if var else None

            plugin = module.register_plugin(log_message, get_option)
            for opt in plugin.get("options", []):
                name = opt["name"]
                values = opt.get("values", [])
                radio_vars[name] = tk.StringVar(value=values[0] if values else "")
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


def main():
    global text_log
    root = tk.Tk()
    root.title("All For One - Gerenciador de PLUGINS para jogos 🎮")
    root.geometry("900x600")
    root.configure(bg="#1f2937")  # fundo escuro

    # Tema clean e moderno
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('Header.TLabel', font=('Helvetica', 20, 'bold'), background='#1f2937', foreground='#ffffff')
    style.configure('TButton', font=('Helvetica', 12, 'bold'), padding=8)
    style.map('TButton', background=[('active', '#10b981')], foreground=[('active', '#ffffff')])
    style.configure('TFrame', background='#374151')
    style.configure('TLabel', background='#374151', foreground='#e5e7eb', font=('Helvetica', 12))
    style.configure('TRadiobutton', background='#374151', foreground='#e5e7eb', font=('Helvetica', 11))

    # Header\    
    header = ttk.Frame(root)
    header.pack(fill='x', pady=(10,0))
    ttk.Label(header, text="ALL FOR ONE ☄️", style='Header.TLabel').pack(side='left', padx=20)

    # Seletor de plugin\    
    selector_frame = ttk.Frame(root)
    selector_frame.pack(fill='x', pady=15, padx=20)
    ttk.Label(selector_frame, text="Selecione um Plugin:").pack(side='left')
    plugin_selector = ttk.Combobox(selector_frame, font=('Helvetica', 11), state='readonly', width=50)
    plugins_mapping = get_plugins_mapping()
    plugin_selector['values'] = list(plugins_mapping.keys())
    plugin_selector.set('Clique e escolha')
    plugin_selector.pack(side='left', padx=10)
    ttk.Button(selector_frame, text="Carregar ⚡️", command=lambda: load_selected_plugin()).pack(pady=10, padx=10)

    # Área de comandos
    commands_container = ttk.Frame(root, relief='ridge')
    commands_container.pack(fill='both', expand=True, padx=20, pady=10)

    # Log\    
    log_frame = ttk.Frame(root)
    log_frame.pack(fill='x', padx=20, pady=(0,20))
    text_log = scrolledtext.ScrolledText(log_frame, height=5, font=('Helvetica', 11))
    text_log.pack(fill='x')

    def load_selected_plugin():
        sel = plugin_selector.get()
        if not sel or sel == 'Clique e escolha':
            messagebox.showwarning("Atenção", "Selecione um plugin.")
            return
        for w in commands_container.winfo_children():
            w.destroy()

        plugin = load_plugin(plugins_mapping[sel])
        if not plugin:
            return

        # Descrição\        
        ttk.Label(commands_container, text=plugin['description'], wraplength=800).pack(pady=10, padx=10)

        # Opções\        
        for opt in plugin.get('options', []):
            f = ttk.Frame(commands_container)
            f.pack(fill='x', pady=5, padx=10)
            ttk.Label(f, text=opt['label']).pack(side='left')
            var = radio_vars.get(opt['name'])
            for val in opt.get('values', []):
                ttk.Radiobutton(f, text=val, variable=var, value=val).pack(side='left', padx=8)

        # Botões em grid 2x
        btn_frame = ttk.Frame(commands_container)
        btn_frame.pack(pady=15, padx=10, fill='x')
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        for idx, cmd in enumerate(plugin.get('commands', [])):
            r = idx // 2
            c = idx % 2
            b = ttk.Button(btn_frame, text=cmd['label'], command=cmd['action'])
            b.grid(row=r, column=c, padx=10, pady=8, sticky='nsew')

    root.mainloop()

if __name__ == '__main__':
    main()
