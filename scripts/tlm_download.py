import argparse
import os
import sys
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional


TLM_GOOGLE_DRIVE_URL = "https://drive.usercontent.google.com/download?id=12qsQ_9ef7PeJ3WAOJz7szIa0Qbk0ItjZ&export=download&authuser=0"
TLM_FILENAME = "tlm_dataset.zip"


def get_data_dir(data_dir_arg: Optional[str]) -> Path:
    """Get and validate the data directory from argument or environment variable."""
    if data_dir_arg:
        data_dir = Path(data_dir_arg)
    else:
        env_path = os.environ.get("RS_OVSS_DATA_PATH")
        if not env_path:
            raise ValueError(
                "No data directory specified. Please provide --data_dir argument "
                "or set RS_OVSS_DATA_PATH environment variable."
            )
        data_dir = Path(env_path)
    
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def download_file(url: str, output_path: Path, force: bool = False) -> bool:
    """Download a file from URL to output path."""
    if output_path.exists() and not force:
        print(f"Skipping {output_path.name} (already exists, use --force to re-download)")
        return False
    
    print(f"Downloading {output_path.name}...")
    try:
        # Set user agent for Google Drive
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)
        
        urllib.request.urlretrieve(url, output_path, reporthook=download_progress)
        print(f"\nCompleted: {output_path.name}")
        return True
    except Exception as e:
        print(f"\nError downloading {output_path.name}: {e}")
        if output_path.exists():
            output_path.unlink()
        raise


def download_progress(block_num: int, block_size: int, total_size: int):
    """Display download progress."""
    downloaded = block_num * block_size
    if total_size > 0:
        percent = min(100, downloaded * 100 / total_size)
        print(f"\rProgress: {percent:.1f}%", end="")
    else:
        # For Google Drive, total_size might be -1
        print(f"\rDownloaded: {downloaded / (1024*1024):.1f} MB", end="")


def unzip_file(zip_path: Path, extract_dir: Path, force: bool = False):
    """Unzip a file to the specified directory."""
    # Check if already extracted (heuristic: directory with similar name exists)
    extract_subdir = extract_dir / zip_path.stem
    if extract_subdir.exists() and not force:
        print(f"Skipping unzip of {zip_path.name} (already extracted, use --force to re-extract)")
        return
    
    print(f"Unzipping {zip_path.name}...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        print(f"Extracted: {zip_path.name}")
    except Exception as e:
        print(f"Error unzipping {zip_path.name}: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Download TLM dataset from Google Drive"
    )
    parser.add_argument(
        "--data_dir",
        type=str,
        default=None,
        help="Output directory for downloaded data (default: RS_OVSS_DATA_PATH env variable)"
    )
    parser.add_argument(
        "--unzip",
        action="store_true",
        help="Unzip downloaded file after download"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download and re-unzip even if files already exist"
    )
    
    args = parser.parse_args()
    
    try:
        data_dir = get_data_dir(args.data_dir)
        print(f"Data directory: {data_dir}")
        
        tlm_dir = data_dir / "tlm"
        tlm_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = tlm_dir / TLM_FILENAME
        
        # Download file
        downloaded = download_file(TLM_GOOGLE_DRIVE_URL, output_path, args.force)
        
        # Unzip if requested
        if args.unzip:
            # if downloaded or args.force:
            unzip_file(output_path, tlm_dir, args.force)
        
        print("\nDownload completed successfully!")
        print(f"File saved to: {tlm_dir}")
        
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
