import os, csv

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