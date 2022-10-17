from dataclasses import dataclass
from datetime import date
from typing import Dict
from typing import List

from pds_doi_service.core.entities.doi import DoiRecord


@dataclass
class RoundupMetadata:
    """Class for standardizing a collection of metadata for recently-updated doi records"""

    first_date: date
    last_date: date
    modified_doi_records: List[DoiRecord]

    def asdict(self):
        return {
            "first_date": self.first_date,
            "last_date": self.last_date,
            "modified_doi_records": [r.to_json_dict() for r in self.modified_doi_records],
        }
