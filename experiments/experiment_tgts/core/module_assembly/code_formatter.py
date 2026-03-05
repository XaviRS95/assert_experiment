class CodeFormatter:
    """Formats different parts of the final module"""

    @staticmethod
    def format_parameters(parameters: str) -> str:
        """Format parameters section"""
        return f'# ({parameters})' if parameters else ''

    @staticmethod
    def format_ports(ports: str) -> str:
        """Format ports section (convert output logic to input logic)"""
        return ports.replace('output logic', 'input logic')

    @staticmethod
    def format_assertion_block(immediate_assertions: list) -> str:
        """Format immediate assertions into an always_comb block"""
        if not immediate_assertions:
            return ''

        assertions_text = '\n\n'.join(immediate_assertions)
        return f"always_comb begin\n    {assertions_text}\n    end"

    @staticmethod
    def format_properties_block(sequential_properties: list) -> str:
        """Format sequential properties"""
        if not sequential_properties:
            return ''
        return '\n'.join(sequential_properties)

    @staticmethod
    def format_functions(func_blocks: list) -> str:
        """Format function blocks"""
        if not func_blocks:
            return ''
        return '\n\n'.join(func_blocks)