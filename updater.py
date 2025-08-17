import os
import requests

OWNER = "TicoDoido"
REPO = "all_for_one"
BRANCH = "main"
LOCAL_ROOT = "."  # pasta local para salvar

def baixar_repo(path=""):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}?ref={BRANCH}"
    r = requests.get(url)
    r.raise_for_status()
    for item in r.json():
        if item['type'] == 'file':
            download_url = item['download_url']
            content = requests.get(download_url).content
            local_path = os.path.join(LOCAL_ROOT, item['path'])
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(content)
            print(f"Baixado: {local_path}")
        elif item['type'] == 'dir':
            baixar_repo(item['path'])  # chamada recursiva para subpastas

if __name__ == "__main__":
    baixar_repo()
