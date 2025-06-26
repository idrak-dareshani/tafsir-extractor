# Qur'anic Tafsir Extractor

A Python tool to extract tafsir (Quranic commentary) content from [tafsir.app](https://tafsir.app) for multiple classical authors. The extracted data is saved in structured JSON and CSV formats for further use.

## Features

- Extract tafsir for:
  - A single ayah
  - An entire surah
  - A range of surahs
  - The entire Quran
- Supports multiple authors: Al-Alusi, Al-Razi, Ibn Katheer, At-Tabari, Al-Qurtubi, Ibn Ashur, Iraab ul Quran
- Saves data as JSON and CSV, organized by author and surah
- Progress and errors are logged to `tafsir_extraction.log`

## Requirements

- Python 3.7+
- Install dependencies:
  ```sh
  pip install requests beautifulsoup4 lxml pandas tqdm
  ```

## Usage

Run the script:

```sh
python main.py
```

Follow the prompts to:
- Select a tafsir author
- Choose extraction mode (single ayah, surah, range, or all)
- Enter surah/ayah numbers as needed

Extracted files are saved in `data/<author>/` and named by surah (e.g. `data/alrazi/2.json`, `data/alrazi/2.csv`). For range or full extraction, each surah is saved individually.

## Output

- JSON and CSV files for each surah (e.g. `data/alrazi/2.json`, `data/alrazi/2.csv`)
- Log file: `tafsir_extraction.log`

## Notes

- Extraction of the entire Quran may take several hours.
- Please use responsibly and respect [tafsir.app](https://tafsir.app) terms of service.