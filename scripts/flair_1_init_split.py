import argparse
import os
import sys
import csv
import random
import urllib.request
from pathlib import Path


# GitHub raw URLs for FLAIR-1 CSV splits
GITHUB_FLAIR_1_ROOT = 'https://raw.githubusercontent.com/IGNF/FLAIR-1/2489539332818265b2aa6c878bbee6cf0994b370/'
GITHUB_CSV_SPLIT = [
    ('train.csv', 'csv_full','flair-1-paths-train.csv'),
    ('val.csv', 'csv_full', 'flair-1-paths-val.csv'),
    ('test.csv': 'csv_full', 'flair-1-paths-test.csv'),
    ('train.csv', 'csv_toy','flair-1-paths-train.csv'),
    ('val.csv', 'csv_toy', 'flair-1-paths-val.csv'),
    ('test.csv': 'csv_toy', 'flair-1-paths-test.csv'),
]
FLAIR_SUBDIR = "flair-1"

def download_csv_from_github(output_dir):
    """Download CSV split files from FLAIR-1 GitHub repository.
    
    Args:
        output_dir: Directory where CSV files will be saved
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Downloading CSV splits from GitHub...")
    
    for out_name, in_subdir, in_name in GITHUB_CSV_SPLIT:
        download_path = output_dir / in_subdir/ in_name
        url = GITHUB_FLAIR_1_ROOT + in_path + '/' + in_name
        
        try:
            print(f"Downloading {filename}...")
            urllib.request.urlretrieve(url, download_path)
            
            print(f"Successfully downloaded {filename}")
        except Exception as e:
            print(f"Error downloading {filename}: {e}")
            raise

        out_name = f"{in_name.split("-")[1]}.csv"
        data_suffix = "train"
        if in_sudbir == "csv_full" :
            out_subdir = 'base'
            if out_name == "test.csv":
                data_suffix = "test"
            renaming_dict = {
                "../flair_aerial_train/" : FLAIR_SUBDIR/"flair_aerial_train",
                "../flair_labels_train/" : FLAIR_SUBDIR/"flair_labels_train",
                "../data/flair_1_aerial_test/" : FLAIR_SUBDIR/"flair_aerial_test",
                "../data/flair_1_labels_test/" : FLAIR_SUBDIR/"flair_labels_test",
            }
        else:
            out_subdir = "dev"
            renaming_dict = {
                "../flair_1_toy_aerial_train" : FLAIR_SUBDIR/"flair_aerial_train",
                "../flair_1_toy_labels_train" : FLAIR_SUBDIR/"flair_labels_train",
                "../flair_1_toy_aerial_test" : FLAIR_SUBDIR/"flair_aerial_train",
                "../flair_1_toy_labels_test" : FLAIR_SUBDIR/"flair_labels_train",
            }
        
        output_csv_path = output_dir / out_subdir/ out_name
        convert_csv(
            download_path, output_csv_path, renaming_dict= renaming_dict)
    print(f"All CSV files downloaded to: {output_dir}")


def convert_csv(input_csv_path, output_csv_path, renaming_dict=None, prefix_path=None):
    """Convert CSV paths using a renaming dictionary or new prefix path.
    
    Extracts the last parts of paths ({domain}/{zone}/img/IMG_{id}.tif) and 
    reconstructs them with new prefixes from renaming_dict or prefix_path.
    
    Args:
        input_csv_path: Path to input CSV file
        output_csv_path: Path to output CSV file
        renaming_dict: Dictionary mapping old prefixes to new prefixes
                      e.g., {'flair_1_toy_dataset/train': 'flair_aerial_train'}
        prefix_path: Single new prefix to use for all paths (alternative to renaming_dict)
    """
    if renaming_dict is None and prefix_path is None:
        raise ValueError("Either renaming_dict or prefix_path must be provided")
    
    pairs = []
    
    with open(input_csv_path, 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if len(row) != 2:
                continue
            
            img_path, msk_path = row
            
            # Process image path
            img_path_parts = Path(img_path).parts
            # Extract last 4 parts: {domain}/{zone}/img/IMG_{id}.tif
            if len(img_path_parts) >= 4:
                relative_parts = img_path_parts[-4:]
                
                if prefix_path:
                    new_img_path = str(Path(prefix_path) / Path(*relative_parts))
                else:
                    # Find matching prefix in renaming_dict
                    old_prefix = str(Path(*img_path_parts[:-4]))
                    new_prefix = renaming_dict.get(old_prefix, old_prefix)
                    new_img_path = str(Path(new_prefix) / Path(*relative_parts))
            else:
                new_img_path = img_path
            
            # Process mask path
            msk_path_parts = Path(msk_path).parts
            # Extract last 4 parts: {domain}/{zone}/msk/MSK_{id}.tif
            if len(msk_path_parts) >= 4:
                relative_parts = msk_path_parts[-4:]
                
                if prefix_path:
                    new_msk_path = str(Path(prefix_path) / Path(*relative_parts))
                else:
                    # Find matching prefix in renaming_dict
                    old_prefix = str(Path(*msk_path_parts[:-4]))
                    new_prefix = renaming_dict.get(old_prefix, old_prefix)
                    new_msk_path = str(Path(new_prefix) / Path(*relative_parts))
            else:
                new_msk_path = msk_path
            
            pairs.append((new_img_path, new_msk_path))
    
    # Write converted CSV
    output_csv_path = Path(output_csv_path)
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(pairs)
    
    print(f"Successfully converted {input_csv_path} to {output_csv_path} with {len(pairs)} pairs")


def create_csv_mapping(aerial_dir, labels_dir, csv_path, root_dir, output_dir=None):
    """Create CSV file mapping FLAIR-1 aerial images to their corresponding label masks.
    
    the directories should follow the FLAIR-1 structure as in the official download
    on https://ignf.github.io/FLAIR/FLAIR1/flair_1.html

    Args:
        aerial_dir: Path to directory containing aerial images
        labels_dir: Path to directory containing label masks
        csv_path: Path where the CSV file will be created OR list of tuples (path, percent)
                  for splitting into multiple files
        root_dir: Root directory for calculating relative paths
        output_dir: Optional directory where CSV files should be written. If None, uses root_dir
    """
    # Get all aerial images with nested structure
    aerial_images = sorted(aerial_dir.glob('*/*/img/IMG_*.tif'))
    
    if not aerial_images:
        print(f"Warning: No images found in {aerial_dir}")
        return
    
    pairs = []
    
    for aerial_img in aerial_images:
        # Extract domain and zone from path: aerial_dir/{domain}/{zone}/img/IMG_{id}.tif
        zone_name = aerial_img.parent.parent.name  # zone
        domain_name = aerial_img.parent.parent.parent.name  # domain
        
        # Get image ID from filename: IMG_{id}.tif -> {id}
        img_id = aerial_img.stem.replace('IMG_', '')
        
        # Construct corresponding mask path
        mask_img = labels_dir / domain_name / zone_name / 'msk' / f'MSK_{img_id}.tif'
        
        if mask_img.exists():
            # Use relative paths from root_dir
            aerial_rel = aerial_img.relative_to(root_dir)
            mask_rel = mask_img.relative_to(root_dir)
            pairs.append((str(aerial_rel), str(mask_rel)))
        else:
            print(f"Warning: No corresponding mask found for {aerial_img.name} at {mask_img}")
    
    # Determine output directory
    out_dir = Path(output_dir) if output_dir else root_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if csv_path is a list of tuples for splitting
    if isinstance(csv_path, list):
        # Shuffle pairs for random split
        random.shuffle(pairs)
        
        # Validate percentages sum to 100
        total_percent = sum(percent for _, percent in csv_path)
        if abs(total_percent - 100) > 0.01:
            print(f"Error: Percentages must sum to 100, got {total_percent}")
            return
        
        start_idx = 0
        for path, percent in csv_path:
            # Calculate number of pairs for this split
            num_pairs = int(len(pairs) * percent / 100)
            
            # Adjust last split to include all remaining pairs
            if path == csv_path[-1][0]:
                end_idx = len(pairs)
            else:
                end_idx = start_idx + num_pairs
            
            split_pairs = pairs[start_idx:end_idx]
            
            # Write CSV
            csv_file = out_dir / path
            with open(csv_file, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(split_pairs)
            
            print(f"Successfully created {csv_file} with {len(split_pairs)} image pairs ({percent}%)")
            start_idx = end_idx
    else:
        # Single CSV file
        csv_file = out_dir / csv_path
        with open(csv_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(pairs)
        
        print(f"Successfully created {csv_file} with {len(pairs)} image pairs")


def main():
    parser = argparse.ArgumentParser(description='Initialize FLAIR-1 dataset split')
    parser.add_argument('--data_dir', type=str, default=None, 
                       help='Root directory containing FLAIR-1 subdirectories (default: RS_OVSS_DATA_PATH env var)')
    parser.add_argument('--output_csv_dir', type=str, default=None,
                       help='Directory where CSV files will be written (default: RS_OVSS_SRC_PATH env var or script directory)')
    parser.add_argument('--use_github_split', action='store_true',
                       help='Download CSV splits from FLAIR-1 GitHub repository instead of creating them')
    args = parser.parse_args()
    
    # Determine output CSV directory
    if args.output_csv_dir:
        output_csv_dir = Path(args.output_csv_dir)
    elif 'RS_OVSS_SRC_PATH' in os.environ:
        output_csv_dir = Path(os.environ['RS_OVSS_SRC_PATH']) / 'data' / 'flair_split'
    else:
        output_csv_dir = Path(__file__).parent / 'data' / 'flair_split' 
    
    print(f"CSV files will be written to: {output_csv_dir}")
    
    # If using GitHub splits, download and exit
    if args.use_github_split:
        github_output_dir = output_csv_dir
        download_csv_from_github(github_output_dir)
        return
    
    # Determine root data directory
    if args.data_dir:
        root_dir = Path(args.data_dir)
    elif 'RS_OVSS_DATA_PATH' in os.environ:
        root_dir = Path(os.environ['RS_OVSS_DATA_PATH'])/"flair_1"
        print(f"Using data directory from RS_OVSS_DATA_PATH: {root_dir}")
    else:
        print("Error: No data directory specified.")
        print("Please provide --data_dir argument or set RS_OVSS_DATA_PATH environment variable.")
        return
    
    # Check if root directory exists
    if not root_dir.exists():
        print(f"Error: Directory '{root_dir}' does not exist")
        return
    
    # Define required subdirectories
    required_dirs = [
        'flair_1_aerial_test',
        'flair_1_labels_test',
        'flair_aerial_train',
        'flair_labels_train'
    ]
    
    # Check if all required subdirectories exist
    missing_dirs = []
    for dir_name in required_dirs:
        dir_path = root_dir / dir_name
        if not dir_path.exists():
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        print(f"Error: The following required subdirectories are missing:")
        for dir_name in missing_dirs:
            print(f"  - {dir_name}")
        return
    
    # Check if toy dataset exists and convert CSVs
    toy_csv_dir = root_dir / 'flair_1_toy_dataset' / 'CSVs'
    if toy_csv_dir.exists():
        print(f"Found toy dataset CSVs at {toy_csv_dir}")
        toy_output_dir = output_csv_dir / 'toy'
        toy_output_dir.mkdir(parents=True, exist_ok=True)
        
        renaming_dict = {
            "../flair_1_toy_aerial_train" : FLAIR_SUBDIR/"flair_aerial_train",
            "../flair_1_toy_labels_train" : FLAIR_SUBDIR/"flair_labels_train",
            "../flair_1_toy_aerial_test" : FLAIR_SUBDIR/"flair_aerial_train",
            "../flair_1_toy_labels_test" : FLAIR_SUBDIR/"flair_labels_train",
        }
        for csv_file in toy_csv_dir.glob('*.csv'):
            output_csv = toy_output_dir / 'dev' / csv_file.name
            convert_csv(
                csv_file, output_csv, renaming_dict= renaming_dict)
    
    # Get paths to train directories
    aerial_train_dir = root_dir / 'flair_aerial_train'
    labels_train_dir = root_dir / 'flair_labels_train'
    # Create train.csv
    create_csv_mapping(
        aerial_train_dir, 
        labels_train_dir, 
        [('train.csv', 80), ('val.csv', 20)], 
        root_dir, 
        output_csv_dir/ 'base')

    # Get paths to test directories
    aerial_test_dir = root_dir / 'flair_1_aerial_test'
    labels_test_dir = root_dir / 'flair_1_labels_test'
    # Create test.csv
    create_csv_mapping(
        aerial_test_dir, 
        labels_test_dir, 
        'test.csv', 
        root_dir, 
        output_csv_dir/ 'base')


if __name__ == '__main__':
    main()
