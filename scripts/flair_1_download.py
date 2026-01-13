import argparse
import os
import sys
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional


FLAIR_1_ROOT = "https://storage.gra.cloud.ovh.net/v1/AUTH_366279ce616242ebb14161b7991a8461/defi-ia/"
FLAIR_1_URLS = [
    FLAIR_1_ROOT+"flair_data_1/flair_aerial_train.zip",
    FLAIR_1_ROOT+"flair_data_1/flair_1_aerial_test.zip",
    FLAIR_1_ROOT+"flair_data_1/flair_labels_train.zip",
    FLAIR_1_ROOT+"flair_data_1/flair_1_labels_test.zip",
    FLAIR_1_ROOT+"flair_data_1/flair-1_metadata_aerial.zip",
    FLAIR_1_ROOT+"flair_data_1/flair_1_shapes.gpkg",
    FLAIR_1_ROOT+"flair_data_1/flair_1_toy_dataset.zip",
]


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
    percent = min(100, downloaded * 100 / total_size) if total_size > 0 else 0
    print(f"\rProgress: {percent:.1f}%", end="")


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


def filter_urls(urls: list, only_labels: bool, only_test: bool, only_toy: bool) -> list:
    """Filter URLs based on specified options."""
    if only_toy:
        return [url for url in urls if "toy_dataset" in url]
    
    filtered_urls = []
    
    for url in urls:
        # Skip toy dataset unless specifically requested
        if "toy_dataset" in url:
            continue
            
        # Filter by labels
        if only_labels and "labels" not in url:
            continue
        # if not only_labels and only_test is False and "labels" in url:
        #     # If not specifically asking for labels and not asking for test, skip labels
        #     pass
        
        # Filter by test/train
        if only_test and "test" not in url:
            continue
        # if not only_test and not only_labels and "test" in url:
        #     # If not asking for test specifically, skip test files (except when asking for labels)
        #     continue
            
        filtered_urls.append(url)
    
    return filtered_urls


def main():
    parser = argparse.ArgumentParser(
        description="Download FLAIR 1 dataset for TACOSS"
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
        help="Unzip downloaded files after download"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download and re-unzip even if files already exist"
    )
    parser.add_argument(
        "--only_labels",
        action="store_true",
        help="Download only label files"
    )
    parser.add_argument(
        "--only_test",
        action="store_true",
        help="Download only test files"
    )
    parser.add_argument(
        "--only_toy",
        action="store_true",
        help="Download only toy dataset"
    )
    
    args = parser.parse_args()
    
    try:
        data_dir = get_data_dir(args.data_dir)
        print(f"Data directory: {data_dir}")
        
        flair_dir = data_dir / "flair_1"
        flair_dir.mkdir(parents=True, exist_ok=True)
        
        # Filter URLs based on arguments
        urls_to_download = filter_urls(FLAIR_1_URLS, args.only_labels, args.only_test, args.only_toy)
        
        if not urls_to_download:
            print("No files match the specified criteria.")
            return
        
        print(f"Will download {len(urls_to_download)} file(s)")
        
        for url in urls_to_download:
            filename = url.split("/")[-1]
            output_path = flair_dir / filename
            
            # Download file
            downloaded = download_file(url, output_path, args.force)
            
            # Unzip if requested and file is a zip
            if args.unzip and filename.endswith(".zip"):
                if downloaded or args.force:
                    unzip_file(output_path, flair_dir, args.force)
        
        print("\nAll downloads completed successfully!")
        print(f"Files saved to: {flair_dir}")
        
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
