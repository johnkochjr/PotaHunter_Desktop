"""
Setup script for POTA Hunter
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="potahunter",
    version="0.1.0",
    author="POTA Hunter Team",
    description="A Parks on the Air spotting and logging application",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/PotaHunter",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Communications :: Ham Radio",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "PySide6>=6.6.0",
        "requests>=2.31.0",
        "adif-io>=0.2.0",
        "maidenhead>=1.7.0",
        "pandas>=2.1.0",
    ],
    entry_points={
        "console_scripts": [
            "potahunter=potahunter.main:main",
        ],
    },
)
