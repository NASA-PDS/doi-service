#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
#------------------------------                                                                                                 

from lxml import etree

from pds_doi_core.util.general_util import DOIGeneralUtil, get_logger

# Get the common logger and set the level for this file.
import logging
logger = get_logger('pds_doi_core.input.out_util')
logger.setLevel(logging.INFO)  # Comment this line once happy with the level of logging set in get_logger() function.
# Note that the get_logger() function may already set the level higher (e.g. DEBUG).  Here, we may reset
# to INFO if we don't want debug statements.

class DOIOutputUtil:
    # This class DOIOutputUtil provide convenient functions to update a DOI object already in memory.
    # The structure of DOI object is a document tree.
    m_house_keeping_dict     = {'authors': 0, 'contributors': 0}

    def _count_existing_children_with_same_tag(self,name_index,num_existing_authors,my_parent,last_token):
        # Given a node my_parent, find the number of children with the same tag as last_token.
        # Example 1:
        #     The my_parent tag is authors, count the number of children of authors that share the same tag as 'first_name'
        # Example 2:
        #     The my_parent tag is authors, count the number of children of authors that share the same tag as 'last_name'

        o_num_existing_last_tag = 0
        if num_existing_authors > 0:
            for jj in range(num_existing_authors):
                # Possible values of partial_xpath below:
                #  'authors/author/last_name'
                #  'authors/author/first_name'
                #  'contributors/contributor/last_name'
                #  'contributors/contributor/first_name'

                #                contributors       /     contributor              /    first_name
                partial_xpath = my_parent[0].tag + '/' +  my_parent[0][jj].tag  + '/' + last_token

                next_tags = list(my_parent[0][jj]) # The number of 'author' element, children to 'authors'

                # For each element 'author', look for tags that share the same last tag as 'last_name' or 'first_name'
                # For each element 'contributor', look for tags that share the same last tag as 'last_name' or 'first_name'
                for kk in range(len(next_tags)):
                    if my_parent[0][jj][kk].tag == last_token:
                        o_num_existing_last_tag += 1

        return(o_num_existing_last_tag)

    def populate_list_values_with_values(self,i_doc,attr_xpath,i_value):                                      
        # This function will process tags that are specified with attr_xpath but may not already exist in the XML document 'i_doc'.
        #
        # Parameters:
        #     i_doc  = The XML document tree as input and output.
        #     attr_xpath = The actual path of the tag to update: 'records/record/authors/author/first_name'
        #     i_value    = The list of values to update.
        #
        # For now, this function only process first_name and last_name tags.

        logger.debug("attr_xpath [%s] [%s]" % (attr_xpath,i_value))

        list_of_tags_to_process = ['first_name','last_name']
        list_of_tags_to_process_2 = ['authors','contributors']

        # A dictionary to keep how many 

        dict_existing_children = {'authors': 0, 'contributors': 0}
        m_house_keeping_dict     = {'authors': 0, 'contributors': 0}
                                  #'authors/author/first_name' : 0, 'contributors/contributor

        splitted_tokens = attr_xpath.split('/')        # ['records/record/authors/author/first_name','records/record/authors/author/last_name']
        fourth_token_from_last  = splitted_tokens[-4]  # ['record']
        third_token_from_last   = splitted_tokens[-3]  # ['authors'] or ['contributors']
        token_before_last = splitted_tokens[-2]  # ['author']  or ['contributor']
        last_token              = splitted_tokens[-1]  # ['last_name','first_name']
        first_time_flag = True
        added_contributor_type_list = [False for ii in range(len(i_value))]

        # Only process the attr_xpath if the last token is in list_of_tags_to_process list and the fourth_token_from_last is 'record'

        if fourth_token_from_last == 'record' and third_token_from_last in list_of_tags_to_process_2 and last_token in list_of_tags_to_process:
            # Define who the parent is.
            #my_parent = i_doc.xpath('record/authors')
            my_parent = i_doc.xpath('record/' + third_token_from_last)   # 'record/authors' or 'record/editors'
            num_children_initial = len(list(my_parent[0]))

            # Create a list of indices containing where in the list of parents, e.g. 'authors' does the 'author' occur.
            # Create a list of indices containing where in the list of parents, e.g. 'contributor' does the 'contributor' occur.
            indices_list_where_author_contributor_added = []

            for name_index,name_value in enumerate(i_value):
                # For each parent, which is 'authors' or 'editor', create a child call 'author' or 'editor' and add last_name to author child. 
                num_existing_authors = len(list(my_parent[0]))  # This could also be num_existing_editors if we are dealing with editor tag
                existing_authors_tags = []
                for my_element in list(my_parent[0]):
                    existing_authors_tags.append(my_element.tag)

                # Count how many existing authors with the same children.
                num_existing_last_tag = self._count_existing_children_with_same_tag(name_index,num_existing_authors,my_parent,last_token)


                if num_existing_last_tag < len(i_value): 
                    my_author = list(my_parent[0])

                    # Save indices in 'authors' or 'contributors' where the last_token was added.
                    if (name_index+num_children_initial) > len(i_value): 
                        indices_list_where_author_contributor_added.append(name_index+num_children_initial-len(i_value))
                    elif (name_index+num_children_initial) == len(i_value): 
                        #indices_list_where_author_contributor_added.append(name_index)
                        if name_index == 0:
                            indices_list_where_author_contributor_added.append(0)
                        else:
                            indices_list_where_author_contributor_added.append(len(i_value))
                    else:
                        indices_list_where_author_contributor_added.append(name_index+num_children_initial)

                    reuse_flag = False

                    if m_house_keeping_dict[my_parent[0].tag] < len(i_value) and num_children_initial < len(i_value):
                        m_house_keeping_dict[my_parent[0].tag] = m_house_keeping_dict[my_parent[0].tag] + 1
                        # If this is the first time in the loop, we have no 'author' or 'contributor' yet, we will create a child.
                        # e.g. create a child 'author' to 'authors' then create 'last_name' to 'author'
                        # e.g. create a child 'contributor' to 'contributor' then create 'last_name' to 'contributor'
                        my_author = etree.SubElement(my_parent[0],token_before_last) # Create 'author' to 'authors' or 'contributor' to 'contribuors'
                        # For contributors, we also add <contributor_type>Editor</contributor_type>
                        if third_token_from_last == 'contributors':
                            my_child  = etree.SubElement(my_author,'contributor_type')
                            my_child.text = 'Editor'

                        my_child  = etree.SubElement(my_author,last_token) # Create 'last_name' to 'author' or 'last_name' to 'contributor'
                        first_time_flag = False
                    else:
                        reuse_flag = True
                        m_house_keeping_dict[my_parent[0].tag] = m_house_keeping_dict[my_parent[0].tag] + 1
                        my_author = list(my_parent[0])
                        # Create a new 'author' or 'contributor' child to 'authors' or 'contributors'
                        my_child  = etree.SubElement(my_author[indices_list_where_author_contributor_added[name_index]],last_token) # Create 'last_name' to 'author' or 'last_name' to 'contributor'

                    # We know have 'last_name' or 'first_name' created, we can fill in the actual value.
                    my_child.text = name_value.lstrip().rstrip()   # The child of authors/author/ has a child called last_name of value 'Maki'.
                else:
                    pass  # Nothing to do.

                num_new_authors = len(list(my_parent[0]))  # Check to see how many authors have not added.
            # end for name_index,name_value in enumerate(i_value):
            num_children_total = len(list(my_parent[0])) # Check to see how many children have been added to the parent.
        return(i_doc)

    def populate_doi_xml_with_values(self,dict_fixedList, xmlText, attr_xpath, i_value):                                      
        # Given an XML object xmlText, this function will update the attr_xpath in xmlText with the new input i_value.
        # Since we don't know the type of xmlText (bytes or text), we may have to encode xmlText from string to bytes.
        elm = None # Set to None so the value can be checked before printing.

        logger.debug("len(xmlText) %s",len(xmlText))
        logger.debug("type(xmlText) %s",type(xmlText))

        #------------------------------                                                                                             
        # Populate the xml attribute with the specified value                                                                       
        #------------------------------                                                                                             

        if isinstance(xmlText,bytes):
            doc = etree.fromstring(xmlText)
        else:
            doc = etree.fromstring(xmlText.encode()) # Have to change the text to bytes then encode it to get it to work.

        if len(doc.xpath(attr_xpath)) == 0:
            # Because the document tree 'doc' does not have the xpath already, will attempt to populate the 'first_name' and 'last_name' tags.

            doc = self.populate_list_values_with_values(doc,attr_xpath,i_value)

        else:

            elm = doc.xpath(attr_xpath)[0]                                                              

            logger.info("VARIABLE_UPDATE: variable [%s] value [%s]" % (attr_xpath,str(i_value)))

            # Do a sanity check to make sure the list update is not 'last_name' or 'first_name' because it would of been
            # done with populate_list_values_with_values() function above.
            list_of_tags_to_not_process = ['first_name','last_name']
            if isinstance(i_value,list):
                if attr_xpath in list_of_tags_to_not_process:
                    logger.error("This function does not suppport this attr_xpath [%s] list_of_tags_to_not_process [%s]." % (attr_xpath,list_of_tags_to_not_process))
                    exit(1)
                if 'last_name' in attr_xpath:
                    logger.error("This function does not suppport this attr_xpath [%s]." % attr_xpath)
                    exit(1)
                if 'first_name' in attr_xpath:
                    logger.error("This function does not suppport this attr_xpath [%s]." % attr_xpath)
                    exit(1)
            else: 
                # Do a normal setting of value to text of element.
                elm.text = i_value

        etree.indent(doc,space="    ")  # Re-indent because we may have new levels added.
        sOutText = etree.tostring(doc,pretty_print=True)
        return(sOutText)

if __name__ == '__main__':
    doiOutputUtil = DOIOutputUtil()
