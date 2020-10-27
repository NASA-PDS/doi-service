import setuptools
import re

PACKAGE = "pds_doi_service"

with open("README.md", "r") as fh:
    long_description = fh.read()

with open(f"./{PACKAGE}/__init__.py") as fi:
    result = re.search(r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]', fi.read())
version = result.group(1)

with open('requirements.txt', 'r') as f:
    pip_requirements = f.readlines()

with open('requirements_dev.txt', 'r') as f:
    pip_dev_requirements = f.readlines()


setuptools.setup(
    name=PACKAGE, # Replace with your own username
    version=version,
    license="apache-2.0",
    author="pds ",
    author_email="pds_operator@jpl.nasa.gov",
    description="short description of my pds module, less than 100-120 characters",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/NASA-PDS/pds-template-python",
    download_url = "https://github.com/NASA-PDS/pds-template-python/releases/download/....",
    packages=setuptools.find_packages(),
    package_data={'': ['pds_doi_service/api/swagger/swagger.yaml']},
    include_package_data=True,
    keywords=['pds', 'doi', 'osti', 'dataCite'],

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',  # pds_doi_service.core package requires Dataclasses
    install_requires=pip_requirements,
    # TO DO if this is th proper wy to handle dev/test dependencies in the CI/CD pipeline
    #extras_require={
    #    'test': pip_dev_requirements
    #},
    scripts=[],
    entry_points={
        'console_scripts': ['pds-doi-start-dev=pds_doi_core.web_api.service:main',
                            'pds-doi-cmd=pds_doi_core.cmd.pds_doi_cmd:main',
                            'pds_doi_api=pds_doi_service.api.__main__:main'],
    },
    data_files=[('pds_doi_service',
                     ['config/conf.ini.default']
                     )
                ]


)
