# Originalmente feito por Denis Moreno
# Golden Axe Beast Rider PS3 USM
import struct
import re
import threading
from pathlib import Path
from tkinter import filedialog, messagebox, ttk, Label, Button
from typing import List, Dict, Any, Tuple, Optional

# Translation dictionaries for the plugin
plugin_translations = {
    "pt_BR": {
        "plugin_name": "USM - Editor de Legendas",
        "plugin_description": "Extrai e reinsere legendas de arquivos USM/SFD (vídeos CRI Middleware)",
        "extract_subtitles": "Extrair Legendas",
        "reinsert_subtitles": "Reinserir Legendas",
        "select_usm_file": "Selecione o arquivo .sfd/.usm",
        "select_txt_file": "Selecione o arquivo de legendas .txt",
        "usm_files": "Arquivos USM/SFD",
        "text_files": "Arquivos de Texto",
        "all_files": "Todos os arquivos",
        "import_success": "Importadas {count} entradas de {file}. (contexto mantido em memória)",
        "export_success": "Reconstrução concluída. Arquivo salvo como: {file} (Δ {delta} bytes).",
        "no_sbt_blocks": "Nenhum bloco @SBT encontrado em {file}.",
        "no_valid_subtitles": "Nenhuma legenda válida foi extraída de {file}.",
        "context_not_found": "Erro: contexto não encontrado em memória. Reabra o arquivo original na interface antes de exportar.",
        "row_count_mismatch": "Erro: número de linhas fornecidas ({provided}) não corresponde ao número de entradas esperadas ({expected}).",
        "file_read_error": "Erro ao ler {file}: {error}",
        "file_write_error": "Erro ao salvar arquivo reconstruído: {error}",
        "time_format_error": "Erro ao processar formato de tempo",
        "unexpected_error": "Erro inesperado: {error}",
        "completed": "Concluído",
        "error": "Erro",
        "progress_title_extract": "Extraindo Legendas",
        "progress_title_reinsert": "Reinserindo Legendas",
        "cancel_button": "Cancelar",
        "subtitles_extracted": "Legendas extraídas: {count}",
        "file_saved": "Arquivo salvo em: {path}",
        "reconstruction_completed": "Reconstrução concluída",
        "choose_original_file": "Selecione o arquivo original .sfd/.usm"
    },
    "en_US": {
        "plugin_name": "USM - Subtitle Editor",
        "plugin_description": "Extracts and reinserts subtitles from USM/SFD files (CRI Middleware videos)",
        "extract_subtitles": "Extract Subtitles",
        "reinsert_subtitles": "Reinsert Subtitles",
        "select_usm_file": "Select .sfd/.usm file",
        "select_txt_file": "Select subtitle .txt file",
        "usm_files": "USM/SFD Files",
        "text_files": "Text Files",
        "all_files": "All files",
        "import_success": "Imported {count} entries from {file}. (context kept in memory)",
        "export_success": "Reconstruction completed. File saved as: {file} (Δ {delta} bytes).",
        "no_sbt_blocks": "No @SBT blocks found in {file}.",
        "no_valid_subtitles": "No valid subtitles were extracted from {file}.",
        "context_not_found": "Error: context not found in memory. Reopen the original file in the interface before exporting.",
        "row_count_mismatch": "Error: number of provided lines ({provided}) does not match expected entries ({expected}).",
        "file_read_error": "Error reading {file}: {error}",
        "file_write_error": "Error saving reconstructed file: {error}",
        "time_format_error": "Error processing time format",
        "unexpected_error": "Unexpected error: {error}",
        "completed": "Completed",
        "error": "Error",
        "progress_title_extract": "Extracting Subtitles",
        "progress_title_reinsert": "Reinserting Subtitles",
        "cancel_button": "Cancel",
        "subtitles_extracted": "Subtitles extracted: {count}",
        "file_saved": "File saved at: {path}",
        "reconstruction_completed": "Reconstruction completed",
        "choose_original_file": "Select original .sfd/.usm file"
    },
    "es_ES": {
        "plugin_name": "USM - Editor de Subtítulos",
        "plugin_description": "Extrae y reinserta subtítulos de archivos USM/SFD (vídeos CRI Middleware)",
        "extract_subtitles": "Extraer Subtítulos",
        "reinsert_subtitles": "Reinsertar Subtítulos",
        "select_usm_file": "Seleccionar archivo .sfd/.usm",
        "select_txt_file": "Seleccionar archivo de subtítulos .txt",
        "usm_files": "Archivos USM/SFD",
        "text_files": "Archivos de Texto",
        "all_files": "Todos los archivos",
        "import_success": "Importadas {count} entradas de {file}. (contexto mantenido en memoria)",
        "export_success": "Reconstrucción completada. Archivo guardado como: {file} (Δ {delta} bytes).",
        "no_sbt_blocks": "No se encontraron bloques @SBT en {file}.",
        "no_valid_subtitles": "No se extrajeron subtítulos válidos de {file}.",
        "context_not_found": "Error: contexto no encontrado en memoria. Vuelva a abrir el archivo original en la interfaz antes de exportar.",
        "row_count_mismatch": "Error: número de líneas proporcionadas ({provided}) no coincide con las entradas esperadas ({expected}).",
        "file_read_error": "Error al leer {file}: {error}",
        "file_write_error": "Error al guardar archivo reconstruido: {error}",
        "time_format_error": "Error al procesar formato de tiempo",
        "unexpected_error": "Error inesperado: {error}",
        "completed": "Completado",
        "error": "Error",
        "progress_title_extract": "Extrayendo Subtítulos",
        "progress_title_reinsert": "Reinsertando Subtítulos",
        "cancel_button": "Cancelar",
        "subtitles_extracted": "Subtítulos extraídos: {count}",
        "file_saved": "Archivo guardado en: {path}",
        "reconstruction_completed": "Reconstrucción completada",
        "choose_original_file": "Seleccionar archivo original .sfd/.usm"
    }
}

# Plugin global variables
logger = print
current_language = "pt_BR"
get_option = lambda name: None

# Global storage for contexts (not saved to disk)
_contexts: Dict[str, Dict[str, Any]] = {}
_last_imported: Optional[str] = None

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
            "commands": [
                {"label": translate("extract_subtitles"), "action": extract_subtitles},
                {"label": translate("reinsert_subtitles"), "action": reinsert_subtitles},
            ]
        }
    
    return get_plugin_info

class ProgressWindow:
    def __init__(self, parent, title, total):
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("400x120")
        self.window.resizable(False, False)
        self.window.grab_set()
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.window, 
            variable=self.progress_var, 
            maximum=total,
            length=380
        )
        self.progress_bar.pack(pady=15, padx=10, fill="x")
        
        self.status_label = Label(self.window, text="0%")
        self.status_label.pack(pady=5)
        
        self.cancel_button = Button(
            self.window, 
            text=translate("cancel_button"), 
            command=self.cancel,
            width=10
        )
        self.cancel_button.pack(pady=5)
        
        self.canceled = False
        self.window.protocol("WM_DELETE_WINDOW", self.cancel)
        
    def cancel(self):
        self.canceled = True
        self.cancel_button.config(state="disabled")
        
    def update(self, value, text):
        self.progress_var.set(value)
        self.status_label.config(text=text)
        
    def destroy(self):
        self.window.grab_release()
        self.window.destroy()

def format_time_ms(ms: int) -> str:
    if ms < 0:
        ms = 0
    milliseconds = ms % 1000
    seconds = (ms // 1000) % 60
    minutes = (ms // (1000 * 60)) % 60
    hours = ms // (1000 * 60 * 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def parse_time_ms(time_str: str) -> int:
    try:
        time_str = time_str.replace('.', ',')
        h, m, s, ms = map(int, re.split(r'[:,]', time_str))
        return (h * 3600 + m * 60 + s) * 1000 + ms
    except Exception:
        return 0

def import_file(filepath: Path) -> Tuple[str, Optional[List[str]], Optional[List[List[str]]]]:
    """
    Lê o arquivo .usm/.sfd, extrai blocos @SBT e devolve (status, headers, rows).
    """
    global _last_imported

    try:
        data_bytes = filepath.read_bytes()
    except IOError as e:
        return (translate("file_read_error", file=filepath.name, error=str(e)), None, None)

    sbt_offsets = [m.start() for m in re.finditer(b'@SBT', data_bytes)]
    if not sbt_offsets:
        return (translate("no_sbt_blocks", file=filepath.name), None, None)

    rows: List[List[str]] = []
    metadata: List[Dict[str, Any]] = []

    METADATA_SIGNATURES = [b'CRIUSF_DIR_STREAM', b'@UTF', b'#HEADER END', b'#CONTENTS END']

    for offset in sbt_offsets:
        try:
            cursor = offset + 4
            chunk_size = struct.unpack('>I', data_bytes[cursor:cursor + 4])[0]
            cursor += 4
            raw_header_data = data_bytes[cursor:cursor + 40]
            if any(sig in raw_header_data for sig in METADATA_SIGNATURES):
                continue

            langid = struct.unpack_from('<B', raw_header_data, 24)[0]
            start_ms = struct.unpack_from('<I', raw_header_data, 32)[0]
            duration_ms = struct.unpack_from('<I', raw_header_data, 36)[0]
            end_ms = start_ms + duration_ms
            time_str = f"{format_time_ms(start_ms)}->{format_time_ms(end_ms)}"

            text_size_cursor = cursor + 40
            text_size = struct.unpack('<I', data_bytes[text_size_cursor:text_size_cursor + 4])[0]
            if text_size == 0 or text_size > chunk_size:
                continue

            text_cursor = text_size_cursor + 4
            text_bytes = data_bytes[text_cursor:text_cursor + text_size]
            text = text_bytes.decode('utf-8', errors='ignore').rstrip('\x00')

            rows.append([time_str, str(langid), text])
            metadata.append({
                'offset': offset,
                'chunk_size': chunk_size,
                'original_text_size': text_size,
                'original_start_ms': start_ms,
                'original_duration_ms': duration_ms,
            })
        except Exception:
            continue

    if not rows:
        return (translate("no_valid_subtitles", file=filepath.name), None, None)

    # salva contexto em memória (chave: path absoluto)
    key = str(filepath.resolve())
    _contexts[key] = {
        'source_path': key,
        'raw_data': data_bytes,
        'metadata': metadata,
        'headers': ["Time", "LangID", "Text"],
        'rows': rows,
    }
    _last_imported = key

    status = translate("import_success", count=len(rows), file=filepath.name)
    return (status, ["Time", "LangID", "Text"], rows)

def _find_context_for(target_path: Path) -> Optional[Dict[str, Any]]:
    """Tenta localizar o contexto associado ao arquivo ou, se ambíguo, retorna o último importado."""
    # 1) busca por path absoluto exato
    key = str(target_path.resolve())
    if key in _contexts:
        return _contexts[key]

    # 2) busca por base name (sem extensão)
    for ctx in _contexts.values():
        try:
            src = Path(ctx['source_path'])
            if src.with_suffix('') == target_path.with_suffix('') or src.stem == target_path.stem:
                return ctx
        except Exception:
            continue

    # 3) fallback para o último importado
    global _last_imported
    if _last_imported and _last_imported in _contexts:
        return _contexts[_last_imported]

    return None

def export_file(filepath: Path, headers: List[str], data: List[List[str]]) -> str:
    """
    Reconstrói o .usm/.sfd usando o contexto carregado em memória (do import_file).
    """
    ctx = _find_context_for(filepath)
    if ctx is None:
        return translate("context_not_found")

    original_data: bytes = ctx['raw_data']
    metadata_entries: List[Dict[str, Any]] = ctx['metadata']

    # monta lines a partir de `data` (que vem da UI)
    new_sub_lines: List[str] = []
    for row in data:
        if isinstance(row, (list, tuple)) and len(row) >= 3:
            new_sub_lines.append(f"{row[0]}|{row[1]}|{row[2]}")
        elif isinstance(row, str):
            new_sub_lines.append(row)
        else:
            new_sub_lines.append("|".join(map(str, row)))

    if len(new_sub_lines) != len(metadata_entries):
        return translate("row_count_mismatch", 
                        provided=len(new_sub_lines), 
                        expected=len(metadata_entries))

    new_file_data = bytearray()
    last_processed_offset = 0
    total_size_delta = 0

    for meta_entry, new_line in zip(metadata_entries, new_sub_lines):
        try:
            time_str, langid_str, new_text = new_line.split('|', 2)
            start_time_str, end_time_str = time_str.split('->', 1)
            new_start_ms = parse_time_ms(start_time_str)
            new_end_ms = parse_time_ms(end_time_str)
            new_duration_ms = new_end_ms - new_start_ms
            if new_duration_ms < 0:
                new_duration_ms = 0
        except Exception:
            # pula linhas mal formatadas
            continue

        offset = meta_entry['offset']
        original_chunk_size = meta_entry['chunk_size']
        original_chunk_end = offset + 8 + original_chunk_size

        original_text_cursor = offset + 8 + 40 + 4
        original_text_bytes = original_data[original_text_cursor: original_text_cursor + meta_entry['original_text_size']]
        original_text = original_text_bytes.decode('utf-8', errors='ignore').rstrip('\x00')

        new_file_data.extend(original_data[last_processed_offset:offset])

        # se nada mudou, copia original
        if (new_start_ms == meta_entry['original_start_ms'] and
            new_duration_ms == meta_entry['original_duration_ms'] and
            new_text == original_text):
            new_file_data.extend(original_data[offset:original_chunk_end])
            last_processed_offset = original_chunk_end
            continue

        new_text_bytes = new_text.encode('utf-8')
        new_text_size = len(new_text_bytes)

        original_header_bytes = bytearray(original_data[offset + 8: offset + 8 + 40])
        struct.pack_into('<I', original_header_bytes, 32, new_start_ms)
        struct.pack_into('<I', original_header_bytes, 36, new_duration_ms)

        required_space = 40 + 4 + new_text_size
        if (required_space + 8) <= original_chunk_size:
            new_chunk_size = original_chunk_size
        else:
            total_needed = required_space + 8
            new_chunk_size = (total_needed + 3) & ~3

        padding_size = new_chunk_size - required_space
        padding = b'\x00' * padding_size
        size_delta = new_chunk_size - original_chunk_size
        total_size_delta += size_delta

        new_chunk = bytearray()
        new_chunk.extend(b'@SBT')
        new_chunk.extend(struct.pack('>I', new_chunk_size))
        new_chunk.extend(original_header_bytes)
        new_chunk.extend(struct.pack('<I', new_text_size))
        new_chunk.extend(new_text_bytes)
        new_chunk.extend(padding)

        new_file_data.extend(new_chunk)
        last_processed_offset = original_chunk_end

    new_file_data.extend(original_data[last_processed_offset:])

    output_path = Path(filepath)
    try:
        output_path.write_bytes(bytes(new_file_data))
    except IOError as e:
        return translate("file_write_error", error=str(e))

    return translate("export_success", file=output_path.name, delta=total_size_delta)

def extract_subtitles():
    file_path = filedialog.askopenfilename(
        title=translate("select_usm_file"),
        filetypes=[(translate("usm_files"), "*.sfd;*.usm"), (translate("all_files"), "*.*")]
    )
    if not file_path:
        return

    def extraction_thread():
        try:
            path = Path(file_path)
            status, headers, rows = import_file(path)
            
            if headers is None or rows is None:
                messagebox.showerror(translate("error"), status)
                return

            # Salva como arquivo de texto
            txt_path = path.with_suffix('.txt')
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write("Time|LangID|Text\n")
                for row in rows:
                    f.write(f"{row[0]}|{row[1]}|{row[2]}\n")

            messagebox.showinfo(
                translate("completed"),
                f"{status}\n\n{translate('subtitles_extracted', count=len(rows))}\n{translate('file_saved', path=txt_path)}"
            )
        except Exception as e:
            messagebox.showerror(
                translate("error"),
                translate("unexpected_error", error=str(e))
            )
    
    threading.Thread(target=extraction_thread, daemon=True).start()

def reinsert_subtitles():
    txt_path = filedialog.askopenfilename(
        title=translate("select_txt_file"),
        filetypes=[(translate("text_files"), "*.txt"), (translate("all_files"), "*.*")]
    )
    if not txt_path:
        return

    # Pede para selecionar o arquivo USM original correspondente
    usm_path = filedialog.askopenfilename(
        title=translate("choose_original_file"),
        filetypes=[(translate("usm_files"), "*.sfd;*.usm"), (translate("all_files"), "*.*")]
    )
    if not usm_path:
        return

    def reinsertion_thread():
        try:
            # Lê o arquivo TXT
            with open(txt_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Pula o cabeçalho se existir
            if lines and "Time|LangID|Text" in lines[0]:
                lines = lines[1:]
            
            data = []
            for line in lines:
                line = line.strip()
                if line:
                    parts = line.split('|', 2)
                    if len(parts) == 3:
                        data.append(parts)
            
            # Exporta para o arquivo USM
            status = export_file(Path(usm_path), ["Time", "LangID", "Text"], data)
            
            messagebox.showinfo(
                translate("reconstruction_completed"),
                status
            )
        except Exception as e:
            messagebox.showerror(
                translate("error"),
                translate("unexpected_error", error=str(e))
            )
    

    threading.Thread(target=reinsertion_thread, daemon=True).start()
