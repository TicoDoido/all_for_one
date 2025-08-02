import struct
import os
import threading
from tkinter import filedialog, messagebox
from collections import defaultdict

# Dicionários de tradução do plugin
plugin_translations = {
    "pt_BR": {
        "plugin_name": "AFS (PS2) Extrai e remonta arquivos",
        "plugin_description": "Extrai e recria arquivos AFS de Playstation 2",
        "extract_file": "Extrair Arquivo",
        "invalid_file_magic": "Arquivo inválido: Magic incorreto (esperado 'AFS\\x00').",
        "metadata_pointer_found": "Ponteiro da tabela de metadados encontrado: Offset={offset}, Tamanho={size}",
        "invalid_metadata_pointer": "Ponteiro de metadados inválido ou nulo. Extraindo sem nomes de grupo.",
        "metadata_pointer_not_found": "Não foi possível encontrar o ponteiro para a tabela de metadados. Extraindo sem nomes de grupo.",
        "extracting_to_group": "Extraindo para o grupo '{group}': {file}",
        "extracting_to_root": "Extraindo para a raiz: {file}",
        "completed": "Concluído",
        "extraction_completed": "Extração de {count} arquivos concluída em:\n{path}",
        "file_not_found": "Arquivo não encontrado: {file}",
        "unexpected_error": "Ocorreu um erro inesperado: {error}",
        "detailed_error": "Erro detalhado: {error}",
        "select_afs_file": "Selecione um arquivo AFS",
        "afs_files": "Arquivos AFS",
        "all_files": "Todos os arquivos"
    },
    "en_US": {
        "plugin_name": "AFS (PS2) Extract and rebuild files",
        "plugin_description": "Extracts and recreates AFS files from Playstation 2",
        "extract_file": "Extract File",
        "invalid_file_magic": "Invalid file: Incorrect magic (expected 'AFS\\x00').",
        "metadata_pointer_found": "Metadata table pointer found: Offset={offset}, Size={size}",
        "invalid_metadata_pointer": "Invalid or null metadata pointer. Extracting without group names.",
        "metadata_pointer_not_found": "Could not find pointer to metadata table. Extracting without group names.",
        "extracting_to_group": "Extracting to group '{group}': {file}",
        "extracting_to_root": "Extracting to root: {file}",
        "completed": "Completed",
        "extraction_completed": "Extraction of {count} files completed in:\n{path}",
        "file_not_found": "File not found: {file}",
        "unexpected_error": "An unexpected error occurred: {error}",
        "detailed_error": "Detailed error: {error}",
        "select_afs_file": "Select an AFS file",
        "afs_files": "AFS files",
        "all_files": "All files"
    },
    "es_ES": {
        "plugin_name": "AFS (PS2) Extraer y reconstruir archivos",
        "plugin_description": "Extrae y recrea archivos AFS de Playstation 2",
        "extract_file": "Extraer Archivo",
        "invalid_file_magic": "Archivo inválido: Magic incorrecto (se esperaba 'AFS\\x00').",
        "metadata_pointer_found": "Puntero de tabla de metadatos encontrado: Offset={offset}, Tamaño={size}",
        "invalid_metadata_pointer": "Puntero de metadatos inválido o nulo. Extrayendo sin nombres de grupo.",
        "metadata_pointer_not_found": "No se pudo encontrar el puntero a la tabla de metadatos. Extrayendo sin nombres de grupo.",
        "extracting_to_group": "Extrayendo al grupo '{group}': {file}",
        "extracting_to_root": "Extrayendo a la raíz: {file}",
        "completed": "Completado",
        "extraction_completed": "Extracción de {count} archivos completada en:\n{path}",
        "file_not_found": "Archivo no encontrado: {file}",
        "unexpected_error": "Ocurrió un error inesperado: {error}",
        "detailed_error": "Error detallado: {error}",
        "select_afs_file": "Seleccionar un archivo AFS",
        "afs_files": "Archivos AFS",
        "all_files": "Todos los archivos"
    }
}

# Variáveis globais do plugin
logger = print
current_language = "pt_BR"

def translate(key, **kwargs):
    """Função de tradução interna do plugin"""
    lang_dict = plugin_translations.get(current_language, plugin_translations["pt_BR"])
    translation = lang_dict.get(key, key)
    
    if kwargs:
        try:
            return translation.format(**kwargs)
        except:
            return translation
    return translation

def register_plugin(log_func, option_getter, host_language="pt_BR"):
    global logger, current_language
    logger = log_func or print
    current_language = host_language
    
    # Retorna uma função que sempre fornece os dados atualizados do plugin
    def get_plugin_info():
        return {
            "name": translate("plugin_name"),
            "description": translate("plugin_description"),
            "commands": [
                {"label": translate("extract_file"), "action": selecionar_arquivo},
            ]
        }
    
    return get_plugin_info

def extrair_afs(arquivo_afs):
    try:
        with open(arquivo_afs, 'rb') as f:
            magic = f.read(4)
            if magic != b'AFS\x00':
                messagebox.showerror(translate("completed"), translate("invalid_file_magic"))
                return

            total_itens = struct.unpack('<I', f.read(4))[0] + 1

            posicoes = []
            tamanhos = []
            for _ in range(total_itens):
                pos, tamanho = struct.unpack('<II', f.read(8))
                posicoes.append(pos)
                tamanhos.append(tamanho)

            ponteiro_meta = f.read(8)
            nomes_grupos = []

            if len(ponteiro_meta) == 8:
                meta_offset, meta_size = struct.unpack('<II', ponteiro_meta)
                logger(translate("metadata_pointer_found", offset=meta_offset, size=meta_size))

                if meta_offset > 0 and meta_size > 0:
                    f.seek(meta_offset)
                    for _ in range(total_itens):
                        meta_bloco = f.read(0x30)
                        if len(meta_bloco) < 16:
                            nomes_grupos.append("")
                            continue
                        
                        nome_bytes = meta_bloco[:16]
                        try:
                            nome_limpo = nome_bytes.split(b'\x00', 1)[0].decode('shift_jis', errors='ignore').strip()
                        except:
                            nome_limpo = ""
                        nomes_grupos.append(nome_limpo)
                else:
                    logger(translate("invalid_metadata_pointer"))
                    nomes_grupos = [""] * total_itens
            else:
                messagebox.showwarning(translate("completed"), translate("metadata_pointer_not_found"))
                nomes_grupos = [""] * total_itens

            pasta_saida = os.path.join(os.path.dirname(arquivo_afs), os.path.splitext(os.path.basename(arquivo_afs))[0])
            os.makedirs(pasta_saida, exist_ok=True)
            
            contagem_sufixos = defaultdict(int)
            base_nome_afs = os.path.splitext(os.path.basename(arquivo_afs))[0]

            for i, (pos, tamanho, grupo) in enumerate(zip(posicoes, tamanhos, nomes_grupos)):
                if tamanho == 0:
                    continue

                f.seek(pos)
                dados = f.read(tamanho)
                
                if grupo:
                    pasta_grupo = os.path.join(pasta_saida, grupo)
                    os.makedirs(pasta_grupo, exist_ok=True)
                    
                    contagem_sufixos[grupo] += 1
                    nome_arquivo = f"{grupo}_{contagem_sufixos[grupo]:04d}.bin"
                    caminho_saida = os.path.join(pasta_grupo, nome_arquivo)
                    logger(translate("extracting_to_group", group=grupo, file=nome_arquivo))
                else:
                    contagem_sufixos['__root__'] += 1
                    nome_arquivo = f"{base_nome_afs}_{contagem_sufixos['__root__']:05d}.bin"
                    caminho_saida = os.path.join(pasta_saida, nome_arquivo)
                    logger(translate("extracting_to_root", file=nome_arquivo))

                with open(caminho_saida, 'wb') as saida:
                    saida.write(dados)

            messagebox.showinfo(translate("completed"), translate("extraction_completed", count=total_itens, path=pasta_saida))
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