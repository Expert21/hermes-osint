from setuptools import setup, find_packages
import os

# Read the README file
readme_path = os.path.join(os.path.dirname(__file__), "README.md")
with open(readme_path, "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="hermes-osint",
    version="1.1.0",
    author="Expert21",
    author_email="your.email@example.com",
    description="Advanced OSINT Intelligence Gathering Tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Expert21/hermes-osint",
    
    # Include both packages and the modules
    packages=find_packages(),
    py_modules=["main", "hermes_cli"],
    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    
    python_requires=">=3.7",
    
    install_requires=[
        "requests",
        "beautifulsoup4",
        "colorama",
        "python-dotenv",
        "urllib3",
        "tqdm",
        "pyyaml",
        "dnspython",
        "validators",
        "reportlab",
    ],
    
    # Create the 'hermes' command using the CLI wrapper
    entry_points={
        "console_scripts": [
            "hermes=hermes_cli:cli",
        ],
    },
    
    include_package_data=True,
    package_data={
        "": ["config.yaml"],
    },
)
