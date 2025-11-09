from pathlib import Path
from setuptools import setup, find_packages

# ------------------------------------------------
# Package Metadata
# ------------------------------------------------
PACKAGE_NAME = "queuectl"
VERSION = "1.0.0"
DESCRIPTION = "QueueCTL — CLI-based background job queue system with workers, retries, DLQ, and web dashboard."
LICENSE = "MIT"

# ------------------------------------------------
# Long Description (README fallback safe)
# ------------------------------------------------
readme_path = Path(__file__).parent / "README.md"
try:
    LONG_DESCRIPTION = readme_path.read_text(encoding="utf-8")
except FileNotFoundError:
    LONG_DESCRIPTION = DESCRIPTION

# ------------------------------------------------
# Setup Definition
# ------------------------------------------------
setup(
    name=PACKAGE_NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    license=LICENSE,
    packages=find_packages(include=["core*", "cli*", "web*"]),
    py_modules=["main"],
    include_package_data=True,
    install_requires=[
        "typer>=0.9.0",
        "flask>=3.0.0",
        "python-dateutil>=2.8.2",
    ],
    entry_points={
        "console_scripts": [
            "queuectl=main:app",
        ],
    },
    python_requires=">=3.9",
)
