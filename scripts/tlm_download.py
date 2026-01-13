import argparse
import os
import sys
import zipfile
from pathlib import Path
from typing import Optional
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup

TLM_GOOGLE_DRIVE_URL = "https://drive.usercontent.google.com/download?id=12qsQ_9ef7PeJ3WAOJz7szIa0Qbk0ItjZ&export=download&authuser=0&confirm=t"
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


def download_from_google(file_id: str, file_name: str, target: str = "."):
    """
    Downloads a file from Google Drive, handling potential confirmation tokens for large files.

    Args:
        file_id (str):
            The ID of the file to download from Google Drive.
        file_name (str):
            The name to save the downloaded file as.
        target (str, optional):
            The directory to save the file in. Defaults to the current directory (".").

    Raises:
        Exception: If the download fails or the file cannot be created.

    Notes:
        This function handles both small and large files. For large files, it automatically processes
        Google's confirmation token to bypass warnings about virus scans or file size limits.

    Example:
        Download a file to the current directory:
            download_from_google(
                file_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                file_name="example_file.txt"
            )

        Download a file to a specific directory:
            download_from_google(
                file_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                file_name="example_file.txt",
                target="./downloads"
            )
    """
    # First try: docs.google.com/uc?export=download&id=FileID
    base_url = "https://docs.google.com/uc"
    session = requests.Session()
    params = {
        "export": "download",
        "id": file_id
    }
    response = session.get(base_url, params=params, stream=True)

    # If Content-Disposition is present, the file is directly available
    if "content-disposition" not in response.headers:
        # Try to get the token from cookies
        token = None
        for k, v in response.cookies.items():
            if k.startswith("download_warning"):
                token = v
                break

        # If no token in cookies, extract it from the HTML
        if not token:
            soup = BeautifulSoup(response.text, "html.parser")
            # Common case: HTML contains a form with id="download-form"
            download_form = soup.find("form", {"id": "download-form"})
            if download_form and download_form.get("action"):
                # Extract action URL, which might be drive.usercontent.google.com/download
                download_url = download_form["action"]
                # Collect all hidden inputs
                hidden_inputs = download_form.find_all("input", {"type": "hidden"})
                form_params = {}
                for inp in hidden_inputs:
                    if inp.get("name") and inp.get("value") is not None:
                        form_params[inp["name"]] = inp["value"]

                # Re-send the GET request with these parameters
                response = session.get(download_url, params=form_params, stream=True)
            else:
                # Otherwise, search for confirm=xxx in HTML
                match = re.search(r'confirm=([0-9A-Za-z-_]+)', response.text)
                if match:
                    token = match.group(1)
                    # Include the confirm token in the request
                    params["confirm"] = token
                    response = session.get(base_url, params=params, stream=True)
                else:
                    raise Exception("Unable to find the download link or confirmation token in the response. Download failed.")

        else:
            # Use the token obtained from cookies and resend the request
            params["confirm"] = token
            response = session.get(base_url, params=params, stream=True)

    # Ensure the download directory exists
    os.makedirs(target, exist_ok=True)
    file_path = os.path.join(target, file_name)

    # Start downloading the file in chunks, with a progress bar
    try:
        total_size = int(response.headers.get('content-length', 0))
        with open(file_path, "wb") as f, tqdm(
            desc=file_name,
            total=total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for chunk in response.iter_content(chunk_size=32768):
                if chunk:
                    f.write(chunk)
                    bar.update(len(chunk))

        print(f"File successfully downloaded to: {file_path}")

    except Exception as e:
        raise Exception(f"File download failed: {e}")


def download_file(id_doc: str, output_path: Path, force: bool = False) -> bool:
    """Download a file from Google Drive to output path."""
    if output_path.exists() and not force:
        print(f"Skipping {output_path.name} (already exists, use --force to re-download)")
        return False
    
    print(f"Downloading {output_path.name}...")
    try:
        # download_file_from_google_drive(id_doc, output_path)
        download_from_google(id_doc, str(output_path.name), str(output_path.parent))
        print(f"\nCompleted: {output_path.name}")
        return True
    except Exception as e:
        print(f"\nError downloading {output_path.name}: {e}")
        if output_path.exists():
            output_path.unlink()
        raise


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
        downloaded = download_file(
            "12qsQ_9ef7PeJ3WAOJz7szIa0Qbk0ItjZ", 
            output_path, 
            args.force)
        
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
