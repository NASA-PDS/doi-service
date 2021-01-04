from dataclasses import dataclass
from enum import Enum
from datetime import datetime



class productTypeEnum(Enum):
    Collection = 0
    Bundle = 1


class doiStatus(Enum):
    Reserved_not_submitted = 'reserved_not_submitted'  # reserved DOI in local database, not published to OSTI, not used in production
    Reserved = 'reserved'                              # reserved DOI submitted to OSTI (OSTI did not published it), incomplete metadata
    Draft = 'draft'                                    # DOI metadata being completed by the Discipline Node, in local database, not published to OSTI
    Review = 'review'                                  # DOI metadata completed by the Discipline Node, ready for review by Engineeting Node
    Pending = 'pending'                                # DOI metadata validated by Engineering Node, submitted to OSTI but not validated yet
    Registered = 'registered'                          # DOI metadata published by OSTI

@dataclass
class Doi:
    title: str
    publication_date: datetime
    product_type: productTypeEnum
    product_type_specific: str
    related_identifier: str
    authors: list = None
    keywords: list = None
    editors: list = None
    description: str = None
    id: str = None
    doi: str = None
    site_url: str = None
    publisher: str = None
    contributor: str = None
    status: str = None
    previous_status: str = None
    message: str = None
    date_record_added: datetime = None
    date_record_updated: datetime = None



