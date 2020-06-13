import pystache

from pds_doi_core.util.general_util import get_logger

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


