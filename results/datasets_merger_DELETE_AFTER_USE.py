import pandas as pd
import os
from pathlib import Path


def merge_csv_parts(parent_folder):
    folder_path = Path(parent_folder)

    # 1. Identify all "base" files (those that DON'T end in _part1.csv)
    # We look for .csv files that don't have the suffix to find our targets
    base_files = [f for f in folder_path.glob("*.csv") if "_part1" not in f.name]

    for base_file in base_files:
        # 2. Construct the name of the potential part1 file
        # This replaces '.csv' with '_part1.csv'
        part1_file = base_file.with_name(f"{base_file.stem}_part1.csv")

        if part1_file.exists():
            print(f"Merging: {part1_file.name} -> {base_file.name}")

            # 3. Read both files
            df_part1 = pd.read_csv(part1_file)
            df_base = pd.read_csv(base_file)

            # 4. Concatenate (Part 1 first)
            combined_df = pd.concat([df_part1, df_base], ignore_index=True)

            # 5. Overwrite the base file with the combined data
            combined_df.to_csv(base_file, index=False)

            # 6. Remove the part1 file
            part1_file.unlink()
            print(f"Done. Deleted {part1_file.name}")
        else:
            print(f"Skipping: No part1 found for {base_file.name}")

# Usage:
merge_csv_parts("results/qwen3-coder_480b")