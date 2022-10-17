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

from pds_doi_service.core.actions.roundup.metadata import RoundupMetadata
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


def get_previous_week_metadata(database: DOIDataBase) -> RoundupMetadata:
    target_week_begin = get_start_of_local_week() - timedelta(days=7)
    target_week_end = target_week_begin + timedelta(days=7, microseconds=-1)
    last_date_of_week = (target_week_end - timedelta(microseconds=1)).date()

    modified_doi_records = fetch_dois_modified_between(target_week_begin, target_week_end, database)

    metadata = RoundupMetadata(
        first_date=target_week_begin.date(), last_date=last_date_of_week, modified_doi_records=modified_doi_records
    )

    return metadata
