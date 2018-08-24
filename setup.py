#!/usr/bin/env python3
import os, setuptools

setup_path = os.path.dirname(__file__)

with open(os.path.join(setup_path, "README.md")) as readme:
    long_description = readme.read()

setuptools.setup(
    name="multiverse",
    version="0.1",
    author="Gustavo Fonseca",
    author_email="gustavo@gfonseca.net",
    description="Multiverse é uma implementação experimental de um pacote "
    "Python que busca tratar da persistência de documentos XML "
    "em múltiplas versões.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="2-clause BSD",
    packages=setuptools.find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests"]
    ),
    include_package_data=False,
    python_requires=">=3.6",
    install_requires=["lxml", "requests", "pymongo"],
    test_suite="tests",
    classifiers=(
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Other Environment",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3 :: Only",
        "Operating System :: OS Independent",
    ),
)
