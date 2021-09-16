#
#  Copyright 2020–21, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
"""
====================
service_validator.py
====================

Contains the base class for creating service-specific validator objects.
"""
from pds_doi_service.core.util.config_parser import DOIConfigUtil


class DOIServiceValidator:
    """
    Abstract base class for performing service-specific validation of output
    label formats. Validation is typically schema-based.
    """

    def __init__(self):
        self._config = DOIConfigUtil.get_config()

    def validate(self, label_contents):
        """
        Validates the provided output label contents against one or more
        schemas utilized by the ServiceValidator instance.

        Parameters
        ----------
        label_contents : str
            Contents of the output label file to validate.

        """
        raise NotImplementedError(
            f"Subclasses of {self.__class__.__name__} must provide an " f"implementation for validate()"
        )
