#!/usr/bin/env python3
import os, setuptools

setup_path = os.path.dirname(__file__)

with open(os.path.join(setup_path, "README.md")) as readme:
    long_description = readme.read()

setuptools.setup(
    name="scielo-kernel",
    version="0.1rc14",
    author="SciELO Dev Team",
    author_email="scielo-dev@googlegroups.com",
    description="Kernel é o componente central da nova arquitetura de sistemas "
    "de informação da Metodologia SciELO. É responsável pela gestão, "
    "preservação e desempenha o papel de fonte autoritativa dos dados de uma "
    "coleção de periódicos científicos.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="2-clause BSD",
    packages=setuptools.find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests", "docs"]
    ),
    include_package_data=False,
    python_requires=">=3.7",
    install_requires=[
        "lxml",
        "requests",
        "pymongo",
        "pyramid",
        "cornice",
        "cornice_swagger",
        "colander",
        "python-slugify",
        "scielo-clea>=0.3.0",
        "waitress",
        "prometheus_client",
        "sentry-sdk",
    ],
    test_suite="tests",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Other Environment",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3 :: Only",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "paste.app_factory": ["main = documentstore.restfulapi:main"],
        "console_scripts": ["kernelctl = documentstore.kernelctl:main"],
    },
)
