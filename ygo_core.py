import requests
import re
import time
import threading
from pathlib import Path
from PIL import Image
from io import BytesIO
from typing import Optional, Tuple, Dict, List

class YGOCardDownloader:
    API_URL = "https://db.ygoprodeck.com/api/v7/cardinfo.php"
    
    def __init__(self):
        self.cards_data = None
    
    def fetch_data(self) -> bool:
        try:
            response = requests.get(self.API_URL, timeout=10)
            response.raise_for_status()
            self.cards_data = response.json().get('data', [])
            return True
        except Exception as e:
            print(f"API Error: {e}")
            return False
    
    @staticmethod
    def sanitize_filename(name: str) -> str:
        return re.sub(r'[\\/*?:"<>|]', "", name)
    
    @staticmethod
    def download_image(
        url: str,
        save_path: Path,
        size: Optional[Tuple[int, int]] = None
    ) -> bool:
        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            
            with Image.open(BytesIO(response.content)) as img:
                if size:
                    img = img.resize(size, Image.Resampling.LANCZOS)
                img.save(save_path)
            return True
        except Exception as e:
            print(f"Download failed: {e}")
            return False
    
    def process_cards(
        self,
        output_dir: Path,
        image_size: str,
        resize: Optional[Tuple[int, int]] = None,
        use_names: bool = True,
        stop_event: Optional[threading.Event] = None,
        progress_callback=None
    ) -> Dict[str, int]:

        if not self.cards_data:
            return {'downloaded': 0, 'skipped': 0}
        results = {'downloaded': 0, 'skipped': 0}
        
        for i, card in enumerate(self.cards_data, 1):
            if stop_event and stop_event.is_set():
                break
                
            try:
                if progress_callback:
                    progress_callback(i, len(self.cards_data))
                url = None
                for img_data in card.get('card_images', []):
                    url = img_data.get(image_size)
                    if url: break
                
                if not url:
                    results['skipped'] += 1
                    continue

                if use_names:
                    name = self.sanitize_filename(card.get('name', f'card_{i}'))
                    filename = output_dir / f"{name}.jpg"
                else:
                    filename = output_dir / f"{card.get('id', i)}.jpg"
                
                counter = 1
                original_filename = filename
                while filename.exists():
                    filename = original_filename.with_stem(f"{original_filename.stem}_{counter}")
                    counter += 1
                if self.download_image(url, filename, resize):
                    results['downloaded'] += 1
                else:
                    results['skipped'] += 1

                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error processing card {i}: {e}")
                results['skipped'] += 1
        
        return results