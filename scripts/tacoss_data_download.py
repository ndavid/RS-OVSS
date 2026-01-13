import argparse
import os
import sys
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional


ZENODO_ROOT = "https://zenodo.org/records/13361624/files/"
TACOSS_FILES = {
    'flair_labels.zip': 'labels',
    'tlm_labels.zip': 'labels',
    'weights.zip': 'weights',
}


def get_directories(data_dir_arg: Optional[str], src_dir_arg: Optional[str]) -> tuple[Path, Path]:
    """Get and validate data and source directories from arguments or environment variables."""
    # Get data directory
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
    
    # Get source directory
    if src_dir_arg:
        src_dir = Path(src_dir_arg)
    else:
        env_path = os.environ.get("RS_OVSS_SRC_PATH")
        if not env_path:
            raise ValueError(
                "No source directory specified. Please provide --src_dir argument "
                "or set RS_OVSS_SRC_PATH environment variable."
            )
        src_dir = Path(env_path)
    
    data_dir.mkdir(parents=True, exist_ok=True)
    src_dir.mkdir(parents=True, exist_ok=True)
    
    return data_dir, src_dir


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
        print(f"Extracted: {zip_path.name} to {extract_dir}")
    except Exception as e:
        print(f"Error unzipping {zip_path.name}: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Download TACOSS labels and weights from Zenodo"
    )
    parser.add_argument(
        "--data_dir",
        type=str,
        default=None,
        help="Data directory (default: RS_OVSS_DATA_PATH env variable)"
    )
    parser.add_argument(
        "--src_dir",
        type=str,
        default=None,
        help="Source directory (default: RS_OVSS_SRC_PATH env variable)"
    )
    parser.add_argument(
        "--only_extract",
        action="store_true",
        help="Only extract existing zip files without downloading"
    )
    parser.add_argument(
        "--only_download",
        action="store_true",
        help="Only download files without extracting"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download and re-unzip even if files already exist"
    )
    
    args = parser.parse_args()
    
    # Validate mutually exclusive arguments
    if args.only_extract and args.only_download:
        parser.error("--only_extract and --only_download cannot be used together")
    
    try:
        data_dir, src_dir = get_directories(args.data_dir, args.src_dir)
        print(f"Data directory: {data_dir}")
        print(f"Source directory: {src_dir}")
        
        # Create tacoss subdirectory for downloads
        tacoss_dir = data_dir / "tacoss"
        tacoss_dir.mkdir(parents=True, exist_ok=True)
        
        for filename, file_type in TACOSS_FILES.items():
            url = ZENODO_ROOT + filename
            output_path = tacoss_dir / filename
            
            # Download file (unless only_extract mode)
            downloaded = False
            if not args.only_extract:
                downloaded = download_file(url, output_path, args.force)
            
            # Extract file (unless only_download mode)
            if not args.only_download:
                if downloaded or args.force or output_path.exists():
                    # Determine extraction directory based on file type
                    if file_type == 'labels':
                        extract_dir = src_dir / 'data'
                    elif file_type == 'weights':
                        extract_dir = src_dir / 'output'
                    else:
                        extract_dir = tacoss_dir
                    
                    extract_dir.mkdir(parents=True, exist_ok=True)
                    if output_path.exists():
                        unzip_file(output_path, extract_dir, args.force)
                    else:
                        print(f"Warning: {output_path.name} not found for extraction")
        
        print("\nAll operations completed successfully!")
        print(f"Files location: {tacoss_dir}")
        
        if not args.only_download:
            print(f"Labels extracted to: {src_dir / 'data'}")
            print(f"Weights extracted to: {src_dir / 'output'}")
        
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
