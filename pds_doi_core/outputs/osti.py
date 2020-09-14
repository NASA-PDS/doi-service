import pystache
import copy
import datetime
from pds_doi_core.util.general_util import get_logger
from pds_doi_core.entities.doi import Doi

logger = get_logger(__name__)


class DOIOutputOsti:
    def create_osti_doi_draft_record(self, doi: Doi):
        # The format of 'publication_date' should match the input to 'release' action.
        doi_fields = copy.copy(doi.__dict__)
        doi_fields['publication_date'] = doi.publication_date.strftime('%Y-%m-%d')
        doi_fields['keywords'] = "; ".join(doi.keywords)
        renderer = pystache.Renderer()
        return renderer.render_path('config/DOI_template_20200407-mustache.xml', doi_fields)


    def create_osti_doi_reserved_record(self, dois: list):
        doi_fields_list = []
        for doi in dois:
            doi_fields = copy.copy(doi.__dict__)
            logger.debug(f"convert datetime {doi_fields['publication_date']}")
            logger.debug(f"type(doi_fields['publication_date') {type(doi_fields['publication_date'])}")
            # It is possible that the 'publication_date' type is string if the input is string, check for it here.
            if not 'str' in str(type(doi_fields['publication_date'])):
                doi_fields['publication_date'] = doi_fields['publication_date'].strftime('%Y-%m-%d')
            doi_fields_list.append(doi_fields)

        renderer = pystache.Renderer()
        return renderer.render_path('config/DOI_IAD2_reserved_template_20200205-mustache.xml', {'dois': doi_fields_list})

    def create_osti_doi_release_record(self, doi: Doi):
        doi_fields = copy.copy(doi.__dict__)
        renderer = pystache.Renderer()
        # Convert 'date_record_added' to proper format if value is not None, otherwise use today's date.
        if 'date_record_added' in doi_fields and doi_fields['date_record_added'] is not None:
            doi_fields['date_record_added'] = doi_fields['date_record_added'].strftime('%Y-%m-%d') 
        else:
            doi_fields['date_record_added'] = datetime.date.today().strftime('%Y-%m-%d')
  
        return renderer.render_path('config/DOI_template_20200407-mustache.xml', doi_fields)
