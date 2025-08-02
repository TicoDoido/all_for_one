import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
import importlib.util
import importlib
import sys

# Variáveis globais
global radio_vars, text_log, current_language, plugin_selector, commands_container
radio_vars = {}
current_language = "pt_BR"  # Idioma padrão

# Dicionários de tradução
translations = {
    "pt_BR": {
        "title": "All For One - Gerenciador de PLUGINS para jogos 🎮",
        "select_plugin": "Selecione um Plugin:",
        "click_to_choose": "Clique e escolha",
        "load": "Carregar ⚡️",
        "warning": "Atenção",
        "select_plugin_warning": "Selecione um plugin.",
        "error": "Erro",
        "plugin_not_found": "Plugin '{}' não encontrado.",
        "plugin_register_error": "O plugin '{}' não possui register_plugin.",
        "plugin_load_error": "Falha ao carregar plugin '{}': {}",
        "language": "Idioma:",
        "pt_BR": "Português (BR)",
        "en_US": "Inglês",
        "es_ES": "Espanhol"
        
    },
    "en_US": {
        "title": "All For One - Game PLUGINS Manager 🎮",
        "select_plugin": "Select a Plugin:",
        "click_to_choose": "Click to choose",
        "load": "Load ⚡️",
        "warning": "Warning",
        "select_plugin_warning": "Please select a plugin.",
        "error": "Error",
        "plugin_not_found": "Plugin '{}' not found.",
        "plugin_register_error": "Plugin '{}' doesn't have register_plugin.",
        "plugin_load_error": "Failed to load plugin '{}': {}",
        "language": "Language:",
        "pt_BR": "Portuguese (BR)",
        "en_US": "English",
        "es_ES": "Spanish"
        
    },
    "es_ES": {
        "title": "All For One - Administrador de PLUGINS para jogos 🎮",
        "select_plugin": "Selecciona un Plugin:",
        "click_to_choose": "Haz clic para elegir",
        "load": "Cargar ⚡️",
        "warning": "Advertencia",
        "select_plugin_warning": "Por favor selecciona un plugin.",
        "error": "Error",
        "plugin_not_found": "Plugin '{}' no encontrado.",
        "plugin_register_error": "El plugin '{}' no tiene register_plugin.",
        "plugin_load_error": "Error al cargar el plugin '{}': {}",
        "language": "Idioma:",
        "pt_BR": "Portugués (BR)",
        "en_US": "Inglés",
        "es_ES": "Español"
        
    }
}


def translate(key, *args):
    lang_dict = translations.get(current_language, translations["pt_BR"])
    value = lang_dict.get(key, key)
    if args:
        try:
            return value.format(*args)
        except Exception:
            return value
    return value


def change_language(new_lang):
    """Altera o idioma, atualiza UI e lista de plugins"""
    global current_language
    current_language = new_lang
    # Atualiza textos da interface
    root.title(translate("title"))
    plugin_label.config(text=translate("select_plugin"))
    load_button.config(text=translate("load"))
    lang_selector.set(current_language)

    # Atualiza lista de plugins no novo idioma
    plugins_mapping = get_plugins_mapping()
    plugin_selector['values'] = list(plugins_mapping.keys())
    plugin_selector.set(translate("click_to_choose"))

    # Limpa container de comandos
    for w in commands_container.winfo_children():
        w.destroy()


def log_message(message):
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
        messagebox.showerror(translate("error"), translate("plugin_not_found", plugin_name))
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
            plugin_getter = module.register_plugin(log_message, get_option, current_language)
            plugin = plugin_getter() if callable(plugin_getter) else plugin_getter
            for opt in plugin.get("options", []):
                radio_vars[opt["name"]] = tk.StringVar(value=opt.get("values", [""])[0])
            return plugin
        else:
            messagebox.showerror(translate("error"), translate("plugin_register_error", plugin_name))
            return None
    except Exception as e:
        messagebox.showerror(translate("error"), translate("plugin_load_error", plugin_name, str(e)))
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


def load_selected_plugin():
    global commands_container, plugin_selector
    sel = plugin_selector.get()
    if not sel or sel == translate("click_to_choose"):
        messagebox.showwarning(translate("warning"), translate("select_plugin_warning"))
        return
    # limpa área de comandos
    for w in commands_container.winfo_children():
        w.destroy()
    # recarrega mapeamento e mantém seleção
    plugins_mapping = get_plugins_mapping()
    plugin_selector['values'] = list(plugins_mapping.keys())
    if sel in plugins_mapping:
        plugin_selector.set(sel)
    else:
        plugin_selector.set(translate("click_to_choose"))
        return
    plugin = load_plugin(plugins_mapping[sel])
    if not plugin:
        return
    ttk.Label(commands_container, text=plugin['description'], wraplength=800).pack(pady=10, padx=10)
    for opt in plugin.get('options', []):
        frame = ttk.Frame(commands_container); frame.pack(fill='x', pady=5, padx=10)
        ttk.Label(frame, text=opt['label']).pack(side='left')
        for val in opt.get('values', []):
            ttk.Radiobutton(frame, text=val, variable=radio_vars[opt['name']], value=val).pack(side='left', padx=8)
    btn_frame = ttk.Frame(commands_container); btn_frame.pack(pady=15, padx=10, fill='x')
    btn_frame.columnconfigure(0, weight=1); btn_frame.columnconfigure(1, weight=1)
    for idx, cmd in enumerate(plugin.get('commands', [])):
        b = ttk.Button(btn_frame, text=cmd['label'], command=cmd['action'])
        b.grid(row=idx//2, column=idx%2, padx=10, pady=8, sticky='nsew')


def main():
    global text_log, plugin_label, plugin_selector, load_button, root, lang_selector, commands_container
    root = tk.Tk(); root.title(translate("title")); root.geometry("900x600"); root.configure(bg="#1f2937")
    style = ttk.Style(root); style.theme_use('clam')
    # configurações de estilo omitidas...
    header = ttk.Frame(root); header.pack(fill='x', pady=(10,0))
    ttk.Label(header, text="ALL FOR ONE ☄️", style='Header.TLabel').pack(side='left', padx=20)
    lang_frame = ttk.Frame(header); lang_frame.pack(side='right', padx=20)
    ttk.Label(lang_frame, text=translate("language")).pack(side='left')
    lang_selector = ttk.Combobox(lang_frame, values=list(translations.keys()), state='readonly')
    lang_selector.set(current_language); lang_selector.pack(side='left', padx=5)
    lang_selector.bind('<<ComboboxSelected>>', lambda e: change_language(lang_selector.get()))
    selector_frame = ttk.Frame(root); selector_frame.pack(fill='x', pady=15, padx=20)
    plugin_label = ttk.Label(selector_frame, text=translate("select_plugin")); plugin_label.pack(side='left')
    plugin_selector = ttk.Combobox(selector_frame, font=('Helvetica', 11), state='readonly', width=50)
    plugin_selector['values'] = list(get_plugins_mapping().keys())
    plugin_selector.set(translate("click_to_choose")); plugin_selector.pack(side='left', padx=10)
    load_button = ttk.Button(selector_frame, text=translate("load"), command=load_selected_plugin)
    load_button.pack(pady=10, padx=10)
    commands_container = ttk.Frame(root, relief='ridge'); commands_container.pack(fill='both', expand=True, padx=20, pady=10)
    log_frame = ttk.Frame(root); log_frame.pack(fill='x', padx=20, pady=(0,20))
    text_log = scrolledtext.ScrolledText(log_frame, height=5, font=('Helvetica', 11)); text_log.pack(fill='x')
    root.mainloop()

if __name__ == '__main__':
    main()
