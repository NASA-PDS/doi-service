from dataclasses import dataclass
from datetime import date
from typing import Callable
from typing import Dict
from typing import List

from pds_doi_service.core.entities.doi import DoiRecord


@dataclass
class RoundupMetadata:
    """Class for standardizing a collection of metadata for recently-updated doi records"""

    first_date: date
    last_date: date
    modified_doi_records: List[DoiRecord]

    def to_json(self, doi_record_mapper: Callable[[DoiRecord], Dict]):
        return {
            "first_date": self.first_date.isoformat(),
            "last_date": self.last_date.isoformat(),
            "modified_doi_records": [doi_record_mapper(r) for r in self.modified_doi_records],
        }
