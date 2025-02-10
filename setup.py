from setuptools import setup, find_packages
from msgraph_toolkit.core.__version__ import __version__
from pathlib import Path

with Path("requirements.txt").open() as f:
    install_requires = f.read().splitlines()

setup(
    name="msgraph-toolkit",
    version=__version__,
    author="Gustavo Inostroza",
    author_email="gusinostrozar@gmail.com",
    description="A package for managing Microsoft Graph operations",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Inostroza7/msgraph-toolkit",
    packages=find_packages(),
    install_requires=install_requires,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)