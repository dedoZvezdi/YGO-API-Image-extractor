import os
import requests
import re
from PIL import Image
from io import BytesIO
from pathlib import Path
import time 



api_url = "https://db.ygoprodeck.com/api/v7/cardinfo.php"


def fetch_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status() 
        return response.json()
    except requests.RequestException as e:
        print(f"Failed to fetch. Error: {e}")
        return None
    

def sanitize_filename(filename): 
    return re.sub(r'[\\/*?:"<>|]', "", filename)


def extract_image_url(card):
    image_urls = {}
    for image in card.get('card_images', []):
        if 'image_url' in image:
            image_urls['normal'] = image.get('image_url')
        if 'image_url_small' in image:
            image_urls['small'] = image.get('image_url_small')
        if 'image_url_cropped' in image:
            image_urls['cropped'] = image.get('image_url_cropped')
    return image_urls


#This exctract only 1 size of the card
# def extract_image_url(card):
#     for image in card.get('card_images', []):
#         url = image.get('image_url_cropped')  # Use image_url or image_url_small to change what size you want (normal,small and cropped are the options)
#         if url:
#             return url 
#     return None

# This is a resizer
# def download_and_resize_image(url, filename, size=(x, x): x is the size in px
#     try:
#         response = requests.get(url)
#         response.raise_for_status()  
#         with Image.open(BytesIO(response.content)) as img:
#             img = img.resize(size, Image.Resampling.LANCZOS)  
#             img.save(filename) 
#         print(f"Downloaded and resized {filename}")
#     except requests.RequestException as e:
#         print(f"{filename}. Error: {e}")
#     except IOError as e:
#         print(f"{filename}. Error: {e}")


def download_image(url, filename):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses
        with Image.open(BytesIO(response.content)) as img:
            # img = img.resize(size, Image.Resampling.LANCZOS)  #  if you want to download with intented size 'comment out'
            img.save(filename) 
        print(f"Downloaded {filename}")
    except requests.RequestException as e:
        print(f"Failed to download {filename}. Error: {e}")
    except IOError as e:
        print(f"Failed to save {filename}. Error: {e}")


def main():
    json_data = fetch_data(api_url)
    if json_data is None or 'data' not in json_data:
        print("No valid data found.")
        return

    pictures_path = Path.home() / '../path'  # Directory for saved images
    output_dir = pictures_path / 'folder_name'  # Folder name for images
    os.makedirs(output_dir, exist_ok=True)

    for card in json_data['data']:
        url = extract_image_url(card)
        card_name = card.get('name')
        #card_id = card.get('id') # if you want to save with id instead of the name of the card 'comment out'
        if url and card_name:
        #if url and card_id is not None:
            #filename = output_dir / f"{card_id}.jpg"
            sanitized_name = sanitize_filename(card_name)
            filename = output_dir / f"{sanitized_name}.jpg"
            
            if not filename.exists(): 
                download_image(url, filename)
                time.sleep(0.1)  
            else:
                print(f" {filename}, skipped")

if __name__ == "__main__":
    main()