class TokenTracker:
    """Tracks prompt and response tokens across operations"""

    def __init__(self):
        self.prompt_tkns = 0
        self.response_tkns = 0

    def save_tokens(self, prompt_tkns: int, response_tkns: int):
        """Add token counts from an operation"""
        self.prompt_tkns = prompt_tkns
        self.response_tkns = response_tkns

    def reset(self):
        """Reset token counts"""
        self.prompt_tkns = 0
        self.response_tkns = 0

    def get_totals(self):
        """Get total token counts"""
        return {
            'prompt_tkns': self.prompt_tkns,
            'response_tkns': self.response_tkns
        }