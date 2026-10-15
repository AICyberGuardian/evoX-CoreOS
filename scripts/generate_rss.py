# /scripts/generate_rss.py
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from scripts.config_rules import PATHS, BASE_URL

def build_rss_feed(data_store):
    base_rss_dir = "rss"
    os.makedirs(base_rss_dir, exist_ok=True)

    global_rss_root = ET.Element("rss", version="2.0")
    global_channel = ET.SubElement(global_rss_root, "channel")
    ET.SubElement(global_channel, "title").text = "PS5 Store AIO - Global Feed"
    ET.SubElement(global_channel, "link").text = BASE_URL
    ET.SubElement(global_channel, "description").text = "Flux RSS global de toutes les mises à jour du store PS5"

    global_opml_root = ET.Element("opml", version="2.0")
    global_head = ET.SubElement(global_opml_root, "head")
    ET.SubElement(global_head, "title").text = "PS5 Store AIO - All Sources OPML"
    global_opml_body = ET.SubElement(global_opml_root, "body")

    # Parcours des dossiers feed pour compiler les sources d'origine
    for cat_tech, cat_paths in PATHS["categories"].items():
        feed_dir = cat_paths.get("feed")
        if feed_dir and os.path.exists(feed_dir):
            cat_outline = ET.SubElement(global_opml_body, "outline", {"text": cat_tech.title(), "title": cat_tech.title()})
            for opml_file in [f for f in os.listdir(feed_dir) if f.endswith('.opml')]:
                opml_path = os.path.join(feed_dir, opml_file)
                try:
                    tree = ET.parse(opml_path)
                    root = tree.getroot()
                    for outline in root.findall(".//outline"):
                        xml_url = outline.get("xmlUrl") or outline.get("xmlurl")
                        if xml_url:
                            ET.SubElement(cat_outline, "outline", {
                                "text": outline.get("text", outline.get("title", "Source")),
                                "title": outline.get("title", outline.get("text", "Source")),
                                "type": "rss",
                                "xmlUrl": xml_url,
                                "description": outline.get("description", "")
                            })
                except Exception as e:
                    print(f"⚠️ Erreur lecture OPML source {opml_path} : {e}")

    # Ajout d'une section dédiée homebrew.page dans l'OPML global
    hb_outline = ET.SubElement(global_opml_body, "outline", {"text": "Homebrew Page", "title": "Homebrew Page"})
    
    for cat_key, cat_info in data_store.items():
        if not isinstance(cat_info, dict):
            continue
        
        sub_rss_dir = os.path.join(base_rss_dir, cat_key)
        os.makedirs(sub_rss_dir, exist_ok=True)

        cat_name = cat_info.get("name", cat_key.upper())
        items = cat_info.get("items", [])

        rss_root = ET.Element("rss", version="2.0")
        channel = ET.SubElement(rss_root, "channel")
        ET.SubElement(channel, "title").text = f"PS5 Store AIO - {cat_name}"
        ET.SubElement(channel, "link").text = BASE_URL
        ET.SubElement(channel, "description").text = f"Mises à jour automatiques pour la catégorie {cat_name}"

        opml_root = ET.Element("opml", version="2.0")
        head = ET.SubElement(opml_root, "head")
        ET.SubElement(head, "title").text = f"PS5 Store Feeds - {cat_name}"
        opml_body = ET.SubElement(opml_root, "body")

        for item in items:
            # Pour homebrew_page, on privilégie le lien source externe ou la page officielle s'il existe
            item_link = item.get("source") if cat_key == "homebrew_page" and item.get("source") else item.get("url")

            item_elem = ET.SubElement(channel, "item")
            ET.SubElement(item_elem, "title").text = item.get("name")
            ET.SubElement(item_elem, "link").text = item_link
            ET.SubElement(item_elem, "description").text = item.get("description")
            ET.SubElement(item_elem, "pubDate").text = item.get("version", "v1.0.0")

            g_item = ET.SubElement(global_channel, "item")
            ET.SubElement(g_item, "title").text = f"[{cat_name}] {item.get('name')}"
            ET.SubElement(g_item, "link").text = item_link
            ET.SubElement(g_item, "description").text = item.get("description")
            ET.SubElement(g_item, "pubDate").text = item.get("version", "v1.0.0")

            outline_target = hb_outline if cat_key == "homebrew_page" else opml_body
            ET.SubElement(outline_target, "outline", {
                "text": item.get("name"),
                "title": item.get("name"),
                "type": "rss",
                "xmlUrl": item_link,
                "description": item.get("description", "")
            })

        xml_str = minidom.parseString(ET.tostring(rss_root)).toprettyxml(indent="  ")
        with open(os.path.join(sub_rss_dir, f"{cat_key}.xml"), "w", encoding="utf-8") as f:
            f.write(xml_str)

        opml_str = minidom.parseString(ET.tostring(opml_root)).toprettyxml(indent="  ")
        with open(os.path.join(sub_rss_dir, f"{cat_key}.opml"), "w", encoding="utf-8") as f:
            f.write(opml_str)

    global_xml_str = minidom.parseString(ET.tostring(global_rss_root)).toprettyxml(indent="  ")
    with open(os.path.join(base_rss_dir, "feed.xml"), "w", encoding="utf-8") as f:
        f.write(global_xml_str)

    global_opml_str = minidom.parseString(ET.tostring(global_opml_root)).toprettyxml(indent="  ")
    with open(os.path.join(base_rss_dir, "source_aio.opml"), "w", encoding="utf-8") as f:
        f.write(global_opml_str)
