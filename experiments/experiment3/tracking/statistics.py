class ExperimentStatistics:
    """Tracks experiment statistics"""

    def __init__(self):
        self.correctly_generated = 0
        self.total_modules = 0

    def increment_total(self):
        """Increment total modules counter"""
        self.total_modules += 1

    def increment_correct(self):
        """Increment correctly generated counter"""
        self.correctly_generated += 1

    def print_progress(self, module_num: int, total_modules: int,
                       compiler_output: str, elapsed_time: float):
        """Print progress information"""
        print(f'Module #{module_num} out of {total_modules}')
        print(f"Status: {compiler_output} | Time: {elapsed_time:.2f}s")
        print("########################################")

    def get_summary(self):
        """Get experiment summary"""
        return {
            'correct': self.correctly_generated,
            'total': self.total_modules,
            'success_rate': (self.correctly_generated / self.total_modules * 100
                             if self.total_modules > 0 else 0)
        }