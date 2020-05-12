#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
#------------------------------                                                                                                 

from lxml import etree


class DOIOutputUtil:
    # This class DOIOutputUtil provide convenient functions to update a DOI object already in memory.
    # The structure of DOI object is a document tree.
    global m_debug_mode
    m_debug_mode = False
    m_module_name = 'DOIOutputUtil:'
    m_debug_mode = False
    m_house_keeping_dict     = {'authors': 0, 'contributors': 0}

    def _count_existing_children_with_same_tag(self,name_index,num_existing_authors,my_parent,last_token):
        # Given a node my_parent, find the number of children with the same tag as last_token.
        # Example 1:
        #     The my_parent tag is authors, count the number of children of authors that share the same tag as 'first_name'
        # Example 2:
        #     The my_parent tag is authors, count the number of children of authors that share the same tag as 'last_name'

        function_name = self.m_module_name + '_count_existing_children_with_same_tag:'
        global m_debug_mode

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
                if m_debug_mode:
                    print(function_name,"name_index,jj,my_parent[0].tag,my_parent[0][jj].tag,last_token",name_index,jj,my_parent[0].tag,my_parent[0][jj].tag,last_token)
                    print(function_name,"name_index,jj,partial_xpath,num_existing_authors",name_index,jj,partial_xpath,num_existing_authors)

                next_tags = list(my_parent[0][jj]) # The number of 'author' element, children to 'authors'

                if m_debug_mode:
                    print(function_name,"name_index,jj,len(next_tags)",name_index,jj,len(next_tags))

                # For each element 'author', look for tags that share the same last tag as 'last_name' or 'first_name'
                # For each element 'contributor', look for tags that share the same last tag as 'last_name' or 'first_name'
                for kk in range(len(next_tags)):
                    if m_debug_mode:
                        print(function_name,"name_index,jj,kk,my_parent[0][jj][kk].tag,last_token",name_index,jj,kk,my_parent[0][jj][kk].tag,last_token)
                    if my_parent[0][jj][kk].tag == last_token:
                        o_num_existing_last_tag += 1
                        if m_debug_mode:
                            print(function_name,"name_index,jj,kk,my_parent[0][jj][kk].tag_EQUAL_last_token,o_num_existing_last_tag",name_index,jj,kk,my_parent[0][jj][kk].tag,last_token,o_num_existing_last_tag)
                if m_debug_mode:
                    print(function_name,"name_index,jj,partial_xpath,num_existing_authors,o_num_existing_last_tag,last_token",name_index,jj,partial_xpath,num_existing_authors,last_token)

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

        function_name = self.m_module_name + 'polulate_list_values_with_values:'

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

        if m_debug_mode:
            print(function_name,"fourth_token_from_last,third_token_from_last,token_before_last,last_token",fourth_token_from_last,third_token_from_last,token_before_last,last_token)
        # Only process the attr_xpath if the last token is in list_of_tags_to_process list and the fourth_token_from_last is 'record'

        if fourth_token_from_last == 'record' and third_token_from_last in list_of_tags_to_process_2 and last_token in list_of_tags_to_process:
            if m_debug_mode:
                print(function_name,"i_doc.tag",i_doc.tag)
            # Define who the parent is.
            #my_parent = i_doc.xpath('record/authors')
            my_parent = i_doc.xpath('record/' + third_token_from_last)   # 'record/authors' or 'record/editors'
            num_children_initial = len(list(my_parent[0]))
            if m_debug_mode:
                print(function_name,"my_parent",my_parent)
                print(function_name,"num_children_initial",num_children_initial)
                print(function_name,"type(my_parent)",type(my_parent))
                print(function_name,"len(my_parent)",len(my_parent))
                print(function_name,"list(my_parent)",list(my_parent))

            # Create a list of indices containing where in the list of parents, e.g. 'authors' does the 'author' occur.
            # Create a list of indices containing where in the list of parents, e.g. 'contributor' does the 'contributor' occur.
            indices_list_where_author_contributor_added = []

            for name_index,name_value in enumerate(i_value):
                if m_debug_mode:
                    print(function_name,"INSPECT_VARIABLE:name_index,name_value,len(value)",name_index,name_value,len(i_value))
                    print(function_name,"type(my_parent[0])",type(my_parent[0]))
                    print(function_name,"my_parent[0].tag)",my_parent[0].tag)
                    print(function_name,"my_parent[0].xpath('author')",my_parent[0].xpath('author'))
                # For each parent, which is 'authors' or 'editor', create a child call 'author' or 'editor' and add last_name to author child. 
                num_existing_authors = len(list(my_parent[0]))  # This could also be num_existing_editors if we are dealing with editor tag
                existing_authors_tags = []
                for my_element in list(my_parent[0]):
                    existing_authors_tags.append(my_element.tag)
                if m_debug_mode:
                    print(function_name,"name_index,third_token_from_last,num_existing_authors,LEN_VALUE,last_token",name_index,third_token_from_last,num_existing_authors,len(i_value),last_token)

                # Count how many existing authors with the same children.
                num_existing_last_tag = self._count_existing_children_with_same_tag(name_index,num_existing_authors,my_parent,last_token)

                if m_debug_mode:
                    print(function_name,"name_index,third_token_from_last,last_token,num_existing_authors,num_existing_last_tag",name_index,third_token_from_last,last_token,num_existing_authors,num_existing_last_tag)

                if num_existing_last_tag < len(i_value): 
                    my_author = list(my_parent[0])
                    if m_debug_mode:
                        print(function_name,"#0001,name_index,last_token,len(my_author)",name_index,last_token,len(my_author))

                    # Save indices in 'authors' or 'contributors' where the last_token was added.
                    if (name_index+num_children_initial) > len(i_value): 
                        indices_list_where_author_contributor_added.append(name_index+num_children_initial-len(i_value))
                        #print(function_name,"#0001,WOULD_OF_ADDED_INDEX_GREATER:",name_index,num_children_initial,(name_index+num_children_initial),len(i_value),indices_list_where_author_contributor_added[name_index],len(indices_list_where_author_contributor_added),indices_list_where_author_contributor_added)
                    elif (name_index+num_children_initial) == len(i_value): 
                        #indices_list_where_author_contributor_added.append(name_index)
                        if name_index == 0:
                            indices_list_where_author_contributor_added.append(0)
                        else:
                            indices_list_where_author_contributor_added.append(len(i_value))
                        #print(function_name,"#0001,WOULD_OF_ADDED_INDEX_EQUAL:",name_index,num_children_initial,(name_index+num_children_initial),len(i_value),indices_list_where_author_contributor_added[name_index],len(indices_list_where_author_contributor_added),indices_list_where_author_contributor_added)
                    else:
                        indices_list_where_author_contributor_added.append(name_index+num_children_initial)
                        #print(function_name,"#0001,WOULD_OF_ADDED_INDEX_LESSER:",name_index,num_children_initial,(name_index+num_children_initial),len(i_value),indices_list_where_author_contributor_added[name_index],len(indices_list_where_author_contributor_added),indices_list_where_author_contributor_added)

                    reuse_flag = False
                    #print(function_name,"CREATE_CHILD_CHECK",my_parent[0].tag,token_before_last,num_existing_authors,len(i_value))

                    if m_house_keeping_dict[my_parent[0].tag] < len(i_value) and num_children_initial < len(i_value):
                        m_house_keeping_dict[my_parent[0].tag] = m_house_keeping_dict[my_parent[0].tag] + 1
                        # If this is the first time in the loop, we have no 'author' or 'contributor' yet, we will create a child.
                        # e.g. create a child 'author' to 'authors' then create 'last_name' to 'author'
                        # e.g. create a child 'contributor' to 'contributor' then create 'last_name' to 'contributor'
                        #print(function_name,"create_child",my_parent[0].tag,token_before_last,last_token,len(list(my_parent[0])))
                        #print(function_name,"CREATE_CHILD",my_parent[0].tag,token_before_last,num_existing_authors,len(i_value))
                        my_author = etree.SubElement(my_parent[0],token_before_last) # Create 'author' to 'authors' or 'contributor' to 'contribuors'
                        # For contributors, we also add <contributor_type>Editor</contributor_type>
                        if third_token_from_last == 'contributors':
                            my_child  = etree.SubElement(my_author,'contributor_type')
                            my_child.text = 'Editor'

                        #print(function_name,"create_child_child",my_parent[0].tag,my_author.tag,last_token,len(list(my_parent[0])))
                        my_child  = etree.SubElement(my_author,last_token) # Create 'last_name' to 'author' or 'last_name' to 'contributor'
                        first_time_flag = False
                    else:
                        reuse_flag = True
                        m_house_keeping_dict[my_parent[0].tag] = m_house_keeping_dict[my_parent[0].tag] + 1
                        my_author = list(my_parent[0])
                        # Create a new 'author' or 'contributor' child to 'authors' or 'contributors'
                        #print(function_name,"reuse_create_child,len(list(my_parent[0]))",my_parent[0].tag,token_before_last,last_token,len(list(my_parent[0])))
                        #print(function_name,"REUSE_CREATE_CHILD,len(list(my_parent[0]))",my_parent[0].tag,token_before_last,last_token,len(list(my_parent[0])))
                        #print(function_name,"my_author",my_author)
                        #print(function_name,"name_index,last_token,len(my_author),my_parent[0].tag",name_index,last_token,len(my_author),my_parent[0].tag)
                        #print(function_name,"name_index,indices_list_where_author_contributor_added,last_token",name_index,indices_list_where_author_contributor_added,last_token)
                        my_child  = etree.SubElement(my_author[indices_list_where_author_contributor_added[name_index]],last_token) # Create 'last_name' to 'author' or 'last_name' to 'contributor'

                    #print(function_name,"MY_PARENT_TAG:my_parent[0].tag",name_index,my_parent[0].tag,token_before_last,last_token,m_house_keeping_dict[my_parent[0].tag])

                    # We know have 'last_name' or 'first_name' created, we can fill in the actual value.
                    my_child.text = name_value.lstrip().rstrip()   # The child of authors/author/ has a child called last_name of value 'Maki'.
                else:
                    pass  # Nothing to do.

                num_new_authors = len(list(my_parent[0]))  # Check to see how many authors have not added.
                if m_debug_mode:
                    print(function_name,"name_index,third_token_from_last,num_existing_authors,num_new_authors,last_token",name_index,third_token_from_last,num_existing_authors,num_new_authors,last_token)
                    print(function_name,"INSPECT_VARIABLE:name_index,name_value,my_child.text",name_index,name_value,my_child.text)
                    #print(function_name,"INSPECT_VARIABLE:name_index,name_value,num_sibblings,num_chidren_initial",name_index,name_value,num_sibblings,num_children_initial)
                    print(function_name,"INSPECT_VARIABLE:name_index,name_value,num_chidren_initial",name_index,name_value,num_children_initial)
            # end for name_index,name_value in enumerate(i_value):
            num_children_total = len(list(my_parent[0])) # Check to see how many children have been added to the parent.
            if m_debug_mode:
                print(function_name,"num_children_initial,num_children_total,third_token_from_last,last_token",num_children_initial,num_children_total,third_token_from_last,last_token)
        return(i_doc)

    #------------------------------                                                                                                 
    #------------------------------                                                                                                 
    def populate_doi_xml_with_values(self,dict_fixedList, xmlText, attr_xpath, i_value):                                      
        # Given an XML object xmlText, this function will update the attr_xpath in xmlText with the new input i_value.
        # Since we don't know the type of xmlText (bytes or text), we may have to encode xmlText from string to bytes.
        function_name = self.m_module_name + 'populate_doi_xml_with_values:'
        global m_debug_mode
        elm = None # Set to None so the value can be checked before printing.
        if m_debug_mode:
            print(function_name,"Append","PopulateDOIXMLWithValues.xmlText: ",xmlText,)                                
            print(function_name,"Append","PopulateDOIXMLWithValues.attr_xpath: " + attr_xpath + "\n")
            print(function_name,"INSPECT_VARIABLE:Append","PopulateDOIXMLWithValues.value: ",i_value)
            print(function_name,"xmltext",len(xmlText),xmlText)
            print(function_name,"INSPECT_VARIABLE:len(xmltext)",len(xmlText))
            print(function_name,"dict_fixedList",dict_fixedList)
            print(function_name,"dict_fixedList",len(dict_fixedList))

        #------------------------------                                                                                             
        # Populate the xml attribute with the specified value                                                                       
        #------------------------------                                                                                             
        if m_debug_mode:
            print(function_name,"type(xmlText)",type(xmlText))

        if isinstance(xmlText,bytes):
            doc = etree.fromstring(xmlText)
        else:
            doc = etree.fromstring(xmlText.encode()) # Have to change the text to bytes then encode it to get it to work.

        if m_debug_mode:
            print(function_name,"INSPECT_VARIABLE:attr_xpath",attr_xpath)
            print(function_name,"type(attr_xpath)",type(attr_xpath))
            print(function_name,"len(attr_xpath)",len(attr_xpath))
            print(function_name,"INSPECT_VARIABLE:doc.xpath(attr_xpath)[",doc.xpath(attr_xpath))
        if len(doc.xpath(attr_xpath)) == 0:
            if m_debug_mode:
                print(function_name,"INSPECT_VARIABLE:EXPATH_BAD:doc.xpath(attr_xpath)",doc.xpath(attr_xpath))
                print(function_name,"ERROR:LEN_XPATH_IS_ZERO:len(doc.xpath(attr_xpath)) == 0")
                print(function_name,"ERROR:attr_xpath",attr_xpath)

            # Because the document tree 'doc' does not have the xpath already, will attempt to populate the 'first_name' and 'last_name' tags.

            doc = self.populate_list_values_with_values(doc,attr_xpath,i_value)

        else:

            if m_debug_mode:
                print(function_name,"INSPECT_VARIABLE:EXPATH_GOOD:doc.xpath(attr_xpath)[0].text",doc.xpath(attr_xpath)[0].text)
            elm = doc.xpath(attr_xpath)[0]                                                              
            if m_debug_mode:
                print(function_name,"INSPECT_VARIABLE:value",i_value)
                print(function_name,"INSPECT_VARIABLE:type(i_value)",type(i_value))
                print(function_name,"INSPECT_VARIABLE:afor_set:elm.text",elm.text)

            if isinstance(i_value,list):
                if 'last_name' in attr_xpath:
                    #elm.text = 'zzztop'
                    print(function_name,"doc.xpath(attr_xpath)",doc.xpath(attr_xpath))
                    print(function_name,"len(doc.xpath(attr_xpath))",len(doc.xpath(attr_xpath)))
                    exit(0)
                    for index,name_value in enumerate(i_value):
                        print(function_name,"INSPECT_VARIABLE:index,name_value,len(i_value)",index,name_value,len(i_value))

                        #elm = doc.xpath(attr_xpath)[0]
                        elm = doc.xpath(attr_xpath)[index]
                        elm.text = name_value
                    #'elm.text = bytes([x.encode('UTF8') for x in value])
                if 'first_name' in attr_xpath:
                    #elm.text = bytes([x.encode('UTF8') for x in value])
                    #elm.text = 'R.'
                    for index,name_value in enumerate(i_value):
                        print(function_name,"INSPECT_VARIABLE:index,name_value,len(i_value)",index,name_value,len(i_value))
                        #elm = doc.xpath(attr_xpath)[0]
                        elm = doc.xpath(attr_xpath)[index]
                        elm.text = name_value
            else: 
                elm.text = i_value

        if m_debug_mode:
            if elm is not None: 
                print(function_name,"INSPECT_VARIABLE:after_set:elm.text",elm.text)

        etree.indent(doc,space="    ")  # Re-indent because we may have new levels added.
        sOutText = etree.tostring(doc,pretty_print=True)
        if m_debug_mode:
            print(function_name,"type(doc)",type(doc))
            # The encoding='unicode' converts the doc from bytes to string otherwise you won't actually the document on separate lines.
            sOutTextTemp = etree.tostring(doc,pretty_print=True,encoding='unicode')
            print(function_name,"sOutTextTemp")
            print(sOutTextTemp)

        return(sOutText)

if __name__ == '__main__':
    global m_debug_mode
    function_name = 'main'
    doiOutputUtil = DOIOutputUtil()
