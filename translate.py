import os
import json

# Configuration
source_folder = "data"
output_base = "data_translated"
target_lang = "en"  # Change to 'en', 'fr', etc.

# Traverse the source folder
for author in os.listdir(source_folder):
    author_path = os.path.join(source_folder, author)
    if not os.path.isdir(author_path):
        continue

    for filename in os.listdir(author_path):
        if not filename.endswith(".json"):
            continue

        file_path = os.path.join(author_path, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                content = json.load(f)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                continue

        # Translate each tafsir_text
        translated_entries = []
        for entry in content:
            try:
                # implement translation
                translated_text = entry["tafsir_text"]
                entry["tafsir_text_translated"] = translated_text
            except Exception as e:
                entry["tafsir_text_translated"] = f"[Translation failed: {e}]"
            translated_entries.append(entry)

        # Output path
        output_dir = os.path.join(output_base, target_lang, author)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)

        # Save the translated file
        with open(output_path, "w", encoding="utf-8") as out_f:
            json.dump(translated_entries, out_f, ensure_ascii=False, indent=2)

        print(f"✅ Translated: {file_path} → {output_path}")
