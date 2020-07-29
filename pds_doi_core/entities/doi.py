from dataclasses import dataclass
from enum import Enum
from datetime import datetime



class productTypeEnum(Enum):
    Collection = 0
    Bundle = 1

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



