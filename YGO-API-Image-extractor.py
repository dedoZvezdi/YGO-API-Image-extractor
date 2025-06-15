import requests
import re
from PIL import Image
from io import BytesIO
from pathlib import Path
import time 
import shutil

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

def get_image_size_choice():
    print("\nChoose image size for all cards:")
    print("1 - Normal")
    print("2 - Small")
    print("3 - Cropped")
    
    while True:
        choice = input("Enter choice (1/2/3): ").strip()
        if choice in ('1', '2', '3'):
            return {
                '1': 'image_url',
                '2': 'image_url_small',
                '3': 'image_url_cropped'
            }[choice]
        print("Invalid choice. Try again.")

def extract_image_url(card, url_key):
    for image in card.get('card_images', []):
        url = image.get(url_key)
        if url:
            return url
    return None

def get_resize_preference():
    while True:
        choice = input("\nDo you want to resize images? (Y/N): ").strip().upper()
        if choice == 'Y':
            while True:
                try:
                    width = int(input("Enter width in pixels: "))
                    height = int(input("Enter height in pixels: "))
                    if width <= 0 or height <= 0:
                        print("Dimensions must be positive numbers!")
                        continue
                    return (width, height)
                except ValueError:
                    print("Please enter valid numbers!")
        elif choice == 'N':
            return None
        else:
            print("Invalid choice. Try again.")

def download_image(url, filename, size=None):
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        with Image.open(BytesIO(response.content)) as img:
            if size:
                img = img.resize(size, Image.Resampling.LANCZOS)
            img.save(filename)
            
        print(f"Downloaded {'and resized ' if size else ''}{filename}")
        return True
        
    except requests.RequestException as e:
        print(f"Download failed for {filename}: {e}")
    except IOError as e:
        print(f"File save failed for {filename}: {e}")
    except Exception as e:
        print(f"Unexpected error with {filename}: {e}")
    
    return False

def get_target_directory():
    while True:  
        dir_input = input("\nEnter target directory (or drag & drop): ").strip(' "\'')
        if not dir_input:
            print("Error: Please enter a directory path.")
            continue
            
        base_dir = Path(dir_input)
        if not base_dir.exists():
            print(f"Error: Directory '{base_dir}' doesn't exist.")
            continue
        
        create_new = input("\nDo you want to create a new subfolder? (Y/N): ").strip().upper()
        if create_new != 'Y':
            print(f"Using existing directory: {base_dir}")
            return base_dir

        while True:
            folder_name = input("\nEnter new folder name: ").strip()
            if not folder_name:
                print("Error: Folder name cannot be empty.")
                continue
                
            invalid_chars = re.findall(r'[\\/*?:"<>|]', folder_name)
            if invalid_chars:
                print(f"Error: Invalid characters detected: {', '.join(set(invalid_chars))}")
                continue
            break
            
        target_dir = base_dir / folder_name
        
        if target_dir.exists():
            print(f"\nFolder '{folder_name}' already exists in:\n{base_dir}")
            while True:  
                print("\nChoose action:")
                print("1 - Overwrite existing folder")
                print("2 - Create with automatic unique name")
                print("3 - Select different parent directory")
                print("0 - Cancel operation")
                
                choice = input("Your choice: ").strip()
                
                if choice == '1':  
                    try:
                        shutil.rmtree(target_dir)
                        target_dir.mkdir()
                        print(f"\nSuccess: Overwritten existing folder\n{target_dir}")
                        return target_dir
                    except Exception as e:
                        print(f"\nError: Failed to overwrite folder\nReason: {e}")
                        break  
                        
                elif choice == '2': 
                    counter = 1
                    while True:
                        new_dir = base_dir / f"{folder_name}_{counter}"
                        if not new_dir.exists():
                            try:
                                new_dir.mkdir()
                                print(f"\nSuccess: Created new folder\n{new_dir}")
                                return new_dir
                            except Exception as e:
                                print(f"\nError: Failed to create folder\nReason: {e}")
                                break  
                        counter += 1
                        
                elif choice == '3':  
                    break  
                    
                elif choice == '0':  
                    return None
                    
                else:
                    print("\nInvalid choice. Please enter 0-3.")
                    continue
                    
        else:  
            try:
                target_dir.mkdir()
                print(f"\nSuccess: Created new folder\n{target_dir}")
                return target_dir
            except Exception as e:
                print(f"\nError: Failed to create folder\nReason: {e}")
                continue

def get_card_reference_choice():
    while True:
        print("\nChoose card reference method:")
        print("1 - By name")
        print("2 - By ID")
        choice = input("Choose -> ").strip()
        
        if choice in ('1', '2'):
            return choice == '1' 
        print("\nInvalid input! Please enter either 1 or 2.")

def main():
    downloaded = 0
    skipped = 0
    
    try:
        url_key = get_image_size_choice()
        resize_dimensions = get_resize_preference()
        
        while True:
            ref_choice = input("\nChoose card reference:\n1 - By name\n2 - By ID\nChoose -> ").strip()
            if ref_choice in ('1', '2'):
                use_name = ref_choice == '1'
                break
            print("Invalid choice. Please enter 1 or 2.")

        print("\nFetching card data...")
        json_data = fetch_data(api_url)
        if not json_data or 'data' not in json_data:
            print("Error: Failed to fetch card data or no cards found.")
            return

        print("\nSelect download location:")
        output_dir = get_target_directory()
        if not output_dir:
            print("Operation canceled by user.")
            return

        total_cards = len(json_data['data'])
        print(f"\nStarting download of {total_cards} cards to: {output_dir}")
        
        for i, card in enumerate(json_data['data'], 1):
            try:
                card_name = card.get('name')
                card_id = card.get('id')
                url = extract_image_url(card, url_key)
                
                if not url:
                    continue

                if use_name and card_name:
                    filename = output_dir / f"{sanitize_filename(card_name)}.jpg"
                elif not use_name and card_id:
                    filename = output_dir / f"{card_id}.jpg"
                else:
                    continue

                if filename.exists():
                    print(f"[{i}/{total_cards}] Skipped (exists): {filename.name}")
                    skipped += 1
                    continue

                success = download_image(url, filename, resize_dimensions)
                if success:
                    downloaded += 1
                    status = "Downloaded" + (" and resized" if resize_dimensions else "")
                    print(f"[{i}/{total_cards}] {status}: {filename.name}")
                
                time.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                print(f"[{i}/{total_cards}] Error processing card: {e}")
                continue

    except KeyboardInterrupt:
        print("\nOperation canceled by user.")
    except Exception as e:
        print(f"\nCritical error: {e}")
    finally:

        if downloaded > 0 or skipped > 0:
            print(f"\nDownload complete! Downloaded: {downloaded}, Skipped: {skipped}")
            if resize_dimensions:
                print(f"Resized to: {resize_dimensions[0]}x{resize_dimensions[1]}px")
            print(f"Location: {output_dir}")
if __name__ == "__main__":
    main()