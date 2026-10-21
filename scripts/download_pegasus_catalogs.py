# download_pegasus_catalogs.py
import os
import json
import urllib.request

def download_catalogs():
    """
    Télécharge et adapte les catalogues Pegasus distants dans le dossier json/pegasus-dl/.
    Convertit également le catalogue BlackBox au format Pegasus-DL sous le nom blackbox_catalog.json.
    """
    output_dir = os.path.join("json", "pegasus-dl")
    os.makedirs(output_dir, exist_ok=True)

    # 1. Catalogues standards (téléchargement direct avec User-Agent)
    standard_urls = {
        "dlps.json": "https://pegasus-dl.dev/catalogs/dlps.json",
        "pippo.json": "https://pegasus-dl.dev/catalogs/pippo.json",
        "pfs.json": "https://pegasus-dl.dev/catalogs/pfs.json",
        "zer0.json": "https://pegasus-dl.dev/catalogs/zer0.json"
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    for filename, url in standard_urls.items():
        dest_path = os.path.join(output_dir, filename)
        try:
            print(f"Téléchargement de {filename}...")
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response, open(dest_path, 'wb') as out_file:
                out_file.write(response.read())
            print(f"Succès : {dest_path}")
        except Exception as e:
            print(f"Erreur pour {filename} : {e}")

    # 2. Téléchargement et adaptation du catalogue BlackBox -> blackbox_catalog.json
    blackbox_url = "https://raw.githubusercontent.com/D3ATHLY/blackbox/main/catalog/catalogue-v2.json"
    blackbox_dest = os.path.join(output_dir, "blackbox_catalog.json")
    
    try:
        print("Téléchargement et conversion du catalogue BlackBox...")
        req = urllib.request.Request(blackbox_url, headers=headers)
        with urllib.request.urlopen(req) as response:
            raw_data = json.loads(response.read().decode('utf-8'))

        # Normalisation au format Pegasus-DL
        adapted_apps = []
        
        # Le contenu source peut varier selon la structure exacte, on gère les listes ou dictionnaires
        items_source = []
        if isinstance(raw_data, list):
            items_source = raw_data
        elif isinstance(raw_data, dict):
            # Cherche la première clé contenant une liste si la structure est emboîtée
            for val in raw_data.values():
                if isinstance(val, list):
                    items_source = val
                    break

        for item in items_source:
            if not isinstance(item, dict):
                continue
            
            # Récupération ou déduction des champs
            title = item.get("name") or item.get("title") or "Unknown Title"
            title_id = item.get("titleId") or item.get("title_id") or "CUSA00000"
            version = item.get("version", "v1.0.0")
            author = item.get("author", "Unknown Author")
            description = item.get("description", "")
            category = item.get("category", "Games / Apps")
            checksum = item.get("checksum") or item.get("sha256") or ""
            
            # Correction ici : on cherche d'abord le champ "cover" (ou "posterUrl"/"icon") de BlackBox, sinon l'image par défaut
            poster_url = item.get("cover") or item.get("posterUrl") or item.get("icon") or "https://cdn.jsdelivr.net/gh/nexgen999/evoX-CoreOS@main/assets/evoX-CoreOS_pkg.jpg"
            
            # Récupération des liens de téléchargement bruts
            raw_url = item.get("url") or item.get("download_url") or ""
            download_links = item.get("downloadLinks", [])
            
            if not download_links and raw_url:
                download_links = [{"name": "Mirror", "url": raw_url}]
            elif not download_links and "links" in item:
                # Si le format utilise "links"
                for l in item["links"]:
                    if isinstance(l, dict):
                        download_links.append({"name": l.get("name", "Mirror"), "url": l.get("url", "")})

            if not download_links:
                continue

            adapted_item = {
                "titleId": title_id,
                "title": title,
                "version": version,
                "author": author,
                "category": category,
                "description": description,
                "checksum": checksum,
                "posterUrl": poster_url,
                "downloadLinks": download_links
            }
            adapted_apps.append(adapted_item)

        final_blackbox_catalog = {
            "name": "BlackBox Catalog (Pegasus Adapted)",
            "description": "Catalogue BlackBox converti pour Pegasus-DL",
            "packages": adapted_apps
        }

        with open(blackbox_dest, "w", encoding="utf-8") as f:
            json.dump(final_blackbox_catalog, f, indent=4, ensure_ascii=False)
            
        print(f"Succès et adaptation : {blackbox_dest} ({len(adapted_apps)} éléments)")

    except Exception as e:
        print(f"Erreur lors de la conversion du catalogue BlackBox : {e}")

if __name__ == "__main__":
    download_catalogs()
