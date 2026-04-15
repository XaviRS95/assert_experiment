from .module_builder import ModuleBuilder


class FinalAssembler:
    """Coordinates the assembly of the final module"""

    def __init__(self):
        self.builder = ModuleBuilder()

    def assemble(self, module_info: dict, comb_results: dict, seq_results: dict) -> str:
        """Assemble all parts into final module"""

        return self.builder.build(
            module_name=module_info['module_name'],
            parameters=module_info['parameters'],
            ports=module_info['ports'],
            inner_vars=module_info['inner_vars'],
            immediate_assertions=comb_results['immediate_assertions'],
            sequential_properties=seq_results['sequential_properties']
        )