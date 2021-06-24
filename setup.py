# -*- coding: utf-8 -*-

import setuptools, versioneer

# Package Metadata
# ----------------
#
# Normally we'd have a `pds` namespace package with `doi_service` inside of it, but when I try to do that
# I get errors like:
#
#    connexion.exceptions.ResolverError: <ResolverError: Cannot resolve operationId
#    "pds_doi_service.api.controllers.dois_controller.get_dois"!
#
# So for now, for this package, we'll keep the single top-level module `pds_doi_service` with no
# namespace package support.


name               = 'pds-doi-service'
description        = 'A short description, about 100–120 characters, suitable for search summaries'
keywords           = ['pds', 'doi', 'osti', 'dataCite']
zip_safe           = False
python_requires    = '>=3.7'
# FIXME: We cannot use namespace packages thanks to ResolverErrors from Flask connexion
# namespace_packages = ['pds']
extras_require     = {}
test_suite         = 'pds_doi_service.test.suite'
entry_points       = {
    'console_scripts': [
        'pds-doi-start-dev=pds_doi_core.web_api.service:main',
        'pds-doi-cmd=pds.doi_service.core.cmd.pds_doi_cmd:main',
        'pds-doi-api=pds.doi_service.api.__main__:main'
    ]
}
package_data = {
    'pds.doi_service': [
        'api/swagger/swagger.yaml',
        'core/util/conf.ini.default',
        'core/actions/email_template_header.mustache',
        'core/actions/email_template_body.txt',
        'core/outputs/DOI_template_20200407-mustache.xml',
        'core/outputs/DOI_IAD2_reserved_template_20200205-mustache.xml',
        'core/input/IAD3_scheematron.sch',
        'core/util/iad_schema.xsd'
    ]
}
classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Web Environment',
    'Framework :: Flask',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: Apache Software License',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 3',
    'Topic :: Scientific/Engineering',
]

# Below here, you shouldn't have to change anything:


with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt', 'r') as f:
    pip_requirements = f.readlines()

with open('requirements_dev.txt', 'r') as f:
    pip_dev_requirements = f.readlines()


setuptools.setup(
    name=name,
    version=versioneer.get_version(),
    license="apache-2.0",
    author="PDS",
    author_email="pds_operator@jpl.nasa.gov",
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/NASA-PDS/' + name,
    download_url='https://github.com/NASA-PDS/' + name + '/releases/',
    packages=setuptools.find_packages('src'),
    include_package_data=True,
    zip_safe=zip_safe,
    # namespace_packages=namespace_packages,  # FIXME: ResolverErrors from Flask connexion if we try to use namespace pkgs
    package_dir={'': 'src'},
    package_data=package_data,
    keywords=keywords,
    classifiers=classifiers,
    python_requires=python_requires,
    install_requires=pip_requirements,
    entry_points=entry_points,
    extras_require=extras_require,
    test_suite=test_suite,
    cmdclass=versioneer.get_cmdclass()
)
