👩‍💻 Development
=================

Quick start
-----------


Get the code, work on a new branch

    git clone https://github.com/NASA-PDS/pds-doi-service.git
    git checkout -b "#<issue number>"


Install virtual env, use python 3.6.

    pip install virtualenv
    python -m venv venv
    source venv/bin/activate


Deploy dependancies:

    pip install -r requirements.txt

or

    pip intall -e .


At this point, we will have the command line tool available as explained in usage.


Testing
-------

The code base finally includes unit and integration tests. Once you've built
out, you can run the unit tests:

    pip install pytest
    pytest

You can run the integration tests with:

    behave


Making Releases
---------------

The release is done on github and pypi.

This is implemented through the CI/CD framework using github action on the master branch.

To trigger a new release (here 1.2.0) the steps are:

1. update the version number in:

    pds-doi-core/__init__.py

2. Create and push a new tag:

    git tag 1.2.0
    git push --tags

3. check that the CI/CD process completed successfully: https://github.com/NASA-PDS/pds-doi-service/actions

4. check that the new release is available.

   - on github: https://github.com/NASA-PDS/pds-doi-service/releases/
   - on pypi: https://pypi.org/project/pds-doi-core/




Contribute
----------

Fork the code from : https://github.com/NASA-PDS/pds-doi-service

Create a pull request when done.

.. _Actions: https://github.com/features/actions
.. _website: https://nasa-pds.github.io/pds-deep-archive/
