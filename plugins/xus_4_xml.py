import os
import struct
import xml.etree.ElementTree as ET
import threading
from tkinter import filedialog, messagebox

# --- Localização ---
plugin_translations = {
    "pt_BR": {
        "plugin_name": "XUS Arquivos de Texto Xbox 360",
        "plugin_description": "Converte arquivos .xus para XML e reconverte de volta. Útil para localização de jogos.",
        "extract_text": "Extrair Texto em XML",
        "rebuild_file": "Recriar XUS com XML",
        "success_extract": "Arquivo XML salvo em: {path}",
        "success_rebuild": "Arquivo XUS salvo em: {path}",
        "error": "Erro",
    },
    "en_US": {
        "plugin_name": "XUS Xbox 360 Text Files",
        "plugin_description": "Converts .xus files to XML and back. Useful for game localization.",
        "extract_text": "Extract Text to XML",
        "rebuild_file": "Rebuild XUS from XML",
        "success_extract": "XML file saved at: {path}",
        "success_rebuild": "XUS file saved at: {path}",
        "error": "Error",
    },
    "es_ES": {
        "plugin_name": "Archivos de texto XUS Xbox 360",
        "plugin_description": "Convierte archivos .xus a XML y viceversa. Útil para localización de juegos.",
        "extract_text": "Extraer texto a XML",
        "rebuild_file": "Reconstruir XUS desde XML",
        "success_extract": "Archivo XML guardado en: {path}",
        "success_rebuild": "Archivo XUS guardado en: {path}",
        "error": "Error",
    }
}

current_language = "pt_BR"
def translate(key, **kwargs):
    return plugin_translations.get(current_language, {}).get(key, key).format(**kwargs)

logger = print
get_option = lambda name: None

def register_plugin(log_func, option_getter, host_language="pt_BR"):
    global logger, get_option, current_language
    logger = log_func or print
    get_option = option_getter or (lambda name: None)
    current_language = host_language

    return {
        "name": translate("plugin_name"),
        "description": translate("plugin_description"),
        "commands": [
            {"label": translate("extract_text"), "action": lambda: threading.Thread(target=select_file_for_xus).start()},
            {"label": translate("rebuild_file"), "action": lambda: threading.Thread(target=select_file_for_xml).start()},
        ]
    }

def get_magic_number_from_xus(file_path):
    with open(file_path, 'rb') as file:
        return file.read(6)

def convert_xus_to_xml(file_path, output_xml_path):
    try:
        with open(file_path, 'rb') as file:
            magic_number = file.read(6)
            valid_magic = [b'XUIS\x01\x02', b'XUIS\x01\x00']
            if magic_number not in valid_magic:
                raise ValueError("Invalid magic number")

            file.seek(10)
            num_items = struct.unpack('>H', file.read(2))[0]
            if magic_number == b'XUIS\x01\x00':
                num_items *= 2

            root = ET.Element("Root")
            for i in range(num_items):
                count = struct.unpack('>H', file.read(2))[0]
                text = file.read(count * 2).decode('utf-16-be').replace('\r\n', '[0D0A]')
                item = ET.Element(f"Item_{i+1}")
                item.text = text
                root.append(item)

        xml_str = ET.tostring(root, encoding='unicode', method='xml')
        xml_str = '\n' + xml_str.replace('><', '>\n<') + '\n'

        with open(output_xml_path, 'w', encoding='utf-8') as out:
            out.write(xml_str)

        messagebox.showinfo("OK", translate("success_extract", path=output_xml_path))
    except Exception as e:
        messagebox.showerror(translate("error"), str(e))

def xml_to_xus(xml_path, output_xus_path):
    try:
        original_path = xml_path.rsplit('.', 1)[0] + '.xus'
        original_magic = get_magic_number_from_xus(original_path)
        new_magic = b'XUIS\x01\x00' if original_magic == b'XUIS\x01\x00' else b'XUIS\x01\x02'

        tree = ET.parse(xml_path)
        root = tree.getroot()
        items_data = []

        for item in root:
            text = (item.text or '').replace('[0D0A]', '\r\n')
            text_bytes = text.encode('utf-16-be')
            count = len(text_bytes) // 2
            items_data.append(struct.pack('>H', count) + text_bytes)

        num_items = len(items_data)
        if original_magic == b'XUIS\x01\x00':
            num_items //= 2

        with open(output_xus_path, 'wb+') as file:
            file.write(new_magic)
            file.seek(10)
            file.write(struct.pack('>H', num_items))
            for item in items_data:
                file.write(item)
            file_size = file.tell()
            file.seek(6)
            file.write(struct.pack('>I', file_size))

        messagebox.showinfo("OK", translate("success_rebuild", path=output_xus_path))
    except Exception as e:
        messagebox.showerror(translate("error"), str(e))

def select_file_for_xus():
    path = filedialog.askopenfilename(filetypes=[("XUS files", "*.xus")])
    if path:
        output = path.rsplit('.', 1)[0] + '.xml'
        convert_xus_to_xml(path, output)

def select_file_for_xml():
    path = filedialog.askopenfilename(filetypes=[("XML files", "*.xml")])
    if path:
        output = path.rsplit('.', 1)[0] + '_novo.xus'
        xml_to_xus(path, output)
