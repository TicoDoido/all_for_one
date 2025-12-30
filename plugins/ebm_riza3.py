import os
import re
import threading
import zlib
from pathlib import Path
from tkinter import filedialog, messagebox, ttk, Label, Button
import tkinter as tk
from typing import List, Optional, Tuple, Dict

# Translation dictionaries for the plugin
plugin_translations = {
    "pt_BR": {
        "plugin_name": "EBM - Atelier Ryza 3",
        "plugin_description": "Extrai e importa textos de arquivos EBM (Atelier Ryza 3)",
        "extract_text": "Extrair texto",
        "import_text": "Importar texto",
        "extract_gz": "Extrair .gz",
        "compress_gz": "Compactar .gz",
        "select_ebm_files": "Selecione os arquivos .ebm",
        "select_txt_files": "Selecione os arquivos .txt",
        "select_gz_files": "Selecione os arquivos .gz",
        "select_compress_files": "Selecione os arquivos para compactar",
        "ebm_files": "Arquivos EBM",
        "text_files": "Arquivos de Texto",
        "gz_files": "Arquivos GZ",
        "all_files": "Todos os arquivos",
        "extraction_completed": "Extração concluída!\n{count} eventos extraídos para: {path}",
        "import_completed": "Importação concluída!\n{replaced} eventos importados. Salvo em: {path}",
        "gz_extraction_completed": "Descompressão concluída!\nArquivo salvo em: {path}",
        "gz_compression_completed": "Compressão concluída!\nArquivo salvo em: {path}",
        "ebm_not_found": "Arquivo EBM correspondente não encontrado: {path}",
        "invalid_ebm_file": "Arquivo EBM inválido: {path}",
        "negative_payload": "Comprimento de payload negativo encontrado",
        "invalid_event_type": "Tipo de evento inválido",
        "header_too_small": "Cabeçalho muito pequeno para escrever comprimento",
        "buffer_too_small": "Buffer muito pequeno para escrever evento",
        "unexpected_error": "Erro inesperado: {error}",
        "progress_title_extract": "Extraindo Eventos EBM",
        "progress_title_import": "Importando Textos",
        "progress_title_gz": "Descompactando .gz",
        "progress_title_gz_compress": "Compactando .gz",
        "cancel_button": "Cancelar",
        "ready": "Pronto",
        "operation_completed": "Operação concluída",
        "import_completed_detailed": "Importação concluída",
        "error": "Erro"
    },
    "en_US": {
        "plugin_name": "EBM - Atelier Ryza 3",
        "plugin_description": "Extracts and imports texts from EBM files (Atelier Ryza 3)",
        "extract_text": "Extract text",
        "import_text": "Import text",
        "extract_gz": "Extract .gz",
        "compress_gz": "Compress .gz",
        "select_ebm_files": "Select .ebm files",
        "select_txt_files": "Select .txt files",
        "select_gz_files": "Select .gz files",
        "select_compress_files": "Select files to compress",
        "ebm_files": "EBM Files",
        "text_files": "Text Files",
        "gz_files": "GZ Files",
        "all_files": "All files",
        "extraction_completed": "Extraction completed!\n{count} events extracted to: {path}",
        "import_completed": "Import completed!\n{replaced} events imported. Saved to: {path}",
        "gz_extraction_completed": "Decompression completed!\nFile saved to: {path}",
        "gz_compression_completed": "Compression completed!\nFile saved to: {path}",
        "ebm_not_found": "Corresponding EBM file not found: {path}",
        "invalid_ebm_file": "Invalid EBM file: {path}",
        "negative_payload": "Negative payload length encountered",
        "invalid_event_type": "Invalid event type",
        "header_too_small": "Header too small to write length",
        "buffer_too_small": "Buffer too small to write event",
        "unexpected_error": "Unexpected error: {error}",
        "progress_title_extract": "Extracting EBM Events",
        "progress_title_import": "Importing Texts",
        "progress_title_gz": "Decompressing .gz",
        "progress_title_gz_compress": "Compressing .gz",
        "cancel_button": "Cancel",
        "ready": "Ready",
        "operation_completed": "Operation completed",
        "import_completed_detailed": "Import completed",
        "error": "Error"
    },
    "es_ES": {
        "plugin_name": "EBM - Atelier Ryza 3",
        "plugin_description": "Extrae e importa textos de archivos EBM (Atelier Ryza 3)",
        "extract_text": "Extraer texto",
        "import_text": "Importar texto",
        "extract_gz": "Extraer .gz",
        "compress_gz": "Comprimir .gz",
        "select_ebm_files": "Seleccionar archivos .ebm",
        "select_txt_files": "Seleccionar archivos .txt",
        "select_gz_files": "Seleccionar archivos .gz",
        "select_compress_files": "Seleccionar archivos para comprimir",
        "ebm_files": "Archivos EBM",
        "text_files": "Archivos de Texto",
        "gz_files": "Archivos GZ",
        "all_files": "Todos los archivos",
        "extraction_completed": "¡Extracción completada!\n{count} eventos extraídos a: {path}",
        "import_completed": "¡Importación completada!\n{replaced} eventos importados. Guardado en: {path}",
        "gz_extraction_completed": "¡Descompresión completada!\nArchivo guardado en: {path}",
        "gz_compression_completed": "¡Compresión completada!\nArchivo guardado en: {path}",
        "ebm_not_found": "Archivo EBM correspondiente no encontrado: {path}",
        "invalid_ebm_file": "Archivo EBM inválido: {path}",
        "negative_payload": "Longitud de carga útil negativa encontrada",
        "invalid_event_type": "Tipo de evento inválido",
        "header_too_small": "Encabezado demasiado pequeño para escribir longitud",
        "buffer_too_small": "Buffer demasiado pequeño para escribir evento",
        "unexpected_error": "Error inesperado: {error}",
        "progress_title_extract": "Extrayendo Eventos EBM",
        "progress_title_import": "Importando Textos",
        "progress_title_gz": "Descomprimiendo .gz",
        "progress_title_gz_compress": "Comprimiendo .gz",
        "cancel_button": "Cancelar",
        "ready": "Listo",
        "operation_completed": "Operación completada",
        "import_completed_detailed": "Importación completada",
        "error": "Error"
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
            "commands": [
                {"label": translate("extract_text"), "action": extract_action},
                {"label": translate("import_text"), "action": import_action},
                {"label": translate("extract_gz"), "action": extract_gz_action},
                {"label": translate("compress_gz"), "action": compress_gz_action},
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

class Reader:
    def __init__(self, buffer: bytes):
        self._buffer = buffer
        self._cursor = 0

    @property
    def length(self) -> int:
        return len(self._buffer) - self._cursor

    @property
    def buffer(self) -> bytes:
        return self._buffer

    @property
    def cursor(self) -> int:
        return self._cursor

    def peek(self, start: int, end: int) -> Optional[bytes]:
        if start > end:
            return None
        if end > len(self._buffer):
            raise EOFError("Peek range extends past buffer end")
        return self._buffer[start:end]

    def consume(self, n: int) -> bytes:
        if self._cursor + n > len(self._buffer):
            raise EOFError("Attempt to consume past end of buffer")
        out = self._buffer[self._cursor:self._cursor + n]
        self._cursor += n
        return out

    def remaining(self) -> bytes:
        return self._buffer[self._cursor:]

class Event:
    def __init__(self, header: bytes, data: bytes, footer: bytes):
        self._header = bytearray(header)
        self._data = bytearray(data)
        self._footer = bytearray(footer)

    @property
    def header(self) -> bytes:
        return bytes(self._header)

    @property
    def data(self) -> str:
        try:
            s = bytes(self._data).decode('utf-8', errors='replace')
        except Exception:
            s = bytes(self._data).decode('latin1', errors='replace')
        return s.rstrip('\x00')

    @property
    def footer(self) -> bytes:
        return bytes(self._footer)

    @property
    def length(self) -> int:
        if len(self._header) < 64:
            data_length = 0
        else:
            raw = bytes(self._header[60:64])
            data_length = int.from_bytes(raw, byteorder='little', signed=True)
        return len(self._header) + data_length + len(self._footer)

    def writeEventText(self, text: str) -> None:
        encoded = text.encode('utf-8')
        length = len(encoded) + 1
        if len(self._header) < 4:
            raise ValueError(translate("header_too_small"))
        pos = len(self._header) - 4
        self._header[pos:pos + 4] = (length).to_bytes(4, byteorder='little', signed=True)
        new_payload = bytearray(length)
        new_payload[0:len(encoded)] = encoded
        self._data = new_payload

    def write(self, dest: bytearray, offset: int = 0) -> None:
        total = bytes(self._header) + bytes(self._data) + bytes(self._footer)
        end = offset + len(total)
        if end > len(dest):
            raise ValueError(translate("buffer_too_small"))
        dest[offset:end] = total

    def clone(self) -> "Event":
        return Event(bytes(self._header), bytes(self._data), bytes(self._footer))

class EBM:
    EVENT_MESSAGE_TYPE = bytes([0x02, 0x00, 0x00, 0x00])
    EVENT_NOTIFICATION_TYPE = bytes([0x03, 0x00, 0x00, 0x00])

    def __init__(self, path: str):
        p = Path(path).expanduser().resolve()
        if not p.exists() or not p.is_file():
            raise ValueError(translate("invalid_ebm_file", path=path))
        raw = p.read_bytes()
        self._reader = Reader(raw)
        first4 = self._reader.consume(4)
        self._length = abs(int.from_bytes(first4, byteorder='little', signed=True))
        self._events: List[Event] = []
        self._path = str(p)

    @property
    def events(self) -> List[Event]:
        return self._events

    @property
    def path(self) -> str:
        return self._path

    def readEvent(self) -> None:
        start = self._reader.cursor
        type_bytes = self._reader.peek(start, start + 4)
        if type_bytes is None or (type_bytes != EBM.EVENT_MESSAGE_TYPE and type_bytes != EBM.EVENT_NOTIFICATION_TYPE):
            raise ValueError(translate("invalid_event_type"))
        header = self._reader.consume(60)
        length_bytes = self._reader.consume(4)
        payload_length = int.from_bytes(length_bytes, byteorder='little', signed=True)
        if payload_length < 0:
            raise ValueError(translate("negative_payload"))
        payload = self._reader.consume(payload_length)
        trailer = self._reader.consume(8)
        header_and_length = header + length_bytes
        self._events.append(Event(header_and_length, payload, trailer))

    def read(self) -> None:
        if not self._length:
            raise ValueError(translate("invalid_ebm_file", path=self._path))
        for _ in range(self._length):
            self.readEvent()

    def save(self, path: str) -> None:
        rest_of_bytes = self._reader.remaining()
        events_length = sum(event.length for event in self._events)
        buf = bytearray(4 + events_length + len(rest_of_bytes))
        buf[0:4] = int(self._length).to_bytes(4, byteorder='little', signed=True)
        offset = 4
        for event in self._events:
            event.write(buf, offset)
            offset += event.length
        buf[offset:offset + len(rest_of_bytes)] = rest_of_bytes
        Path(path).write_bytes(bytes(buf))

def event_type_label(event: Event) -> str:
    h = event.header
    if len(h) >= 4:
        t = h[0:4]
        if t == EBM.EVENT_MESSAGE_TYPE:
            return "message"
        if t == EBM.EVENT_NOTIFICATION_TYPE:
            return "notification"
    return "unknown"

def build_txt_from_ebm(ebm: EBM) -> str:
    parts: List[str] = []
    for idx, ev in enumerate(ebm.events):
        parts.append(f"### EVENT {idx:04d} [{event_type_label(ev)}]\n")
        parts.append(ev.data.rstrip("\n"))
        parts.append("\n\n")
    return "".join(parts).rstrip() + "\n"

def parse_txt_to_event_texts(txt: str) -> Dict[int, str]:
    pattern = re.compile(r"^### EVENT (?P<idx>\d{4}) \[(?P<type>.*?)\]\s*$", flags=re.M)
    matches = list(pattern.finditer(txt))
    result: Dict[int, str] = {}
    if not matches:
        result[0] = txt.rstrip("\n")
        return result

    for i, m in enumerate(matches):
        idx = int(m.group("idx"))
        start = m.end()
        end = matches[i+1].start() if i+1 < len(matches) else len(txt)
        content = txt[start:end].lstrip("\n").rstrip("\n")
        result[idx] = content
    return result

def extract_action():
    fs = filedialog.askopenfilenames(
        title=translate("select_ebm_files"),
        filetypes=[(translate("ebm_files"), "*.ebm"), (translate("all_files"), "*.*")]
    )
    if not fs:
        return
    
    def extraction_thread():
        for f in fs:
            try:
                ebm = EBM(f)
                ebm.read()
                content = build_txt_from_ebm(ebm)
                ebm_path = Path(f).resolve()
                out_txt = ebm_path.with_suffix(".txt")
                out_txt.write_text(content, encoding="utf-8")
                logger(translate("extraction_completed", count=len(ebm.events), path=out_txt))
            except Exception as e:
                messagebox.showerror(
                    translate("error"),
                    translate("unexpected_error", error=str(e))
                )
        
        messagebox.showinfo(
            translate("ready"),
            translate("operation_completed")
        )
    
    threading.Thread(target=extraction_thread, daemon=True).start()

def import_action():
    fs = filedialog.askopenfilenames(
        title=translate("select_txt_files"),
        filetypes=[(translate("text_files"), "*.txt"), (translate("all_files"), "*.*")]
    )
    if not fs:
        return
    
    def import_thread():
        for f in fs:
            try:
                txt_path = Path(f).resolve()
                base = txt_path.stem
                ebm_candidate = txt_path.with_suffix(".ebm")
                if not ebm_candidate.exists():
                    raise FileNotFoundError(
                        translate("ebm_not_found", path=ebm_candidate)
                    )
                
                ebm = EBM(str(ebm_candidate))
                ebm.read()
                txt_content = txt_path.read_text(encoding="utf-8")
                mapping = parse_txt_to_event_texts(txt_content)
                replaced = 0
                
                for idx, ev in enumerate(ebm.events):
                    if idx in mapping:
                        ev.writeEventText(mapping[idx])
                        replaced += 1

                out_path = ebm_candidate
                ebm.save(str(out_path))
                logger(translate("import_completed", replaced=replaced, path=out_path))
            except Exception as e:
                messagebox.showerror(
                    translate("error"),
                    translate("unexpected_error", error=str(e))
                )
        
        messagebox.showinfo(
            translate("ready"),
            translate("import_completed_detailed")
        )
    
    threading.Thread(target=import_thread, daemon=True).start()

def extract_gz_action():
    fs = filedialog.askopenfilenames(
        title=translate("select_gz_files"),
        filetypes=[(translate("gz_files"), "*.gz"), (translate("all_files"), "*.*")]
    )
    if not fs:
        return

    def gz_thread():
        for f in fs:
            try:
                p = Path(f).resolve()
                out_path = p.with_suffix('')  # removes .gz
                # Read and decompress blocks: each block is preceded by 4 bytes LE size
                data = p.read_bytes()
                cursor = 0
                decompressed_parts: List[bytes] = []
                total_len = len(data)
                # progress window (optional)
                try:
                    parent = tk._default_root or tk.Tk()
                    if not tk._default_root:
                        parent.withdraw()
                    pw = ProgressWindow(parent, translate("progress_title_gz"), total_len)
                except Exception:
                    pw = None

                while cursor < total_len:
                    # need at least 4 bytes for size
                    if cursor + 4 > total_len:
                        # nothing more or corrupt - break
                        break
                    size_bytes = data[cursor:cursor + 4]
                    cursor += 4
                    block_size = int.from_bytes(size_bytes, byteorder='little', signed=False)
                    if block_size == 0:
                        # zero-length block -> skip or break
                        continue
                    if cursor + block_size > total_len:
                        raise EOFError("Block size extends past end of file")
                    block = data[cursor:cursor + block_size]
                    cursor += block_size
                    try:
                        dec = zlib.decompress(block)
                    except zlib.error as ze:
                        # if decompression fails, raise user-friendly error
                        raise ValueError(f"zlib decompression failed: {ze}")
                    decompressed_parts.append(dec)

                    if pw:
                        pw.update(cursor, f"{cursor}/{total_len} bytes")
                        if pw.canceled:
                            break

                # join and write
                full = b"".join(decompressed_parts)
                out_path.write_bytes(full)
                if pw:
                    pw.destroy()
                logger(translate("gz_extraction_completed", path=out_path))
            except Exception as e:
                messagebox.showerror(
                    translate("error"),
                    translate("unexpected_error", error=str(e))
                )
        try:
            messagebox.showinfo(
                translate("ready"),
                translate("operation_completed")
            )
        except Exception:
            pass

    threading.Thread(target=gz_thread, daemon=True).start()

# New: compress back into .gz with 16KB chunks
CHUNK_SIZE = 16 * 1024  # 16 KB
DEFAULT_COMPRESSION_LEVEL = 6

def compress_gz_action():
    fs = filedialog.askopenfilenames(
        title=translate("select_compress_files"),
        filetypes=[(translate("all_files"), "*.*")]
    )
    if not fs:
        return

    def compress_thread():
        for f in fs:
            try:
                p = Path(f).resolve()
                out_path = p.with_name(p.name + '.gz')  # append .gz to filename (e.g. file.txt -> file.txt.gz)

                total_size = p.stat().st_size
                try:
                    parent = tk._default_root or tk.Tk()
                    if not tk._default_root:
                        parent.withdraw()
                    pw = ProgressWindow(parent, translate("progress_title_gz_compress"), total_size)
                except Exception:
                    pw = None

                with p.open('rb') as src, out_path.open('wb') as dst:
                    written = 0
                    while True:
                        chunk = src.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        compressor = zlib.compressobj(
                            level=9,
                            method=zlib.DEFLATED,
                            wbits=15,      # 15 -> zlib header + adler32 (equivalente a TDEFL_WRITE_ZLIB_HEADER)
                            memLevel=9,
                            strategy=zlib.Z_DEFAULT_STRATEGY
                        )

                        comp = compressor.compress(chunk)
                        comp += compressor.flush(zlib.Z_FINISH)
                        size_bytes = len(comp).to_bytes(4, byteorder='little', signed=False)
                        dst.write(size_bytes)
                        dst.write(comp)

                        written += len(chunk)
                        if pw:
                            pw.update(written, f"{written}/{total_size} bytes")
                            if pw.canceled:
                                break

                if pw:
                    pw.destroy()
                logger(translate("gz_compression_completed", path=out_path))
            except Exception as e:
                messagebox.showerror(
                    translate("error"),
                    translate("unexpected_error", error=str(e))
                )
        try:
            messagebox.showinfo(
                translate("ready"),
                translate("operation_completed")
            )
        except Exception:
            pass

    threading.Thread(target=compress_thread, daemon=True).start()
