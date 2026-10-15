# scripts/fetchers/homebrew_page_fetcher.py
import os
import json
import hashlib
import urllib.request
from scripts.config_rules import PATHS, BASE_URL

def fetch_homebrew_page_catalog(credits_set):
    catalog_url = "https://homebrew.page/catalog/v1.json"
    feed_dir = os.path.join(PATHS["json_dir"], "homebrew_page")
    os.makedirs(feed_dir, exist_ok=True)
    
    by_category = {}
    all_flat = []
    
    try:
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)
        
        req = urllib.request.urlopen(catalog_url)
        data = json.loads(req.read().decode('utf-8'))
        
        # Le catalogue homebrew.page stocke ses applications dans la clé 'apps'
        records = data if isinstance(data, list) else data.get('apps', data.get('records', data.get('items', [])))
        
        for item in records:
            artifact_url = item.get('artifact_url')
            if not artifact_url:
                continue
                
            kind = item.get('kind', 'app').lower() # ex: game, tool, app
            cat_display = kind.capitalize() + "s" if not kind.endswith('s') else kind.capitalize()
            
            title = item.get('name', 'Unknown App')
            version = item.get('version', 'v1.0.0') or 'v1.0.0'
            author = item.get('author', 'Unknown Author')
            description = item.get('description', '')
            sha256_val = item.get('sha256')
            titleid = item.get('titleid', 'PPSA00000')
            
            version_clean = version.replace('/', '_')
            target_dir = os.path.join(PATHS.get("categories", {}).get("apps", {}).get("root", "downloads/apps"), "homebrew_page", kind, titleid, version_clean)
            os.makedirs(target_dir, exist_ok=True)
            
            filename = f"{titleid}.zip"
            local_file_path = os.path.join(target_dir, filename)
            
            if not os.path.exists(local_file_path):
                try:
                    urllib.request.urlretrieve(artifact_url, local_file_path)
                except Exception as e:
                    print(f"    ⚠️ Erreur téléchargement Homebrew.page ({title}): {e}")
                    continue
                    
            hasher = hashlib.sha256()
            with open(local_file_path, 'rb') as fb:
                for chunk in iter(lambda: fb.read(4096), b""):
                    hasher.update(chunk)
            computed_sha = hasher.hexdigest()
            
            final_sha = sha256_val if sha256_val else computed_sha
            
            item_data = {
                "name": title,
                "filename": filename,
                "url": f"{BASE_URL}/{target_dir.replace(os.sep, '/')}/{filename}",
                "local_path": local_file_path,
                "description": description if description else f"Application {title} par {author}",
                "version": version,
                "category": cat_display,
                "kind": kind,
                "titleid": titleid,
                "author": author,
                "checksum": final_sha,
                "source": item.get('source_repo') or f"https://homebrew.page/app/{titleid}"
            }
            
            if kind not in by_category:
                by_category[kind] = {"name": cat_display, "items": []}
                
            by_category[kind]["items"].append(item_data)
            all_flat.append(item_data)
            
            credits_set.add(f"- **{author}** : [{title} (Homebrew.page)](https://homebrew.page/app/{titleid})")
            
    except Exception as e:
        print(f"    ⚠️ Impossible de récupérer le catalogue homebrew.page : {e}")
        
    return by_category, all_flat
