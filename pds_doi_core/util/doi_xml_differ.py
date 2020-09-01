#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
#------------------------------

import datetime
import os
from lxml import etree

from pds_doi_core.input.exceptions import InputFormatException
from pds_doi_core.util.general_util import get_logger
logger = get_logger('pds_doi_core.util.doi_xml_differ')

class DOIDiffer:
    def _resolve_special_fields(field_name, historical_value, new_value):
        # Some fields may have different format.  For example:
        # The historical field 'publication_date' format may be 2019-09-26
        # Where the new 'publication_date' format may be 09/26/2019
        # The 'full_name' for contributor may have 'Planetary Data System:" preceding the node name.

        o_difference_is_acceptable_flag = False
        if field_name == 'publication_date':
            try:
                reformatted_date = datetime.datetime.strptime(historical_value,"%Y-%m-%d")  # Parse using yyyy-mm-dd format.
                historical_date_as_string  = reformatted_date.strftime('%m/%d/%Y')          # Convert to dd/mm/yyyy format.
                if historical_date_as_string == new_value:
                    o_difference_is_acceptable_flag = True

                #print("historical_date_as_string,new_value,o_difference_is_acceptable_flag",historical_date_as_string,new_value,o_difference_is_acceptable_flag)
                #exit(0)
            except Exception:
                print("_resolve_special_fields:ERROR: Failed to parse publication_date as %Y-%m-%d format.",historical_value)
                raise InputFormatException(f"Failed to parse publication_date {historical_value} as %Y-%m-%d format.")
        elif field_name == 'full_name':
            # Historical value may be: "Atmospheres Node"
            # But new value may have "Planetary Data System:" preceding the node name as in "Planetary Data System: Atmospheres Node"
            # So an 'in' check may be sufficient.
            if historical_value.lower() in new_value.lower():
                o_difference_is_acceptable_flag = True
        elif field_name == 'keywords':
            # The 'keywords' field can be in any particular order. Split the keywords using ';' and then perform the 'in' function.
            historical_value_tokens = historical_value.split(';')
            historical_value_tokens = [x.lstrip().rstrip() for x in historical_value_tokens] # Remove leading and trailing blanks. 
            new_value_tokens        = new_value.split(';')
            new_value_tokens        = [x.lstrip().rstrip() for x in new_value_tokens]        # Remove leading and trailing blanks.
            o_difference_is_acceptable_flag = True 
            for ii in range(len(historical_value_tokens)):
                # If one token differ, then the whole 'keywords' field is different.  
                # Make a 2nd attempt by looking at each token in the list of tokens.
                if historical_value_tokens[ii] not in new_value_tokens:
                    # Loop again through all new_value_tokens to look for substring.
                    o_difference_is_acceptable_flag = False
                    for jj in range(len(new_value_tokens)):
                        if historical_value_tokens[ii].lower() in new_value_tokens[jj].lower(): 
                            o_difference_is_acceptable_flag = True
                    if not o_difference_is_acceptable_flag:
                        logger.error("KEYWORD_SEARCH_FAILED:[{historical_value_tokens[ii].lstrip().rstrip()} IN {new_value_tokens}")
        elif field_name == 'publisher':
            # Historical value may be: "Atmospheres Node"
            # but new value may be "NASA Planetary Data System" due to new requirement, the comparison should be more forgiving. 
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
                if historical_value_tokens[ii].lower() not in new_value.lower():
                    o_difference_is_acceptable_flag = False

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
                                   'product_type'   : ['Collection','Bundle', 'Dataset']}

        # If the given field name is one of the keys in _acceptable_values_dict, look to see if the value is acceptable.
        if field_name in _acceptable_values_dict:
            print("_resolve_apparent_differences:field_name,_acceptable_values_dict[field_name]",field_name,_acceptable_values_dict[field_name])
            # Check to see if each value in the acceptable values also occurs in historical_value
            for ii, acceptable_value in enumerate(_acceptable_values_dict[field_name]): 
                if acceptable_value.lower() in historical_value.lower():
                    o_difference_is_acceptable_flag = True
                    #print("_resolve_apparent_differences:acceptable_value in historical_value:",acceptable_value,historical_value)
                    #exit(0)
                    break;
        else:
            #print("_resolve_apparent_differences:ERROR: Cannot find field_name in _acceptable_values_dict",field_name)
            #print("_resolve_apparent_differences:WARNING: Cannot find field_name in _acceptable_values_dict:",field_name)
            logger.warning(f"Cannot find field_name {field_name} in _acceptable_values_dict")
            # Make another attempting by checking to see if some fields have different format.
            o_difference_is_acceptable_flag = DOIDiffer._resolve_special_fields(field_name, historical_value, new_value)

        #print("_resolve_apparent_differences:o_difference_is_acceptable_flag,field_name,historical_value",o_difference_is_acceptable_flag,field_name,historical_value)
        #exit(0)
        return o_difference_is_acceptable_flag

    def _determine_xpath_tag(child_level_1):
        # Given the field name from historical document, determine the full xpath tag in the new document tree, e.g
        #     'title'      in 'record/title' xpath or
        #     'first_name' in 'record/authors/author/first_name' xpath.
        #     'last_name'  in 'record/authors/author/last_name' xpath.
        o_xpath_tag = child_level_1.tag
        #o_xpath_tag = None
        print("0:o_xpath_tag",o_xpath_tag)
        #print("0:child_level_1.tag",child_level_1.tag)
        if child_level_1.getparent() is not None:
            #print("2:PARENT_NAME",child_level_1.getparent().tag,child_level_1.tag)
            #o_xpath_tag = child_level_1.getparent().tag + '/' + o_xpath_tag
            print("2:o_xpath_tag",o_xpath_tag)
            #print("2:child_level_1.tag,child_level_1.getparent().tag",child_level_1.tag,child_level_1.getparent().tag)
            if child_level_1.getparent().getparent() is not None:
                #print("3:PARENT_NAME",child_level_1.getparent().getparent().tag,child_level_1.tag)
                #print("3:child_level_1.tag.child_level_1.getparent().getparent().tag",child_level_1.tag,child_level_1.getparent().getparent().tag)
                #o_xpath_tag = child_level_1.getparent().tag + '/' + o_xpath_tag
                print("3:o_xpath_tag",o_xpath_tag)
                if child_level_1.getparent().getparent().getparent() is not None:
                   #print("4:PARENT_NAME",child_level_1.getparent().getparent().getparent().tag,child_level_1.tag)
                   o_xpath_tag = child_level_1.getparent().getparent().tag + '/' + child_level_1.getparent().tag + '/' + o_xpath_tag
                   print("4:o_xpath_tag",o_xpath_tag)
                   #print("4:PARENT_NAME,o_xpath_tag",child_level_1.getparent().getparent().getparent().tag,o_xpath_tag)
                   #pass;

    #    if child_level_1.tag == 'first_name':
    #        print("_determine_xpath_tag:",child_level_1.getparent().getparent().tag,len(child_level_1.getparent().getparent()))
    ##        print(child_level_1.xpath('first_name')0
    #        print("_determine_xpath_tag:",child_level_1.getparent().getparent()[0])
    #        #print(child_level_1.getparent().getparent()[1])
    #        #print(child_level_1.getparent().getparent()[2])
    #        #print(child_level_1.getparent().getparent()[3])
    #
    #        #print(child_level_1.getparent().getparent()[0].xpath('first_name')[0].text)
    #        #print(child_level_1.getparent().getparent()[1].xpath('first_name')[0].text)
    #        #print(child_level_1.getparent().getparent()[2].xpath('first_name')[0].text)
    #        #print(child_level_1.getparent().getparent()[3].xpath('first_name')[0].text)
    #
    #
    #
    #
    #
    #        # 0:o_xpath_tag first_name
    #        # 2:o_xpath_tag first_name
    #        # 3:o_xpath_tag first_name
    #        # 4:o_xpath_tag authors/author/first_name
    #        # authors 4
    #        print("_determine_xpath_tag:first_name",child_level_1.tag,child_level_1.text)
    #
    #        #exit(0)

    #    if child_level_1.tag == 'sponsoring_organization':
    #        print("_determine_xpath_tag:sponsoring_organization",child_level_1.tag,child_level_1.text)
    #        o_xpath_tag = 'sponsor_org' # The new code uses 'sponsor_org' tag versus 'sponsoring_organization'
        if child_level_1.tag == 'accession_number':
            o_xpath_tag = 'product_nos' # The new code uses 'product_nos' tag instead of 'accession_number'
        if child_level_1.tag == 'date_record_added':
            #o_xpath_tag = None          # The new code does not have 'date_record_added' for command 'draft' 
            print("_determine_xpath_tag:date_record_added found")
            #exit(0)
            pass

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
                logger.warning(f"New code does not produced field{child_level_1.tag} in DOI output.  Will skip comparing this field.")
                return o_field_differ_name, o_values_differ

            print("CHILD_LEVEL_1_TAG,NEW_CHILD_LEN,CHILD_LEVEL_1_PARENT_CHILDREN_LEN",child_level_1.tag,child_level_1.getparent().tag,child_level_1.getparent().getparent().tag,len(new_child),child_level_1.getparent().getparent().tag,len(list(child_level_1.getparent().getparent())))
    #def _get_indices_where_tag_occur(tag_name,my_parent_tag,indices_where_field_occur_dict):
            field_index = DOIDiffer._get_indices_where_tag_occur(child_level_1.tag,child_level_1.getparent().tag,indices_where_field_occur_dict)
            #if field_index == -1:
            #    logger.warning(f"New code does not produced field{child_level_1.tag} in DOI output.  Will skip comparing this field.")
            #    return o_field_differ_name, o_values_differ

            print("_compare_individual_field:child_level_1.tag,field_index",child_level_1.tag,field_index)
            print("NEW_CHILD",len(new_child),new_child,field_index)

            if child_level_1.text.lstrip().rstrip() == new_child[field_index].text.lstrip().rstrip():
                pass # Field is the same which is good.
                print("FIELD_SAME_TRUE:",child_level_1,child_level_1.text, ' == ',new_child[field_index].text)
            else:
                # Fields are different.  Attempt to resolve the apparent differences.
                print("FIELD_SAME_FALSE:",child_level_1,child_level_1.text,' != ',new_child[field_index].text)

                o_difference_is_acceptable_flag = DOIDiffer._resolve_apparent_differences(field_name=child_level_1.tag, historical_value=child_level_1.text, new_value=new_child[0].text.lstrip().rstrip())

                if not o_difference_is_acceptable_flag:
                    # The differences are not acceptable between historical and new field, save the field name.
                    o_field_differ_name = child_level_1.tag
                    # Save the values different.
                    o_values_differ = "historical:[" + child_level_1.text + "], new:[" + new_child[0].text + "]"
                    print("FIELD_SAME_FALSE_FINALLY:",child_level_1,child_level_1.text, ' == ',new_child[field_index].text)
                else:
                    print("FIELD_SAME_TRUE_FINALLY:",child_level_1,child_level_1.text, ' == ',new_child[field_index].text)

        return o_field_differ_name, o_values_differ

    def _pre_condition_documents(historical_doc, new_doc):
        # Pre-condition both documents before comparing so they have the same order.

        new_root        = new_doc.getroot()
        historical_root = historical_doc.getroot()

        # Build a dictionary of all elements in historical_root
        # using the 'related_identifiers/related_identifier/identifier_valuetitle' as key.
        historical_dict_list = {}
        for element in historical_root.iter("record"):
            sorting_element = element.xpath("related_identifiers/related_identifier/identifier_value")
            historical_dict_list[sorting_element[0].text] = element

        # Build a dictionary of all elements in new_root using the 'title' as key.
        new_dict_list = {}
        for element in new_root.iter("record"):
            #sorting_element = element.xpath("title")
            sorting_element = element.xpath("related_identifiers/related_identifier/identifier_value")
            new_dict_list[sorting_element[0].text] = element

        # Rebuilt the historical tree in the order of the 'title' field.
        historical_root = etree.Element("records")
        for key in sorted(historical_dict_list.keys()):
            historical_root.append(historical_dict_list[key])

        # Rebuilt the new tree in the order of the 'title' field.
        new_root = etree.Element("records")
        for key in sorted(new_dict_list.keys()):
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
            print("_update_indices_where_tag_occur:INDICES_UPDATED:",full_tag,indices_where_field_occur_dict[full_tag])
        else:
            print("_update_indices_where_tag_occur:full_tag [" + full_tag + "]  is not in indices_where_field_occur_dict")
        return indices_where_field_occur_dict

    def _get_indices_where_tag_occur(tag_name,my_parent_tag,indices_where_field_occur_dict):
        # Return where in the tree where the combination of my_parent_tag and tag_name occur, e.g.
        #    author_first_name
        #    contributor_contributor_type
        full_tag = my_parent_tag + '_'+ tag_name
        if full_tag in indices_where_field_occur_dict:
            return indices_where_field_occur_dict[full_tag]
        else:
            print("_get_indices_where_tag_occur:tag_name is not in indices_where_field_occur_dict:",tag_name)
            logger.debug(f"tag_name '{tag_name}' is not in indices_where_field_occur_dict:")
            return 0

    def _setup_where_field_occur_dict(self):
        # For fields that can have multiple occurences, a dictionary is necessary to  
        # remember where each field occur in the historical tree so it can be used to find the field in the new tree.
        indices_where_field_occur_dict = {'author_first_name'      : 0,
                                          'author_last_name'       : 0,
                                          'contributor_first_name' : 0,
                                          'contributor_last_name'  : 0,
                                          'contributor_contributor_type' : 0}
        return indices_where_field_occur_dict

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
        # the field 'title' is picked to be the key to sort the document tree by.
        # Assumption: the document built by both software uses the same input and it is unlikely
        #             that the 'title' field differ.
        # Pre-condition both documents so they have the same order.

        historical_doc, new_doc = DOIDiffer._pre_condition_documents(historical_doc, new_doc)

        element_index = 0
        # Loop through all elements in historical document and if 'record' is found, compare all fields within 'record' element.




        first_name_tags_index = 0
        last_name_tags_index  = 0

        # For fields that can have multiple occurences, a dictionary is necessary to  
        # remember where each field occur in the historical tree so it can be used to find the field in the new tree.
    #    indices_where_field_occur_dict = {'author_first_name'      : 0,
    #                                      'author_last_name'       : 0,
    #                                      'contributor_first_name' : 0,
    #                                      'contributor_last_name'  : 0}

        for historical_element in historical_doc.iter():
            if historical_element.tag == 'record':

                # For fields that can have multiple occurences, a dictionary is necessary to  
                # remember where each field occur in the historical tree so it can be used to find the field in the new tree.
                indices_where_field_occur_dict = {'author_first_name'      : 0,
                                                  'author_last_name'       : 0,
                                                  'contributor_first_name' : 0,
                                                  'contributor_last_name'  : 0,
                                                  'contributor_contributor_type' : 0}
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


                    #if child_level_1.tag == 'first_name':
                    #    first_name_tags_index += 1
                    print("HISTORICAL_ELEMENT_TAG,CHILD_LEVEL_1_TAG,CHILD_INDEX",historical_element.tag,child_level_1.tag,child_index,first_name_tags_index,last_name_tags_index)

                    # Do the fields compare and save the field name differ and the two values.
                    o_field_differ_name, o_values_differ = DOIDiffer._compare_individual_field(historical_element,child_level_1,new_element,element_index,indices_where_field_occur_dict)

                    print("IAM_TAG,MY_PARENT_TAG",child_level_1.tag,child_level_1.getparent().tag)
                    #exit(0)
                    my_parent_tag = child_level_1.getparent().tag
                    DOIDiffer._update_indices_where_tag_occur(child_level_1.tag,my_parent_tag,indices_where_field_occur_dict)

                    if o_field_differ_name:
                        o_fields_differ_list.append(o_field_differ_name)  # Save the field name that differs.
                        o_values_differ_list.append(o_values_differ)      # Save the values where the fields differ.
                        o_record_index_differ_list.append(element_index)  # Save the index where the fields differ.

                    child_index += 1
                # end for child_level_1 in historical_element.iter():

                element_index += 1
        # end for element in historical_doc.iter()

        #print("historical_xml_output,new_xml_output",historical_xml_output,new_xml_output)
        #print("o_fields_differ_list",len(o_fields_differ_list),o_fields_differ_list)
        #print("o_values_differ_list",len(o_values_differ_list),o_values_differ_list)
        #print("o_record_index_differ_list",len(o_record_index_differ_list),o_record_index_differ_list)
        #exit(0)

        return o_fields_differ_list, o_values_differ_list, o_record_index_differ_list

if __name__ == '__main__':
    historical_xml_output = os.path.join("./","temp_doi_label_historical_for_unit_test.xml")
    new_xml_output       = 'temp_doi_label_for_unit_test.xml'

    historical_xml_output = os.path.join("./","aaaSubmitted_by_ATMOS_reserve_2020624","DOI_reserved_all_records.xml")
    new_xml_output       = 'DOI_Reserve_ATM-2020-06-30_from_new_code.xml'

    historical_xml_output = 'temp_doi_label.xml'
    new_xml_output        = 'temp_doi_label.xml'

    o_fields_differ_list, o_values_differ_list, o_record_index_differ_list = DOIDiffer.doi_xml_differ(historical_xml_output,new_xml_output)

    print("o_fields_differ_list",len(o_fields_differ_list),o_fields_differ_list)
    print("o_values_differ_list",len(o_values_differ_list),o_values_differ_list)
    print("o_record_index_differ_list",len(o_record_index_differ_list),o_record_index_differ_list)





