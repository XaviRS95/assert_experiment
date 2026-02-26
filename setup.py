from setuptools import setup, find_packages

setup(
    name="sv-experiment-project",
    version="0.1.0",
    description="SystemVerilog code generation and testing experiments",

    # Automatically find all packages (experiments, utils, prompts)
    packages=find_packages(),

    # Minimum Python version
    python_requires=">=3.8",

    # Add your external dependencies here
    install_requires=[
        "requests==2.32.5"
    ]
)