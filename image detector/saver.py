import os
import urllib.request

# --- Configuration ---
# Directory to save images into
IMAGE_DIR = "images"

# Dictionary with new, more reliable image URLs
IMAGE_URLS = {
    "apple.png": "https://i.imgur.com/vH51C4R.png",
    "broccoli.png": "https://i.imgur.com/gmtmk27.png",
    "carrot.png": "https://i.imgur.com/ad2T18b.png",
    "pizza.png": "https://i.imgur.com/eB9E5aC.png",
    "burger.png": "https://i.imgur.com/L53m2p4.png",
    "donut.png": "https://i.imgur.com/qbjL617.png",
}

def download_all_images():
    """
    Creates the image directory and downloads all required images from the web.
    """
    # Create the 'images' directory if it doesn't already exist
    if not os.path.exists(IMAGE_DIR):
        print(f"Creating directory: '{IMAGE_DIR}'")
        os.makedirs(IMAGE_DIR)
    else:
        print(f"Directory '{IMAGE_DIR}' already exists.")

    print("\nStarting image download...")
    
    # Loop through all the image URLs
    for filename, url in IMAGE_URLS.items():
        # Create the full path to save the file
        save_path = os.path.join(IMAGE_DIR, filename)
        
        # Check if the file already exists to avoid re-downloading
        if not os.path.exists(save_path):
            print(f"Downloading '{filename}'...")
            try:
                # Use a proper user-agent header to avoid being blocked
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response, open(save_path, 'wb') as out_file:
                    data = response.read() # a `bytes` object
                    out_file.write(data)
            except Exception as e:
                print(f"  --> Failed to download {filename}. Error: {e}")
        else:
            print(f"Skipping '{filename}', already downloaded.")
            
    # Removed the emoji to prevent encoding errors on Windows
    print("\nDownload process complete!")

if __name__ == "__main__":
    download_all_images()