# /scripts/release_notes_builder.py
import os
import json
from datetime import datetime
from scripts.config_rules import PATHS

def generate_release_notes(data_store_by_cat):
    print("📝 Génération des notes de version pour la Release...")
    json_dir = PATHS.get("json_dir", "json")
    notes_path = "release_notes.md"
    date_str = datetime.now().strftime("v%Y.%m.%d-%H%M")
    
    categories = ["payloads", "pkg", "ffpfsc", "apps", "homebrew_page"]
    
    content = f"### 🚀 Synthèse de la mise à jour ({date_str})\n\n"
    content += "Le store PlayStation 5 a été mis à jour avec succès.\n\n"
    
    content += "#### 📦 Archives AIO Disponibles (Dossier `archives/`) :\n"
    archives_dir = os.path.abspath("archives")
    if os.path.exists(archives_dir):
        all_archives = sorted([f for f in os.listdir(archives_dir) if f.endswith(".zip")])
        for arch in all_archives:
            content += f"- `{arch}`\n"
            
    content += "\n#### 📂 Fichiers inclus / mis à jour :\n"
    content += "📜 [Consulter le journal complet des modifications (CHANGELOG.md)](CHANGELOG.md)\n\n"

    content += "#### 🛠 Détail des Packs & Contenu\n"
    
    icons = {
        "payloads": "⚡",
        "pkg": "🎮",
        "ffpfsc": "📄",
        "apps": "🛠",
        "homebrew_page": "🌐"
    }

    for cat_key in categories:
        json_file_path = os.path.join(json_dir, f"{cat_key}.json")
        icon = icons.get(cat_key, "📦")
        display_title = "HOMEBREW PAGE" if cat_key == "homebrew_page" else cat_key.upper()
        content += f"<details>\n<summary><b>{icon} Pack {display_title}</b></summary>\n\n"
        
        has_items = False
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r', encoding='utf-8') as f:
                json_content = json.load(f)
                
            if isinstance(json_content, dict):
                # Si c'est un format global plat type homebrew_page.json {"apps": [...]}
                if cat_key == "homebrew_page" and "apps" in json_content:
                    file_entries = [item.get('filename') for item in json_content["apps"] if isinstance(item, dict) and item.get('filename')]
                    if file_entries:
                        has_items = True
                        content += f"* **Applications Homebrew.page**\n"
                        seen = set()
                        for fname in file_entries:
                            if fname not in seen:
                                seen.add(fname)
                                content += f"  * `{fname}`\n"
                else:
                    # Format standard par sous-sections
                    for section_key, section_val in json_content.items():
                        if section_key == "name":
                            continue
                            
                        file_entries = []
                        items_list = []
                        if isinstance(section_val, list):
                            items_list = section_val
                        elif isinstance(section_val, dict):
                            items_list = section_val.get('items', [])
                            
                        for item in items_list:
                            if isinstance(item, dict):
                                fname = item.get('filename')
                                if fname:
                                    file_entries.append(fname)
                                
                        if file_entries:
                            has_items = True
                            content += f"* **{section_key}**\n"
                            seen = set()
                            for fname in file_entries:
                                if fname not in seen:
                                    seen.add(fname)
                                    content += f"  * `{fname}`\n"
        
        if not has_items:
            content += "*Aucun élément dans ce pack.*\n"
            
        content += "\n</details>\n\n"

    with open(notes_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("    ✅ Fichier release_notes.md généré avec succès !")
