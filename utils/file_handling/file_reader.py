import csv, os
from pathlib import Path

def read_modules_file(filepath: str) -> list:
    """
    Reads SystemVerilog modules from a CSV file.

    Args:
        filepath: Path to the CSV file containing a 'modules' column

    Returns:
        List of module strings (excluding the header row)
    """
    modules = []

    final_filepath = f'{Path(__file__).parent.parent.parent.absolute()}/datasets/{filepath}'

    if not os.path.exists(final_filepath):
        raise FileNotFoundError(f"CSV file not found: {final_filepath}")

    with open(final_filepath, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)  # Uses first row as headers

        for row in reader:
            if 'modules' in row and row['modules'].strip():
                modules.append(row['modules'].strip())

    print(f"Loaded {len(modules)} modules from {final_filepath}")
    return modules