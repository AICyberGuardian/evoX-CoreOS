# download_pegasus_catalogs.py
import os
import json
import urllib.request

def convert_to_bytes(size_str):
    """Convertit eng Gréisst als String (bspw. '1.5 GB', '500 MB') an Bytes (int)."""
    if not size_str or not isinstance(size_str, str):
        return 0
    size_str = size_str.strip().upper()
    try:
        if "GB" in size_str or "GO" in size_str:
            return int(float(size_str.replace("GB", "").replace("GO", "").strip()) * 1024 * 1024 * 1024)
        elif "MB" in size_str or "MO" in size_str:
            return int(float(size_str.replace("MB", "").replace("MO", "").strip()) * 1024 * 1024)
        elif "KB" in size_str or "KO" in size_str:
            return int(float(size_str.replace("KB", "").replace("KO", "").strip()) * 1024)
        elif "B" in size_str:
            return int(float(size_str.replace("B", "").strip()))
        else:
            return int(float(size_str))
    except ValueError:
        return 0

def extract_author_credits(item):
    """Extrahéiert an vereenegt d'Auteuren an d'Gruppen (PiPPo, DLPS, zer0, pfs, etc.)."""
    for field in ["author", "credits", "repo", "groups", "sources"]:
        val = item.get(field)
        if val:
            if isinstance(val, list):
                return ", ".join(str(v) for v in val)
            return str(val)
    return "Community"

def build_pegasus_standard(items_source):
    """
    1. FORMAT PEGASUS STANDARD
    Generéiert eng Struktur mat 'game_list'
    """
    pegasus_list = []
    for item in items_source:
        if not isinstance(item, dict):
            continue
        
        title = item.get("name") or item.get("title") or "Unknown Title"
        author = extract_author_credits(item)
        description = item.get("description", "")
        if author and author != "Community":
            description = f"Credits / Groups: {author}\n\n{description}"

        cover = item.get("posterUrl") or item.get("cover") or item.get("icon") or ""
        
        raw_url = item.get("url") or item.get("download_url") or ""
        files_field = item.get("files", [])
        if not raw_url and isinstance(files_field, list) and len(files_field) > 0:
            raw_url = files_field[0].get("url", "")

        pegasus_list.append({
            "title": title,
            "summary": description,
            "assets": {
                "cover": cover
            },
            "launch": raw_url,
            "metadata": {
                "version": item.get("version", "v1.0.0"),
                "category": item.get("category", "Games / Apps"),
                "size": item.get("size", "0 MB"),
                "developer": author
            }
        })
    
    return {"game_list": pegasus_list}

def build_pegasus_adapted(items_source):
    """
    2. FORMAT PEGASUS-DL ADAPTED
    Generéiert eng Struktur mat 'packages' a 'downloadLinks'
    """
    adapted_apps = []
    for item in items_source:
        if not isinstance(item, dict):
            continue

        title = item.get("name") or item.get("title") or "Unknown Title"
        title_id = item.get("titleId") or item.get("title_id") or item.get("id") or "CUSA00000"
        version = item.get("version", "v1.0.0")
        author = extract_author_credits(item)
        description = item.get("description", "")
        category = item.get("category", "Games / Apps")
        checksum = item.get("checksum") or item.get("sha256") or ""
        poster_url = item.get("posterUrl") or item.get("cover") or item.get("icon") or "https://cdn.jsdelivr.net/gh/nexgen999/evoX-CoreOS@main/assets/evoX-CoreOS_pkg.jpg"

        # Traitement dei download links
        download_links = []
        files_field = item.get("files", [])
        if isinstance(files_field, list):
            for f_item in files_field:
                if isinstance(f_item, dict) and "url" in f_item:
                    download_links.append({
                        "name": f_item.get("name", "Mirror"),
                        "url": f_item.get("url")
                    })

        if not download_links:
            dl_list = item.get("downloadLinks") or item.get("links") or []
            if isinstance(dl_list, list):
                for l in dl_list:
                    if isinstance(l, dict):
                        download_links.append({
                            "name": l.get("name", "Mirror"),
                            "url": l.get("url", "")
                        })

        if not download_links:
            raw_url = item.get("download_url") or item.get("url") or ""
            if raw_url:
                download_links = [{"name": "Direct Download", "url": raw_url}]

        if not download_links:
            continue

        adapted_apps.append({
            "titleId": title_id,
            "title": title,
            "version": version,
            "author": author,
            "category": category,
            "description": description,
            "checksum": checksum,
            "posterUrl": poster_url,
            "downloadLinks": download_links
        })

    return {
        "name": "BlackBox Catalog (Pegasus Adapted)",
        "description": "Catalogue BlackBox converti pour Pegasus-DL",
        "packages": adapted_apps
    }

def download_catalogs():
    output_dir = os.path.join("json", "pegasus-dl")
    os.makedirs(output_dir, exist_ok=True)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    # 1. Standard Catalogues (DLPS, PiPPo, PFS, Zer0)
    standard_urls = {
        "dlps.json": "https://pegasus-dl.dev/catalogs/dlps.json",
        "pippo.json": "https://pegasus-dl.dev/catalogs/pippo.json",
        "pfs.json": "https://pegasus-dl.dev/catalogs/pfs.json",
        "zer0.json": "https://pegasus-dl.dev/catalogs/zer0.json"
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

    # 2. BlackBox Source Téléchargement
    blackbox_url = "https://raw.githubusercontent.com/D3ATHLY/blackbox/main/catalog/catalogue-v2.json"
    
    try:
        print("Téléchargement du catalogue BlackBox source...")
        req = urllib.request.Request(blackbox_url, headers=headers)
        with urllib.request.urlopen(req) as response:
            raw_data = json.loads(response.read().decode('utf-8'))

        items_source = []
        if isinstance(raw_data, list):
            items_source = raw_data
        elif isinstance(raw_data, dict):
            items_source = raw_data.get("apps") or raw_data.get("items") or raw_data.get("packages") or []
            if not items_source:
                for val in raw_data.values():
                    if isinstance(val, list):
                        items_source = val
                        break

        # A) Génération de Blackbox Pegasus Standard
        pegasus_standard = build_pegasus_standard(items_source)
        pegasus_std_dest = os.path.join(output_dir, "blackbox_pegasus.json")
        with open(pegasus_std_dest, "w", encoding="utf-8") as f:
            json.dump(pegasus_standard, f, indent=4, ensure_ascii=False)
        print(f"Succès généré : {pegasus_std_dest}")

        # B) Génération de Blackbox Pegasus-DL Adapted
        pegasus_adapted = build_pegasus_adapted(items_source)
        pegasus_adapted_dest = os.path.join(output_dir, "blackbox_catalog.json")
        with open(pegasus_adapted_dest, "w", encoding="utf-8") as f:
            json.dump(pegasus_adapted, f, indent=4, ensure_ascii=False)
        print(f"Succès généré : {pegasus_adapted_dest}")

    except Exception as e:
        print(f"Erreur lors du traitement de BlackBox : {e}")

if __name__ == "__main__":
    download_catalogs()
