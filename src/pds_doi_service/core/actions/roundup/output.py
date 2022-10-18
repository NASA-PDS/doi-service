from typing import Dict

from pds_doi_service.core.entities.doi import DoiRecord


def prepare_doi_record_for_email(record: DoiRecord) -> Dict:
    """Map a DoiRecord to the set of information required for rendering it in output"""
    update_type = "submitted" if record.date_added == record.date_updated else "updated"
    prepared_record = {
        "datacite_id": record.doi,
        "pds_id": record.identifier,
        "title": record.title,
        "update_type": update_type,
        "last_modified": record.date_updated.date(),
        "status": record.status.title(),
    }

    return prepared_record


def prepare_doi_record_for_ads_sftp(record: DoiRecord, json_compatible: bool = False) -> Dict:
    """Map a DoiRecord to the set of information required for rendering it in output"""
    update_type = "submitted" if record.date_added == record.date_updated else "updated"
    prepared_record = {
        "datacite_id": record.doi,
        "pds_id": record.identifier,
        "title": record.title,
        "update_type": update_type,
        "last_modified": record.date_updated.isoformat(),
        "status": record.status.title(),
    }

    return prepared_record
