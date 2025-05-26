"""
Setup script for the Google Maps Business Scraper.
"""

from setuptools import setup, find_packages

setup(
    name="google_maps_scraper",
    version="1.0.0",
    description="A robust Google Maps business scraper for extracting business names and phone numbers in Sri Lanka",
    author="Manus AI",
    packages=find_packages(),
    install_requires=[
        "playwright>=1.40.0",
        "pyyaml>=6.0",
        "pandas>=2.0.0",
        "httpx>=0.24.0",
    ],
    entry_points={
        "console_scripts": [
            "google-maps-scraper=google_maps_scraper.src.main:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
