#!/usr/bin/env python3
"""Setup script for FRACKTAL (Fractal Recursive Symbolic Ontology Engine)"""
from setuptools import setup, find_packages
import os

def read_readme():
    """Read README.md file."""
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

def read_requirements():
    """Read requirements.txt file."""
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="fracktal",
    version="1.0.0",
    author="Gregory Betti",
    author_email="gorygrey@protonmail.com",
    description="Advanced semantic compression through recursive symbolic pattern recognition",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/Betti-Labs/FRACKTAL",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: System :: Archiving :: Compression",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "black>=23.7.0",
            "flake8>=6.0.0",
            "jupyter>=1.0.0",
            "ipywidgets>=8.0.7",
        ],
        "viz": [
            "matplotlib>=3.7.2",
            "seaborn>=0.12.2",
            "plotly>=5.15.0",
            "networkx>=3.1",
            "graphviz>=0.20.1",
        ],
        "full": [
            "pytest>=7.4.0",
            "black>=23.7.0",
            "flake8>=6.0.0",
            "jupyter>=1.0.0",
            "ipywidgets>=8.0.7",
            "matplotlib>=3.7.2",
            "seaborn>=0.12.2",
            "plotly>=5.15.0",
            "networkx>=3.1",
            "graphviz>=0.20.1",
            "tqdm>=4.65.0",
            "colorama>=0.4.6",
            "rich>=13.4.2",
        ],
    },
    entry_points={
        "console_scripts": [
            "fracktal=fracktal.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "fracktal": [
            "*.md",
            "docs/*.md",
            "examples/*.py",
            "tests/*.py",
        ],
    },
    keywords=[
        "compression",
        "semantic",
        "symbolic",
        "ontology",
        "fractal",
        "recursive",
        "pattern-recognition",
        "data-compression",
        "information-theory",
        "artificial-intelligence",
        "machine-learning",
        "knowledge-representation",
    ],
    project_urls={
        "Bug Reports": "https://github.com/Betti-Labs/FRACKTAL/issues",
        "Source": "https://github.com/Betti-Labs/FRACKTAL",
        "Documentation": "https://github.com/Betti-Labs/FRACKTAL/tree/main/docs",
        "Research Paper": "https://github.com/Betti-Labs/FRACKTAL/blob/main/FRSOE_Paper_BettiLabs.md",
    },
) 