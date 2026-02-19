"""
setup.py
--------
Package configuration for Reqfix.
This is what PyPI reads to display your package page.
"""

from setuptools import setup, find_packages

# Read the README for the long description on PyPI page
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(

    name="reqfix",
    version="0.1.0",
    author="Sakshi Rajesh Kamble",                      
    author_email="sakshikamble512@gmail.com",               
    maintainer="Sakshi Rajesh Kamble",                    
    maintainer_email="sakshikamble512@gmail.com",              

    # -------------------------------------------------------------------------
    # WHAT YOUR PACKAGE IS 
    # -------------------------------------------------------------------------
    description="Fix your Python dependency conflicts automatically",
    long_description=long_description,
    long_description_content_type="text/markdown",  # renders README on PyPI
    license="MIT",


    # -------------------------------------------------------------------------
    # DISCOVERABILITY — how people find your package on PyPI search
    # -------------------------------------------------------------------------
    keywords=[
        "pip", "dependencies", "requirements", "conflict",
        "resolver", "packaging", "devtools", "cli"
    ],
    classifiers=[
        # Who is this for?
        "Intended Audience :: Developers",

        # What kind of project?
        "Topic :: Software Development :: Build Tools",
        "Topic :: System :: Systems Administration",

        # License
        "License :: OSI Approved :: MIT License",

        # Python versions supported
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",

        # Maturity level
        "Development Status :: 3 - Alpha",

        # OS support
        "Operating System :: OS Independent",
    ],

    # -------------------------------------------------------------------------
    # TECHNICAL CONFIG
    # -------------------------------------------------------------------------
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "packaging>=23.0",
        "rich>=13.0.0",
        "click>=8.1.0",
    ],
    entry_points={
        "console_scripts": [
            "reqfix=cli.main:cli",
        ],
    },
)