#!/bin/bash

# Define source and destination directories
SOURCE_DIR="/RAID/algotrade/sapumal"
DEST_DIR="/home/savindu/savindu/dataset/dataset"

# Create destination directory if it does not exist
mkdir -p "$DEST_DIR"

# Loop through all directories inside the source directory
for dir in "$SOURCE_DIR"/*/; do
    # Extract directory name
    dir_name=$(basename "$dir")

    # Skip the specific directory
    if [[ "$dir_name" == "xep_m201902_ctm" ]]; then
        continue
    fi

    # Extract year and month from directory name (assuming format xep_mYYYYMM)
    if [[ "$dir_name" =~ xep_m([0-9]{6}) ]]; then
        year_month="${BASH_REMATCH[1]}"
        
        # Create the target directory inside the destination
        mkdir -p "$DEST_DIR/$year_month"
        
        # Copy ctm and wct files to the respective year-month directory
        find "$dir" -maxdepth 1 -type f \( -name "ctm*.parquet" -o -name "wct*.parquet" \) -exec cp {} "$DEST_DIR/$year_month/" \;
        
        echo "Copied files from $dir to $DEST_DIR/$year_month/"
    fi
done

echo "File copy complete!"
