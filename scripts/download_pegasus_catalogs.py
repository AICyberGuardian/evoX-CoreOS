# download_pegasus_catalogs.py
import os
import urllib.request

def download_catalogs():
    """
    Télécharge les catalogues Pegasus distants dans le dossier json/pegasus-dl/
    en contournant les restrictions 403 Forbidden grâce à un User-Agent.
    """
    urls = {
        "dlps.json": "https://pegasus-dl.dev/catalogs/dlps.json",
        "pippo.json": "https://pegasus-dl.dev/catalogs/pippo.json",
        "pfs.json": "https://pegasus-dl.dev/catalogs/pfs.json",
        "zer0.json": "https://pegasus-dl.dev/catalogs/zer0.json"
    }

    output_dir = os.path.join("json", "pegasus-dl")
    os.makedirs(output_dir, exist_ok=True)

    # En-tête pour simuler un navigateur et éviter le blocage 403
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    for filename, url in urls.items():
        dest_path = os.path.join(output_dir, filename)
        try:
            print(f"Téléchargement de {filename}...")
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response, open(dest_path, 'wb') as out_file:
                out_file.write(response.read())
            print(f"Succès : {dest_path}")
        except Exception as e:
            print(f"Erreur pour {filename} : {e}")

if __name__ == "__main__":
    download_catalogs()
