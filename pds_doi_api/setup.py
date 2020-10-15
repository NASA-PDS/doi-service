# coding: utf-8

import sys
from setuptools import setup, find_packages

NAME = "pds_doi_api"
VERSION = "0.1.0"
# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = ["connexion"]

setup(
    name=NAME,
    version=VERSION,
    description="Planetary Data System DOI Service API",
    author_email="",
    url="",
    keywords=["Swagger", "Planetary Data System DOI Service API"],
    install_requires=REQUIRES,
    packages=find_packages(),
    package_data={'': ['swagger/swagger.yaml']},
    include_package_data=True,
    entry_points={
        'console_scripts': ['pds_doi_api=pds_doi_api.__main__:main']},
    long_description="""\
    PDS API for managing DOI registration with OSTI service.
    """
)
