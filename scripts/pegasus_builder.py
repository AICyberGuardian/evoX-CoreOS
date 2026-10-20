# scripts/pegasus_builder.py
import os
import json
from scripts.config_rules import PATHS

def apply_pegasus_metadata(items_list):
    """
    Injecte les métadonnées personnalisées (titleId, title, icône/poster) 
    configurées via l'application Manager avec des vérifications de diagnostic.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.abspath(os.path.join(base_dir, "..", "assets", "icon", "pegasus_metadata.json"))
    
    metadata = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception:
            pass
    else:
        alt_config_path = os.path.abspath("assets/icon/pegasus_metadata.json")
        if os.path.exists(alt_config_path):
            try:
                with open(alt_config_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
            except Exception:
                pass

    for item in items_list:
        fname = item.get("filename")
        if not fname and "downloadLinks" in item and item["downloadLinks"]:
            fname = os.path.basename(item["downloadLinks"][0].get("url", ""))
        
        if fname and fname in metadata:
            overrides = metadata[fname]
            if overrides.get("titleId"):
                item["titleId"] = overrides["titleId"]
            if overrides.get("title"):
                item["title"] = overrides["title"]
            if overrides.get("icon"):
                icon_name = overrides['icon']
                if icon_name.strip():
                    item["posterUrl"] = f"https://cdn.jsdelivr.net/gh/nexgen999/evoX-CoreOS@main/assets/icon/{icon_name}"
                
    return items_list

def generate_pegasus_catalog(pkg_flat, ffpfsc_flat, output_path="json/pegasus_catalog.json"):
    """
    Génère le catalogue unifié Pegasus compatible avec les éléments PKG et FFPFSC,
    en y appliquant les métadonnées personnalisées et la structure downloadLinks requise par Pegasus-DL.
    """
    print("🎯 Génération du catalogue unifié Pegasus-DL...")
    all_items = []
    
    # Fusion et formatage des éléments PKG et FFPFSC
    for item in pkg_flat + ffpfsc_flat:
        if isinstance(item, dict):
            raw_url = item.get("url") or item.get("local_path") or ""
            if not raw_url and "downloadLinks" in item and item["downloadLinks"]:
                raw_url = item["downloadLinks"][0].get("url", "")

            if not raw_url:
                continue

            fname = item.get("filename")
            if not fname:
                fname = os.path.basename(raw_url)
            
            item["filename"] = fname
            
            # Évite les doublons
            if fname and not any(i.get("filename") == fname for i in all_items):
                title = item.get("name", os.path.splitext(fname)[0].replace("_", " ").title())
                title_id = item.get("titleId") or item.get("title_id") or "CUSA00000"
                version = item.get("version", "v1.0.0")
                author = item.get("author", "Unknown Author")
                description = item.get("description", f"Paquet {title} pour PS5")
                category = item.get("category", "Games / Apps")
                checksum = item.get("checksum") or item.get("sha256") or ""
                poster_url = item.get("posterUrl") or "https://cdn.jsdelivr.net/gh/nexgen999/evoX-CoreOS@main/assets/evoX-CoreOS_pkg.jpg"

                # Structure obligatoire exigée par Pegasus-DL avec downloadLinks
                download_links = [
                    {
                        "name": "Mirror",
                        "url": raw_url
                    }
                ]

                formatted_item = {
                    "titleId": title_id,
                    "title": title,
                    "version": version,
                    "author": author,
                    "category": category,
                    "description": description,
                    "checksum": checksum,
                    "posterUrl": poster_url,
                    "filename": fname,
                    "downloadLinks": download_links
                }
                
                all_items.append(formatted_item)

    # Application des surcharges du fichier pegasus_metadata.json
    final_items = apply_pegasus_metadata(all_items)

    # Structure finale globale du catalogue attendue par Pegasus-DL
    catalog_output = {
        "name": "Evox-CoreOS Catalog",
        "description": "Catalogue automatisé Pegasus-DL pour PKG et FFPFSC",
        "packages": final_items
    }

    # 1. Enregistrement standard (json/pegasus_catalog.json)
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(catalog_output, f, indent=4, ensure_ascii=False)
    
    print(f"    ➔ Catalogue Pegasus généré : {output_path} ({len(final_items)} éléments)")

    # 2. Enregistrement direct vers le fichier final cible (json/pegasus-dl/catalog.json)
    final_dl_path = "json/pegasus-dl/catalog.json"
    os.makedirs(os.path.dirname(final_dl_path), exist_ok=True)
    with open(final_dl_path, "w", encoding="utf-8") as f:
        json.dump(catalog_output, f, indent=4, ensure_ascii=False)
    
    print(f"    ➔ Catalogue Pegasus-DL final mis à jour : {final_dl_path}")
