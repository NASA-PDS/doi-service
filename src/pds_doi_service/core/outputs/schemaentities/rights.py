from dataclasses import asdict
from dataclasses import dataclass
from typing import Dict
from typing import Optional
from typing import Type

from pds_doi_service.core.util.general_util import sanitize_json_string


@dataclass
class Rights:
    """
    Provides a dataclass for the Rights entities referred to in the DataCite Metadata Schema v4 attribute id 16.
    """

    text: Optional[str] = ""
    uri: Optional[str] = ""
    identifier: Optional[str] = ""
    identifier_scheme: Optional[str] = ""
    scheme_uri: Optional[str] = ""
    language: str = "en-US"

    @classmethod
    def get_label_mappings(cls) -> Dict[str, str]:
        """Implements a dict mapping class fieldname (eg 'text', 'uri', etc.) onto the attribute names used by the endpoint"""
        raise NotImplementedError

    @classmethod
    def fieldname_from_endpoint_attribute_name(cls, datacite_attribute_name: str) -> str:
        """Given an endpoint rights-management attribute name, return the corresponding Rights class field name"""
        try:
            return [k for k, v in cls.get_label_mappings().items() if v == datacite_attribute_name][0]
        except IndexError:
            raise ValueError(
                f"Could not resolve fieldname mapping from attribute name for attribute name {datacite_attribute_name} in class {cls.__name__}. Expected one of {cls.get_label_mappings().values()}"
            )

    @classmethod
    def endpoint_attribute_name_from_fieldname(cls, fieldname: str) -> str:
        """Given a Rights class field name, return the corresponding endpoint rights-management attribute name"""
        return cls.get_label_mappings()[fieldname]

    def to_endpoint_dict(self) -> Dict[str, str]:
        """Return this object in the appropriate form for submission to endpoint as dict"""
        output = {}
        for fieldname, value in asdict(self).items():
            if value != "":
                datacite_attribute_name = self.get_label_mappings()[fieldname]
                output[datacite_attribute_name] = sanitize_json_string(value)

        return output

    def convert(self, rights_subclass: Type):
        """
        Return a subclassed equivalent of this Rights object.
        This is necessary to allow instantiation of a Rights object prior to any knowledge of which endpoint will use it.
        """
        return rights_subclass(**asdict(self))

    @classmethod
    def from_endpoint_data(cls, data: Dict[str, str]):
        """Parse a Rights object from endpoint rights data"""
        output_kwargs = {}
        for datacite_attribute_name, value in data.items():
            rights_class_fieldname = cls.fieldname_from_endpoint_attribute_name(datacite_attribute_name)
            output_kwargs[rights_class_fieldname] = value
        return cls(**output_kwargs)


GOVERNMENT_WORKS_COPYRIGHT = Rights(
    text="This is a work of the U.S. Government and is not subject to copyright protection in the United States. "
    "Foreign copyrights may apply.",
    uri="https://www.usa.gov/government-works",
)

CC0_LICENSE = Rights(
    scheme_uri="https://spdx.org/licenses/CC0-1.0.html",
    identifier_scheme="SPDX",
    identifier="CC0-1.0",
    uri="http://creativecommons.org/publicdomain/zero/1.0/",
)
