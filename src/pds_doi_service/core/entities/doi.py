#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#

"""
======
doi.py
======

Contains the dataclass and enumeration definitions for Doi objects.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, unique


@unique
class ProductType(str, Enum):
    """Enumerates the types of products that can be assigned a DOI."""
    Collection = 'Collection'
    Bundle = 'Bundle'
    Text = 'Text'
    Dataset = 'Dataset'


@unique
class DoiStatus(str, Enum):
    """
    Enumerates the stages of the DOI workflow.

    The workflow stages consist of:
        Error -
            An error has occurred with the DOI submission.
        Unknown -
            Default starting state for DOI transactions.
        Reserve_not_submitted -
            DOI reserve request in local database, but not published/released.
            Used for testing of the reserve action.
        Reserved -
            DOI reserve request submitted, but not yet published/released.
        Draft -
            DOI request stored as draft in local database to allow additional
            metadata to be assigned before review request is made.
        Review -
            DOI request has all metadata assigned by the Discipline Node and is
            ready for review by the Engineering Node.
        Pending -
            DOI request has been reviewed by Engineering Node and released
            (submitted to DOI service provider), but not yet published.
        Registered -
            DOI request has been registered with the service provider.
            Note that for DataCite entries, registered must still be pushed
            to "Findable" to be considered published.
        Findable -
            DOI request has been marked as "findable" by DataCite, meaning it
            is publicly available.
        Deactivated -
            The submitted DOI has been deactivated (deleted).

    """
    Error = 'error'
    Unknown = 'unknown'
    Reserved_not_submitted = 'reserved_not_submitted'
    Reserved = 'reserved'
    Draft = 'draft'
    Review = 'review'
    Pending = 'pending'
    Registered = 'registered'
    Findable = 'findable'
    Deactivated = 'deactivated'


@dataclass
class Doi:
    """The dataclass definition for a Doi object."""
    title: str
    publication_date: datetime
    product_type: ProductType
    product_type_specific: str
    related_identifier: str
    authors: list = None
    keywords: set = field(default_factory=set)
    editors: list = None
    description: str = None
    id: str = None
    doi: str = None
    site_url: str = None
    publisher: str = None
    contributor: str = None
    status: DoiStatus = None
    previous_status: DoiStatus = None
    message: str = None
    date_record_added: datetime = None
    date_record_updated: datetime = None
