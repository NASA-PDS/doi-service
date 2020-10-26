import datetime
from lxml import etree

from pds_doi_service.core.util.general_util import get_logger

logger = get_logger(__name__)

class DOIReleaseOstiUtil:
    # This class DOIReleaseOstiUtil contains utility functions specific to the 'reserve' action to:
    #
    #   1.  remove empty fields from a document that has already been rendered,
    #   2.  rebuild the render document with 'trimmed' fields.

    def remove_empty_fields_from_render_doc(self, render_doc):
        # It is possible that the some fields in render_doc may be emptied if the dictionary in doi_record_list does not
        # have the particular fields.  Example:
        #   
        #    <title></title>
        #    <doi></doi>
        #    <publication_date></publication_date>
        #    <authors></authors>
        #
        # These fields will cause OSTI to reject the PUT request without any meaningful error messages.  It will simply
        # says 'no records submitted'.

        o_response_dicts = []

        doc = etree.fromstring(render_doc.encode())  # The content of render_doc may have preamble.  Change to bytes.
        my_root = doc.getroottree()

        # Trim down input to just fields we want.
        element_record = 0
        for element in my_root.iter():
            if element.tag == 'record':
                my_record = my_root.xpath(element.tag)[0]

                response_dict = {}  # This dictionary will be added to o_response_dicts when all fields have been extracted.

                if my_root.xpath('record/title')[element_record] is not None and my_root.xpath('record/title')[element_record].text:
                    response_dict['title']               = my_root.xpath('record/title')[element_record].text
                if my_root.xpath('record/id')[element_record] is not None and len(my_root.xpath('record/id')[element_record].text) > 0:
                    response_dict['id']                  = my_root.xpath('record/id')[element_record].text
                if my_root.xpath('record/site_url')[element_record] is not None and len(my_root.xpath('record/site_url')[element_record].text) > 0:
                    response_dict['site_url']                  = my_root.xpath('record/site_url')[element_record].text
                if my_root.xpath('record/doi')[element_record] is not None and my_root.xpath('record/doi')[element_record].text:
                    response_dict['doi']                 = my_root.xpath('record/doi')[element_record].text
                if my_root.xpath('record/publication_date')[element_record] is not None and my_root.xpath('record/publication_date')[element_record].text:
                    response_dict['publication_date']      = my_root.xpath('record/publication_date')[element_record].text
                if my_root.xpath('record/product_type')[element_record] is not None and my_root.xpath('record/product_type')[element_record].text:
                    response_dict['product_type']          = my_root.xpath('record/product_type')[element_record].text
                if my_root.xpath('record/product_type_specific')[element_record] is not None and my_root.xpath('record/product_type_specific')[element_record].text:
                    response_dict['product_type_specific'] = my_root.xpath('record/product_type_specific')[element_record].text

                if my_root.xpath('record/authors'):
                    num_authors = len(my_root.xpath('record/authors')[0])
                    logger.debug(f"num_authors {num_authors}")

                    # Only create an entry for 'authors' in response_dict if there are any sub fields 'record/authors'
                    if num_authors > 0:
                        response_dict['authors'] = []
                        for ii in range(num_authors):
                            one_author = {}
                            author_element = my_root.xpath('record/authors')[0]

                            # No need to check for existence of 'first_name' and 'last_name' since schematron would already have done that validation.
                            one_author['first_name'] = author_element.xpath('author/first_name')[ii].text
                            one_author['last_name']  = author_element.xpath('author/last_name')[ii].text
                            response_dict['authors'].append(one_author)

                        logger.debug("response_dict['authors'] {response_dict['authors']}")
                    else:
                        pass

                if my_root.xpath('record/related_identifiers'):
                    num_identifiers = len(my_root.xpath('record/related_identifiers')[0])
                    logger.debug(f"num_identifiers {num_identifiers}")

                    # Only create an entry for 'related_identifiers' if there are any sub fields 'record/related_identifiers'
                    if num_identifiers > 0:
                        response_dict['related_identifiers'] = []
                        for ii in range(num_identifiers):
                            one_identifier = {}
                            identifier_element = my_root.xpath('record/related_identifiers')[0]

                            # No need to check for existence of 'identifier_value' and 'identifier_type' since schematron would already have done that validation.
                            one_identifier['identifier_value'] = identifier_element.xpath('related_identifier/identifier_value')[ii].text 
                            one_identifier['identifier_type']  = identifier_element.xpath('related_identifier/identifier_type')[ii].text 
                            one_identifier['relation_type']    = identifier_element.xpath('related_identifier/relation_type')[ii].text 

                            response_dict['related_identifiers'].append(one_identifier)
                        logger.debug("response_dict['related_identifiers'] {response_dict['related_identifiers']}")
                    else:
                        pass

                o_response_dicts.append(response_dict)
                element_record += 1


        logger.debug(f"o_response_dicts {o_response_dicts}")

        return o_response_dicts

    def rebuild_render_doc(self, render_dict_list):
        o_render_doc = None 

        logger.debug(f"render_dict_list {render_dict_list}{len(render_dict_list)}")

        render_text_list = [] 
        render_text_list.append("<records>")
        for dict_index, render_dict in enumerate(render_dict_list): 
            render_text_list.append("<record>")
            render_keys = list(render_dict.keys())
            logger.debug(f"render_keys {render_keys} {len(render_keys)}")
            for render_key in render_keys:
                # The keys 'related_identifiers' and 'authors' have extra sub fields and need to be rendered differently.
                if render_key == 'related_identifiers':
                    render_text_list.append("<related_identifiers>")
                    for ii in range(len(render_dict[render_key])):
                       render_text_list.append("    <related_identifier>")
                       render_text_list.append("       <identifier_type>"  + render_dict['related_identifiers'][ii]['identifier_type']  + "</identifier_type>")
                       render_text_list.append("       <identifier_value>" + render_dict['related_identifiers'][ii]['identifier_value'] + "</identifier_value>")
                       render_text_list.append("       <relation_type>"    + render_dict['related_identifiers'][ii]['relation_type']    + "</relation_type>")
                       render_text_list.append("    </related_identifier>")
                    render_text_list.append("</related_identifiers>")
                elif render_key == 'authors':
                    render_text_list.append("<authors>")
                    for ii in range(len(render_dict[render_key])):
                        render_text_list.append("    <author>")
                        render_text_list.append("        <first_name>" + render_dict['authors'][ii]['first_name'] + "</first_name>")
                        render_text_list.append("        <last_name>"  + render_dict['authors'][ii]['last_name' ] + "</last_name>")
                        render_text_list.append("    </author>")
                    render_text_list.append("</authors>")
                elif render_key == 'publication_date':
                    # If the 'publication_date' is provided, validate it.
                    try:
                        datetime.datetime.strptime(render_dict['publication_date'], '%Y-%m-%d')
                        render_text_list.append("<" + render_key + ">" + render_dict[render_key] + "</" + render_key + ">")
                    except ValueError:
                        logger.error(f"Incorrect date format, should be YYYY-MM-DD.  Provided value {render_dict['publication_date']}")
                        raise ValueError(f"Incorrect date format, should be YYYY-MM-DD.  Provided value {render_dict['publication_date']}") from None
                else:
                    render_text_list.append("<" + render_key + ">" + render_dict[render_key] + "</" + render_key + ">")


            render_text_list.append("</record>")
        render_text_list.append("</records>")
        logger.debug(f"render_text_list {render_text_list} {len(render_text_list)}")

        o_render_doc = '\n'.join(render_text_list)  # Combine all values in render_text_list for a complete document.
        logger.debug(f"o_render_doc {o_render_doc}")

        return o_render_doc
