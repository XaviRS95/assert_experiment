from .code_formatter import CodeFormatter
class ModuleBuilder:
    """Builds the final SystemVerilog module"""

    def __init__(self):
        self.formatter = CodeFormatter()

    def build(self, module_name: str, parameters: str, ports: str,
              inner_vars: str, func_blocks: list,
              immediate_assertions: list, sequential_properties: list) -> str:
        """Build the complete module"""

        formatted_params = self.formatter.format_parameters(parameters)
        formatted_ports = self.formatter.format_ports(ports)
        formatted_assertions = self.formatter.format_assertion_block(immediate_assertions)
        formatted_properties = self.formatter.format_properties_block(sequential_properties)
        formatted_functions = self.formatter.format_functions(func_blocks)

        return f"""module {module_name}_asserts {formatted_params} ({formatted_ports});

    {inner_vars}

    {formatted_functions}

    {formatted_assertions}

    {formatted_properties}

endmodule"""