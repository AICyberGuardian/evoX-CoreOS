# update_store.py
import os
import json
import hashlib
import zipfile
from datetime import datetime
from scripts.config_rules import PATHS, BASE_URL
from scripts.fetchers.payloads_fetcher import fetch_payloads_category
from scripts.fetchers.pkg_fetcher import fetch_pkg_category
from scripts.fetchers.ffpfsc_fetcher import fetch_ffpfsc_category
from scripts.fetchers.apps_fetcher import fetch_apps_category
from scripts.fetchers.homebrew_page_fetcher import fetch_homebrew_page_catalog
from scripts.generate_json import build_all
from scripts.generate_rss import build_rss_feed
from scripts.generate_readme import build_readme
from scripts.changelog_builder import generate_build_changelog
from scripts.pegasus_builder import generate_pegasus_catalog
from scripts.download_pegasus_catalogs import download_catalogs
from scripts.release_notes_builder import generate_release_notes
from scripts.build_reporter import generate_build_reports

def clean_latest_versions_only(flat_list):
    """
    Filtre la liste pour ne garder que la version la plus récente (latest) 
    pour chaque application/payload, en se basant sur le nom de base.
    """
    latest_map = {}
    for item in flat_list:
        if not isinstance(item, dict):
            continue
        name = item.get("name", "")
        base_key = name.lower().split('_v')[0].split(' v')[0].strip()
        
        if base_key not in latest_map:
            latest_map[base_key] = item
        else:
            existing_filename = latest_map[base_key].get("filename", "")
            current_filename = item.get("filename", "")
            if current_filename > existing_filename:
                latest_map[base_key] = item

    return list(latest_map.values())

def recover_local_orphans(category_name, flat_list, allowed_exts):
    """
    Scanne le dossier physique de la catégorie pour récupérer les fichiers orphelins 
    présents en local (notamment les fichiers internes ou les sources en échec 503).
    """
    root_dir = PATHS.get("categories", {}).get(category_name, {}).get("root", category_name)
    if not os.path.exists(root_dir):
        return flat_list

    known_filenames = {item.get("filename") for item in flat_list if isinstance(item, dict)}
    recovered_count = 0

    for dirpath, _, filenames in os.walk(root_dir):
        if "archives" in dirpath.split(os.sep):
            continue

        for filename in filenames:
            if not filename.lower().endswith(tuple(allowed_exts)):
                continue
            
            if filename not in known_filenames:
                local_path = os.path.join(dirpath, filename)
                
                hasher = hashlib.sha256()
                try:
                    with open(local_path, 'rb') as fb:
                        for chunk in iter(lambda: fb.read(4096), b""):
                            hasher.update(chunk)
                    checksum = hasher.hexdigest()
                except Exception:
                    checksum = ""

                display_name = os.path.splitext(filename)[0].replace('_', ' ').title()
                version = "Local-Backup"
                
                parts = dirpath.split(os.sep)
                if len(parts) > 1:
                    repo_or_title = parts[1]
                    if len(parts) > 2:
                        version = parts[2]
                else:
                    repo_or_title = display_name

                orphan_item = {
                    "name": display_name,
                    "filename": filename,
                    "url": "",
                    "local_path": local_path,
                    "description": f"Récupéré depuis le stockage local (Interne / Fallback)",
                    "version": version,
                    "checksum": checksum
                }
                
                flat_list.append(orphan_item)
                known_filenames.add(filename)
                recovered_count += 1
                print(f"    ♻️ [Fallback Local] Récupération de l'orphelin : {filename} ({category_name})")

    if recovered_count > 0:
        print(f"    ✅ {recovered_count} élément(s) local(aux) préservé(s) pour {category_name}.")
    
    flat_list = clean_latest_versions_only(flat_list)
    return flat_list

def build_aio_archives(payloads_flat, pkg_flat, ffpfsc_flat, apps_flat, hb_page_by_cat, hb_page_flat):
    print("📦 [Bonus] Génération dynamique des archives AIO ZIP (< 1.4 Go par fichier)...")
    
    base_workspace = os.path.abspath(os.getcwd())
    archives_dir = os.path.join(base_workspace, "archives")
    os.makedirs(archives_dir, exist_ok=True)

    for existing_f in os.listdir(archives_dir):
        if existing_f.endswith(".zip"):
            try:
                os.remove(os.path.join(archives_dir, existing_f))
            except Exception:
                pass

    MAX_SIZE_BYTES = int(1.4 * 1024 * 1024 * 1024)

    def create_dynamic_zips(base_name, items):
        if not items:
            return

        current_chunk = []
        current_size = 0
        
        chunks = []
        for item in items:
            file_path = item.get("local_path") if isinstance(item, dict) else None
            f_size = os.path.getsize(file_path) if file_path and os.path.exists(file_path) else 0
            
            if current_size + f_size > MAX_SIZE_BYTES and current_chunk:
                chunks.append(current_chunk)
                current_chunk = [item]
                current_size = f_size
            else:
                current_chunk.append(item)
                current_size += f_size
        if current_chunk:
            chunks.append(current_chunk)

        total_parts = len(chunks)
        
        for idx, chunk in enumerate(chunks, start=1):
            if total_parts > 1 or "ultimate_pack" in base_name:
                zip_name = f"{base_name}_part{idx}_latest.zip"
            else:
                zip_name = f"{base_name}_latest.zip"
                
            zip_path = os.path.join(archives_dir, zip_name)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for item in chunk:
                    file_path = item.get("local_path") if isinstance(item, dict) else None
                    if file_path and os.path.exists(file_path):
                        norm_path = os.path.abspath(file_path)
                        if "archives" in norm_path.split(os.sep) or "json" in norm_path.split(os.sep):
                            continue
                        zf.write(norm_path, arcname=os.path.basename(norm_path))
                        
            size_bytes = os.path.getsize(zip_path) if os.path.exists(zip_path) else 0
            print(f"    ➔ Archive générée : {zip_path} ({size_bytes / (1024*1024):.2f} Mo)")

    # Zips standard
    create_dynamic_zips("PS5_payloads_aio", payloads_flat)
    create_dynamic_zips("PS5_pkg_aio", pkg_flat)
    create_dynamic_zips("PS5_ffpfsc_aio", ffpfsc_flat)
    create_dynamic_zips("PS5_apps_aio", apps_flat)

    # Zips par catégorie ProsperoStore (anciennement homebrewpage)
    for kind, cat_data in hb_page_by_cat.items():
        create_dynamic_zips(f"prosperostore-{kind}_aio", cat_data["items"])
    
    # Pack Ultimate regroupant absolument tout
    ultimate_items = payloads_flat + pkg_flat + ffpfsc_flat + apps_flat + hb_page_flat
    create_dynamic_zips("PS5_ultimate_pack", ultimate_items)

def generate_pack_aio_json(github_releases_base):
    print("📋 Génération du fichier d'index JSON des packs AIO (/json/pack/pack_aio.json)...")
    pack_dir = os.path.join(PATHS.get("json_dir", "json"), "pack")
    os.makedirs(pack_dir, exist_ok=True)
    
    archives_dir = os.path.abspath("archives")
    packs_data = []

    if os.path.exists(archives_dir):
        for zip_file in sorted(os.listdir(archives_dir)):
            if zip_file.endswith(".zip"):
                zip_path = os.path.join(archives_dir, zip_file)
                size_bytes = os.path.getsize(zip_path) if os.path.exists(zip_path) else 0
                
                pack_type = "unknown"
                if "payloads" in zip_file:
                    pack_type = "payloads"
                elif "pkg" in zip_file:
                    pack_type = "pkg"
                elif "ffpfsc" in zip_file:
                    pack_type = "ffpfsc"
                elif "apps" in zip_file:
                    pack_type = "apps"
                elif "prosperostore" in zip_file:
                    pack_type = "homebrew_page"
                elif "ultimate_pack" in zip_file:
                    pack_type = "ultimate"

                packs_data.append({
                    "filename": zip_file,
                    "display_name": zip_file.replace("_latest.zip", "").replace("_", " ").upper(),
                    "pack_type": pack_type,
                    "size_bytes": size_bytes,
                    "size_mb": round(size_bytes / (1024 * 1024), 2),
                    "url": f"{github_releases_base}/{zip_file}"
                })

    output_path = os.path.join(pack_dir, "pack_aio.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "updated_at": datetime.now().isoformat(),
            "packs": packs_data
        }, f, indent=4, ensure_ascii=False)
    
    print(f"    ✅ Fichier généré avec succès : {output_path}")

def main():
    print("🚀 Démarrage de la mise à jour globale du store PS5...")
    credits_set = set()
    data_store_flat = {}
    
    try:
        os.makedirs(PATHS["archives_dir"], exist_ok=True)
        os.makedirs(PATHS["json_dir"], exist_ok=True)
        os.makedirs(PATHS["payloads_dir"], exist_ok=True)

        print("📥 [0/5] Téléchargement des catalogues Pegasus distants...")
        download_catalogs()

        print("🔍 [1/5] Scraping des sources et du catalogue ProsperoStore...")
        payloads_by_cat, payloads_flat = fetch_payloads_category(credits_set)
        pkg_by_cat, pkg_flat = fetch_pkg_category(credits_set)
        ffpfsc_by_cat, ffpfsc_flat = fetch_ffpfsc_category(credits_set)
        apps_by_cat, apps_flat = fetch_apps_category(credits_set)
        hb_page_by_cat, hb_page_flat = fetch_homebrew_page_catalog(credits_set)

        print("🛡️ [1.5/5] Récupération de sécurité des fichiers locaux (Fallback anti-disparition)...")
        payloads_flat = recover_local_orphans("payloads", payloads_flat, [".elf", ".bin"])
        pkg_flat = recover_local_orphans("pkg", pkg_flat, [".pkg"])
        ffpfsc_flat = recover_local_orphans("ffpfsc", ffpfsc_flat, [".ffpfsc", ".bin", ".elf"])
        apps_flat = recover_local_orphans("apps", apps_flat, [".elf", ".zip"])

        data_store = {
            "payloads": (payloads_by_cat, payloads_flat),
            "pkg": (pkg_by_cat, pkg_flat),
            "ffpfsc": (ffpfsc_by_cat, ffpfsc_flat),
            "apps": (apps_by_cat, apps_flat),
            "homebrew_page": (hb_page_by_cat, hb_page_flat)
        }

        data_store_by_cat = {
            "payloads": payloads_by_cat,
            "pkg": pkg_by_cat,
            "ffpfsc": ffpfsc_by_cat,
            "apps": apps_by_cat,
            "homebrew_page": hb_page_by_cat
        }

        data_store_flat = {
            "payloads": {"name": "Payloads", "items": payloads_flat},
            "pkg": {"name": "Packages PKG", "items": pkg_flat},
            "ffpfsc": {"name": "Fichiers FFPFSC", "items": ffpfsc_flat},
            "apps": {"name": "Applications", "items": apps_flat},
            "homebrew_page": {"name": "ProsperoStore", "items": hb_page_flat}
        }

        print("📦 [2/5] Génération de l'arborescence JSON complète...")
        build_all(data_store)

        print("🎯 [2.5/5] Génération du catalogue Pegasus-DL...")
        generate_pegasus_catalog(pkg_flat, ffpfsc_flat)

        print("📡 [3/5] Génération des flux RSS et OPML... ")
        build_rss_feed(data_store_flat)

        build_aio_archives(payloads_flat, pkg_flat, ffpfsc_flat, apps_flat, hb_page_by_cat, hb_page_flat)

        clean_url = BASE_URL.replace("https://", "").replace("http://", "")
        url_parts = clean_url.split("/")
        owner = url_parts[0].split(".")[0]
        repo = url_parts[1] if len(url_parts) > 1 else "evoX-CoreOS"
        github_releases_base = f"https://github.com/{owner}/{repo}/releases/download/latest"

        generate_pack_aio_json(github_releases_base)

        print("📝 [4/4] Mise à jour du README.md, des Crédits, du Changelog et des Notes de Release...")
        build_readme(credits_set, data_store_by_cat)
        generate_build_changelog()
        generate_release_notes(data_store_by_cat)

        print("📊 [5/5] Génération des rapports de build (Build-Report)...")
        generate_build_reports(data_store_flat, status="Succès 🚀")

        print("✅ Mise à jour du store et des packages terminée avec succès !")

    except Exception as e:
        print(f"❌ Erreur critique détectée dans le pipeline : {e}")
        generate_build_reports(data_store_flat, status=f"Échec ❌ ({str(e)})")
        raise e

if __name__ == "__main__":
    main()
