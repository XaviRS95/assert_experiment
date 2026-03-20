import csv, os

class ResultsWriter:
    """Handles writing results to CSV"""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.file = None
        self.writer = None

    def __enter__(self):
        self.file = open(self.filepath, "a", newline="", encoding="utf-8")
        self.writer = csv.writer(self.file)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            self.file.close()

    def write_result(self, original_code: str, generated_code: str,
                     compiler_output: str, elapsed_time: float,
                     prompt_tkns: int, response_tkns: int):
        """Write a single result row"""
        self.writer.writerow([
            original_code,
            generated_code,
            compiler_output,
            elapsed_time,
            prompt_tkns,
            response_tkns
        ])

        # FORCE the data out of the buffer and onto the disk
        if self.file:
            self.file.flush()
            os.fsync(self.file.fileno())  # Optional: forces OS-level write