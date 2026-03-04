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

def ensure_output_directory(filepath: str):
    """Ensure output directory exists"""
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)


def initialize_csv_file(filepath: str):
    """Initialize CSV file with headers"""
    if os.path.exists(filepath):
        os.remove(filepath)

    ensure_output_directory(filepath)

    with open(filepath, "w", newline="", encoding="utf-8") as results_file:
        writer = csv.writer(results_file)
        writer.writerow(["original_code", "generated_code", "iverilog_output",
                         "time(s)", "prompt_tkns", "output_tkns"])