# Parte do script feito por Krisp
import struct
import os
import threading
from tkinter import filedialog, messagebox
from collections import defaultdict

# ==========================
# Traduções
# ==========================
plugin_translations = {
    "pt_BR": {
        "plugin_name": "AFS (PS2) Extrai e remonta arquivos",
        "plugin_description": "Extrai e recria arquivos AFS de Playstation 2",
        "extract_file": "Extrair Arquivo",
        "rebuild_file": "Reconstruir AFS",
        "select_afs_file": "Selecione um arquivo AFS",
        "select_original_afs": "Selecione o AFS ORIGINAL (será sobrescrito)",
        "select_extracted_folder": "Selecione a pasta extraída (se necessário)",
        "invalid_file_magic": "Arquivo inválido: Magic incorreto (esperado 'AFS\\x00').",
        "metadata_pointer_found": "Ponteiro da tabela de metadados encontrado!!!",
        "invalid_metadata_pointer": "Ponteiro de metadados inválido ou nulo. Extraindo sem nomes de grupo.",
        "metadata_pointer_not_found": "Não foi possível encontrar o ponteiro para a tabela de metadados. Extraindo sem nomes de grupo.",
        "extracting_to_group": "Extraindo:{file}",
        "extracting_to_root": "Extrair: {file}",
        "completed": "Concluído",
        "extraction_completed": "Extração de {count} arquivos concluída em:\n{path}",
        "file_not_found": "Arquivo não encontrado: {file}",
        "unexpected_error": "Ocorreu um erro inesperado: {error}",
        "detailed_error": "Erro detalhado: {error}",
        "afs_files": "Arquivos AFS",
        "all_files": "Todos os arquivos",
        "rebuild_started": "Reconstrução iniciada",
        "rebuild_ok": "AFS reconstruído (sobrescrito) em:\n{path}",
        "list_missing": "Lista .txt não encontrada:\n{path}",
        "folder_missing": "Pasta de extração não encontrada:\n{path}",
        "list_count_mismatch": "A contagem de arquivos na lista ({lst}) difere da do AFS original ({afs}). Operação abortada.",
        "missing_extracted_file": "Arquivo listado não existe na pasta extraída:\n{path}",
        "reading_list": "Lendo lista:\n{path}",
        "writing_file": "Escrevendo arquivo {i}/{n}: {name}",
        "metadata_copied": "Bloco de metadados copiado para o final (novo ponteiro: 0x{ptr:08X}).",
        "header_updated": "Tabela de posições/tamanhos e ponteiro de metadados atualizados.",
    },
    "en_US": {
        "plugin_name": "AFS (PS2) Extract and rebuild files",
        "plugin_description": "Extracts and recreates AFS files from Playstation 2",
        "extract_file": "Extract File",
        "rebuild_file": "Rebuild AFS",
        "select_afs_file": "Select an AFS file",
        "select_original_afs": "Select the ORIGINAL AFS (will be overwritten)",
        "select_extracted_folder": "Select the extracted folder (if needed)",
        "invalid_file_magic": "Invalid file: Incorrect magic (expected 'AFS\\x00').",
        "metadata_pointer_found": "Metadata table pointer found!!!",
        "invalid_metadata_pointer": "Invalid or null metadata pointer. Extracting without group names.",
        "metadata_pointer_not_found": "Could not find pointer to metadata table. Extracting without group names.",
        "extracting_to_group": "Extracting:{file}",
        "extracting_to_root": "Extracting: {file}",
        "completed": "Completed",
        "extraction_completed": "Extraction of {count} files completed in:\n{path}",
        "file_not_found": "File not found: {file}",
        "unexpected_error": "An unexpected error occurred: {error}",
        "detailed_error": "Detailed error: {error}",
        "afs_files": "AFS files",
        "all_files": "All files",
        "rebuild_started": "Rebuild started",
        "rebuild_ok": "AFS rebuilt (overwritten) at:\n{path}",
        "list_missing": "List .txt not found:\n{path}",
        "folder_missing": "Extracted folder not found:\n{path}",
        "list_count_mismatch": "File count in list ({lst}) differs from original AFS ({afs}). Aborting.",
        "missing_extracted_file": "Listed file does not exist in extracted folder:\n{path}",
        "reading_list": "Reading list:\n{path}",
        "writing_file": "Writing file {i}/{n}: {name}",
        "metadata_copied": "Metadata block copied to the end (new pointer: 0x{ptr:08X}).",
        "header_updated": "Offsets/sizes table and metadata pointer updated.",
    },
    "es_ES": {
        "plugin_name": "AFS (PS2) Extraer y reconstruir archivos",
        "plugin_description": "Extrae y recrea archivos AFS de Playstation 2",
        "extract_file": "Extraer Archivo",
        "rebuild_file": "Reconstruir AFS",
        "select_afs_file": "Seleccionar un archivo AFS",
        "select_original_afs": "Seleccione el AFS ORIGINAL (será sobrescrito)",
        "select_extracted_folder": "Seleccione la carpeta extraída (si es necesario)",
        "invalid_file_magic": "Archivo inválido: Magic incorrecto (se esperaba 'AFS\\x00').",
        "metadata_pointer_found": "¡Puntero de tabla de metadatos encontrado!",
        "invalid_metadata_pointer": "Puntero de metadatos inválido o nulo. Extrayendo sin nombres de grupo.",
        "metadata_pointer_not_found": "No se pudo encontrar el puntero a la tabla de metadatos. Extrayendo sin nombres de grupo.",
        "extracting_to_group": "Extrayendo:{file}",
        "extracting_to_root": "Extrayendo: {file}",
        "completed": "Completado",
        "extraction_completed": "Extracción de {count} archivos completada en:\n{path}",
        "file_not_found": "Archivo no encontrado: {file}",
        "unexpected_error": "Ocurrió un error inesperado: {error}",
        "detailed_error": "Error detallado: {error}",
        "afs_files": "Archivos AFS",
        "all_files": "Todos los archivos",
        "rebuild_started": "Reconstrucción iniciada",
        "rebuild_ok": "AFS reconstruido (sobrescrito) en:\n{path}",
        "list_missing": "No se encontró la lista .txt:\n{path}",
        "folder_missing": "Carpeta extraída no encontrada:\n{path}",
        "list_count_mismatch": "El número de archivos en la lista ({lst}) difiere del AFS original ({afs}). Abortando.",
        "missing_extracted_file": "El archivo listado no existe en la carpeta extraída:\n{path}",
        "reading_list": "Leyendo lista:\n{path}",
        "writing_file": "Escribiendo archivo {i}/{n}: {name}",
        "metadata_copied": "Bloque de metadatos copiado al final (nuevo puntero: 0x{ptr:08X}).",
        "header_updated": "Tabla de offsets/tamaños y puntero de metadatos actualizados.",
    }
}

# ==========================
# Globais e utilidades
# ==========================
logger = print
current_language = "pt_BR"

def translate(key, **kwargs):
    lang_dict = plugin_translations.get(current_language, plugin_translations["pt_BR"])
    translation = lang_dict.get(key, key)
    if kwargs:
        try:
            return translation.format(**kwargs)
        except Exception:
            return translation
    return translation

def pad_to_boundary(fobj, boundary):
    """Escreve zeros até o offset atual virar múltiplo de 'boundary'."""
    cur = fobj.tell()
    pad = (-cur) % boundary
    if pad:
        fobj.write(b"\x00" * pad)

# ==========================
# Registro do plugin
# ==========================
def register_plugin(log_func, option_getter, host_language="pt_BR"):
    global logger, current_language
    logger = log_func or print
    current_language = host_language

    def get_plugin_info():
        return {
            "name": translate("plugin_name"),
            "description": translate("plugin_description"),
            "commands": [
                {"label": translate("extract_file"), "action": selecionar_arquivo},
                {"label": translate("rebuild_file"), "action": selecionar_reconstrucao},
            ]
        }
    return get_plugin_info

# ==========================
# EXTRAÇÃO (igual à sua implementação anterior)
# ==========================
def extrair_afs(arquivo_afs):
    try:
        with open(arquivo_afs, 'rb') as f:
            magic = f.read(4)
            if magic != b'AFS\x00':
                messagebox.showerror(translate("completed"), translate("invalid_file_magic"))
                return

            total_itens = struct.unpack('<I', f.read(4))[0]
            posicoes, tamanhos = [], []
            for _ in range(total_itens):
                posicoes.append(struct.unpack('<I', f.read(4))[0])
                tamanhos.append(struct.unpack('<I', f.read(4))[0])

            nomes_grupos = []
            # Descobrir ponteiro de metadados
            if tamanhos[-1] == 0:
                ponteiro_meta = posicoes[-1]
                posicoes.pop(); tamanhos.pop()
            else:
                ponteiro_meta = struct.unpack('<I', f.read(4))[0]

            if ponteiro_meta > 0:
                logger(translate("metadata_pointer_found"))
                f.seek(ponteiro_meta)
                for _ in range(len(posicoes)):
                    nome_bytes = f.read(32)
                    if len(nome_bytes) < 32:
                        nomes_grupos.append("")
                        continue
                    try:
                        nome_limpo = nome_bytes.strip(b'\x00').decode('shift_jis', errors='ignore').strip()
                    except Exception:
                        nome_limpo = ""
                    nomes_grupos.append(nome_limpo)
                    f.seek(16, 1)  # pular 16 bytes (campos não utilizados aqui)
            else:
                messagebox.showwarning(translate("completed"), translate("metadata_pointer_not_found"))
                nomes_grupos = [""] * len(posicoes)

            pasta_saida = os.path.join(os.path.dirname(arquivo_afs), os.path.splitext(os.path.basename(arquivo_afs))[0])
            os.makedirs(pasta_saida, exist_ok=True)

            contagem_sufixos = defaultdict(int)
            base_nome_afs = os.path.splitext(os.path.basename(arquivo_afs))[0]
            lista_arquivos = []

            for i, (pos, tamanho, grupo) in enumerate(zip(posicoes, tamanhos, nomes_grupos)):
                if tamanho == 0:
                    continue
                f.seek(pos)
                dados = f.read(tamanho)

                if grupo:
                    nome_base = grupo
                    nome_arquivo = nome_base
                    caminho_saida = os.path.join(pasta_saida, nome_arquivo)
                    contador = 1
                    while os.path.exists(caminho_saida):
                        nome_arquivo = f"{nome_base}_{contador}"
                        caminho_saida = os.path.join(pasta_saida, nome_arquivo)
                        contador += 1
                    logger(translate("extracting_to_root", file=nome_arquivo))
                else:
                    contagem_sufixos['__root__'] += 1
                    nome_arquivo = f"{base_nome_afs}_{contagem_sufixos['__root__']:05d}.bin"
                    caminho_saida = os.path.join(pasta_saida, nome_arquivo)
                    logger(translate("extracting_to_root", file=nome_arquivo))

                with open(caminho_saida, 'wb') as saida:
                    saida.write(dados)

                nome_arquivo = os.path.normpath(nome_arquivo)
                lista_arquivos.append(nome_arquivo)

            lista_txt = os.path.join(os.path.dirname(arquivo_afs), os.path.splitext(os.path.basename(arquivo_afs))[0]) + ".txt"
            with open(lista_txt, 'w', encoding='utf-8', newline='\n') as arquivo_lista:
                for nome in lista_arquivos:
                    arquivo_lista.write(nome + '\n')

            messagebox.showinfo(translate("completed"), translate("extraction_completed", count=len(posicoes), path=pasta_saida))

    except FileNotFoundError:
        messagebox.showerror(translate("completed"), translate("file_not_found", file=arquivo_afs))
    except Exception as e:
        messagebox.showerror(translate("completed"), translate("unexpected_error", error=str(e)))
        logger(translate("detailed_error", error=str(e)))

def selecionar_arquivo():
    caminho = filedialog.askopenfilename(
        title=translate("select_afs_file"),
        filetypes=[(translate("afs_files"), "*.afs"), (translate("all_files"), "*.*")]
    )
    if caminho:
        threading.Thread(target=extrair_afs, args=(caminho,), daemon=True).start()

# ==========================
# RECONSTRUÇÃO IN-PLACE
# ==========================
def reconstruir_afs_inplace(afs_original_path):
    try:
        # Primeiro: abrir em modo r+b para leitura e escrita no mesmo arquivo
        with open(afs_original_path, 'r+b') as f:
            # --- Ler cabeçalho ---
            magic = f.read(4)
            if magic != b'AFS\x00':
                messagebox.showerror(translate("completed"), translate("invalid_file_magic"))
                return

            total_itens = struct.unpack('<I', f.read(4))[0]
            orig_pos = []
            orig_size = []
            for _ in range(total_itens):
                orig_pos.append(struct.unpack('<I', f.read(4))[0])
                orig_size.append(struct.unpack('<I', f.read(4))[0])

            # Detecta formato do ponteiro de metadados
            meta_as_entry = False
            if orig_size[-1] == 0:
                meta_as_entry = True
                orig_meta_ptr = orig_pos[-1]
                data_count = total_itens - 1
            else:
                orig_meta_ptr = struct.unpack('<I', f.read(4))[0]
                data_count = total_itens

            # Lê o bloco de metadados ORIGINAL (do ponteiro até o EOF) para manter em memória
            f.seek(0, os.SEEK_END)
            file_end = f.tell()
            if orig_meta_ptr > 0 and orig_meta_ptr < file_end:
                f.seek(orig_meta_ptr)
                metadata_blob = f.read()
            else:
                metadata_blob = b""

            # Preparar informações sobre a tabela para reescrever depois
            table_size = total_itens * 8
            ptr_offset_pos = 8 + table_size  # se existir ponteiro separado, este é o offset dele

            # --- Localizar pasta extraída e lista .txt ---
            base = os.path.splitext(os.path.basename(afs_original_path))[0]
            extracted_dir = os.path.join(os.path.dirname(afs_original_path), base)
            list_txt = os.path.join(os.path.dirname(afs_original_path), base + ".txt")

            if not os.path.isfile(list_txt):
                messagebox.showerror(translate("completed"), translate("list_missing", path=list_txt))
                return
            if not os.path.isdir(extracted_dir):
                messagebox.showerror(translate("completed"), translate("folder_missing", path=extracted_dir))
                return

            logger(translate("reading_list", path=list_txt))

            # Leitura robusta da lista (tenta utf-8, cai para cp1252/latin-1)
            lines = None
            for enc in ('utf-8', 'cp1252', 'latin-1'):
                try:
                    with open(list_txt, 'r', encoding=enc) as fh:
                        lines = [ln.strip() for ln in fh.readlines() if ln.strip()]
                    break
                except Exception:
                    continue
            if lines is None:
                with open(list_txt, 'r', errors='ignore') as fh:
                    lines = [ln.strip() for ln in fh.readlines() if ln.strip()]

            if len(lines) != data_count:
                messagebox.showerror(
                    translate("completed"),
                    translate("list_count_mismatch", lst=len(lines), afs=data_count)
                )
                return

            # Montar caminhos absolutos dos arquivos listados
            file_paths = []
            for rel in lines:
                candidate = os.path.join(extracted_dir, rel)
                if not os.path.isfile(candidate):
                    alt = os.path.join(extracted_dir, os.path.basename(rel))
                    if os.path.isfile(alt):
                        candidate = alt
                    else:
                        messagebox.showerror(translate("completed"), translate("missing_extracted_file", path=candidate))
                        return
                file_paths.append(candidate)

            # --- Iniciar escrita dos dados IN-PLACE ---
            # Vamos começar a escrever a partir da primeira posição original
            first_data_offset = orig_pos[0]
            # Garantir que o ponteiro do arquivo esteja no primeiro offset
            f.seek(0, os.SEEK_SET)
            # (Não sobrescrevemos o cabeçalho agora; apenas nos posicionamos para gravar os dados)
            # Se o primeiro_data_offset for menor que onde estamos, ainda podemos escrever (posicionar)
            f.seek(first_data_offset, os.SEEK_SET)

            new_pos = []
            new_size = []

            for idx, path in enumerate(file_paths, start=1):
                logger(translate("writing_file", i=idx, n=len(file_paths), name=os.path.basename(path)))

                start = f.tell()

                with open(path, 'rb') as rf:
                    data = rf.read()
                f.write(data)
                size = len(data)

                # Padding pós-arquivo até múltiplo de 2048
                pad_to_boundary(f, 2048)

                new_pos.append(start)
                new_size.append(size)

            # Agora escrevemos o bloco de metadados original no final (expande o arquivo se necessário)
            new_meta_ptr = f.tell()
            if metadata_blob:
                f.write(metadata_blob)
            logger(translate("metadata_copied", ptr=new_meta_ptr))

            # Finalmente, reescreve a tabela de offsets/tamanhos e o ponteiro/meta-entry na posição correta do header
            # Escrevemos diretamente no arquivo aberto (in-place)
            f.seek(8, os.SEEK_SET)  # após magic + count

            if meta_as_entry:
                # Escrever N entradas de dados
                for p, s in zip(new_pos, new_size):
                    f.write(struct.pack('<I', p))
                    f.write(struct.pack('<I', s))
                # última entrada = ponteiro de metadados com tamanho zero
                f.write(struct.pack('<I', new_meta_ptr))
                f.write(struct.pack('<I', 0))
            else:
                # Escrever entradas (total_itens)
                for p, s in zip(new_pos, new_size):
                    f.write(struct.pack('<I', p))
                    f.write(struct.pack('<I', s))
                # Escrever ponteiro separado logo após a tabela
                f.seek(ptr_offset_pos, os.SEEK_SET)
                f.write(struct.pack('<I', new_meta_ptr))

            logger(translate("header_updated"))

        # Fim do with open(arquivo fechado)
        messagebox.showinfo(translate("rebuild_started"), translate("rebuild_ok", path=afs_original_path))

    except FileNotFoundError as e:
        messagebox.showerror(translate("completed"), translate("file_not_found", file=str(e)))
    except Exception as e:
        messagebox.showerror(translate("completed"), translate("unexpected_error", error=str(e)))
        logger(translate("detailed_error", error=str(e)))

def selecionar_reconstrucao():
    afs_path = filedialog.askopenfilename(
        title=translate("select_original_afs"),
        filetypes=[(translate("afs_files"), "*.afs"), (translate("all_files"), "*.*")]
    )
    if afs_path:
        threading.Thread(target=reconstruir_afs_inplace, args=(afs_path,), daemon=True).start()
