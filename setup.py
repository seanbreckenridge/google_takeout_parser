from pathlib import Path
from setuptools import setup, find_packages

long_description = Path("README.md").read_text()
reqs = Path("requirements.txt").read_text().strip().splitlines()

pkg = "google_takeout_parser"
setup(
    name=pkg,
    version="0.1.2",
    url="https://github.com/seanbreckenridge/google_takeout_parser",
    author="Sean Breckenridge",
    author_email="seanbrecke@gmail.com",
    description=(
        """Parses data out of your Google Takeout (History, Activity, Youtube, Locations, etc...)"""
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    packages=find_packages(
        include=["google_takeout_parser", "google_takeout_parser.parse_html"]
    ),
    install_requires=reqs,
    package_data={pkg: ["py.typed"]},
    zip_safe=False,
    keywords="google data parsing",
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "google_takeout_parser = google_takeout_parser.__main__:main"
        ]
    },
    extras_require={
        "testing": [
            "pytest",
            "mypy",
            "flake8",
        ],
        ':python_version<"3.7"': [
            "typing_extensions",
        ],
    },
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
