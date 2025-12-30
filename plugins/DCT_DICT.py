import struct
import os
import re
import threading
from tkinter import filedialog, messagebox, ttk, Label, Button

# Translation dictionaries for the plugin
plugin_translations = {
    "pt_BR": {
        "plugin_name": "DCT/DICT - Extrator e Reinseridor de Texto",
        "plugin_description": "Extrai e reinsere textos de arquivos DCT/DICT",
        "extract_texts": "Extrair Textos",
        "reinsert_texts": "Reinserir Textos",
        "select_binary_file": "Selecione o arquivo binário",
        "select_dct_file": "Selecione o arquivo .dct",
        "binary_files": "Arquivos Binários",
        "dct_files": "Arquivos DCT",
        "all_files": "Todos os arquivos",
        "extraction_completed": "Extração finalizada!\n\nTextos extraídos: {count}\nArquivo salvo em:\n{path}",
        "reinsertion_completed": "Reinserção concluída com sucesso!\n\nPonteiros atualizados: {count}\nArquivo gerado:\n{path}",
        "txt_file_not_found": "Arquivo TXT correspondente não encontrado:\n{path}",
        "no_valid_pointers": "Nenhum ponteiro válido encontrado",
        "unexpected_error": "Erro inesperado: {error}",
        "auto": "Auto (UTF-8 → CP1252)",
        "utf8": "UTF-8",
        "cp1252": "CP1252 (Windows)",
        "extract_encoding": "Codificação de Extração",
        "reinsert_encoding": "Codificação de Reinserção"
    },
    "en_US": {
        "plugin_name": "DCT/DICT - Text Extractor and Reinserter",
        "plugin_description": "Extracts and reinserts texts from DCT/DICT files",
        "extract_texts": "Extract Texts",
        "reinsert_texts": "Reinsert Texts",
        "select_binary_file": "Select binary file",
        "select_dct_file": "Select .dct file",
        "binary_files": "Binary Files",
        "dct_files": "DCT Files",
        "all_files": "All files",
        "extraction_completed": "Extraction completed!\n\nTexts extracted: {count}\nFile saved at:\n{path}",
        "reinsertion_completed": "Reinsertion completed successfully!\n\nPointers updated: {count}\nFile generated:\n{path}",
        "txt_file_not_found": "Corresponding TXT file not found:\n{path}",
        "no_valid_pointers": "No valid pointers found",
        "unexpected_error": "Unexpected error: {error}",
        "auto": "Auto (UTF-8 → CP1252)",
        "utf8": "UTF-8",
        "cp1252": "CP1252 (Windows)",
        "extract_encoding": "Extraction Encoding",
        "reinsert_encoding": "Reinsertion Encoding"
    },
    "es_ES": {
        "plugin_name": "DCT/DICT - Extractor y Reinsertador de Texto",
        "plugin_description": "Extrae y reinserta textos de archivos DCT/DICT",
        "extract_texts": "Extraer Textos",
        "reinsert_texts": "Reinsertar Textos",
        "select_binary_file": "Seleccionar archivo binario",
        "select_dct_file": "Seleccionar archivo .dct",
        "binary_files": "Archivos Binarios",
        "dct_files": "Archivos DCT",
        "all_files": "Todos los archivos",
        "extraction_completed": "¡Extracción finalizada!\n\nTextos extraídos: {count}\nArchivo guardado en:\n{path}",
        "reinsertion_completed": "¡Reinserción completada con éxito!\n\nPunteros actualizados: {count}\nArchivo generado:\n{path}",
        "txt_file_not_found": "Archivo TXT correspondiente no encontrado:\n{path}",
        "no_valid_pointers": "No se encontraron punteros válidos",
        "unexpected_error": "Error inesperado: {error}",
        "auto": "Auto (UTF-8 → CP1252)",
        "utf8": "UTF-8",
        "cp1252": "CP1252 (Windows)",
        "extract_encoding": "Codificación de Extracción",
        "reinsert_encoding": "Codificación de Reinserción"
    }
}

# Plugin global variables
logger = print
current_language = "pt_BR"
get_option = lambda name: None

def translate(key, **kwargs):
    """Internal plugin translation function"""
    lang_dict = plugin_translations.get(current_language, plugin_translations["pt_BR"])
    translation = lang_dict.get(key, key)
    
    if kwargs:
        try:
            return translation.format(**kwargs)
        except:
            return translation
    return translation

def register_plugin(log_func, option_getter, host_language="pt_BR"):
    global logger, current_language, get_option
    logger = log_func or print
    current_language = host_language
    get_option = option_getter or (lambda name: None)
    
    def get_plugin_info():
        return {
            "name": translate("plugin_name"),
            "description": translate("plugin_description"),
            "options": [
                {
                    "name": "extract_encoding",
                    "label": translate("extract_encoding"),
                    "values": ["utf-8","cp1252"]
                },
                {
                    "name": "reinsert_encoding",
                    "label": translate("reinsert_encoding"),
                    "values": ["utf-8", "cp1252"]
                }
            ],
            "commands": [
                {"label": translate("extract_texts"), "action": extract_texts},
                {"label": translate("reinsert_texts"), "action": reinsert_texts},
            ]
        }
    
    return get_plugin_info

def decode_texto(bytes_data, encoding_choice):
    """Decodifica bytes segundo a escolha do usuário."""
    if encoding_choice == translate("utf8"):
        return bytes_data.decode("utf-8", errors="ignore")
    elif encoding_choice == translate("cp1252"):
        return bytes_data.decode("cp1252", errors="ignore")
    else:
        # Fallback padrão
        try:
            return bytes_data.decode("utf-8", errors="ignore")
        except Exception:
            return bytes_data.decode("cp1252", errors="ignore")

def encode_texto(text, encoding_choice):
    """Codifica texto para bytes segundo a escolha do usuário."""
    if encoding_choice == translate("utf8"):
        return text.encode("utf-8", errors="ignore")
    elif encoding_choice == translate("cp1252"):
        return text.encode("cp1252", errors="ignore")
    else:
        # Fallback padrão
        return text.encode("cp1252", errors="ignore")

def ler_textos_do_txt(caminho_txt):
    reinsert_encoding = get_option("reinsert_encoding")
    """Lê o .txt com codificação UTF-8 e retorna mapping {idx: text}."""
    with open(caminho_txt, "r", encoding=reinsert_encoding, errors="ignore") as f:
        content = f.read()

    pattern = re.compile(r"====\s*Texto\s*(\d+)\s*====\s*\r?\n", re.IGNORECASE)
    parts = []
    mapping = {}

    for m in pattern.finditer(content):
        idx = int(m.group(1))
        if parts:
            prev_idx, prev_start = parts[-1]
            block_text = content[prev_start:m.start()]
            mapping[prev_idx] = block_text.rstrip("\r\n")
        parts.append((idx, m.end()))

    if parts:
        last_idx, last_pos = parts[-1]
        mapping[last_idx] = content[last_pos:].rstrip("\r\n")

    return mapping

def extract_texts():
    caminho = filedialog.askopenfilename(
        title=translate("select_binary_file"),
        filetypes=[(translate("binary_files"), "*.*")]
    )
    if not caminho:
        return

    def extraction_thread():
        try:
            extract_encoding = get_option("extract_encoding")
            if extract_encoding is None:
                extract_encoding = translate("auto")
            
            with open(caminho, "rb") as f:
                inicio_ponteiros = 0x14
                f.seek(24)
                inicio_textos = struct.unpack("<I", f.read(4))[0] + 25
                pointer_block_size = inicio_textos - inicio_ponteiros

                textos = []
                idx_logico = 1
                f.seek(inicio_ponteiros)
                pos_atual = f.tell()
                
                while pos_atual < inicio_textos:
                    chunk = f.read(4)
                    id_bin = struct.unpack("<I", chunk)[0]

                    if id_bin == 0:
                        continue
                    
                    pos_atual = f.tell()
                    if pos_atual >= inicio_textos:
                        break
                    
                    chunk_ptr = f.read(4)
                    ponteiro_rel = struct.unpack("<I", chunk_ptr)[0]
                    offset_texto = ponteiro_rel + pos_atual + 1
                    pos_atual += 4

                    f.seek(offset_texto)
                    texto_bytes = bytearray()

                    while True:
                        b = f.read(1)
                        if not b or b == b"\x00":
                            break
                        texto_bytes += b

                    texto = decode_texto(bytes(texto_bytes), extract_encoding)
                    texto = texto.replace("\r\n", "\\r\\n").replace("\n", "\\n")
                    textos.append(f"==== Texto {idx_logico} ====\n{texto}")
                    idx_logico += 1
                    f.seek(pos_atual)

            nome_saida = os.path.splitext(caminho)[0] + ".txt"
            with open(nome_saida, "w", encoding="utf-8", errors="ignore") as out:
                out.write("\n".join(textos))

            messagebox.showinfo(
                translate("completed"),
                translate("extraction_completed", count=len(textos), path=nome_saida)
            )
        except Exception as e:
            messagebox.showerror(
                translate("error"),
                translate("unexpected_error", error=str(e))
            )
    
    threading.Thread(target=extraction_thread, daemon=True).start()

def reinsert_texts():
    caminho_bin = filedialog.askopenfilename(
        title=translate("select_dct_file"),
        filetypes=[(translate("dct_files"), "*.dct"), (translate("all_files"), "*.*")]
    )
    if not caminho_bin:
        return

    caminho_txt = os.path.splitext(caminho_bin)[0] + ".txt"
    if not os.path.exists(caminho_txt):
        messagebox.showerror(
            translate("error"),
            translate("txt_file_not_found", path=caminho_txt)
        )
        return

    def reinsertion_thread():
        try:
            reinsert_encoding = get_option("reinsert_encoding")
            if reinsert_encoding is None:
                reinsert_encoding = translate("cp1252")
            
            textos_map = ler_textos_do_txt(caminho_txt)
            textos_map = {int(k): v for k, v in textos_map.items()}
            inicio_ponteiros = 0x14

            with open(caminho_bin, "rb") as f:
                f.seek(24)
                inicio_textos = struct.unpack("<I", f.read(4))[0] + 25
                pointer_block_size = inicio_textos - inicio_ponteiros
                ponteiros = []
                f.seek(inicio_ponteiros)
                pos_atual = f.tell()
                
                while pos_atual < inicio_textos:
                    id_bin = struct.unpack("<I", f.read(4))[0]
                    if id_bin == 0:
                        continue
                    entry_pos = f.tell()
                    if entry_pos >= inicio_textos:
                        break
                    ponteiro_rel = struct.unpack("<I", f.read(4))[0]
                    ponteiros.append(entry_pos)
                    pos_atual = f.tell()

                if not ponteiros:
                    messagebox.showerror(
                        translate("error"),
                        translate("no_valid_pointers")
                    )
                    return

            novo_nome = os.path.splitext(caminho_bin)[0] + "_MOD" + os.path.splitext(caminho_bin)[1]

            with open(caminho_bin, "rb") as src, open(novo_nome, "wb") as dst:
                src.seek(0)
                dst.write(src.read(inicio_textos))
                absolute_offsets = []
                cur_offset = inicio_textos

                for i in range(len(ponteiros)):
                    absolute_offsets.append(cur_offset)
                    texto = textos_map.get(i + 1, "")
                    texto = texto.replace("\\r\\n", "\r\n").replace("\\n", "\n")
                    texto_bytes = encode_texto(texto, reinsert_encoding) + b"\x00"
                    dst.write(texto_bytes)
                    cur_offset += len(texto_bytes)

            with open(novo_nome, "r+b") as f:
                for i, (entry_pos) in enumerate(ponteiros):
                    absolute_offset = absolute_offsets[i]
                    ponteiro_rel_new = absolute_offset - entry_pos - 1
                    f.seek(entry_pos)
                    f.write(struct.pack("<I", ponteiro_rel_new))

            messagebox.showinfo(
                translate("completed"),
                translate("reinsertion_completed", count=len(ponteiros), path=novo_nome)
            )
        except Exception as e:
            messagebox.showerror(
                translate("error"),
                translate("unexpected_error", error=str(e))
            )
    
    threading.Thread(target=reinsertion_thread, daemon=True).start()