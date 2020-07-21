import pystache

from pds_doi_core.util.general_util import get_logger

#from pds_doi_core.outputs.osti_reserve import DOIReserveOstiUtil
from pds_doi_core.outputs.osti_release import DOIReleaseOstiUtil

logger = get_logger(__name__)


class DOIOutputOsti:
    def create_osti_doi_draft_record(self, doi_fields):
        doi_fields['publication_date'] = doi_fields['publication_date'].strftime('%m/%d/%Y')
        doi_fields['keywords'] = "; ".join(doi_fields['keywords'])
        renderer = pystache.Renderer()
        return renderer.render_path('config/DOI_template_20200407-mustache.xml', doi_fields)


    def create_osti_doi_reserved_record(self, doi_record_list):
        for doi_record in doi_record_list:
            logger.debug(f"convert datetime {doi_record['publication_date']}")
            doi_record['publication_date'] = doi_record['publication_date'].strftime('%m/%d/%Y')

        renderer = pystache.Renderer()
        return renderer.render_path('config/DOI_IAD2_reserved_template_20200205-mustache.xml', {'dois': doi_record_list})

    def create_osti_doi_release_record(self, doi_record_list):
        renderer = pystache.Renderer()
        release_util = DOIReleaseOstiUtil()

        # Render the document using the provided template.  Because the template is 'large' to accommodate all possible fields
        # that the user can provide, it may be necessary to trim the rendered document.
        first_render_doc = renderer.render_path('config/DOI_IAD2_released_template_20200715-mustache.xml', {'dois': doi_record_list})

        # It is possible that the some fields in first_render_doc may be emptied if the dictionary in doi_record_list does not
        # have the particular fields.  Example:
        #
        #    <title></title>
        #    <doi></doi>
        #    <publication_date></publication_date>
        #
        # If that is the case, the field representing the tag in first_render_doc will need to be removed
        # as OSTI does not behave well if they are empty.

        sanitized_dicts = release_util.remove_empty_fields_from_render_doc(first_render_doc)

        # Rebuild the document with the sanitized_dicts should now only contain fields that are not empty.
        o_render_doc = release_util.rebuild_render_doc(sanitized_dicts)

        return o_render_doc
