import argparse
import os
import sys
import csv
import random
from pathlib import Path


def create_csv_mapping(aerial_dir, csv_path, root_dir, output_dir=None, percent=100):
    """Create CSV file mapping TLM aerial images to their corresponding label masks.
    
    Args:
        aerial_dir: Path to directory containing aerial images
        csv_path: Path where the CSV file will be created
        root_dir: Root directory for calculating relative paths
        output_dir: Optional directory where CSV files should be written. If None, uses root_dir
        percent: Percentage of data to include (1-100)
    """
    # Get all aerial images (adjust pattern based on TLM structure)
    aerial_images = sorted(aerial_dir.glob('**/*.tif'))
    
    if not aerial_images:
        print(f"Warning: No images found in {aerial_dir}")
        return
    
    id_list = []
    
    for aerial_img in aerial_images:
        # Get relative path from aerial_dir
        rel_path = aerial_img.relative_to(aerial_dir)
        img_name = rel_path.stem
        tlm_id = "_".join(img_name.split("_")[:-1])
        print(tlm_id)
        id_list.append([tlm_id])
    
    # Apply percentage filter if less than 100%
    if percent < 100:
        random.shuffle(id_list)
        num_id = max(1, int(len(id_list) * percent / 100))
        id_list = id_list[:num_id]
        print(f"Selected {num_id} pairs ({percent}% of {len(id_list)} total)")
    
    # Determine output directory
    out_dir = Path(output_dir) if output_dir else root_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Write CSV file
    csv_file = out_dir / csv_path
    csv_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(csv_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(id_list)
    
    print(f"Successfully created {csv_file} with {len(id_list)} image pairs")


def main():
    parser = argparse.ArgumentParser(description='Initialize TLM dataset test split')
    parser.add_argument('--data_dir', type=str, default=None, 
                       help='Root directory containing TLM subdirectories (default: RS_OVSS_DATA_PATH env var)')
    parser.add_argument('--output_csv_dir', type=str, default=None,
                       help='Directory where CSV file will be written (default: RS_OVSS_SRC_PATH env var or script directory)')
    parser.add_argument('--percent', type=float, default=100,
                       help='Percentage of data to include in split (1-100, default: 100)')
    parser.add_argument('--aerial_subdir', type=str, default='SI',
                       help='Subdirectory name for aerial images (default: SI)')
    args = parser.parse_args()
    
    # Validate percent
    if args.percent <= 0 or args.percent > 100:
        print("Error: --percent must be between 1 and 100")
        return
    
    # Determine root data directory
    if args.data_dir:
        root_dir = Path(args.data_dir)
    elif 'RS_OVSS_DATA_PATH' in os.environ:
        root_dir = Path(os.environ['RS_OVSS_DATA_PATH']) 
        print(f"Using data directory from RS_OVSS_DATA_PATH: {root_dir}")
    else:
        print("Error: No data directory specified.")
        print("Please provide --data_dir argument or set RS_OVSS_DATA_PATH environment variable.")
        return
    
    # Check if root directory exists
    if not root_dir.exists():
        print(f"Error: Directory '{root_dir}' does not exist")
        return
    
    # Determine output CSV directory
    if args.output_csv_dir:
        output_csv_dir = Path(args.output_csv_dir)
    elif 'RS_OVSS_SRC_PATH' in os.environ:
        output_csv_dir = Path(os.environ['RS_OVSS_SRC_PATH']) / 'data' / 'tlm_split'
    else:
        output_csv_dir = Path(__file__).parent / 'data' / 'tlm_split'
    
    print(f"CSV file will be written to: {output_csv_dir}")
    
    # Get paths to aerial and labels directories
    aerial_dir = root_dir / "soleil_dataset" / args.aerial_subdir
    
    # Check if required subdirectories exist
    if not aerial_dir.exists():
        print(f"Error: Aerial directory '{aerial_dir}' does not exist")
        return
    
    # Create test.csv
    create_csv_mapping(
        aerial_dir,
        'soleil_100m.csv',
        root_dir,
        output_csv_dir,
        percent=args.percent
    )


if __name__ == '__main__':
    main()
