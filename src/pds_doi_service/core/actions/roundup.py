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

Contains functions for sending email notifications for recently-updated DOIs.
"""
import json
import logging
import os
from datetime import date
from datetime import datetime
from datetime import timedelta
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict
from typing import List

import jinja2
from pds_doi_service.core.db.doi_database import DOIDataBase
from pds_doi_service.core.entities.doi import DoiRecord
from pds_doi_service.core.util.emailer import Emailer as PDSEmailer
from pkg_resources import resource_filename


def get_start_of_local_week() -> datetime:
    """Return the start of the local-timezones week as a tz-aware datetime"""
    today = datetime.now().date()
    start_of_today = datetime(today.year, today.month, today.day)
    return start_of_today.astimezone() - timedelta(days=today.weekday())


def fetch_dois_modified_between(begin: datetime, end: datetime, database: DOIDataBase) -> List[DoiRecord]:
    doi_records = database.select_latest_records({})
    return [r for r in doi_records if begin <= r.date_added < end or begin <= r.date_updated < end]


def get_email_content_template(template_filename: str = "email_weekly_roundup.jinja2"):
    template_filepath = resource_filename(__name__, os.path.join("templates", template_filename))
    logging.info(f"Using template {template_filepath}")
    with open(template_filepath, "r") as infile:
        template = jinja2.Template(infile.read())
    return template


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


def prepare_email_html_content(first_date: date, last_date: date, modified_doi_records: List[DoiRecord]) -> str:
    template = get_email_content_template()
    template_dict = {
        "first_date": first_date,
        "last_date": last_date,
        "doi_records": [prepare_doi_record_for_template(r) for r in modified_doi_records],
    }

    full_content = template.render(template_dict)
    logging.info(full_content)
    return full_content


def attach_json_data(filename: str, doi_records: List[DoiRecord], msg: MIMEMultipart) -> None:
    data = json.dumps([r.to_json_dict() for r in doi_records])
    part = MIMEText(data, "plain", "utf-8")
    part.set_charset("utf-8")
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f"attachment; filename={filename}")
    msg.attach(part)


def prepare_email_message(
    sender_email: str, receiver_email: str, first_date: date, last_date: date, modified_doi_records: List[DoiRecord]
) -> MIMEMultipart:
    email_subject = f"DOI WEEKLY ROUNDUP: {first_date} through {last_date}"

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["Subject"] = email_subject
    msg["To"] = receiver_email

    email_content = prepare_email_html_content(first_date, last_date, modified_doi_records)
    msg.attach(MIMEText(email_content, "html"))
    attachment_filename = f"updated_dois_{first_date.isoformat()}_{last_date.isoformat()}.json"
    attach_json_data(attachment_filename, modified_doi_records, msg)

    return msg


def run(database: DOIDataBase, sender_email: str, receiver_email: str) -> None:
    """
    Send an email consisting of a summary of all DOIs updated in the previous week (i.e. between the previous Sunday
    and the Monday before that, inclusive), with a JSON attachment for those DoiRecords.
    """
    target_week_begin = get_start_of_local_week() - timedelta(days=7)
    target_week_end = target_week_begin + timedelta(days=7, microseconds=-1)
    last_date_of_week = (target_week_end - timedelta(microseconds=1)).date()

    modified_doi_records = fetch_dois_modified_between(target_week_begin, target_week_end, database)

    msg = prepare_email_message(
        sender_email, receiver_email, target_week_begin.date(), last_date_of_week, modified_doi_records
    )

    emailer = PDSEmailer()
    emailer.send_message(msg)
