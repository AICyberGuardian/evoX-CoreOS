# /scripts/build_reporter.py
import os
import urllib.request
from datetime import datetime

def generate_build_reports(data_store_flat, status="Succès 🚀"):
    print("📊 [Bonus] Génération des rapports de build (Build-Report)...")
    
    report_dir = "Build-Report"
    os.makedirs(report_dir, exist_ok=True)
    
    date_str = datetime.now().strftime("%d/%m/%Y à %H:%M")
    
    # ----------------------------------------------------
    # 1. Génération de build_log.md
    # ----------------------------------------------------
    log_path = os.path.join(report_dir, "build_log.md")
    
    log_content = f"# 📋 Journal d'exécution de la Build ({date_str})\n\n"
    log_content += f"> *Statut global du pipeline : **{status}***\n\n"
    log_content += "Ce rapport résume l'état de la dernière exécution du pipeline de mise à jour du store.\n\n"
    
    if data_store_flat:
        log_content += "## 📦 Récapitulatif par Catégorie\n\n"
        log_content += "| Catégorie | Nom affiché | Nombre d'éléments |\n"
        log_content += "| :--- | :--- | :--- |\n"
        
        total_items = 0
        for cat_key, cat_info in data_store_flat.items():
            name = cat_info.get("name", cat_key.upper())
            items = cat_info.get("items", [])
            count = len(items)
            total_items += count
            log_content += f"| `{cat_key}` | {name} | **{count}** |\n"
            
        log_content += f"\n* **Total cumulé des éléments traités** : `{total_items}`\n\n"
    
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(log_content)
    print("    ✅ Rapport build_log.md généré avec succès.")

    # ----------------------------------------------------
    # 2. Génération de repository_status.md (Vérification des liens)
    # ----------------------------------------------------
    status_path = os.path.join(report_dir, "repository_status.md")
    
    status_content = f"# 🔍 État des Sources & Dépôts ({date_str})\n\n"
    status_content += "Test de validité et de disponibilité des sources distantes intégrées dans le store.\n\n"
    status_content += "| Source / Dépôt | URL | Statut | Type |\n"
    status_content += "| :--- | :--- | :--- | :--- |\n"
    
    urls_to_test = [
        ("Homebrew.page Catalog", "https://homebrew.page/catalog/v1.json", "Catalog API"),
        ("GitHub - evoX-CoreOS", "https://github.com/nexgen999/evoX-CoreOS", "Dépôt Principal"),
    ]
    
    if data_store_flat:
        for cat_key, cat_info in data_store_flat.items():
            items = cat_info.get("items", [])
            if items and isinstance(items[0], dict):
                sample_item = items[0]
                sample_url = sample_item.get("url") or sample_item.get("source")
                if sample_url and sample_url.startswith("http"):
                    name = sample_item.get("name", "Sample Item")
                    urls_to_test.append((f"[{cat_key}] {name}", sample_url, "Artefact / Source"))

    for name, url, kind in urls_to_test:
        status_badge = "❌ Inaccessible"
        try:
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    status_badge = "✅ Valide (200 OK)"
                else:
                    status_badge = f"⚠️ Erreur ({response.status})"
        except Exception:
            status_badge = "❌ Hors ligne / Erreur"
            
        status_content += f"| {name} | [{url}]({url}) | {status_badge} | {kind} |\n"

    with open(status_path, "w", encoding="utf-8") as f:
        f.write(status_content)
    print("    ✅ Rapport repository_status.md généré avec succès.")
