import argparse, sys
from pathlib import Path
from PIL import Image
from typing import Optional


def compress_jpeg_images(source_path: str, quality: int = 80) -> None:
    """
    Compresses images in a folder and saves them to the output folder as JPEG.

    Arguments:
        source_path (str): Path to the source folder containing JPEG images.
        output_path (str): Output path for compressed images.
        quality (int): Compression quality (default: 80).

    """
    patterns = ['**/*.jpeg', '**/*.jpg', '**/*.png', '**/*.gif', '**/*.bmp']
    
    try:
        source_folder = Path(source_path)
        output_folder = Path(f'{source_folder}_compressed')
        # output_folder.mkdir(parents=True, exist_ok=True)
        for file_path in [file for pattern in patterns for file in source_folder.rglob(pattern)]:
            try:
                # Replace spaces and dashes in the file name
                new_file_name = file_path.name.replace(' ', '_').replace('-', '_')
                # Replace spaces and dashes in the folder names
                new_folder_path = '/'.join(part.replace(' ', '_').replace('-', '_') for part in file_path.parts[:-1])
                # Combine the updated folder path and file name
                new_file_path = Path(new_folder_path) / new_file_name
                output_file_path = output_folder / new_file_path.relative_to(source_folder)
                output_file_path.parent.mkdir(parents=True, exist_ok=True)
                with Image.open(file_path) as image:
                    image.save(output_file_path, 'JPEG', quality=quality)
            except (IOError, OSError) as e:
                print(f"Error processing file: {file_path}. Skipping... ({e})")
    
    except FileNotFoundError:
        print(f"Folder not found: {source_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Compress JPEG images in a folder')
    parser.add_argument('source_path', type=str, nargs='?', default='.', help='Path to the folder containing JPEG images (default: current directory)')
    # parser.add_argument('output_path', type=str, nargs='?', default='./compressed_images', help='Output path for compressed images (default: ./output)')
    parser.add_argument('--quality', type=int, default=80, help='Compression quality (default: 80)')
    args = parser.parse_args()

    try:
        compress_jpeg_images(args.source_path, quality=args.quality)
    except Exception as e:
        print(f"An error occurred: {e}")
