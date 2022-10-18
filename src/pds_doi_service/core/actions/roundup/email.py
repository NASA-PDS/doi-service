#
#  Copyright 2022, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
"""
======
email.py
======

Contains functions for sending recently-updated DOI metadata as an email.
"""
import json
import logging
import os
from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

import jinja2
from pds_doi_service.core.actions.roundup.enumerate import get_previous_week_metadata
from pds_doi_service.core.actions.roundup.metadata import RoundupMetadata
from pds_doi_service.core.actions.roundup.output import prepare_doi_record_for_email
from pds_doi_service.core.db.doi_database import DOIDataBase
from pds_doi_service.core.entities.doi import DoiRecord
from pds_doi_service.core.util.emailer import Emailer as PDSEmailer
from pkg_resources import resource_filename


def get_email_content_template(template_filename: str = "email_weekly_roundup.jinja2") -> jinja2.Template:
    template_filepath = resource_filename(__name__, os.path.join("../templates", template_filename))
    logging.info(f"Using template {template_filepath}")
    with open(template_filepath, "r") as infile:
        template = jinja2.Template(infile.read())
    return template


def prepare_email_html_content(metadata: RoundupMetadata) -> str:
    template = get_email_content_template()
    template_dict = {
        "first_date": metadata.first_date,
        "last_date": metadata.last_date,
        "doi_records": [prepare_doi_record_for_email(r) for r in metadata.modified_doi_records],
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


def prepare_email_message(sender_email: str, receiver_email: str, metadata: RoundupMetadata) -> MIMEMultipart:
    email_subject = f"DOI WEEKLY ROUNDUP: {metadata.first_date} through {metadata.last_date}"

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["Subject"] = email_subject
    msg["To"] = receiver_email

    email_content = prepare_email_html_content(metadata)
    msg.attach(MIMEText(email_content, "html"))
    attachment_filename = f"updated_dois_{metadata.first_date.isoformat()}_{metadata.last_date.isoformat()}.json"
    attach_json_data(attachment_filename, metadata.modified_doi_records, msg)

    return msg


def run(database: DOIDataBase, sender_email: str, receiver_email: str) -> None:
    """
    Send an email consisting of a summary of all DOIs updated in the previous week (i.e. between the previous Sunday
    and the Monday before that, inclusive), with a JSON attachment for those DoiRecords.
    """
    metadata = get_previous_week_metadata(database)

    msg = prepare_email_message(sender_email, receiver_email, metadata)

    emailer = PDSEmailer()
    emailer.send_message(msg)
