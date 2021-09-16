#
#  Copyright 2020–21, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
"""
==========
service.py
==========

Contains the factory class for providing the appropriate objects based on the
configured DOI service provider (OSTI, DataCite, etc...)
"""
from pds_doi_service.core.outputs.datacite import DOIDataCiteRecord
from pds_doi_service.core.outputs.datacite import DOIDataCiteValidator
from pds_doi_service.core.outputs.datacite import DOIDataCiteWebClient
from pds_doi_service.core.outputs.datacite import DOIDataCiteWebParser
from pds_doi_service.core.outputs.osti import DOIOstiRecord
from pds_doi_service.core.outputs.osti import DOIOstiValidator
from pds_doi_service.core.outputs.osti import DOIOstiWebClient
from pds_doi_service.core.outputs.osti import DOIOstiWebParser
from pds_doi_service.core.util.config_parser import DOIConfigUtil
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger(__name__)


SERVICE_TYPE_OSTI = "osti"
SERVICE_TYPE_DATACITE = "datacite"
"""Constants for the available service types supported by this module"""

VALID_SERVICE_TYPES = [SERVICE_TYPE_OSTI, SERVICE_TYPE_DATACITE]
"""The list of expected service types"""


class DOIServiceFactory:
    """
    Class responsible for instantiating and returning the appropriate objects
    based on the currently configured DOI service provider.

    Users of this class select the type of object they need (validator, parser,
    etc.) via method call and this class determines the correct object type to
    return. Since all service-specific classes adhere to parent interfaces, the
    objects returned should be interchangeable with one another.

    All methods defined by this class are static, so no instantiation of
    DOIServiceFactory should be necessary.

    """

    _DOI_RECORD_MAP = {SERVICE_TYPE_OSTI: DOIOstiRecord, SERVICE_TYPE_DATACITE: DOIDataCiteRecord}
    """The available DOIRecord subclasses mapped to the corresponding service types"""

    _SERVICE_VALIDATOR_MAP = {SERVICE_TYPE_OSTI: DOIOstiValidator, SERVICE_TYPE_DATACITE: DOIDataCiteValidator}
    """The available DOIValidator subclasses mapped to the corresponding service types"""

    _WEB_CLIENT_MAP = {SERVICE_TYPE_OSTI: DOIOstiWebClient, SERVICE_TYPE_DATACITE: DOIDataCiteWebClient}
    """The available DOIWebClient subclasses mapped to the corresponding service types"""

    _WEB_PARSER_MAP = {SERVICE_TYPE_OSTI: DOIOstiWebParser, SERVICE_TYPE_DATACITE: DOIDataCiteWebParser}
    """The available DOIWebParser subclasses mapped to the corresponding service types"""

    _config = DOIConfigUtil().get_config()

    @staticmethod
    def _check_service_type(service_type):
        """
        Checks if the provided service type is among the expected values.

        Parameters
        ----------
        service_type : str
            Service type to check. Is automatically converted to lowercase
            to provide a case-insensitive check.

        Raises
        ------
        ValueError
            If the service type is not among the valid types recognized by this
            class (or if no type is specified by the INI config at all).

        """
        if service_type.lower() not in VALID_SERVICE_TYPES:
            raise ValueError(
                f'Unsupported service type "{service_type}" provided.\n'
                f"Service type should be assigned to the SERVICE.provider field of "
                f"the INI config with one of the following values: {VALID_SERVICE_TYPES}"
            )

    @staticmethod
    def get_service_type():
        """
        Returns the configured service type as defined within the INI config.

        Returns
        -------
        service_type : str
            The service type to be used. This value is converted to lowercase
            by this method before it is returned.

        """
        service_type = DOIServiceFactory._config.get("SERVICE", "provider", fallback="unassigned")

        return service_type.lower()

    @staticmethod
    def get_doi_record_service(service_type=None):
        """
        Returns the appropriate DOIRecord subclass for the current service type.

        Parameters
        ----------
        service_type : str, optional
            The service type to return a DOIRecord subclass for. Defaults to
            the SERVICE.provider value of the INI config.

        Returns
        -------
        DOIRecord
            A subclass instance of DOIRecord selected based on the configured
            DOI service type.

        """
        if not service_type:
            service_type = DOIServiceFactory.get_service_type()

        DOIServiceFactory._check_service_type(service_type)

        doi_record_class = DOIServiceFactory._DOI_RECORD_MAP[service_type]
        logger.debug("Returning instance of %s for service type %s", doi_record_class.__name__, service_type)

        return doi_record_class()

    @staticmethod
    def get_validator_service(service_type=None):
        """
        Returns the appropriate DOIValidator subclass for the current service type.

        Parameters
        ----------
        service_type : str, optional
            The service type to return a DOIValidator subclass for. Defaults to
            the SERVICE.provider value of the INI config.

        Returns
        -------
        DOIValidator
            A subclass instance of DOIValidator selected based on the configured
            DOI service type.

        """
        if not service_type:
            service_type = DOIServiceFactory.get_service_type()

        DOIServiceFactory._check_service_type(service_type)

        doi_validator_class = DOIServiceFactory._SERVICE_VALIDATOR_MAP[service_type]
        logger.debug("Returning instance of %s for service type %s", doi_validator_class.__name__, service_type)

        return doi_validator_class()

    @staticmethod
    def get_web_client_service(service_type=None):
        """
        Returns the appropriate DOIWebClient subclass for the current service type.

        Parameters
        ----------
        service_type : str, optional
            The service type to return a DOIWebClient subclass for. Defaults to
            the SERVICE.provider value of the INI config.

        Returns
        -------
        DOIWebClient
            A subclass instance of DOIWebClient selected based on the configured
            DOI service type.

        """
        if not service_type:
            service_type = DOIServiceFactory.get_service_type()

        DOIServiceFactory._check_service_type(service_type)

        web_client_class = DOIServiceFactory._WEB_CLIENT_MAP[service_type]
        logger.debug("Returning instance of %s for service type %s", web_client_class.__name__, service_type)

        return web_client_class()

    @staticmethod
    def get_web_parser_service(service_type=None):
        """
        Returns the appropriate DOIWebParser subclass for the current service type.

        Parameters
        ----------
        service_type : str, optional
            The service type to return a DOIWebParser subclass for. Defaults to
            the SERVICE.provider value of the INI config.

        Returns
        -------
        DOIWebParser
            A subclass instance of DOIWebParser selected based on the configured
            DOI service type.

        """
        if not service_type:
            service_type = DOIServiceFactory.get_service_type()

        DOIServiceFactory._check_service_type(service_type)

        web_parser_class = DOIServiceFactory._WEB_PARSER_MAP[service_type]
        logger.debug("Returning instance of %s for service type %s", web_parser_class.__name__, service_type)

        return web_parser_class()
