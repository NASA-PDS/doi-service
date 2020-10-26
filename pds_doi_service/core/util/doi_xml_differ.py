#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
#------------------------------

import datetime
from lxml import etree

from pds_doi_service.core.input.exceptions import InputFormatException
from pds_doi_service.core.input.node_util import NodeUtil
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger('pds_doi_core.util.doi_xml_differ')

class DOIDiffer:
    # This class provide a way to answer the question if two DOIs (XML format) are similar.

    def _resolve_special_fields(field_name, historical_value, new_value):
        # Some fields may have different format.  For example:
        # The historical field 'publication_date' format may be 2019-09-26
        # Where the new 'publication_date' format may be 09/26/2019
        # The 'full_name' for contributor may have 'Planetary Data System:" preceding the node name.
        # Historical may have keywords that will not be in new code so a list is needed to skip.
        # Use all lowercase for consistency.
        keywords_to_skip_compare = NodeUtil.get_permissible_values()
        keywords_to_skip_compare.append('PDS3'.lower())


        o_difference_is_acceptable_flag = False
        if field_name == 'id':
            if new_value is None:
                o_difference_is_acceptable_flag = True  # The DOI fromo 'draft' may not have the 'id' field.
            else:
                if historical_value.lstrip().rstrip() == new_value.lstrip().rstrip():
                    o_difference_is_acceptable_flag = True
        elif field_name == 'date_record_added':
            o_difference_is_acceptable_flag = True  # The record may be added on different day.
        elif field_name == 'publication_date':
            try:
                reformatted_date = datetime.datetime.strptime(historical_value,"%Y-%m-%d")  # Parse using yyyy-mm-dd format.
                historical_date_as_string  = reformatted_date.strftime('%m/%d/%Y')          # Convert to dd/mm/yyyy format.
                if historical_date_as_string == new_value:
                    o_difference_is_acceptable_flag = True
            except Exception:
                logger.error(f"Failed to parse publication_date {historical_value} as %Y-%m-%d format.")

                # Try a different method before raising 
                try:
                    reformatted_date = datetime.datetime.strptime(historical_value,"%m/%d/%Y")  # Parse using mm/dd/yyy format.
                    historical_date_as_string  = reformatted_date.strftime('%Y-%m-%d')
                    if historical_date_as_string == new_value:
                        o_difference_is_acceptable_flag = True
                except Exception:
                    logger.error(f"Failed to parse publication_date {historical_value} as %m/%d/%Y format.")
                    raise InputFormatException(f"Failed to parse publication_date {historical_value} as %Y-%m-%d  and %m/%d/%Y formats.")
        elif field_name == 'keywords':
            # We will relax the keywords check since there will be new module used to build the keywords.
            # Comment out the next two lines if desire to un-relax the check after the module has been added.
            o_difference_is_acceptable_flag = True 
            return o_difference_is_acceptable_flag

            # Code is not pretty, will be clean up later.
            # The 'keywords' field can be in any particular order. Split the keywords using ';' and then perform the 'in' function.
            historical_value_tokens = historical_value.split(';')
            historical_value_tokens = [x.lstrip().rstrip().lower() for x in historical_value_tokens] # Remove leading and trailing blanks. 
            new_value_tokens        = new_value.split(';')
            new_value_tokens        = [x.lstrip().rstrip().lower() for x in new_value_tokens]        # Remove leading and trailing blanks.
            o_difference_is_acceptable_flag = True 
            for ii in range(len(historical_value_tokens)):
                # If one token differ, then the whole 'keywords' field is different.  
                # Make a 2nd attempt by looking at each token in the list of tokens.
                if historical_value_tokens[ii].lower() in keywords_to_skip_compare:
                    continue
                if historical_value_tokens[ii] not in new_value_tokens:
                    # Loop again through all new_value_tokens to look for substring.
                    # If one token matches, then the difference is acceptable.
                    o_difference_is_acceptable_flag = False
                    for jj in range(len(new_value_tokens)):
                        if historical_value_tokens[ii] in new_value_tokens[jj]: 
                            o_difference_is_acceptable_flag = True
                        else:
                            # Split the historical_value_tokens[ii] with spaces "solar wind" into ["solar", "wind"]
                            space_split_historical_tokens = historical_value_tokens[ii].split()
                            logger.debug(f"KEYWORD_SEARCH_FAILED:len(space_split_historical_tokens {len(space_split_historical_tokens)}")
                            for kk in range(len(space_split_historical_tokens)):
                                logger.debug(f"KEYWORD_SEARCH_FAILED:INSPECTING_IN {space_split_historical_tokens[kk]} IN {new_value_tokens[jj],space_split_historical_tokens[kk] in new_value_tokens[jj]}")
                                if space_split_historical_tokens[kk] in new_value_tokens[jj]:
                                    o_difference_is_acceptable_flag = True
                                else:
                                    pass
                                    logger.debug(f"KEYWORD_SEARCH_FAILED:historical_value_tokens[ii] NOT_IN new_value_tokens[jj] {historical_value_tokens[ii],new_value_tokens[jj]}")
                    if not o_difference_is_acceptable_flag:
                        logger.error(f"KEYWORD_SEARCH_FAILED:[{historical_value_tokens[ii].lstrip().rstrip()} IN {new_value_tokens}")
                        logger.error(f"KEYWORD_SEARCH_FAILED:keywords_to_skip_compare [{keywords_to_skip_compare}")
                        #exit(0)
        elif field_name == 'publisher':
            # Historical value may be: "Atmospheres Node"
            # But new value may have "Planetary Data System:" preceding the node name as in "Planetary Data System: Atmospheres Node"
            # So an 'in' check may be sufficient.
            if 'Node' in historical_value:
                o_difference_is_acceptable_flag = True 
        elif field_name == 'availability':
            if 'NSSDCA' in historical_value:
                o_difference_is_acceptable_flag = True 
        elif field_name == 'product_type_specific':
            # Historical value may be: "PDS4 Bundle"
            # whereas new value may be "PDS4 Refereed Data Bundle"
            historical_value_tokens = historical_value.split()
            o_difference_is_acceptable_flag = True 
            for ii in range(len(historical_value_tokens)):
                # If just one token in historical not in new, then the difference is not acceptable.
                if historical_value_tokens[ii].lower() not in new_value.lower():
                    o_difference_is_acceptable_flag = False
        elif field_name == 'first_name':
            # Historical may not have the first_name as expected:
            #    'first_name': 'C. T.'
            # Whereas new code may have two distinct names.
            #    'first_name': 'C.'
            #    'middle_name': 'T.'
            # so a check for in should be sufficient.
            if new_value.lower() in historical_value.lower():
                o_difference_is_acceptable_flag = True
        elif field_name == 'description' or field_name == 'title':
            # Remove tabs, new lines, spaces, split and join the string back to all lowercase.
            sanitized_new_value        = ' '.join(new_value.split())
            sanitized_new_value        = [x.lower() for x in sanitized_new_value]
            sanitized_historical_value = ' '.join(historical_value.split())
            sanitized_historical_value = [x.lower() for x in sanitized_historical_value] 
            if sanitized_new_value == sanitized_historical_value:
                o_difference_is_acceptable_flag = True
        elif field_name == 'full_name':
            # ['historical:[PDS Geosciences (GEO) Node], new:[Planetary Data System: Geosciences Node]']
            historical_value_tokens = historical_value.split()
            keywords_to_skip_compare.append('pds')
            new_list_to_skip_compare = []
            for keyword in keywords_to_skip_compare: 
                new_list_to_skip_compare.append(keyword)
                new_list_to_skip_compare.append('(' + keyword + ')')  # Add the parenthesis to each keyword so it become ('geo')
            sanitized_new_value        = new_value.split()
            sanitized_new_value        = [x.lower() for x in sanitized_new_value]

            num_tokens_compared = 0
            for historical_token in historical_value_tokens:
                if historical_token.lower() in new_list_to_skip_compare:
                    logger.debug(f"FULL_NAME:SKIPPING historical_token.lower() {historical_token.lower()}")
                    num_tokens_compared += 1
                    continue
                if historical_token.lower() in sanitized_new_value:
                    num_tokens_compared += 1
                logger.debug(f"FULL_NAME:historical_token,sanitized_new_value,o_difference_is_acceptable_flag {historical_token,sanitized_new_value,o_difference_is_acceptable_flag}")

            logger.debug(f"FULL_NAME:historical_value,sanitized_new_value,o_difference_is_acceptable_flag {historical_value,sanitized_new_value,o_difference_is_acceptable_flag,new_list_to_skip_compare,num_tokens_compared,len(historical_value_tokens)}")
            # If all tokens from historical_value can be found in new_value then we are successful.
            if num_tokens_compared == len(historical_value_tokens):
                o_difference_is_acceptable_flag = True
#            exit(0)


        return o_difference_is_acceptable_flag

    def _resolve_apparent_differences(field_name, historical_value, new_value):
        # Given the name of the field that may not compare exactly, this function look for acceptable
        # values using the field_name as the key or add new method(s) of comparison.
        #
        # It is possible that the value may differ depending on how the software was written.  For example:
        #
        # Historical element:
        #   
        #                  <identifier_type>URL</identifier_type>
        #                  <identifier_value>urn:nasa:pds:bundle_mpf_asimet::1.0</identifier_value>
        #                  <relation_type>Cites</relation_type>
        #
        # New element:
        #
        #                  <identifier_type>URN</identifier_type>
        #                  <identifier_value>urn:nasa:pds:bundle_mpf_asimet::1.0</identifier_value>
        #                  <relation_type>IsIdenticalTo</relation_type>
        #
        # The latter was produced after metadata requirements have changed.

        o_difference_is_acceptable_flag = False
        if not field_name:
            return o_difference_is_acceptable_flag

        _acceptable_values_dict = {'identifier_type': ['URL','URN'],
                                   'relation_type'  : ['Cites','IsIdenticalTo'],
                                   'product_type'   : ['Collection','Bundle', 'Dataset', 'Text']}

        # If the given field name is one of the keys in _acceptable_values_dict, look to see if the value is acceptable.
        if field_name in _acceptable_values_dict:
            # Check to see if each value in the acceptable values also occurs in historical_value
            for ii, acceptable_value in enumerate(_acceptable_values_dict[field_name]): 
                if acceptable_value.lower() in historical_value.lower():
                    o_difference_is_acceptable_flag = True
                    break;
        else:
            logger.debug(f"Cannot find field_name {field_name} in _acceptable_values_dict.  Will call _resolve_special_fields()")
            # Make another attempting by checking to see if some fields have different format or values.
            o_difference_is_acceptable_flag = DOIDiffer._resolve_special_fields(field_name, historical_value, new_value)

        return o_difference_is_acceptable_flag

    def _determine_xpath_tag(child_level_1):
        # Given the field name from historical document, determine the full xpath tag in the new document tree, e.g
        # Assumes that the parent tag 'record' is a given.
        #     'title'      in 'title' xpath or
        #     'first_name' in 'authors/author/first_name' xpath or
        #     'last_name'  in 'authors/author/last_name' xpath.

        o_xpath_tag  = child_level_1.tag
        original_tag = child_level_1.tag

        # Travel up from child_level_1.tag until no more parent and build the xpath.
        levels_travelled_up = 0
        if child_level_1.getparent() is not None:
            levels_travelled_up += 1    # LEVEL 1
            if child_level_1.getparent().getparent() is not None:
                levels_travelled_up += 1  # LEVEL 2
                o_xpath_tag = original_tag 
                if child_level_1.getparent().getparent().getparent() is not None:
                   levels_travelled_up += 1 # LEVEL 3
                   o_xpath_tag = child_level_1.getparent().getparent().tag + '/' + child_level_1.getparent().tag + '/' + original_tag
            else:
                logger.debug(f"child_level_1.getparent().getparent() is indeed None {child_level_1.tag}")

        if child_level_1.tag == 'accession_number':
            o_xpath_tag = 'product_nos' # The new code uses 'product_nos' tag instead of 'accession_number'
        if child_level_1.tag == 'date_record_added':
            pass

        logger.debug(f"FINAL_TAG {o_xpath_tag,original_tag,levels_travelled_up}")

        return o_xpath_tag

    def _compare_individual_field(historical_element,child_level_1,new_element,element_index,indices_where_field_occur_dict):
        # Given an XML element from a historical document, compare the field in the element with the new document.

        o_field_differ_name = None  # Returning the name of the field that is not similiar.
        o_values_differ     = None  # Returning a string containing the historical value and the new value to allow the user to inspect.

        historical_has_children = False
        if len(child_level_1):
           historical_has_children = True

        # It is possible that the element to compare comes from a closing tag, which means there is no .text field.
        # Which means there is no meaningful work to perform.
        if child_level_1.text is None:
            return o_field_differ_name, o_values_differ

        if not historical_has_children:
            o_xpath_tag = DOIDiffer._determine_xpath_tag(child_level_1)
            # Find the element in the new element with the same same tag as the historical element. 
            new_child  = new_element.xpath(o_xpath_tag)

            if new_child is None or len(new_child) == 0:
                logger.warning(f"New code does not produced field {child_level_1.tag} in DOI output.  Will skip comparing this field.")
                return o_field_differ_name, o_values_differ


            field_index = DOIDiffer._get_indices_where_tag_occur(child_level_1.tag,child_level_1.getparent().tag,indices_where_field_occur_dict)

            # Because some fields are forced to exist eventhough it is an empty string, check for None-ness otherwise
            # the lstrip() will failed on None.  e.g <id> </id>
            logger.info(f"child_level_1.tag,field_index,len(new_child) {child_level_1.tag,field_index,len(new_child)}")
            if new_child[field_index].text is not None:
                if (child_level_1.text.lstrip().rstrip() == new_child[field_index].text.lstrip().rstrip()):
                    pass # Field is the same which is good.
                    logger.debug(f"FIELD_SAME_TRUE: {child_level_1,child_level_1.text} == {new_child[field_index].text}")
                else:
                    # Fields are different.  Attempt to resolve the apparent differences.
                    logger.debug(f"FIELD_SAME_FALSE: {child_level_1,child_level_1.text} != {new_child[field_index].text}")

                    # It is possible for new_child[0].text to be None so do not perform lstrip() and rstrip()
                    o_difference_is_acceptable_flag = DOIDiffer._resolve_apparent_differences(field_name=child_level_1.tag, historical_value=child_level_1.text, new_value=new_child[0].text)

                    if not o_difference_is_acceptable_flag:
                        # The differences are not acceptable between historical and new field, save the field name.
                        o_field_differ_name = child_level_1.tag
                        # Save the values different.
                        o_values_differ = "historical:[" + child_level_1.text + "], new:[" + new_child[0].text + "]"
                        logger.info(f"FIELD_SAME_FALSE_FINALLY: {child_level_1,child_level_1.text} != {new_child[field_index].text}")
                    else:
                        logger.info(f"FIELD_SAME_TRUE_FINALLY: {child_level_1,child_level_1.text} == {new_child[field_index].text}")

        return o_field_differ_name, o_values_differ

    def _pre_condition_documents(historical_doc, new_doc):
        # Pre-condition both documents before comparing so they have the same order.

        new_root        = new_doc.getroot()
        historical_root = historical_doc.getroot()

        identifier_list_from_historical = []

        # Build a dictionary of all elements in historical_root
        # using the 'related_identifiers/related_identifier/identifier_value' as key.
        historical_dict_list = {}
        for element in historical_root.iter("record"):
            # Some historical document does not have 'related_identifiers/related_identifier/identifier_value field' so
            # an alternative one is 'product_nos'
            if element.xpath("related_identifiers/related_identifier/identifier_value"):
                sorting_element = element.xpath("related_identifiers/related_identifier/identifier_value")
            else:
                sorting_element = element.xpath("accession_number")
            logger.info(f":related_identifiers/related_identifier/identifier_value:len(sorting_element) {len(sorting_element)}")
            if len(sorting_element) == 0:
                sorting_element = element.xpath("product_nos")
                logger.info(f":product_nos:len(sorting_element) {len(sorting_element)}")
            historical_dict_list[sorting_element[0].text] = element
            # Save each identifier_value so it can be checked when processing new records.
            identifier_list_from_historical.append(sorting_element[0].text)

        # Build a dictionary of all elements in new_root using the 'identifier_value' as key.
        new_dict_list = {}
        for element in new_root.iter("record"):
            if element.xpath("related_identifiers/related_identifier/identifier_value"):
                sorting_element = element.xpath("related_identifiers/related_identifier/identifier_value")
            else:
                sorting_element = element.xpath("accession_number")

            new_dict_list[sorting_element[0].text] = element

        # Rebuilt the historical tree in the order of the 'identifier_value' field.
        historical_root = etree.Element("records")
        for key in sorted(historical_dict_list.keys()):
            publication_date = historical_dict_list[key].xpath("publication_date")[0].text
            historical_root.append(historical_dict_list[key])

        # Rebuilt the new tree in the order of the 'identifier_value' field.
        new_root = etree.Element("records")
        for key in sorted(new_dict_list.keys()):
            # It is possible that the historical doesn't have the record.  Check before adding so both will have the same number of records.
            if key in identifier_list_from_historical:
                publication_date = new_dict_list[key].xpath("publication_date")[0].text
                new_root.append(new_dict_list[key])

        # Re-parse both documents now with the 'record' elements in the same order.
        new_doc        = etree.fromstring(etree.tostring(new_root))
        historical_doc = etree.fromstring(etree.tostring(historical_root))

        return historical_doc, new_doc

    def _update_indices_where_tag_occur(tag_name,my_parent_tag,indices_where_field_occur_dict):
        # Check if 'first_name' of 'author' is in dictionary or not and increment by 1 if found.
        full_tag = my_parent_tag + '_'+ tag_name
        if full_tag in indices_where_field_occur_dict:
            indices_where_field_occur_dict[full_tag] += 1  
        else:
            pass
        return indices_where_field_occur_dict

    def _get_indices_where_tag_occur(tag_name,my_parent_tag,indices_where_field_occur_dict):
        # Return where in the tree where the combination of my_parent_tag and tag_name occur, e.g.
        #    author_first_name
        #    contributor_contributor_type
        full_tag = my_parent_tag + '_'+ tag_name
        if full_tag in indices_where_field_occur_dict:
            return indices_where_field_occur_dict[full_tag]
        else:
            logger.debug(f"tag_name '{tag_name}' is not in indices_where_field_occur_dict:")
            return 0

    def _setup_where_field_occur_dict():
        # For fields that can have multiple occurences, a dictionary is necessary to  
        # remember where each field occur in the historical tree so it can be used to find the field in the new tree.
        indices_where_field_occur_dict = {'author_first_name'      : 0,
                                          'author_last_name'       : 0,
                                          'contributor_first_name' : 0,
                                          'contributor_last_name'  : 0,
                                          'contributor_full_name'  : 0,
                                          'contributor_contributor_type' : 0}
        return indices_where_field_occur_dict

    def _differ_single_record(new_doc,historical_element,element_index,io_fields_differ_list,io_values_differ_list,io_record_index_differ_list):
        # Given a 'record' element, compare all fields within and return info about any fields that differed.

        indices_where_field_occur_dict = DOIDiffer._setup_where_field_occur_dict()

        logger.info(f"element_index,historical_element.tag {element_index,historical_element.tag}")
        # Get the same 'record' element from the new_doc XML tree.  Assumes the ordering is the same.
        new_element = new_doc.xpath(historical_element.tag)[element_index]

        # Loop through until cannot find any more elements.  Travel all way to the leaves and then compare the fields.
        child_index = 0
        top_parent_name = historical_element.tag

        for child_level_1 in historical_element.iter():
            # The element with the tag 'record' is not useful, so it is skipped.
            # The Comment element is also not useful, so it is skipped.
            if child_level_1.tag == 'record' or child_level_1.tag is etree.Comment:
                continue

            # Do the fields compare and save the field name differ and the two values list.
            o_field_differ_name, o_values_differ = DOIDiffer._compare_individual_field(historical_element,child_level_1,new_element,element_index,indices_where_field_occur_dict)

            my_parent_tag = child_level_1.getparent().tag
            DOIDiffer._update_indices_where_tag_occur(child_level_1.tag,my_parent_tag,indices_where_field_occur_dict)

            if o_field_differ_name:
                io_fields_differ_list.append(o_field_differ_name)  # Save the field name that differs.
                io_values_differ_list.append(o_values_differ)      # Save the values where the fields differ.
                io_record_index_differ_list.append(element_index)  # Save the index where the fields differ.

            child_index += 1
        # end for child_level_1 in historical_element.iter():

        return io_fields_differ_list,io_values_differ_list,io_record_index_differ_list

    @staticmethod
    def doi_xml_differ(historical_xml_output,new_xml_output):
        # Function compares two XML file specifically the output from a 'reserve' or 'draft' action.
        # Assumptions:
        #    1. The elements in the XML tree may not share the same order, so they will be sorted by title.
        #    2. The document uses 'records' as the root element tag and 'record' as element tag for each record.

        # The structure of the XML file:

        # <?xml version="1.0" encoding="UTF-8"?>
        # <records>
        #     <record status="reserved_not_submitted"> 
        #         <title>Apollo 15 and 17 Heat Flow Experiment Concatenated Data Sets Bundle this title is different</title>
        #         <authors>
        #              <author>
        #                 <first_name>M.</first_name>
        #                 <last_name>St. Clair</last_name>
        #             </author>
        #         </authors>
        #         <publication_date>02/27/2020</publication_date>
        #         <product_type>Collection is different</product_type>
        #         <product_type_specific>PDS4 Bundle</product_type_specific>
        # 
        #         <related_identifiers>
        #             <related_identifier>
        #                 <identifier_type>URL instead of URN</identifier_type>
        #                 <identifier_value>urn:nasa:pds:a15_17_hfe_concatenated::1.0</identifier_value>
        #                 <relation_type>IsIdenticalTo</relation_type>
        #             </related_identifier>

        o_fields_differ_list = []  # A list of fields that differ between two input files.
        o_values_differ_list = []  # A list of values that differ between two input files.
        o_record_index_differ_list = []  # A list of indices where the fields differ.

        # Build an XML tree from both input.
        new_doc        = etree.parse(new_xml_output)
        historical_doc = etree.parse(historical_xml_output)

        # Because the ordering of the 'record' element in the document tree is not known,
        # the field 'related_identifiers/related_identifier/identifier_value' is picked to be the key to sort the document tree by.
        # Assumption: the document built by both software uses the same input and it is unlikely
        #             that the 'identifier_value' field differ.
        # Pre-condition both documents so they have the same order.

        historical_doc, new_doc = DOIDiffer._pre_condition_documents(historical_doc, new_doc)

        element_index = 0

        # Loop through all elements in historical document and if 'record' is found, compare all fields within 'record' element.
        records_compared = 0

        for historical_element in historical_doc.iter():
            if historical_element.tag == 'record':
                # Special logic:
                # Sometimes historical code does not produce the correct number of records.  One example
                # was historical only produced 6 and new code produces 8.
                logger.debug(f'elemet index {element_index}')
                o_fields_differ_list,o_values_differ_list,o_record_index_differ_list = DOIDiffer._differ_single_record(new_doc,historical_element,element_index,o_fields_differ_list,o_values_differ_list,o_record_index_differ_list)

                element_index += 1
                records_compared += 1

        logger.debug(f"records_compared {records_compared,historical_xml_output,new_xml_output}")

        return o_fields_differ_list, o_values_differ_list, o_record_index_differ_list

if __name__ == '__main__':
    historical_xml_output = '/Users/loubrieu/PycharmProjects/pds-doi-service/aaDOI_production_submitted_labels/PPI_InSight_Bundles_Collections_20200812/aaRegistered_by_EN_active/DOI_registered_all_records_corrected.xml'
    new_xml_output       = '/Users/loubrieu/PycharmProjects/pds-doi-service/output/test.xml'

    #historical_xml_output = os.path.join("./","aaaSubmitted_by_ATMOS_reserve_2020624","DOI_reserved_all_records.xml")
    #new_xml_output       = 'DOI_Reserve_ATM-2020-06-30_from_new_code.xml'

    #historical_xml_output = 'temp_doi_label.xml'
    #new_xml_output        = 'temp_doi_label.xml'

    #historical_xml_output = 'aaDOI_production_submitted_labels/GEO_Insight_cruise_20200611/aaRegistered_by_EN/DOI_registered_all_records.xml'
    #new_xml_output       = 'temp_doi_label.xml'

    o_fields_differ_list, o_values_differ_list, o_record_index_differ_list = DOIDiffer.doi_xml_differ(historical_xml_output,new_xml_output)

    print("o_fields_differ_list",len(o_fields_differ_list),o_fields_differ_list)
    print("o_values_differ_list",len(o_values_differ_list),o_values_differ_list)
    print("o_record_index_differ_list",len(o_record_index_differ_list),o_record_index_differ_list)
    print("historical_xml_output,new_xml_output",historical_xml_output,new_xml_output)
