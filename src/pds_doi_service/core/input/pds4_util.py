"""
==========
pds4_util.py
==========

Contains functions and classes for parsing PDS4 XML labels.
"""
import sys
from datetime import datetime
from datetime import timezone
from enum import Enum
from typing import Dict
from typing import List
from typing import Sequence
from typing import Union

from pds_doi_service.core.entities.doi import Doi
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.entities.doi import ProductType
from pds_doi_service.core.entities.exceptions import InputFormatException
from pds_doi_service.core.util.general_util import create_landing_page_url
from pds_doi_service.core.util.general_util import get_logger
from pds_doi_service.core.util.keyword_tokenizer import KeywordTokenizer

logger = get_logger(__name__)
logger.info(f": sys.getdefaultencoding: " f"{sys.getdefaultencoding()}")


class BestParserMethod(Enum):
    BY_COMMA = 1
    BY_SEMI_COLON = 2


class DOIPDS4LabelUtil:
    """
    Class used for parsing DOI metadata fields from a PDS4 XML label.

    The xpath_dict dictionary is central to the DOI service's ability to extract structured metadata
    from PDS4 XML labels, providing a mapping between internal field names and their corresponding locations
      in the XML document structure.
    """

    def __init__(self):
        """xpath_dict is a {dict} where each key is comprised of a [list] of values"""
        self.xpath_dict = {
            "lid": "/*/pds4:Identification_Area/pds4:logical_identifier",
            "vid": "/*/pds4:Identification_Area/pds4:version_id",
            "title": "/*/pds4:Identification_Area/pds4:title",
            "publication_year": "/*/pds4:Identification_Area/pds4:Citation_Information/pds4:publication_year",
            "modification_date": "/*/pds4:Identification_Area/pds4:Modification_History/pds4:Modification_Detail/pds4:modification_date",
            "description": "/*/pds4:Identification_Area/pds4:Citation_Information/pds4:description",
            "product_class": "/*/pds4:Identification_Area/pds4:product_class",
            "authors": "/*/pds4:Identification_Area/pds4:Citation_Information/pds4:author_list",
            "editors": "/*/pds4:Identification_Area/pds4:Citation_Information/pds4:editor_list",
            "investigation_area": "/*/pds4:Context_Area/pds4:Investigation_Area/pds4:name",
            "observing_system_component": "/*/pds4:Context_Area/pds4:Observing_System/pds4:Observing_System_Component/pds4:name",
            "target_identification": "/*/pds4:Context_Area/pds4:Target_Identification/pds4:name",
            "primary_result_summary": "/*/pds4:Context_Area/pds4:Primary_Result_Summary/*",
            "doi": "/*/pds4:Identification_Area/pds4:Citation_Information/pds4:doi",
            "list_authors": "/*/pds4:Identification_Area/pds4:Citation_Information/pds4:List_Author/*",
            "list_editors": "/*/pds4:Identification_Area/pds4:Citation_Information/pds4:List_Editor/*",
            "list_contributors": "/*/pds4:Identification_Area/pds4:Citation_Information/pds4:List_Contributor/*",
        }

    def build_xpath_dict(self, role_type: str, dict_type: str) -> dict:
        """
        Builds an XPath dictionary for a given role type and dictionary type.

        This method constructs an XPath dictionary that maps PDS4 XML elements to
        their corresponding fields in the DOI metadata. It supports three types of
        dictionaries:
        - xpath_dict: maps the overall List_Author, List_Editor, or List_Contributor class
        - xpath_dict_person_attributes: maps Person attributes (given_name, family_name, person_orcid)
        - xpath_dict_organization_attributes: maps Organization attributes (contributor_type, organization_name, organization_rorid)

        Parameters
        ----------
        role_type : str
            The type of contributor to extract. Must be one of: "Author", "Editor", or "Contributor".
        dict_type : str
            The type of dictionary to build. Must be one of: "xpath_dict", "xpath_dict_person_attributes", or "xpath_dict_organization_attributes".

        Returns
        -------
        dict
            A dictionary mapping PDS4 XML elements to their corresponding DOI metadata fields.

        Examples
        --------
        >>> pds4_util = DOIPDS4LabelUtil()
        >>> xpath_dict = pds4_util.build_xpath_dict("Author", "xpath_dict")
        >>> # Returns: {
        >>> # 'xpath_list_author_class': '/*/pds4:Identification_Area/pds4:Citation_Information/pds4:List_Author/*',
        >>> # 'xpath_list_authors_person_class': '/*/pds4:Identification_Area/pds4:Citation_Information/pds4:List_Author/pds4:Person/*',
        >>> # 'xpath_list_authors_organization_class': '/*/pds4:Identification_Area/pds4:Citation_Information/pds4:List_Author/pds4:Organization/*',
        >>> }

        Notes
        -----
        - The method uses debug logging to track the construction process.
        - The method uses the role_type to construct the appropriate XPath expressions.
        - The method uses the dict_type to construct the appropriate XPath expressions.
        """
        list_key = role_type.lower() + "s"  # "authors" or "editors" or "contributors"

        if dict_type == "xpath_dict":
            return {
                f"xpath_list_{role_type.lower()}_class": f"/*/pds4:Identification_Area/pds4:Citation_Information/pds4:List_{role_type}/*",
                f"xpath_list_{list_key}_person_class": f"/*/pds4:Identification_Area/pds4:Citation_Information/pds4:List_{role_type}/pds4:Person/*",
                f"xpath_list_{list_key}_organization_class": f"/*/pds4:Identification_Area/pds4:Citation_Information/pds4:List_{role_type}/pds4:Organization/*",
            }

        elif dict_type == "xpath_dict_person_attributes":
            return {
                "contributor_type": f"/*/pds4:Identification_Area/pds4:Citation_Information/pds4:List_{role_type}/pds4:Person/pds4:contributor_type",
                "given_name": f"/*/pds4:Identification_Area/pds4:Citation_Information/pds4:List_{role_type}/pds4:Person/pds4:given_name",
                "family_name": f"/*/pds4:Identification_Area/pds4:Citation_Information/pds4:List_{role_type}/pds4:Person/pds4:family_name",
                "person_orcid": f"/*/pds4:Identification_Area/pds4:Citation_Information/pds4:List_{role_type}/pds4:Person/pds4:person_orcid",
            }

        elif dict_type == "xpath_dict_organization_attributes":
            return {
                "contributor_type": f"/*/pds4:Identification_Area/pds4:Citation_Information/pds4:List_{role_type}/pds4:Organization/pds4:contributor_type",
                "organization_name": f"/*/pds4:Identification_Area/pds4:Citation_Information/pds4:List_{role_type}/pds4:Organization/pds4:organization_name",
                "organization_rorid": f"/*/pds4:Identification_Area/pds4:Citation_Information/pds4:List_{role_type}/pds4:Organization/pds4:organization_rorid",
            }

        else:
            logger.debug(f": build_xpath_dict.sys.exit() -- invalid dict_type " f"{dict_type}")

    def map_list_author_editor_fields_to_doi_fields(self, list_authors):
        field_map = {
            "given_name": "first_name",
            "middle_name": "middle_name",
            "family_name": "last_name",
            "name_type": "name_type",
            "person_orcid": "orcid",
            "organization_name": "name",
            "Affiliation": "affiliation",
            "organization_rorid": "rorid",
            "contributor_type": "contributor_type",
        }

        mapped_list_authors = []

        for author in list_authors:
            dict_authors = {}

            for key, value in author.items():
                logger.debug(f": map_list_author_editor_fields_to_doi_fields.key,value " f"{key, value}")
                if key in field_map:
                    new_key = field_map[key]
                    dict_authors[new_key] = value

            mapped_list_authors.append(dict_authors)

        return mapped_list_authors

    # Debug code to get list_authors from pds4_fields
    # dict_list_authors = {"nameIdentifier": "Organizational", "name": "Planetary Data System: Geosciences Node", "rorid": "https://ror.org/02e9yx751"}
    def get_list_auth_edit_cont(self, xml_tree, role_type: str):
        """
        Extract and parse author, editor, or contributor information from PDS4 XML labels.

        This method processes PDS4 XML labels to extract structured contributor information
        (authors, editors, or contributors) from the List_Author, List_Editor, or List_Contributor
        sections. It handles both Person and Organization elements, extracting their attributes
        and organizing them into standardized dictionary structures.

        The method uses XPath expressions to locate contributor elements and their attributes,
        then builds a list of dictionaries where each dictionary represents a single contributor
        with their metadata (name, affiliation, identifiers, etc.).

        Parameters
        ----------
        xml_tree : lxml.etree._Element
            The parsed XML tree representing a PDS4 label.
        role_type : str
            The type of contributor to extract. Must be one of: "Author", "Editor", or "Contributor".
            This determines which XPath expressions and field mappings to use.

        Returns
        -------
        list of dict
            A list of contributor dictionaries, where each dictionary contains:
            - name_type: "Personal" for Person elements or "Organizational" for Organization elements
            - Affiliation: List of affiliation information
            - Additional fields based on the contributor type (e.g., given_name, family_name,
              name_identifier, etc.)

        Examples
        --------
        >>> pds4_util = DOIPDS4LabelUtil()
        >>> authors = pds4_util.get_list_auth_edit_cont(xml_tree, "Author")
        >>> # Returns: [{"name_type": "Personal", "given_name": "John", "family_name": "Doe", ...}]

        Notes
        -----
        - The method handles both Person and Organization elements within the specified role type.
        - XML instances are 1-based for indexing purposes.
        - All extracted text is preserved as-is from the XML source.
        - The method uses debug logging to track the extraction process.
        """
        # For default namespace, we need to use a different approach
        # The XML uses default namespace, so we don't need namespace mapping for XPath
        pds4_namespace = {"pds4": "http://pds.nasa.gov/pds4/pds/v1"}
        pds4_namespace_prefix = "{http://pds.nasa.gov/pds4/pds/v1}"

        xpath_dict = self.build_xpath_dict(role_type, "xpath_dict")
        xpath_dict_person_attributes = self.build_xpath_dict(role_type, "xpath_dict_person_attributes")
        xpath_dict_organization_attributes = self.build_xpath_dict(role_type, "xpath_dict_organization_attributes")

        # get Class in List_Auth:
        #   -- <Person> | <Organization>
        #        -- number of instances of each class
        #
        #
        #  Use list_authors as "holder" for the list of authors, editors, or contributors
        #    -- cast list_editors and list_contributors to list_authors
        list_authors = []
        person_instance = 0  # xml instances are 1-based
        organization_instance = 0  # xml instances are 1-based

        # adjust the dictionary to reflect the role_type
        list_key = role_type.lower() + "s"  # "authors" or "editors" or "contributors"

        xpath = xpath_dict[f"xpath_list_{role_type.lower()}_class"]
        logger.debug(f": get_list_aec.xpath,role_type,xpath " f"{role_type, xpath}")

        list_aec_classes = xml_tree.xpath(xpath, namespaces=pds4_namespace)
        logger.debug(
            f": get_list_aec.xpath,list_aec_classes,len(list_aec_classes) "
            f"{role_type, list_aec_classes, len(list_aec_classes)}"
        )

        # for each Class in List_Auth:
        #   -- <Person> | <Organization>
        #        -- number of instances of each class
        for list_author_class in list_aec_classes:
            logger.debug(f": get_list_aec.list_author_class.tag " f"{list_author_class.tag}")
            # logger.debug(f": get_list_aec.list_author_class.text " f"{list_author_class.text}")

            if list_author_class.tag == pds4_namespace_prefix + "Person":
                logger.debug(f": get_list_aec.list_author_class.tag == Person " f"{list_author_class.tag}")

                person_instance += 1
                logger.debug(f": get_list_aec.person_instance " f"{person_instance}")

                dict_list_authors = {}
                dict_list_authors["name_type"] = "Personal"
                dict_list_authors["Affiliation"] = []

                # adjust the dictionary to reflect the role_type
                xpath = xpath_dict[f"xpath_list_{list_key}_person_class"]
                xpath = xpath.replace("pds4:Person/*", "pds4:Person[" + str(person_instance) + "]/*")
                logger.debug(f": get_list_aec.xpath " f"{xpath}")

                # Convert XPath for default namespace
                xpath_person_attributes = xml_tree.xpath(xpath, namespaces=pds4_namespace)
                logger.debug(
                    f": get_list_aec.xpath_person_attributes,len(xpath_person_attributes) "
                    f"{xpath_person_attributes, len(xpath_person_attributes)}"
                )

                for xpath_person_attribute in xpath_person_attributes:
                    logger.debug(f": get_list_aec.xpath_person_attribute.tag " f"{xpath_person_attribute.tag}")
                    logger.debug(f": get_list_aec.xpath_person_attribute.text " f"{xpath_person_attribute.text}")

                    element_tag = xpath_person_attribute.tag.replace(pds4_namespace_prefix, "")
                    element_text = xpath_person_attribute.text
                    logger.debug(f": get_list_aec.element_tag " f"{element_tag}")
                    logger.debug(f": get_list_aec.element_text " f"{element_text}")

                    if element_tag in xpath_dict_person_attributes:
                        dict_list_authors[element_tag] = element_text
                        logger.debug(
                            f": get_list_aec.dict_list_authors[tag] " f"{element_tag, dict_list_authors[element_tag]}"
                        )
                    else:
                        logger.debug(
                            f": get_list_aec.each_element.tag not in xpath_dict_person_attributes[key] "
                            f"{element_tag}"
                        )

                list_authors.append(dict_list_authors)
                logger.debug(f": get_list_aec.list_authors.len, list_authors " f"{len(list_authors), list_authors}")

                for each_item in list_authors:
                    logger.debug(f": get_list_aec.each_item " f"{each_item}")

            elif list_author_class.tag == pds4_namespace_prefix + "Organization":
                logger.debug(f": get_list_aec.list_author_class.tag == Organization " f"{list_author_class.tag}")

                organization_instance += 1
                logger.debug(f": get_list_aec.organization_instance " f"{organization_instance}")

                dict_list_authors = {}
                dict_list_authors["name_type"] = "Organizational"
                dict_list_authors["Affiliation"] = []

                # adjust the dictionary to reflect the role_type
                xpath = xpath_dict[f"xpath_list_{list_key}_organization_class"]
                xpath = xpath.replace("pds4:Organization/*", "pds4:Organization[" + str(organization_instance) + "]/*")
                logger.debug(f": get_list_aec.xpath " f"{xpath}")

                # Convert XPath for default namespace
                xpath_organization_attributes = xml_tree.xpath(xpath, namespaces=pds4_namespace)
                logger.debug(
                    f": get_list_aec.xpath_organization_attributes,len(xpath_organization_attributes) "
                    f"{xpath_organization_attributes, len(xpath_organization_attributes)}"
                )

                for xpath_organization_attribute in xpath_organization_attributes:
                    logger.debug(
                        f": get_list_aec.xpath_organization_attribute.tag " f"{xpath_organization_attribute.tag}"
                    )
                    logger.debug(
                        f": get_list_aec.xpath_organization_attribute.text " f"{xpath_organization_attribute.text}"
                    )

                    element_tag = xpath_organization_attribute.tag.replace(pds4_namespace_prefix, "")
                    element_text = xpath_organization_attribute.text
                    logger.debug(f": get_list_aec.element_tag " f"{element_tag}")
                    logger.debug(f": get_list_aec.element_text " f"{element_text}")

                    if element_tag in xpath_dict_organization_attributes:
                        dict_list_authors[element_tag] = element_text
                        logger.debug(
                            f": get_list_aec.dict_list_authors[tag] " f"{element_tag, dict_list_authors[element_tag]}"
                        )
                    else:
                        logger.debug(
                            f": get_list_aec.each_element.tag not in xpath_dict_organization_attributes[key] "
                            f"{element_tag}"
                        )

                list_authors.append(dict_list_authors)
                logger.debug(f": get_list_aec.list_authors.len, list_authors " f"{len(list_authors), list_authors}")

                for each_item in list_authors:
                    logger.debug(f": get_list_aec.each_item " f"{each_item}")

            else:
                logger.debug(
                    f": get_list_aec.sys.exit -- neither <Person> nor <Organization> class was found as child class of <List_Authors> class "
                    f"{list_author_class.text}"
                )
                # Continue processing other classes instead of exiting
                sys.exit()

        # Need to map List_Author fields to DOI fields
        mapped_list_authors = self.map_list_author_editor_fields_to_doi_fields(list_authors)
        logger.debug(
            f": get_list_aec.mapped_list_authors.len, mapped_list_authors "
            f"{len(mapped_list_authors), mapped_list_authors}"
        )
        logger.debug(f": get_list_aec.role_type END " f"{role_type}")

        return mapped_list_authors

    def is_pds4_label(self, xml_tree):
        """
        If reading xpaths with the PDS4 namespace returns anything, it should
        be safe to assume its a PDS4 label, additional validation can occur
        downstream.
        """
        if self.read_pds4(xml_tree):
            return True

        return False

    def get_doi_fields_from_pds4(self, xml_tree):
        # Store xml_tree as instance variable for use in other methods
        self.xml_tree = xml_tree

        pds4_fields = self.read_pds4(xml_tree)

        logger.debug(f": get_doi_fields_from_pds4.pds4_fields.type " f"{type(pds4_fields)}")
        logger.debug(f": get_doi_fields_from_pds4.pds4_fields " f"{pds4_fields}")
        doi_fields = self.process_pds4_fields(pds4_fields)
        logger.debug(f": get_doi_fields_from_pds4.doi_fields " f"{doi_fields}")

        return doi_fields

    def read_pds4(self, xml_tree):
        """
        Reads values from a PDS4 XML Label into a local dictionary using the
        mapping of field names to xpath locations.

        Parameters
        ----------
        xml_tree : lxml.etree.Element
            The root of the parsed PDS4 label to read.

        Returns
        -------
        pds4_field_value_dict : dict
            The dictionary of values read from the parsed PDS4 label.
            The key names correspond to the keys of the xpath mapping
            stored by this class. If the provided XML tree does not
            correspond to a valid PSD4 label, then this will be an empty
            dictionary.

        """
        pds4_field_value_dict = {}

        pds4_namespace = {"pds4": "http://pds.nasa.gov/pds4/pds/v1"}

        for key, xpath in self.xpath_dict.items():
            elements = xml_tree.xpath(xpath, namespaces=pds4_namespace)
            # 202501 -- add logger
            logger.debug(f": xpath.dict.elements: " f"{type(elements)}")
            logger.debug(f": xpath.dict: key, xpath " f"{key, xpath}")
            logger.debug(f": xpath_dict.elements,len(xpath_dict.elements) " f"{elements, len(elements)}")

            if elements:
                pds4_field_value_dict[key] = " ".join(
                    [element.text.strip() for element in elements if element.text]
                ).strip()
            # 20250501 -- add logger
            if elements:
                logger.debug(f": pds4_field_value_dict.key,value: " f"{key, pds4_field_value_dict[key]}")

        return pds4_field_value_dict

    def _check_for_possible_full_name(self, names_list):
        """
        Given a list of names:
        Case 1: "R. Deen, H. Abarca, P. Zamani, J. Maki"
        determine if each token can be potentially a person' name:
          "R. Deen", "H. Abarca", "J. Maki"
        This happens very rarely but it does happen.
           Case 4 :"VanBommel, S. J., Guinness, E., Stein, T., and the MER Science Team"
        """
        o_list_contains_full_name_flag = False
        num_dots_found = 0
        num_person_names = 0

        for one_name in names_list:
            if "." in one_name:
                num_dots_found += 1
                """
                Now that the dot is found, look to see the name contains at
                least two tokens.
                """
                if len(one_name.strip().split(".")) >= 2:
                    """'R. Deen' split to ['R','Deen'], "J. Maki" split to ['J','Maki']"""
                    num_person_names += 1
            else:
                # The name does not contain a dot, split using spaces.
                # Case 4  --> Should be parsed by semi-colon
                #   "VanBommel, S. J., Guinness, E., Stein, T., and the MER Science Team"
                # A person's name should contain at least two tokens.
                if len(one_name.strip().split()) >= 2:
                    num_person_names += 1

        # If every name contains a dot, the list can potentially hold a person's
        # name. This does not work if the convention of having the dot
        # in each person's name is broken.
        if num_dots_found == len(names_list) or num_person_names == len(names_list):
            o_list_contains_full_name_flag = True

        logger.debug(
            f"num_dots_found,num_person_names,len(names_list),names_list "
            f"{num_dots_found, num_person_names, len(names_list), names_list}"
        )
        logger.debug(f"o_list_contains_full_name_flag " f"{o_list_contains_full_name_flag, names_list, len(names_list)}")

        return o_list_contains_full_name_flag

    def _find_method_to_parse_authors(self, pds4_fields_authors):
        """
        This function makes a best guess as to which parsing method is correct
        for a given list of authors.

        Examples of cases:
            Case 1 --> Should be parsed by semi-colon
                pds4_fields_authors = "Lemmon, M."
            Case 2 --> Should be parsed by comma
                pds4_fields_authors = "R. Deen, H. Abarca, P. Zamani, J. Maki"
            Case 3 --> Should be parsed by semi-colon
                pds4_fields_authors = "Davies, A.; Veeder, G."
            Case 4  --> Should be parsed by semi-colon
                pds4_fields_authors = "VanBommel, S. J., Guinness, E., Stein, T., and the MER Science Team"
            Case 5 --> Should be parsed by semi-colon
                pds4_fields_authors = "MER Science Team"

        Parameters
        ----------
        pds4_fields_authors : str
            A listing of authors which may be delimited by comma or semi-colon

        Returns
        -------
        o_best_method : BestParserMethod
            The best method of parsing the list of authors.

        """
        # The 'authors' field from data providers can be inconsistent.
        # Sometimes a comma ',' is used to separate the names, sometimes its
        # semi-colons ';'
        authors_from_comma_split = pds4_fields_authors.split(",")
        authors_from_semi_colon_split = pds4_fields_authors.split(";")

        # Check from authors_from_comma_split to see if it possibly contains full name.
        # Mostly this case: "R. Deen, H. Abarca, P. Zamani, J. Maki"
        # When it is not obvious because it looks similarly to this case:
        # "VanBommel, S. J., Guinness, E., Stein, T., and the MER Science Team"
        comma_parsed_list_contains_full_name = self._check_for_possible_full_name(authors_from_comma_split)

        number_commas = pds4_fields_authors.count(",")
        number_semi_colons = pds4_fields_authors.count(";")

        if number_semi_colons == 0:
            if number_commas >= 1:
                if comma_parsed_list_contains_full_name:
                    # Case 2
                    o_best_method = BestParserMethod.BY_COMMA
                else:
                    # Case 1 or Case 4
                    o_best_method = BestParserMethod.BY_SEMI_COLON
            else:
                # Case 5
                o_best_method = BestParserMethod.BY_SEMI_COLON
        else:
            # Case 3
            o_best_method = BestParserMethod.BY_SEMI_COLON

        logger.debug(
            f"o_best_method,pds4_fields_authors "
            f"{o_best_method, pds4_fields_authors} "
            f"number_commas,number_semi_colons "
            f"{number_commas, number_semi_colons}"
        )
        logger.debug(
            f"len(authors_from_comma_split),len(authors_from_semi_colon_split) "
            f"{len(authors_from_comma_split), len(authors_from_semi_colon_split)}"
        )

        return o_best_method

    def process_pds4_fields(self, pds4_fields):
        try:
            # Initialize doi_suffix to None as default value
            doi_suffix = None

            product_class = pds4_fields["product_class"]
            product_class_suffix = product_class.split("_")[1]

            if product_class == "Product_Document":
                product_specific_type = "PDS4 Refereed Document"
                product_type = ProductType.Document
            elif product_class == "Product_Bundle":
                product_specific_type = "PDS4 Refereed Data Bundle"
                product_type = ProductType.Bundle
            elif product_class == "Product_Collection":
                product_specific_type = "PDS4 Refereed Data Collection"
                product_type = ProductType.Collection
            else:
                product_specific_type = "PDS4 Refereed Data " + product_class_suffix
                product_type = ProductType.Dataset

            editors = self.get_editor_names(pds4_fields["editors"].split(";")) if "editors" in pds4_fields else None

            """ Handle authors field - check if it exists before processing
                 -- process <author_list> as optional
            """
            authors_list = []
            if "authors" in pds4_fields:
                """
                The 'authors' field is inconsistent on the use of separators.
                Try to make a best guess on which method is better.
                """
                o_best_method = self._find_method_to_parse_authors(pds4_fields["authors"])

                if o_best_method == BestParserMethod.BY_COMMA:
                    authors_list = pds4_fields["authors"].split(",")
                elif o_best_method == BestParserMethod.BY_SEMI_COLON:
                    authors_list = pds4_fields["authors"].split(";")
                else:
                    logger.error(f"o_best_method,pds4_fields['authors'] " f"{o_best_method, pds4_fields['authors']}")
                    raise InputFormatException("Cannot split the authors using comma or semi-colon.")
            else:
                logger.warning("No 'authors' field found in PDS4 label. Using empty authors list.")
                doi_suffix = None

            if "doi" in pds4_fields:
                doi_prefix_suffix = pds4_fields["doi"].split("/")
                if len(doi_prefix_suffix) == 2:
                    doi_suffix = doi_prefix_suffix[1]

            timestamp = datetime.now(tz=timezone.utc)

            identifier = pds4_fields["lid"]

            if pds4_fields["vid"]:
                identifier += "::" + pds4_fields["vid"]

            site_url = create_landing_page_url(identifier, product_type)

            # The Doi class Constructor serves as the core data structure that flows through the entire DOI service
            # - initially created in the process_pds4_fields method of DOIPDS4LabelUtil class when
            # processing PDS4 XML labels
            # - from initial parsing of PDS4 labels, through validation and modification in various actions,
            #   to final submission to DOI service providers and storage in the transaction database.
            #
            # Creates a standardized Doi object from the extracted PDS4 label fields.
            # This is a critical transformation point where raw XML data is converted into
            # a structured object that follows DOI metadata conventions. The Doi object
            # serves as the central data structure used throughout the DOI service for
            # all operations (reserve, update, release).
            #
            # The fields are populated as follows:
            # - Basic metadata: title, description, identifiers, DOI (if existing)
            # - Publication information: date, publisher
            # - Product classification: product_type, product_type_specific
            # - Contributors: authors (with name parsing), editors
            # - Discovery metadata: keywords (extracted from multiple fields)
            # - Administrative metadata: status, timestamps, ID suffix
            #
            # initialize dictionaries of values: list_Authots in XML label
            dict_list_authors = {}
            dict_list_editors = {}

            # debug code to test list_authors
            # dict_list_authors = {"nameIdentifier": "Organizational", "name": "Planetary Data System: Geosciences Node", "rorid": "https://ror.org/02e9yx751"}

            doi = Doi(
                doi=pds4_fields.get("doi"),
                status=DoiStatus.Unknown,
                title=pds4_fields["title"],
                description=pds4_fields["description"],
                publication_date=self.get_publication_date(pds4_fields),
                product_type=product_type,
                product_type_specific=product_specific_type,
                pds_identifier=identifier,
                site_url=site_url,
                authors=self.get_author_names(authors_list),
                editors=editors,
                keywords=self.get_keywords(pds4_fields),
                date_record_added=timestamp,
                date_record_updated=timestamp,
                id=doi_suffix,  # e.g., 1k63-7383
                list_authors=self.get_list_auth_edit_cont(self.xml_tree, "Author"),
                list_editors=self.get_list_auth_edit_cont(self.xml_tree, "Editor"),
                list_contributors=self.get_list_auth_edit_cont(self.xml_tree, "Contributor"),
            )

            logger.debug(f": doi.type " f"{type(doi)}")
            logger.debug(f": doi.doi " f"{doi.doi}")
            logger.debug(f": doi.status " f"{doi.status}")
            logger.debug(f": doi.title " f"{doi.title}")
            logger.debug(f": doi.description " f"{doi.description}")
            logger.debug(f": doi.publication_date " f"{doi.publication_date}")
            logger.debug(f": doi.product_type " f"{doi.product_type}")
            logger.debug(f": doi.product_type_specific " f"{doi.product_type_specific}")
            logger.debug(f": doi.pds_identifier " f"{doi.pds_identifier}")
            logger.debug(f": doi.site_url " f"{doi.site_url}")
            logger.debug(f": doi.authors " f"{doi.authors}")
            logger.debug(f": doi.editors " f"{doi.editors}")
            logger.debug(f": doi.keywords " f"{doi.keywords}")
            logger.debug(f": doi.date_record_added " f"{doi.date_record_added}")
            logger.debug(f": doi.date_record_updated " f"{doi.date_record_updated}")
            logger.debug(f": doi.id " f"{doi.id}")
            logger.debug(f": doi.list_authors " f"{doi.list_authors}")
            logger.debug(f": doi.list_editors " f"{doi.list_editors}")
            logger.debug(f": doi.list_contributors " f"{doi.list_contributors}")

        except KeyError as key_err:
            missing_key = key_err.args[0]
            msg = (
                f"Could not find a value for an expected PS4 label field: {key_err}.\n"
                f"Please ensure there is a value present in the label for the "
                f"following xpath: {self.xpath_dict[missing_key]}"
            )
            logger.error(msg)
            raise InputFormatException(msg)

        """
        - can can be only a single source for  <authors>
        -- ascertain if <author_list> and/or <List_Author> metadata is present in the XML label.
        -- if both; <List_Author> metadata supercedes <author_list>
        -- if only <author_list>; use <author_list> metadata
        -- if only <List_Author>; use <List_Author> metadata
        """
        if len(doi.list_authors) > 0:
            doi.authors = doi.list_authors
            logger.debug(
                f": process_pds4_fields.doi.authors replaced with doi.list_authors " f"{len(doi.authors), doi.authors}"
            )
        else:
            logger.debug(
                f": process_pds4_fields.doi.authors NOT replaced with doi.list_authors "
                f"{len(doi.authors), doi.authors}"
            )
        if len(doi.list_editors) > 0:
            doi.editors = doi.list_editors
            logger.debug(
                f": process_pds4_fields.doi.editors replaced with doi.list_editors " f"{len(doi.editors), doi.editors}"
            )
        else:
            logger.debug(
                f": process_pds4_fields.doi.editors NOT replaced with doi.list_editors "
                f"{len(doi.editors) if doi.editors is not None else 0}, {doi.editors}"
            )
        if len(doi.list_contributors) > 0:
            if doi.editors is None:
                doi.editors = doi.list_contributors
            else:
                doi.editors.extend(doi.list_contributors)
            """  logger.debug(f": process_pds4_fields.doi.contributors replaced with doi.list_contributors " f"{len(doi.contributors), doi.contributors}") """
            logger.debug(
                f": process_pds4_fields.doi.list_contributors " f"{len(doi.list_contributors), doi.list_contributors}"
            )
            logger.debug(
                f": process_pds4_fields.doi.list_contributors appended to doi.editors "
                f"{len(doi.editors) if doi.editors is not None else 0}, {doi.editors}"
            )
        else:
            """logger.debug(f": process_pds4_fields.doi.contributors NOT replaced with doi.contributors " f"{len(doi.contributors), doi.contributors}")"""
            logger.debug(
                f": process_pds4_fields.doi.list_contributors NOT appended to doi.editors "
                f"{len(doi.editors) if doi.editors is not None else 0}, {doi.editors}"
            )

        logger.debug(f": doi.authors_replaced " f"{doi.authors}")
        logger.debug(f": doi.editors_replaced " f"{doi.editors}")

        return doi

    def get_publication_date(self, pds4_fields):
        """
        Determines the publication date for a DOI from PDS4 label fields.

        This method extracts and processes date information from a PDS4 label with
        a specific order of precedence:

        1. First priority: 'modification_date' field - If present, this field is used
           as it typically contains the most recent update date. If multiple modification
           dates are present (common in PDS4 labels that track version history), the
           earliest date is selected by sorting the dates.

        2. Second priority: 'publication_year' field - If no modification date is found,
           the publication year is used. Since this field only contains a year, the
           resulting date will have month and day set to January 1st.

        3. Fallback: Current date - If neither of the above fields are present, the
           current date and time (in UTC) is used as a fallback.

        Parameters
        ----------
        pds4_fields : dict
            Dictionary containing values extracted from a PDS4 label, where keys
            correspond to field names and values contain the text content.

        Returns
        -------
        datetime
            A datetime object representing the publication date. The precision will
            depend on which source field was used (full date for modification_date,
            year-only precision for publication_year).
        """
        """
        The field 'modification_date' is favored first.
        If it is present use it, otherwise use 'publication_year' field next.
        """
        if "modification_date" in pds4_fields:
            logger.debug(
                f"pds4_fields['modification_date'] "
                f"{pds4_fields['modification_date'], type(pds4_fields['modification_date'])}"
            )

            """
            Some PDS4 labels have more than one 'modification_date' field,
            so sort in ascending and select the first date.
            """
            latest_mod_date = sorted(pds4_fields["modification_date"].split(), reverse=False)[0]
            publication_date = datetime.strptime(latest_mod_date, "%Y-%m-%d")
        elif "publication_year" in pds4_fields:
            publication_date = datetime.strptime(pds4_fields["publication_year"], "%Y")
        else:
            publication_date = datetime.now(tz=timezone.utc)

        return publication_date

    def get_keywords(self, pds4_fields):
        """
        Extracts keywords from specific fields in the PDS4 label to create a set of relevant keywords.

        This method processes text from multiple predefined fields in the PDS4 label that commonly
        contain keyword-relevant information. It uses a KeywordTokenizer to parse and extract
        meaningful keywords from these fields.

        The following fields are checked for keyword extraction:
        - investigation_area: Information about the mission or investigation
        - observing_system_component: Information about instruments or systems used
        - target_identification: Information about the celestial body or target
        - primary_result_summary: Summary of the primary scientific results
        - description: General description text that may contain relevant terms

        Parameters
        ----------
        pds4_fields : dict
            Dictionary containing values extracted from a PDS4 label, where keys
            correspond to field names and values contain the text content.

        Returns
        -------
        set
            A set of unique keywords extracted from the PDS4 label fields. The
            keywords are processed and normalized by the KeywordTokenizer.

            for example: keyword_tokenizer.get_keywords() {'subsystem', 'saturn', 'cassini-huygens'}
        """
        keyword_fields = {
            "investigation_area",
            "observing_system_component",
            "target_identification",
            "primary_result_summary",
        }

        keyword_tokenizer = KeywordTokenizer()

        for keyword_src in keyword_fields:
            if keyword_src in pds4_fields.keys():
                keyword_tokenizer.process_text(pds4_fields[keyword_src])

        logger.debug(f": keyword_tokenizer.get_keywords() " f"{keyword_tokenizer.get_keywords()}")

        return keyword_tokenizer.get_keywords()

    @staticmethod
    def _smart_first_last_name_detector(split_fullname, default_order=(0, -1)):
        if len(split_fullname[0]) == 1 or split_fullname[0][-1] == ".":
            return 0, -1
        elif len(split_fullname[-1]) == 1 or split_fullname[-1][-1] == ".":
            return -1, 0
        else:
            return default_order

    @staticmethod
    def _get_name_components(
        full_name: str,
    ) -> Dict[str, Union[str, Sequence[str]]]:
        """
        Given a raw full_name string and some splitting configuration, return a dict describing the named entity
        :param full_name: a raw full-name string to parse
        :returns: the parsed entity
        :rtype: Dict[str, Union[str, List[str]]]
        """

        # helper function to encapsulate logic for detecting organizational names

        def name_str_is_organization(separators: List[str], name: str) -> bool:
            is_mononym = not any([sep in name for sep in separators])
            return is_mononym

        # An ordered tuple of chars by which to split full_name into name chunks, with earlier elements taking
        # precedence at each stage of splitting (last/given, then first/middle)
        primary_separators = [",", ". "]

        # Detect organization names, which lack separable chunks
        # Modified code to not set 'Affiliation' where "Organizational" test cases
        if name_str_is_organization(primary_separators, full_name):
            entity = {
                "name": full_name,
                "affiliation": [
                ],
                "name_type": "Organizational",
            }

            logger.debug(f"parsed organization {entity}")
            return entity

        # Perform primary split, intuiting last/given name order from the separator
        primary_separators_present_in_full_name = [sep for sep in primary_separators if sep in full_name]
        primary_separator = primary_separators_present_in_full_name[0]
        comma_separated = "," in primary_separator
        if comma_separated:
            last_name, given_names_str = [s.strip() for s in full_name.strip().split(primary_separator, maxsplit=1)]
        else:
            given_names_str, last_name = [s.strip() for s in full_name.strip().rsplit(primary_separator, maxsplit=1)]

        # Perform split of given names string into a first name and middle names, if required, and return entity
        given_names_separators = [
            " ",
        ]
        separators_present_in_given_name_str = [sep for sep in given_names_separators if sep in given_names_str]

        if separators_present_in_given_name_str:
            separator = separators_present_in_given_name_str[0]
            uses_abbreviation = separator == ". "

            first_name, middle_names_str = [s.strip() for s in given_names_str.split(separator, maxsplit=1)]
            return {
                "first_name": first_name + ("." if uses_abbreviation else ""),
                "middle_name": middle_names_str,
                "last_name": last_name,
                "affiliation": [],
                "name_type": "Personal",
            }
        else:
            first_name_uses_abbreviation = primary_separator == ". "
            return {
                "first_name": given_names_str + ("." if first_name_uses_abbreviation else ""),
                "last_name": last_name,
                "affiliation": [],
                "name_type": "Personal",
            }

    def get_names(
        self,
        name_list: List[str],
    ) -> List[Dict[str, Union[str, Sequence[str]]]]:
        """
        Given a list of personal/organizational name strings and some parsing configuration, return a list of Dicts
        representing the named entities.
        :param name_list: a list of raw name strings to parse
        :returns: a List of parsed entities
        :rtype: List[Dict[str, Union[str, List[str]]]]
        """
        logger.debug(f"name_list {name_list}")

        persons = []

        for full_name in name_list:
            persons.append(self._get_name_components(full_name))

        return persons

    def get_author_names(self, name_list: List[str]) -> List[Dict[str, Union[str, Sequence[str]]]]:
        """
        Parse a list of author name strings into structured author dictionaries.

        This method is a convenience wrapper around get_names() specifically for
        author names. It processes raw author name strings and returns structured
        dictionaries containing parsed name components.

        Parameters
        ----------
        name_list : List[str]
            A list of raw author name strings to parse.

        Returns
        -------
        List[Dict[str, Union[str, Sequence[str]]]]
            A list of parsed author dictionaries, each containing name components
            such as first_name, last_name, middle_name, affiliation, and name_type.

        Examples
        --------
        >>> pds4_util = DOIPDS4LabelUtil()
        >>> authors = pds4_util.get_author_names(["Doe, John", "Smith, Jane A."])
        >>> # Returns structured author dictionaries
        """
        return self.get_names(name_list)

    def get_editor_names(self, name_list):
        """
        Parse a list of editor name strings into structured editor dictionaries.

        This method is a convenience wrapper around get_names() specifically for
        editor names. It processes raw editor name strings and returns structured
        dictionaries containing parsed name components.

        Parameters
        ----------
        name_list : List[str]
            A list of raw editor name strings to parse.

        Returns
        -------
        List[Dict[str, Union[str, Sequence[str]]]]
            A list of parsed editor dictionaries, each containing name components
            such as first_name, last_name, middle_name, affiliation, and name_type.

        Examples
        --------
        >>> pds4_util = DOIPDS4LabelUtil()
        >>> editors = pds4_util.get_editor_names(["Doe, John", "Smith, Jane A."])
        >>> # Returns structured editor dictionaries
        """
        return self.get_names(name_list)
