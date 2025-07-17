#!/usr/bin/env python3
"""
Tafsir Content Extractor for tafsir.app/alrazi

This script extracts tafsir content from tafsir.app/alrazi/{surah}/{ayat}
and structures it for use in web applications.

Requirements:
    pip install requests beautifulsoup4 lxml pandas tqdm

Usage:
    python tafsir_extractor.py
"""

import requests
import json
import time
import os
import csv
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import logging
from tqdm import tqdm
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tafsir_extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TafsirContent:
    """Data structure for storing tafsir content"""
    surah_number: int
    surah_name_arabic: str
    surah_name_english: str
    ayah_number: int
    #ayah_text_arabic: str
    #ayah_text_transliteration: str
    #ayah_text_translation: str
    tafsir_text: str
    tafsir_author: str
    url: str
    extraction_timestamp: str

@dataclass
class SurahInfo:
    """Data structure for Surah information"""
    number: int
    name_arabic: str
    name_english: str
    total_ayahs: int
    revelation_place: str

class TafsirExtractor:
    """Main class for extracting tafsir content from tafsir.app"""
    
    def __init__(self, tafsir_author: str = "alrazi", delay: float = 1.0):
        # Available tafsir authors
        self.available_authors = {
            "alaloosi": "Al-Alusi",
            "alrazi": "Al-Razi", 
            "ibn-katheer": "Ibn Katheer",
            "tabari": "At-Tabari",
            "qurtubi": "Al-Qurtubi",
            "ibn-aashoor": "Ibn Ashur",
            "iraab-daas": "Iraab ul Quran"
        }
        
        if tafsir_author not in self.available_authors:
            raise ValueError(f"Invalid tafsir author. Available options: {list(self.available_authors.keys())}")
        
        self.tafsir_author_key = tafsir_author
        self.tafsir_author_name = self.available_authors[tafsir_author]
        self.base_url = f"https://tafsir.app/{tafsir_author}"
        self.delay = delay  # Delay between requests to be respectful
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Quran structure - 114 Surahs with their ayah counts
        self.surah_info = self._get_surah_info()
    
    def _get_surah_info(self) -> Dict[int, SurahInfo]:
        """Get information about all Surahs in the Quran"""
        # This is the standard Quran structure with ayah counts
        surah_data = [
            (1, "الفاتحة", "Al-Fatihah", 7, "Makkah"),
            (2, "البقرة", "Al-Baqarah", 286, "Madinah"),
            (3, "آل عمران", "Aal-E-Imran", 200, "Madinah"),
            (4, "النساء", "An-Nisa", 176, "Madinah"),
            (5, "المائدة", "Al-Maidah", 120, "Madinah"),
            (6, "الأنعام", "Al-An'am", 165, "Makkah"),
            (7, "الأعراف", "Al-A'raf", 206, "Makkah"),
            (8, "الأنفال", "Al-Anfal", 75, "Madinah"),
            (9, "التوبة", "At-Tawbah", 129, "Madinah"),
            (10, "يونس", "Yunus", 109, "Makkah"),
            (11, "هود", "Hud", 123, "Makkah"),
            (12, "يوسف", "Yusuf", 111, "Makkah"),
            (13, "الرعد", "Ar-Ra'd", 43, "Madinah"),
            (14, "إبراهيم", "Ibrahim", 52, "Makkah"),
            (15, "الحجر", "Al-Hijr", 99, "Makkah"),
            (16, "النحل", "An-Nahl", 128, "Makkah"),
            (17, "الإسراء", "Al-Isra", 111, "Makkah"),
            (18, "الكهف", "Al-Kahf", 110, "Makkah"),
            (19, "مريم", "Maryam", 98, "Makkah"),
            (20, "طه", "Taha", 135, "Makkah"),
            (21, "الأنبياء", "Al-Anbiya", 112, "Makkah"),
            (22, "الحج", "Al-Hajj", 78, "Madinah"),
            (23, "المؤمنون", "Al-Mu'minun", 118, "Makkah"),
            (24, "النور", "An-Nur", 64, "Madinah"),
            (25, "الفرقان", "Al-Furqan", 77, "Makkah"),
            (26, "الشعراء", "Ash-Shu'ara", 227, "Makkah"),
            (27, "النمل", "An-Naml", 93, "Makkah"),
            (28, "القصص", "Al-Qasas", 88, "Makkah"),
            (29, "العنكبوت", "Al-Ankabut", 69, "Makkah"),
            (30, "الروم", "Ar-Rum", 60, "Makkah"),
            (31, "لقمان", "Luqman", 34, "Makkah"),
            (32, "السجدة", "As-Sajdah", 30, "Makkah"),
            (33, "الأحزاب", "Al-Ahzab", 73, "Madinah"),
            (34, "سبأ", "Saba", 54, "Makkah"),
            (35, "فاطر", "Fatir", 45, "Makkah"),
            (36, "يس", "Ya-Sin", 83, "Makkah"),
            (37, "الصافات", "As-Saffat", 182, "Makkah"),
            (38, "ص", "Sad", 88, "Makkah"),
            (39, "الزمر", "Az-Zumar", 75, "Makkah"),
            (40, "غافر", "Ghafir", 85, "Makkah"),
            (41, "فصلت", "Fussilat", 54, "Makkah"),
            (42, "الشورى", "Ash-Shura", 53, "Makkah"),
            (43, "الزخرف", "Az-Zukhruf", 89, "Makkah"),
            (44, "الدخان", "Ad-Dukhan", 59, "Makkah"),
            (45, "الجاثية", "Al-Jathiyah", 37, "Makkah"),
            (46, "الأحقاف", "Al-Ahqaf", 35, "Makkah"),
            (47, "محمد", "Muhammad", 38, "Madinah"),
            (48, "الفتح", "Al-Fath", 29, "Madinah"),
            (49, "الحجرات", "Al-Hujurat", 18, "Madinah"),
            (50, "ق", "Qaf", 45, "Makkah"),
            (51, "الذاريات", "Adh-Dhariyat", 60, "Makkah"),
            (52, "الطور", "At-Tur", 49, "Makkah"),
            (53, "النجم", "An-Najm", 62, "Makkah"),
            (54, "القمر", "Al-Qamar", 55, "Makkah"),
            (55, "الرحمن", "Ar-Rahman", 78, "Makkah"),
            (56, "الواقعة", "Al-Waqiah", 96, "Makkah"),
            (57, "الحديد", "Al-Hadid", 29, "Madinah"),
            (58, "المجادلة", "Al-Mujadila", 22, "Madinah"),
            (59, "الحشر", "Al-Hashr", 24, "Madinah"),
            (60, "الممتحنة", "Al-Mumtahanah", 13, "Madinah"),
            (61, "الصف", "As-Saff", 14, "Madinah"),
            (62, "الجمعة", "Al-Jumu'ah", 11, "Madinah"),
            (63, "المنافقون", "Al-Munafiqun", 11, "Madinah"),
            (64, "التغابن", "At-Taghabun", 18, "Madinah"),
            (65, "الطلاق", "At-Talaq", 12, "Madinah"),
            (66, "التحريم", "At-Tahrim", 12, "Madinah"),
            (67, "الملك", "Al-Mulk", 30, "Makkah"),
            (68, "القلم", "Al-Qalam", 52, "Makkah"),
            (69, "الحاقة", "Al-Haqqah", 52, "Makkah"),
            (70, "المعارج", "Al-Ma'arij", 44, "Makkah"),
            (71, "نوح", "Nuh", 28, "Makkah"),
            (72, "الجن", "Al-Jinn", 28, "Makkah"),
            (73, "المزمل", "Al-Muzzammil", 20, "Makkah"),
            (74, "المدثر", "Al-Muddaththir", 56, "Makkah"),
            (75, "القيامة", "Al-Qiyamah", 40, "Makkah"),
            (76, "الإنسان", "Al-Insan", 31, "Madinah"),
            (77, "المرسلات", "Al-Mursalat", 50, "Makkah"),
            (78, "النبأ", "An-Naba", 40, "Makkah"),
            (79, "النازعات", "An-Nazi'at", 46, "Makkah"),
            (80, "عبس", "Abasa", 42, "Makkah"),
            (81, "التكوير", "At-Takwir", 29, "Makkah"),
            (82, "الانفطار", "Al-Infitar", 19, "Makkah"),
            (83, "المطففين", "Al-Mutaffifin", 36, "Makkah"),
            (84, "الانشقاق", "Al-Inshiqaq", 25, "Makkah"),
            (85, "البروج", "Al-Buruj", 22, "Makkah"),
            (86, "الطارق", "At-Tariq", 17, "Makkah"),
            (87, "الأعلى", "Al-A'la", 19, "Makkah"),
            (88, "الغاشية", "Al-Ghashiyah", 26, "Makkah"),
            (89, "الفجر", "Al-Fajr", 30, "Makkah"),
            (90, "البلد", "Al-Balad", 20, "Makkah"),
            (91, "الشمس", "Ash-Shams", 15, "Makkah"),
            (92, "الليل", "Al-Layl", 21, "Makkah"),
            (93, "الضحى", "Ad-Duhaa", 11, "Makkah"),
            (94, "الشرح", "Ash-Sharh", 8, "Makkah"),
            (95, "التين", "At-Tin", 8, "Makkah"),
            (96, "العلق", "Al-Alaq", 19, "Makkah"),
            (97, "القدر", "Al-Qadr", 5, "Makkah"),
            (98, "البينة", "Al-Bayyinah", 8, "Madinah"),
            (99, "الزلزلة", "Az-Zalzalah", 8, "Madinah"),
            (100, "العاديات", "Al-Adiyat", 11, "Makkah"),
            (101, "القارعة", "Al-Qari'ah", 11, "Makkah"),
            (102, "التكاثر", "At-Takathur", 8, "Makkah"),
            (103, "العصر", "Al-Asr", 3, "Makkah"),
            (104, "الهمزة", "Al-Humazah", 9, "Makkah"),
            (105, "الفيل", "Al-Fil", 5, "Makkah"),
            (106, "قريش", "Quraysh", 4, "Makkah"),
            (107, "الماعون", "Al-Ma'un", 7, "Makkah"),
            (108, "الكوثر", "Al-Kawthar", 3, "Makkah"),
            (109, "الكافرون", "Al-Kafirun", 6, "Makkah"),
            (110, "النصر", "An-Nasr", 3, "Madinah"),
            (111, "المسد", "Al-Masad", 5, "Makkah"),
            (112, "الإخلاص", "Al-Ikhlas", 4, "Makkah"),
            (113, "الفلق", "Al-Falaq", 5, "Makkah"),
            (114, "الناس", "An-Nas", 6, "Makkah")
        ]
        
        return {
            num: SurahInfo(num, ar_name, en_name, ayahs, place)
            for num, ar_name, en_name, ayahs, place in surah_data
        }
    
    def _make_request(self, url: str) -> Optional[requests.Response]:
        """Make HTTP request with error handling and rate limiting"""
        try:
            time.sleep(self.delay)
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            return None
    
    def _parse_tafsir_content(self, html_content: str, surah: int, ayah: int) -> Optional[TafsirContent]:
        """Parse HTML content and extract tafsir information"""
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Extract Arabic text of the ayah
            ayah_div = soup.find('div', id='preloaded-data')
            ayah_text = ayah_div.get_text()
            json_data = json.loads(ayah_text)
            ayah_arabic = json_data.get('ayah')
            
            # Extract tafsir text
            tafsir_div = soup.find('div', id='preloaded-text')
            tafsir_text = tafsir_div.get_text(separator='\n')
            lines = [line.strip() for line in tafsir_text.splitlines()]
            tafsir_text = '\n'.join([line for line in lines if line])
            
            # Get surah information
            surah_info = self.surah_info.get(surah)
            if not surah_info:
                logger.warning(f"Unknown surah number: {surah}")
                return None
            
            # Create TafsirContent object
            content = TafsirContent(
                surah_number=surah,
                surah_name_arabic=surah_info.name_arabic,
                surah_name_english=surah_info.name_english,
                ayah_number=ayah,
                #ayah_text_arabic=ayah_arabic,
                #ayah_text_transliteration=transliteration,
                #ayah_text_translation=translation,
                tafsir_text=tafsir_text,
                tafsir_author=self.tafsir_author_name,
                url=f"{self.base_url}/{surah}/{ayah}",
                extraction_timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            )
            
            return content
            
        except Exception as e:
            logger.error(f"Error parsing content for Surah {surah}, Ayah {ayah}: {e}")
            return None
    
    def extract_single_ayah(self, surah: int, ayah: int) -> Optional[TafsirContent]:
        """Extract tafsir content for a single ayah"""
        if surah not in self.surah_info:
            logger.error(f"Invalid surah number: {surah}")
            return None
        
        if ayah < 1 or ayah > self.surah_info[surah].total_ayahs:
            logger.error(f"Invalid ayah number {ayah} for surah {surah}")
            return None
        
        url = f"{self.base_url}/{surah}/{ayah}"
        logger.info(f"Extracting: {url}")
        
        response = self._make_request(url)
        if not response:
            return None
        
        return self._parse_tafsir_content(response.text, surah, ayah)
    
    def extract_surah(self, surah: int) -> List[TafsirContent]:
        """Extract tafsir content for an entire surah"""
        if surah not in self.surah_info:
            logger.error(f"Invalid surah number: {surah}")
            return []
        
        surah_info = self.surah_info[surah]
        logger.info(f"Extracting Surah {surah}: {surah_info.name_english} ({surah_info.total_ayahs} ayahs)")
        
        results = []
        for ayah in tqdm(range(1, surah_info.total_ayahs + 1), desc=f"Surah {surah}"):
            content = self.extract_single_ayah(surah, ayah)
            if content:
                results.append(content)
            else:
                logger.warning(f"Failed to extract Surah {surah}, Ayah {ayah}")
        
        return results

    def extract_multiple_surah(self, start_surah: int, end_surah: int) -> List[TafsirContent]:
        """Extract tafsir content for the selected surah"""
        logger.info("Starting extraction of selected surah")
        all_results = []
        
        for surah_num in tqdm(range(start_surah, end_surah+1), desc="Surahs"):
            surah_results = self.extract_surah(surah_num)
            all_results.extend(surah_results)
            
            # Save each surah individually
            if surah_results:
                self.save_to_json(surah_results, surah_numbers=[surah_num])
                #self.save_to_csv(surah_results, surah_numbers=[surah_num])
            
            # # Save intermediate results every 10 surahs
            # if surah_num % 10 == 0:
            #     self._save_intermediate_results(all_results, f"intermediate_surah_{surah_num}")
        
        return all_results

    def extract_all(self) -> List[TafsirContent]:
        """Extract tafsir content for the entire Quran"""
        logger.info("Starting extraction of entire Quran tafsir")
        all_results = []
        
        for surah_num in tqdm(range(1, 115), desc="Surahs"):
            surah_results = self.extract_surah(surah_num)
            all_results.extend(surah_results)
            
            # Save each surah individually
            if surah_results:
                self.save_to_json(surah_results, surah_numbers=[surah_num])
                #self.save_to_csv(surah_results, surah_numbers=[surah_num])
            
            # # Save intermediate results every 10 surahs
            # if surah_num % 10 == 0:
            #     self._save_intermediate_results(all_results, f"intermediate_surah_{surah_num}")
        
        return all_results
    
    def _save_intermediate_results(self, data: List[TafsirContent], filename: str):
        """Save intermediate results to prevent data loss"""
        try:
            safe_filename = f"{filename}_{self.tafsir_author_key}.json"
            with open(safe_filename, 'w', encoding='utf-8') as f:
                json.dump([asdict(item) for item in data], f, ensure_ascii=False, indent=2)
            logger.info(f"Saved intermediate results: {safe_filename}")
        except Exception as e:
            logger.error(f"Failed to save intermediate results: {e}")
    
    def save_to_json(self, data: List[TafsirContent], filename: str = None, surah_numbers: List[int] = None):
        """Save extracted data to JSON file"""
        if filename is None:
            if surah_numbers and len(set(surah_numbers)) == 1:
                # Single surah
                surah_num = surah_numbers[0]
                os.makedirs(f"data/{self.tafsir_author_key}", exist_ok=True)
                filename = f"data/{self.tafsir_author_key}/{surah_num}.json"
            elif surah_numbers and len(set(surah_numbers)) > 1:
                # Multiple surahs
                min_surah = min(surah_numbers)
                max_surah = max(surah_numbers)
                filename = f"{self.tafsir_author_key}_{min_surah}-{max_surah}.json"
            else:
                # Default fallback
                filename = f"{self.tafsir_author_key}_all.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump([asdict(item) for item in data], f, ensure_ascii=False, indent=2)
            logger.info(f"Data saved to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Failed to save JSON: {e}")
            return None
    
    def save_to_csv(self, data: List[TafsirContent], filename: str = None, surah_numbers: List[int] = None):
        """Save extracted data to CSV file"""
        if filename is None:
            if surah_numbers and len(set(surah_numbers)) == 1:
                # Single surah
                surah_num = surah_numbers[0]
                os.makedirs(f"data/{self.tafsir_author_key}", exist_ok=True)
                filename = f"data/{self.tafsir_author_key}/{surah_num}.csv"
            elif surah_numbers and len(set(surah_numbers)) > 1:
                # Multiple surahs
                min_surah = min(surah_numbers)
                max_surah = max(surah_numbers)
                filename = f"{self.tafsir_author_key}_{min_surah}-{max_surah}.csv"
            else:
                # Default fallback
                filename = f"{self.tafsir_author_key}_all.csv"
        try:
            df = pd.DataFrame([asdict(item) for item in data])
            df.to_csv(filename, index=False, encoding='utf-8')
            logger.info(f"Data saved to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Failed to save CSV: {e}")
            return None

def main():
    """Main execution function"""
    print("=== Tafsir Content Extractor ===")
    
    # Ask user to select tafsir author
    available_authors = {
        "1": ("alaloosi", "Al-Alusi"),
        "2": ("alrazi", "Al-Razi"),
        "3": ("ibn-katheer", "Ibn Katheer"),
        "4": ("tabari", "At-Tabari"),
        "5": ("qurtubi", "Al-Qurtubi"),
        "6": ("ibn-aashoor", "Ibn Ashur"),
        "7": ("iraab-daas", "Iraab ul Quran")
    }
    
    print("\nAvailable Tafsir Authors:")
    for key, (author_key, author_name) in available_authors.items():
        print(f"{key}. {author_name} ({author_key})")
    
    author_choice = input("Select tafsir author (1-5): ").strip()
    
    if author_choice not in available_authors:
        print("Invalid choice. Defaulting to Al-Razi.")
        author_key = "alrazi"
    else:
        author_key, author_name = available_authors[author_choice]
        print(f"Selected: {author_name}")
    
    # Initialize extractor with selected author
    extractor = TafsirExtractor(tafsir_author=author_key, delay=1.0)
    
    # Example usage - extract specific ayahs
    print("\nExtraction Options:")
    print("1. Extract single ayah")
    print("2. Extract entire surah")
    print("3. Extract specific range (WARNING: This will take some time)")
    print("4. Extract all (WARNING: This will take a very long time)")
    
    choice = input("Enter your choice (1-4): ").strip()
    
    results = []
    
    if choice == "1":
        surah = int(input("Enter surah number (1-114): "))
        ayah = int(input("Enter ayah number: "))
        result = extractor.extract_single_ayah(surah, ayah)
        if result:
            results = [result]
            print(f"\nExtracted content for Surah {surah}, Ayah {ayah} - {extractor.tafsir_author_name}")
            print(f"Tafsir text length: {len(result.tafsir_text)} characters")
    
    elif choice == "2":
        surah = int(input("Enter surah number (1-114): "))
        results = extractor.extract_surah(surah)
        print(f"\nExtracted {len(results)} ayahs from Surah {surah} - {extractor.tafsir_author_name}")
    
    elif choice == "3":
        start_surah = int(input("Enter start surah number: "))
        end_surah = int(input("Enter end surah number: "))
        confirm = input(f"This will extract the multiple surah from {extractor.tafsir_author_name}. This may take some time. Continue? (yes/no): ")
        if confirm.lower() == 'yes':
            results = extractor.extract_multiple_surah(start_surah, end_surah)
        # for surah_num in range(start_surah, end_surah + 1):
        #     surah_results = extractor.extract_surah(surah_num)
        #     results.extend(surah_results)
            print(f"\nExtracted {len(results)} total ayahs from Surahs {start_surah}-{end_surah} - {extractor.tafsir_author_name}")
    
    elif choice == "4":
        confirm = input(f"This will extract the entire Quran from {extractor.tafsir_author_name}. This may take hours. Continue? (yes/no): ")
        if confirm.lower() == 'yes':
            results = extractor.extract_all()
            print(f"\nExtracted {len(results)} total ayahs from the entire Quran - {extractor.tafsir_author_name}")
    
    # Save results
    if results:
        # Get surah numbers from results for filename generation
        surah_numbers = list(set([result.surah_number for result in results]))
        
        if choice == "1" or choice == "2":
            # Save to JSON and CSV with surah-specific filenames
            json_filename = extractor.save_to_json(results, surah_numbers=surah_numbers)
            #csv_filename = extractor.save_to_csv(results, surah_numbers=surah_numbers)
        
            print(f"\nExtraction completed successfully!")
            print(f"Files created:")
            if json_filename:
                print(f"- {json_filename}: {len(results)} records")
            #if csv_filename:
            #    print(f"- {csv_filename}: {len(results)} records")
            print(f"- tafsir_extraction.log: Extraction log file")
            print(f"- Author: {extractor.tafsir_author_name} ({extractor.tafsir_author_key})")

        elif choice == "3":  # Extract specific
            print(f"\nNote: Individual surah files have been created for each of the selected surahs.")
            print(f"Format: {extractor.tafsir_author_key}/{{surah_number}}.json")

        elif choice == "4":  # Extract all
            print(f"\nNote: Individual surah files have been created for each of the 114 surahs.")
            print(f"Format: {extractor.tafsir_author_key}/{{surah_number}}.json")

if __name__ == "__main__":
    main()