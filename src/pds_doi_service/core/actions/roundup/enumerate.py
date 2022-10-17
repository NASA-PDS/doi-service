#
#  Copyright 2022, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
"""
======
roundup.py
======

Contains functions for enumerating recently-updated DOIs.
"""
from datetime import datetime
from datetime import timedelta
from typing import Dict
from typing import List

from pds_doi_service.core.db.doi_database import DOIDataBase
from pds_doi_service.core.entities.doi import DoiRecord


def get_start_of_local_week() -> datetime:
    """Return the start of the local-timezones week as a tz-aware datetime"""
    today = datetime.now().date()
    start_of_today = datetime(today.year, today.month, today.day)
    return start_of_today.astimezone() - timedelta(days=today.weekday())


def fetch_dois_modified_between(begin: datetime, end: datetime, database: DOIDataBase) -> List[DoiRecord]:
    doi_records = database.select_latest_records({})
    return [r for r in doi_records if begin <= r.date_added < end or begin <= r.date_updated < end]


def prepare_doi_record_for_template(record: DoiRecord) -> Dict[str, object]:
    """Map a DoiRecord to the set of information required for rendering it in the template"""
    update_type = "submitted" if record.date_added == record.date_updated else "updated"
    prepared_record = {
        "datacite_id": record.doi,
        "pds_id": record.identifier,
        "update_type": update_type,
        "last_modified": record.date_updated,
        "status": record.status.title(),
    }

    return prepared_record
