#!/usr/bin/env python3
"""
XPC2 extractor & reinserter
Lógica principal retirada de um script do Quick BMS por Aluigi
https://aluigi.altervista.org/quickbms.htm
Logica do MES feita por mim mesmo(TicoDoido)

Funções:
- Extrair arquivos de um container XPC2
- Reinserir arquivos na ordem original, atualizando offsets e tamanhos

Formato conforme especificado:
Magic = XPC2
Tamanho total do arquivo (4 bytes LE)
Total de arquivos (2 bytes LE) + repetido (2 bytes LE)
Valor de cálculo para cabeçalho (4 bytes LE)
Posição 32: 4 bytes LE = início da tabela de arquivos
Posição 36: 4 bytes LE = onde começam os dados dos arquivos (files_inserted_offset)

Cada item do índice:
- 16 bytes nome (remover nulos)
- offset, tamanho comprimido, tipo, tamanho descomprimido
Próximo cabeçalho = header_calc * 32 - 32

Compressão: zlib
"""
import os
import struct
import re
import zlib
import threading
from tkinter import filedialog, messagebox

# ==========================
# Traduções do plugin MES (todas as strings usadas no código)
# ==========================

plugin_translations = {
    "pt_BR": {
        "plugin_name": "MES|XPC Deadly Premonition Director's Cut",
        "plugin_description": "Extrai e reinsere textos de arquivos .MES\nExtrai e reinsere arquivos em containers XPC2 (zlib)",
        "extract_mes": "Extrair .MES",
        "reinsert_mes": "Remontar .MES a partir do .TXT",
        "select_mes_file": "Selecione o arquivo .MES",
        "select_txt_file": "Selecione o arquivo .TXT",
        "msg_done_extract": "Extração concluída: {out}",
        "msg_done_reinsert": "Remontagem concluída: {out}",
        "msg_title_error": "Erro",
        "msg_title_done": "Pronto",

        "warn_magic_diff": "Aviso: magic diferente ({magic!r})",
        "log_version_header": "Versão: {version} | header_count: {header_size}",
        "err_expected_id10": "Esperado exatamente 10 bytes no ID",
        "err_unexpected_end_block": "Fim inesperado ao ler bloco {idx}",
        "log_bt_token": "[BT{value:02X}]",
        "log_cr_token": "[CR{hexval}]",
        "log_lf_token": "[LF{hexval}]",

        "warn_id_len": "AVISO: ID de tamanho incorreto em {idx}, preenchendo com zeros.",
        "warn_no_original": "Original .MES não encontrado: {path} (usar fallback de IDs).",
        "log_reading": "Lendo: {path}",
        "log_offsets": "Offsets válidos encontrados: {n}",
        "log_extracted": "Tudo extraído em: {out}",
        "log_rewrite_done": "Arquivo reescrito com sucesso: {out}",

        "warn_fail_read_id": "AVISO: falha ao ler ID no offset {off}: {err}",
        "warn_missing_offset_entry": "AVISO: sem offset para a entrada válida #{i} (escrevendo 0).",
        "warn_cr_invalid": "AVISO: CR token inválido na linha {line}: [{token}]",
        "warn_lf_invalid": "AVISO: LF token inválido na linha {line}: [{token}]",
        "warn_token_invalid": "AVISO: token inválido na linha {line}: [{token}]",

        "msg_error_reinsert": "Erro ao usar original .MES para obter IDs: {err}",
        "extract_xpc": "Extrair XPC2",
        "reinsert_xpc": "Reinserir XPC2",
        "select_xpc_file": "Selecione o arquivo XPC2",
        "select_xpc_file_folder": "Selecione o arquivo XPC2",
        "select_folder_files": "Selecione a pasta com os arquivos modificados",
        "msg_title_error": "Erro",
        "msg_title_done": "Concluído",
        "msg_extract_done": "Extração concluída.",
        "msg_reinsert_done": "Reinserção concluída.",
        "log_magic_invalid": "Magic inválido, esperado 'XPC2'",
        "log_magic_ok": "Magic OK. total_size={total_size}, total_files_1={tf1}, total_files_2={tf2}, header_calc={hc}",
        "log_table_info": "Tabela={table}, Offset de arquivos={files_offset}, Total={total}",
        "log_extracting_to": "Extraindo {n} arquivos para: {out_dir}",
        "log_skip_zero": "[{idx}] Pulando {name} (comp_size=0)",
        "log_decompress_error": "[{idx}] Erro ao descomprimir {name}, salvando comprimido",
        "log_extracted_file": "[{idx}] Extraído: {name} ({size} bytes)",
        "log_extraction_finished": "Extração concluída.",
        "log_reinsert_start": "Reinserindo {total} arquivos em {path}",
        "log_start_write_offset": "Iniciando escrita em offset {offset}",
        "log_reinserted": "[{idx}] Reinserido {name} ({uncomp} bytes -> {comp} bytes)",
        "log_reinsert_finished": "Reinserção concluída e arquivo atualizado.",
        "msg_error_open": "Erro ao abrir o arquivo: {err}",
    },

    "en_US": {
        "plugin_name": "MES Deadly Premonition Director's Cut Extractor|Reinserter",
        "plugin_description": "Extracts and reinserts texts from .MES files\nExtracts and reinserts files in XPC2 containers (zlib)",
        "extract_mes": "Extract .MES",
        "reinsert_mes": "Reinsert .MES from .TXT",
        "select_mes_file": "Select the .MES file",
        "select_txt_file": "Select the .TXT file",
        "msg_done_extract": "Extraction finished: {out}",
        "msg_done_reinsert": "Reinsertion finished: {out}",
        "msg_title_error": "Error",
        "msg_title_done": "Done",

        "warn_magic_diff": "Warning: different magic ({magic!r})",
        "log_version_header": "Version: {version} | header_count: {header_size}",
        "err_expected_id10": "Expected exactly 10 bytes for ID",
        "err_unexpected_end_block": "Unexpected EOF reading block {idx}",
        "log_bt_token": "[BT{value:02X}]",
        "log_cr_token": "[CR{hexval}]",
        "log_lf_token": "[LF{hexval}]",

        "warn_id_len": "WARN: ID wrong length at {idx}, filling with zeros.",
        "warn_no_original": "Original .MES not found: {path} (using fallback IDs).",
        "log_reading": "Reading: {path}",
        "log_offsets": "Valid offsets found: {n}",
        "log_extracted": "All extracted to: {out}",
        "log_rewrite_done": "File rewritten successfully: {out}",

        "warn_fail_read_id": "WARN: failed to read ID at offset {off}: {err}",
        "warn_missing_offset_entry": "WARN: no offset for valid entry #{i} (writing 0).",
        "warn_cr_invalid": "WARN: CR token invalid on line {line}: [{token}]",
        "warn_lf_invalid": "WARN: LF token invalid on line {line}: [{token}]",
        "warn_token_invalid": "WARN: invalid token on line {line}: [{token}]",

        "msg_error_reinsert": "Error using original .MES to get IDs: {err}",
        "extract_xpc": "Extract XPC2",
        "reinsert_xpc": "Reinsert XPC2",
        "select_xpc_file": "Select the XPC2 file",
        "select_xpc_file_folder": "Select the XPC2 file",
        "select_folder_files": "Select the folder with modified files",
        "msg_title_error": "Error",
        "msg_title_done": "Done",
        "msg_extract_done": "Extraction finished.",
        "msg_reinsert_done": "Reinsertion finished.",
        "log_magic_invalid": "Invalid magic, expected 'XPC2'",
        "log_magic_ok": "Magic OK. total_size={total_size}, total_files_1={tf1}, total_files_2={tf2}, header_calc={hc}",
        "log_table_info": "Table={table}, Files offset={files_offset}, Total={total}",
        "log_extracting_to": "Extracting {n} files to: {out_dir}",
        "log_skip_zero": "[{idx}] Skipping {name} (comp_size=0)",
        "log_decompress_error": "[{idx}] Error decompressing {name}, saving compressed",
        "log_extracted_file": "[{idx}] Extracted: {name} ({size} bytes)",
        "log_extraction_finished": "Extraction finished.",
        "log_reinsert_start": "Reinserting {total} files into {path}",
        "log_start_write_offset": "Starting write at offset {offset}",
        "log_reinserted": "[{idx}] Reinserted {name} ({uncomp} bytes -> {comp} bytes)",
        "log_reinsert_finished": "Reinsertion finished and file updated.",
        "msg_error_open": "Error opening file: {err}",
    },

    "es_ES": {
        "plugin_name": "MES Deadly Premonition Director's Cut Extractor|Reinserter",
        "plugin_description": "Extrae y reinscribe textos de archivos .MES\nExtrae y reingresa archivos en contenedores XPC2 (zlib)",
        "extract_mes": "Extraer .MES",
        "reinsert_mes": "Reinsertar .MES desde .TXT",
        "select_mes_file": "Seleccione el archivo .MES",
        "select_txt_file": "Seleccione el archivo .TXT",
        "msg_done_extract": "Extracción finalizada: {out}",
        "msg_done_reinsert": "Remontaje finalizado: {out}",
        "msg_title_error": "Error",
        "msg_title_done": "Listo",

        "warn_magic_diff": "Aviso: magic diferente ({magic!r})",
        "log_version_header": "Versión: {version} | header_count: {header_size}",
        "err_expected_id10": "Se esperaban exactamente 10 bytes en el ID",
        "err_unexpected_end_block": "Fin inesperado al leer el bloque {idx}",
        "log_bt_token": "[BT{value:02X}]",
        "log_cr_token": "[CR{hexval}]",
        "log_lf_token": "[LF{hexval}]",

        "warn_id_len": "AVISO: ID con longitud incorrecta en {idx}, rellenando con ceros.",
        "warn_no_original": "Original .MES no encontrado: {path} (usar fallback de IDs).",
        "log_reading": "Leyendo: {path}",
        "log_offsets": "Offsets válidos encontrados: {n}",
        "log_extracted": "Todo extraído en: {out}",
        "log_rewrite_done": "Archivo reescrito con éxito: {out}",

        "warn_fail_read_id": "AVISO: fallo al leer ID en offset {off}: {err}",
        "warn_missing_offset_entry": "AVISO: sin offset para la entrada válida #{i} (escribiendo 0).",
        "warn_cr_invalid": "AVISO: token CR inválido en la línea {line}: [{token}]",
        "warn_lf_invalid": "AVISO: token LF inválido en la línea {line}: [{token}]",
        "warn_token_invalid": "AVISO: token inválido en la línea {line}: [{token}]",

        "msg_error_reinsert": "Error al usar .MES original para obtener IDs: {err}",
        "extract_xpc": "Extraer XPC2",
        "reinsert_xpc": "Reinsertar XPC2",
        "select_xpc_file": "Seleccione el archivo XPC2",
        "select_xpc_file_folder": "Seleccione el archivo XPC2",
        "select_folder_files": "Seleccione la carpeta con los archivos modificados",
        "msg_title_error": "Error",
        "msg_title_done": "Completado",
        "msg_extract_done": "Extracción completada.",
        "msg_reinsert_done": "Reinserción completada.",
        "log_magic_invalid": "Magic inválido, se esperaba 'XPC2'",
        "log_magic_ok": "Magic OK. total_size={total_size}, total_files_1={tf1}, total_files_2={tf2}, header_calc={hc}",
        "log_table_info": "Tabla={table}, Offset de archivos={files_offset}, Total={total}",
        "log_extracting_to": "Extrayendo {n} archivos a: {out_dir}",
        "log_skip_zero": "[{idx}] Saltando {name} (comp_size=0)",
        "log_decompress_error": "[{idx}] Error al descomprimir {name}, guardando comprimido",
        "log_extracted_file": "[{idx}] Extraído: {name} ({size} bytes)",
        "log_extraction_finished": "Extracción completada.",
        "log_reinsert_start": "Reinsertando {total} archivos en {path}",
        "log_start_write_offset": "Iniciando escritura en offset {offset}",
        "log_reinserted": "[{idx}] Reinsertado {name} ({uncomp} bytes -> {comp} bytes)",
        "log_reinsert_finished": "Reinserción completada y archivo actualizado.",
        "msg_error_open": "Error al abrir el archivo: {err}",
    }
}

# ==========================
# Globais e utilitários do plugin
# ==========================
logger = print
current_language = "pt_BR"

def translate(key, **kwargs):
    lang_dict = plugin_translations.get(current_language, plugin_translations["pt_BR"])
    text = lang_dict.get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text

def read_u32_le(f):
    data = f.read(4)
    if len(data) < 4:
        raise EOFError("truncated")
    return struct.unpack('<I', data)[0]

def read_u16_le(f):
    data = f.read(2)
    if len(data) < 2:
        raise EOFError("truncated")
    return struct.unpack('<H', data)[0]

def read_sized_string(b):
    b = b.split(b'\x00', 1)[0]
    try:
        return b.decode('utf-8', errors='replace')
    except Exception:
        return b.decode('latin1', errors='replace')
        
class XPCExtractor:
    def extract(self, path, log_callback=None):
        log = log_callback or logger
        try:
            with open(path, 'rb') as f:
                magic = f.read(4)
                if magic != b'XPC2':
                    log(translate("log_magic_invalid"))
                    raise ValueError(translate("log_magic_invalid"))

                total_size = read_u32_le(f)
                total_files_1 = read_u16_le(f)
                total_files_2 = read_u16_le(f)
                header_calc = read_u32_le(f)

                log(translate("log_magic_ok", total_size=total_size, tf1=total_files_1, tf2=total_files_2, hc=header_calc))

                f.seek(32)
                file_table_start = read_u32_le(f)
                files_inserted_offset = read_u32_le(f)

                total_files = total_files_1 or total_files_2
                log(translate("log_table_info", table=file_table_start, files_offset=files_inserted_offset, total=total_files))

                f.seek(file_table_start)

                entries = []
                stride = header_calc * 32 - 32
                if stride < 0:
                    stride = 0

                for i in range(total_files):
                    entry_pos = f.tell()
                    raw_name = f.read(16)
                    name = read_sized_string(raw_name) or f"file_{i}"

                    offset = read_u32_le(f)
                    comp_size = read_u32_le(f)
                    ftype = read_u32_le(f)
                    uncomp_size = read_u32_le(f)

                    entries.append({'name': name, 'offset': offset, 'comp_size': comp_size,
                                    'type': ftype, 'uncomp_size': uncomp_size})

                    if stride > 0:
                        f.seek(entry_pos + 32 + stride)

                out_dir = self._make_output_dir(path)
                log(translate("log_extracting_to", n=len(entries), out_dir=out_dir))

                for idx, e in enumerate(entries):
                    if e['comp_size'] == 0:
                        log(translate("log_skip_zero", idx=idx, name=e['name']))
                        continue

                    f.seek(e['offset'])
                    comp_data = f.read(e['comp_size'])

                    try:
                        data = zlib.decompress(comp_data)
                    except zlib.error:
                        log(translate("log_decompress_error", idx=idx, name=e['name']))
                        out_path = os.path.join(out_dir, e['name'] + ".z")
                        self._safe_write(out_path, comp_data)
                        continue

                    out_path = os.path.join(out_dir, e['name'])
                    self._safe_write(out_path, data)
                    log(translate("log_extracted_file", idx=idx, name=e['name'], size=len(data)))

                log(translate("log_extraction_finished"))

        except Exception as ex:
            log(translate("msg_error_open", err=str(ex)))
            raise

    def reinsert_files(self, path, folder, log_callback=None):
        log = log_callback or logger
        try:
            with open(path, 'r+b') as f:
                magic = f.read(4)
                if magic != b'XPC2':
                    log(translate("log_magic_invalid"))
                    raise ValueError(translate("log_magic_invalid"))

                total_size = read_u32_le(f)
                total_files_1 = read_u16_le(f)
                total_files_2 = read_u16_le(f)
                header_calc = read_u32_le(f)

                f.seek(32)
                file_table_start = read_u32_le(f)
                files_inserted_offset = read_u32_le(f)
                total_files = total_files_1 or total_files_2
                stride = header_calc * 32 - 32
                if stride < 0:
                    stride = 0

                log(translate("log_reinsert_start", total=total_files, path=path))
                f.seek(file_table_start)

                entries_pos = []
                for i in range(total_files):
                    entry_pos = f.tell()
                    name = read_sized_string(f.read(16))
                    f.seek(16, 1)  # pular offset/tamanhos
                    entries_pos.append((entry_pos, name))
                    if stride > 0:
                        f.seek(entry_pos + 32 + stride)

                current_offset = files_inserted_offset
                f.seek(current_offset)
                log(translate("log_start_write_offset", offset=files_inserted_offset))

                for idx, (entry_pos, name) in enumerate(entries_pos):
                    file_path = os.path.join(folder, name)
                    if not os.path.isfile(file_path):
                        log(f"[{idx}] {translate('log_skip_zero', idx=idx, name=name)}")
                        continue

                    with open(file_path, 'rb') as fi:
                        data = fi.read()

                    comp_data = zlib.compress(data, level=9)
                    comp_size = len(comp_data)
                    uncomp_size = len(data)

                    f.seek(current_offset)
                    f.write(comp_data)

                    f.seek(entry_pos + 16)
                    f.write(struct.pack('<I', current_offset))
                    f.write(struct.pack('<I', comp_size))
                    f.seek(4, 1)
                    f.write(struct.pack('<I', uncomp_size << 8))

                    log(translate("log_reinserted", idx=idx, name=name, uncomp=uncomp_size, comp=comp_size))
                    current_offset += comp_size

                f.seek(4)
                f.write(struct.pack('<I', current_offset))
                f.truncate(current_offset)
                log(translate("log_reinsert_finished"))

        except Exception as ex:
            log(translate("msg_error_open", err=str(ex)))
            raise

    def _make_output_dir(self, path):
        base_dir = os.path.dirname(path)
        base_name = os.path.splitext(os.path.basename(path))[0]
        out_dir = os.path.join(base_dir, base_name)
        os.makedirs(out_dir, exist_ok=True)
        return out_dir

    def _safe_write(self, path, data):
        folder = os.path.dirname(path)
        os.makedirs(folder, exist_ok=True)
        with open(path, 'wb') as f:
            f.write(data)

def selecionar_extrair_xpc():
    path = filedialog.askopenfilename(
        title=translate("select_xpc_file"),
        filetypes=[("XPC files", "*.xpc;*.XPC;*.bin"), ("All files", "*.*")]
    )
    if not path:
        return
    threading.Thread(target=_run_extract_xpc, args=(path,), daemon=True).start()

def _run_extract_xpc(path):
    try:
        extractor = XPCExtractor()
        extractor.extract(path, log_callback=logger)
        messagebox.showinfo(translate("msg_title_done"), translate("msg_extract_done"))
    except Exception as e:
        logger(str(e))
        messagebox.showerror(translate("msg_title_error"), str(e))

def selecionar_reinserir_xpc():
    path = filedialog.askopenfilename(
        title=translate("select_xpc_file_folder"),
        filetypes=[("XPC files", "*.xpc;*.XPC;*.bin"), ("All files", "*.*")]
    )
    if not path:
        return
    folder = filedialog.askdirectory(title=translate("select_folder_files"))
    if not folder:
        return
    threading.Thread(target=_run_reinsert_xpc, args=(path, folder), daemon=True).start()

def _run_reinsert_xpc(path, folder):
    try:
        extractor = XPCExtractor()
        extractor.reinsert_files(path, folder, log_callback=logger)
        messagebox.showinfo(translate("msg_title_done"), translate("msg_reinsert_done"))
    except Exception as e:
        logger(str(e))
        messagebox.showerror(translate("msg_title_error"), str(e))

# ==========================
# Tabela de caracteres (mantida igual ao seu script)
# ==========================
CHAR_TABLE = {
    0x0000: ' ',
    0x0100: '!',
    0x0200: '"',
    0x0300: '#',
    0x0400: '$',
    0x0500: '%',
    0x0600: '&',
    0x0700: "'",
    0x0800: '<',
    0x0900: '>',
    0x0A00: '*',
    0x0B00: '+',
    0x0C00: ',',
    0x0D00: '-',
    0x0E00: '.',
    0x0F00: '/',
    0x1000: "0",
    0x1100: "1",
    0x1200: "2",
    0x1300: "3",
    0x1400: "4",
    0x1500: "5",
    0x1600: "6",
    0x1700: "7",
    0x1800: "8",
    0x1900: "9",
    0x1A00: ":",
    0x1B00: ";",
    0x1D00: "=",
    0x1E00: "®",
    0x1F00: "?",
    0x2100: 'A',
    0x2200: 'B',
    0x2300: 'C',
    0x2400: 'D',
    0x2500: 'E',
    0x2600: 'F',
    0x2700: 'G',
    0x2800: 'H',
    0x2900: 'I',
    0x2A00: 'J',
    0x2B00: 'K',
    0x2C00: 'L',
    0x2D00: 'M',
    0x2E00: 'N',
    0x2F00: 'O',
    0x3000: 'P',
    0x3100: 'Q',
    0x3200: 'R',
    0x3300: 'S',
    0x3400: 'T',
    0x3500: 'U',
    0x3600: 'V',
    0x3700: 'W',
    0x3800: 'X',
    0x3900: 'Y',
    0x3A00: 'Z',
    0x3C00: '¥',
    0x3E00: '^',
    0x3F00: '_',
    0x4000: '`',
    0x4100: 'a',
    0x4200: 'b',
    0x4300: 'c',
    0x4400: 'd',
    0x4500: 'e',
    0x4600: 'f',
    0x4700: 'g',
    0x4800: 'h',
    0x4900: 'i',
    0x4A00: 'j',
    0x4B00: 'k',
    0x4C00: 'l',
    0x4D00: 'm',
    0x4E00: 'n',
    0x4F00: 'o',
    0x5000: 'p',
    0x5100: 'q',
    0x5200: 'r',
    0x5300: 's',
    0x5400: 't',
    0x5500: 'u',
    0x5600: 'v',
    0x5700: 'w',
    0x5800: 'x',
    0x5900: 'y',
    0x5A00: 'z',
    0x5B00: '{',
    0x5C00: '|',
    0x5D00: '}',
    0x8000: '¡',
    0x8100: '¢',
    0x8200: '£',
    0x8300: '¤',
    0x8400: '¥',
    0x8500: '¦',
    0x8600: '§',
    0x8800: '¨',
    0x8900: '©',
    0x8A00: 'ª',
    0x8B00: '«',
    0x8C00: '¬',
    0x8D00: '®',
    0x8E00: '°',
    0x8F00: '±',
    0x9000: '²',
    0x9100: '³',
    0x9200: '´',
    0x9300: 'µ',
    0x9400: '¶',
    0x9700: '¹',
    0x9800: 'º',
    0x9900: '»',
    0x9A00: '¼',
    0x9B00: '½',
    0x9C00: '¾',
    0x9E00: '¿',
    0x9F00: 'À',
    0xA000: 'Á',
    0xA100: 'Â',
    0xA200: 'Ã',
    0xA300: 'Ä',
    0xA400: 'Å',
    0xA500: 'Æ',
    0xA600: 'Ç',
    0xA700: 'È',
    0xA800: 'É',
    0xA900: 'Ê',
    0xAA00: 'Ë',
    0xAB00: 'Ì',
    0xAC00: 'Í',
    0xAD00: 'Î',
    0xAE00: 'Ï',
    0xAF00: 'Ð',
    0xB000: 'Ñ',
    0xB100: 'Ò',
    0xB200: 'Ó',
    0xB300: 'Ô',
    0xB400: 'Õ',
    0xB500: 'Ö',
    0xB700: 'Ø',
    0xB800: 'Ù',
    0xB900: 'Ú',
    0xBA00: 'Û',
    0xBB00: 'Ü',
    0xBC00: 'Ý',
    0xBD00: 'Þ',
    0xBE00: 'ß',
    0xC000: 'à',
    0xC100: 'á',
    0xC200: 'â',
    0xC300: 'ã',
    0xC400: 'ä',
    0xC500: 'å',
    0xC600: 'æ',
    0xC700: 'ç',
    0xC800: 'è',
    0xC900: 'é',
    0xCA00: 'ê',
    0xCB00: 'ë',
    0xCC00: 'ì',
    0xCD00: 'í',
    0xCE00: 'î',
    0xCF00: 'ï',
    0xD000: 'ð',
    0xD100: 'ñ',
    0xD200: 'ò',
    0xD300: 'ó',
    0xD400: 'ô',
    0xD500: 'õ',
    0xD600: 'ö',
    0xD700: '÷',
    0xD800: 'ø',
    0xD900: 'ù',
    0xDA00: 'ú',
    0xDB00: 'û',
    0xDC00: 'ü',
    0xDD00: 'ý',
    0xDE00: 'þ',
    0xDF00: 'ÿ',
    0xE200: 'ꝏ',
    0xE300: '𝄞',
}

# -------------------------
# Helpers de I/O e encoding
# -------------------------
def read_u32_le(f):
    data = f.read(4)
    if len(data) < 4:
        raise EOFError(translate("err_expected_id10"))
    return struct.unpack('<I', data)[0]

def word_to_char(raw_bytes):
    if len(raw_bytes) != 2:
        return '??'
    word = raw_bytes[0] << 8 | raw_bytes[1]
    if word in CHAR_TABLE:
        return CHAR_TABLE[word]
    return f"[{word:04X}]"

def build_reverse_table():
    rev = {}
    for k, v in CHAR_TABLE.items():
        packed = struct.pack('>H', k)
        if v not in rev:
            rev[v] = packed
    return rev

REVERSE_TABLE = build_reverse_table()

# -------------------------
# Extração .MES
# -------------------------
def extract_mes(path, log_fn=None):
    if log_fn is None:
        log_fn = logger
    log_fn(translate("log_reading", path=path))
    with open(path, "rb") as f:
        magic = f.read(4)
        if magic != b".MES":
            log_fn(translate("warn_magic_diff", magic=magic))
        version = read_u32_le(f)
        header_size = read_u32_le(f)
        log_fn(translate("log_version_header", version=version, header_size=header_size))

        header_start = f.tell()
        f.seek(header_start)
        header = f.read(header_size * 4)

        offsets = []
        for i in range(0, len(header), 4):
            val = struct.unpack_from("<I", header, i)[0]
            if val != 0:
                offsets.append(val)
        log_fn(translate("log_offsets", n=len(offsets)))

        base = os.path.splitext(os.path.basename(path))[0]
        out_txt_path = os.path.join(os.path.dirname(path), f"{base}.txt")

        with open(out_txt_path, "w", encoding="utf-8") as out:
            for idx, off in enumerate(offsets, start=1):
                f.seek(off)

                ID_10 = f.read(10)
                if len(ID_10) != 10:
                    raise ValueError(translate("err_expected_id10"))
                chars = []
                while True:
                    raw = f.read(2)
                    if len(raw) < 2:
                        log_fn(translate("err_unexpected_end_block", idx=idx))
                        break
                    if raw == b'\xFF\xFF':
                        break
                    elif raw == b'\xF4\xFF':
                        nextraw = f.read(2)
                        value = int.from_bytes(nextraw, 'little')
                        chars.append(translate("log_bt_token", value=value))
                    elif raw == b'\xFE\xFF':
                        nextraw = f.read(2)
                        chars.append(translate("log_cr_token", hexval=nextraw.hex().upper()))
                    elif raw == b'\xF2\xFF':
                        nextraw = f.read(4)
                        chars.append(translate("log_lf_token", hexval=nextraw.hex().upper()))
                    else:
                        chars.append(word_to_char(raw))

                text = ''.join(chars)
                out.write(text)
                out.write("\n")

        log_fn(translate("log_extracted", out=out_txt_path))
        return out_txt_path

# -------------------------
# Reinsere .MES
# -------------------------
def reinsert_mes(txt_path, log_fn=None):
    if log_fn is None:
        log_fn = logger

    base = os.path.splitext(os.path.basename(txt_path))[0]
    mes_path = os.path.join(os.path.dirname(txt_path), f"{base}.MES")
    original_mes = os.path.join(os.path.dirname(txt_path), f"{base}.MES")

    with open(txt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    ids_bytes_list = []

    if os.path.exists(original_mes):
        try:
            with open(original_mes, "rb") as orig:
                magic = orig.read(4)
                if magic != b".MES":
                    log_fn(translate("warn_magic_diff", magic=magic))
                version = read_u32_le(orig)
                header_count_orig = read_u32_le(orig)
                raw_header = orig.read(header_count_orig * 4)

                offsets = []
                for idx in range(header_count_orig):
                    val = struct.unpack_from('<I', raw_header, idx*4)[0]
                    if val != 0:
                        offsets.append(val)

                log_fn(translate("log_reading", path=original_mes) + f" -> {len(offsets)} offsets válidos encontrados.")

                for i, off in enumerate(offsets):
                    try:
                        orig.seek(off)
                        id10 = orig.read(10)
                        if len(id10) != 10:
                            log_fn(translate("warn_id_len", idx=i+1))
                            id10 = (id10 + b'\x00'*10)[:10]
                        ids_bytes_list.append(id10)
                    except Exception as e:
                        log_fn(translate("warn_fail_read_id", off=off, err=str(e)))
                        ids_bytes_list.append(b'\x00'*10)
        except Exception as e:
            log_fn(translate("msg_error_reinsert", err=str(e)))
            ids_bytes_list = []
    else:
        log_fn(translate("warn_no_original", path=original_mes))

    if not ids_bytes_list:
        log_fn(translate("warn_no_original", path=original_mes))
        id_pattern = re.compile(r"(\[[0-9A-Fa-f]{4}\]\s*){5}")
        for line in lines:
            m = id_pattern.match(line)
            if m:
                tokens = re.findall(r"\[([0-9A-Fa-f]{4})\]", line[:m.end()])
                try:
                    id_bytes = b''.join([struct.pack(">H", int(x, 16)) for x in tokens])
                except Exception:
                    id_bytes = b'\x00'*10
                if len(id_bytes) != 10:
                    id_bytes = (id_bytes + b'\x00'*10)[:10]
                ids_bytes_list.append(id_bytes)
            else:
                ids_bytes_list.append(b'\x00'*10)
        log_fn(translate("log_reading", path=txt_path) + f" -> {len(ids_bytes_list)} IDs obtidos via fallback.")

    blocks = []
    for line_idx, line in enumerate(lines):
        line = line.rstrip("\n\r")
        text_part = line
        if " = " in line:
            parts = line.split(" = ", 1)
            text_part = parts[1]

        text_bytes = b''
        i = 0
        while i < len(text_part):
            if text_part[i] == '[':
                end_idx = text_part.find(']', i)
                if end_idx == -1:
                    text_bytes += REVERSE_TABLE.get(text_part[i], b'\x00\x00')
                    i += 1
                    continue

                token = text_part[i+1:end_idx]

                if token.startswith("BT"):
                    hexval = token[2:]
                    val = int(hexval, 16) if hexval else 0
                    text_bytes += b'\xF4\xFF' + struct.pack('<H', val)

                elif token.startswith("CR"):
                    hexval = token[2:]
                    try:
                        text_bytes += b'\xFE\xFF' + bytes.fromhex(hexval)
                    except Exception:
                        log_fn(translate("warn_cr_invalid", line=line_idx+1, token=token))
                        text_bytes += b'\xFE\xFF' + b'\x00\x00'

                elif token.startswith("LF"):
                    hexval = token[2:]
                    try:
                        text_bytes += b'\xF2\xFF' + bytes.fromhex(hexval)
                    except Exception:
                        log_fn(translate("warn_lf_invalid", line=line_idx+1, token=token))
                        text_bytes += b'\xF2\xFF' + b'\x00\x00\x00\x00'

                else:
                    try:
                        val = int(token, 16)
                        text_bytes += struct.pack('>H', val)
                    except ValueError:
                        for ch in f"[{token}]":
                            text_bytes += REVERSE_TABLE.get(ch, b'\x00\x00')
                            log_fn(translate("warn_token_invalid", line=line_idx+1, token=token))
                i = end_idx + 1
            else:
                text_bytes += REVERSE_TABLE.get(text_part[i], b'\x00\x00')
                i += 1

        text_bytes += b'\xFF\xFF'

        if line_idx < len(ids_bytes_list):
            id_bytes = ids_bytes_list[line_idx]
            if len(id_bytes) != 10:
                log_fn(translate("warn_id_len", idx=line_idx+1))
                id_bytes = (id_bytes + b'\x00'*10)[:10]
        else:
            log_fn(translate("warn_id_len", idx=line_idx+1))
            id_bytes = b'\x00'*10

        blocks.append(id_bytes + text_bytes)

    raw_header = None
    if os.path.exists(original_mes):
        try:
            with open(original_mes, 'rb') as orig:
                orig.seek(8)
                header_count_orig = struct.unpack('<I', orig.read(4))[0]
                orig.seek(12)
                raw_header = orig.read(header_count_orig * 4)
        except Exception:
            raw_header = None

    with open(mes_path, 'r+b') as out:
        out.seek(8)
        header_count_orig = struct.unpack('<I', out.read(4))[0]
        out.seek(header_count_orig * 4, 1)

        real_offsets = []
        for block in blocks:
            real_offsets.append(out.tell())
            out.write(block)

        out.seek(12)
        if raw_header is not None:
            ptr_idx = 0
            for i in range(len(raw_header)//4):
                val = struct.unpack_from('<I', raw_header, i*4)[0]
                if val == 0:
                    out.write(struct.pack('<I', 0))
                else:
                    if ptr_idx < len(real_offsets):
                        out.write(struct.pack('<I', real_offsets[ptr_idx]))
                        ptr_idx += 1
                    else:
                        out.write(struct.pack('<I', 0))
                        log_fn(translate("warn_missing_offset_entry", i=i))
        else:
            for off in real_offsets:
                out.write(struct.pack('<I', off))

    log_fn(translate("log_rewrite_done", out=mes_path))
    return mes_path

# ==========================
# Funções de seleção / integração com host (ALL FOR ONE)
# ==========================
def selecionar_extrair_mes():
    path = filedialog.askopenfilename(
        title=translate("select_mes_file"),
        filetypes=[("MES files", "*.MES"), (translate("select_txt_file"), "*.*")]
    )
    if not path:
        return
    threading.Thread(target=_run_extract, args=(path,), daemon=True).start()

def _run_extract(path):
    try:
        out = extract_mes(path, log_fn=logger)
        messagebox.showinfo(translate("msg_title_done"), translate("msg_done_extract", out=out))
    except Exception as e:
        logger(f"Erro: {e}")
        messagebox.showerror(translate("msg_title_error"), str(e))

def selecionar_reinserir_mes():
    path = filedialog.askopenfilename(
        title=translate("select_txt_file"),
        filetypes=[("TXT files", "*.txt"), (translate("select_txt_file"), "*.*")]
    )
    if not path:
        return
    threading.Thread(target=_run_reinsert, args=(path,), daemon=True).start()

def _run_reinsert(path):
    try:
        out = reinsert_mes(path, log_fn=logger)
        messagebox.showinfo(translate("msg_title_done"), translate("msg_done_reinsert", out=out))
    except Exception as e:
        logger(f"Erro: {e}")
        messagebox.showerror(translate("msg_title_error"), str(e))

# ==========================
# Registro do plugin (padrão)
# ==========================
def register_plugin(log_func, option_getter, host_language="pt_BR"):
    """
    Retorna get_plugin_info() compatível com o host.
    """
    global logger, current_language
    logger = log_func or print
    current_language = host_language

    def get_plugin_info():
        return {
            "name": translate("plugin_name"),
            "description": translate("plugin_description"),
            "commands": [
                {"label": translate("extract_mes"), "action": selecionar_extrair_mes},
                {"label": translate("reinsert_mes"), "action": selecionar_reinserir_mes},
                {"label": translate("extract_xpc"), "action": selecionar_extrair_xpc},
                {"label": translate("reinsert_xpc"), "action": selecionar_reinserir_xpc},
            ]
        }
    return get_plugin_info
