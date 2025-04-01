import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
import importlib.util
import importlib
import sys

def load_plugin(plugin_name, plugin_dir="plugins"):
    """Carrega ou recarrega um plugin específico no momento da seleção."""
    original_dont_write_bytecode = sys.dont_write_bytecode  # Salva o estado original
    sys.dont_write_bytecode = True  # Desativa a criação de .pyc
    
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
            return module.register_plugin()
        else:
            messagebox.showerror("Erro", f"O plugin '{plugin_name}' não possui a função 'register_plugin'.")
            return None
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao carregar plugin '{plugin_name}': {e}")
        return None

def get_plugins_mapping(plugin_dir="plugins"):
    mapping = {}
    if not os.path.exists(plugin_dir):
        os.makedirs(plugin_dir)
    for filename in os.listdir(plugin_dir):
        if filename.endswith(".py"):
            file_plugin_name = filename[:-3]
            plugin_data = load_plugin(file_plugin_name, plugin_dir)
            if plugin_data and "name" in plugin_data:
                mapping[plugin_data["name"]] = file_plugin_name
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
    global text_log
    root = tk.Tk()
    root.title("All For One - Gerenciador de PLUGINS para JOGOS")
    root.geometry("700x600")
    root.configure(bg="#2c3e50")

    style = ttk.Style()
    style.configure("TButton", font=("Arial", 12), padding=6)
    style.configure("TLabel", font=("Arial", 12), background="#2c3e50", foreground="white")

    plugins_mapping = get_plugins_mapping()
    plugin_display_names = list(plugins_mapping.keys())

    title_label = ttk.Label(root, text="Selecione um Plugin", font=("Arial", 16, "bold"))
    title_label.pack(pady=10)

    plugin_selector = ttk.Combobox(root, values=plugin_display_names, state="readonly", width=60)
    plugin_selector.set("Selecione um plugin")
    plugin_selector.pack(pady=10)

    def load_selected_plugin():
        selected_display_name = plugin_selector.get()
        if not selected_display_name:
            messagebox.showwarning("Atenção", "Selecione um plugin para carregar.")
            return

        plugin_file_name = plugins_mapping.get(selected_display_name)
        if not plugin_file_name:
            messagebox.showerror("Erro", f"Plugin '{selected_display_name}' não encontrado.")
            return

        log_message(f"Carregando plugin '{selected_display_name}'...")

        for widget in commands_frame.winfo_children():
            widget.destroy()

        selected_plugin = load_plugin(plugin_file_name)
        if selected_plugin:
            log_message(f"Plugin '{selected_display_name}' carregado com sucesso.")
            label = ttk.Label(commands_frame, text=selected_plugin["description"], font=("Arial", 12, "bold"), wraplength=680)
            label.pack(pady=10)
            for command in selected_plugin["commands"]:
                button = ttk.Button(commands_frame, text=command["label"], command=command["action"])
                button.pack(pady=5)
        else:
            log_message(f"Erro: Falha ao carregar '{selected_display_name}'.")

    load_button = ttk.Button(root, text="Carregar Plugin", command=load_selected_plugin)
    load_button.pack(pady=10)

    commands_frame = tk.Frame(root, bg="#34495e", padx=10, pady=10)
    commands_frame.pack(fill="both", expand=True, pady=10)

    text_log = scrolledtext.ScrolledText(root, wrap=tk.WORD, state=tk.DISABLED, height=10, bg="#ecf0f1", font=("Arial", 10))
    text_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()
