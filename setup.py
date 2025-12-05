
from setuptools import setup, find_packages
import os

# Read the README file
readme_path = os.path.join(os.path.dirname(__file__), "README.md")
with open(readme_path, "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="Hermes",
    version="2.0.0",
    author="Isaiah Myles (Expert21)",
    author_email="isaiahmyles04@gmail.com",
    description="Universal OSINT Orchestration Platform - Integrate and automate best-in-class intelligence tools",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Expert21/hermes-osint",
    
    # Include both packages and the modules
    packages=find_packages(),
    py_modules=["main", "hermes_cli"],
    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Developers",
        "Topic :: Security",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Environment :: Console",
        "Operating System :: OS Independent",
    ],
    
    python_requires=">=3.10",
    
    install_requires=[
        # Core dependencies
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "aiohttp>=3.9.0",
        
        # CLI & Output
        "rich>=13.7.0",  # Enhanced CLI output
        "colorama>=0.4.6",
        "tqdm>=4.66.0",
        
        # Configuration & Data
        "pyyaml>=6.0.1",
        "python-dotenv>=1.0.0",
        
        # Security
        "cryptography>=41.0.0",
        
        # Network & Validation
        "urllib3>=2.1.0",
        "dnspython>=2.4.0",
        "validators>=0.22.0",
        
        # Docker Integration
        "docker>=7.0.0",
        
        # System
        "psutil>=5.9.0",
        
        # Reporting
        "reportlab>=4.0.0",
    ],
    
    # Create the 'hermes' command using the CLI wrapper
    entry_points={
        "console_scripts": [
            "hermes=hermes_cli:cli",
        ],
    },
    
    include_package_data=True,
)
