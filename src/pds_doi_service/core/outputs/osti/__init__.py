"""
====
OSTI
====

This package contains the OSTI-specific implementations for the abstract
classes of the outputs package.
"""

from .osti_record import DOIOstiRecord
from .osti_web_client import DOIOstiWebClient
from .osti_web_parser import DOIOstiJsonWebParser, DOIOstiXmlWebParser
