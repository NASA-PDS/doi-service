"""
========
DataCite
========

This package contains the DataCite-specific implementations for the abstract
classes of the outputs package.
"""
from .datacite_record import DOIDataCiteRecord  # noqa: F401
from .datacite_validator import DOIDataCiteValidator  # noqa: F401
from .datacite_web_client import DOIDataCiteWebClient  # noqa: F401
from .datacite_web_parser import DOIDataCiteWebParser  # noqa: F401
