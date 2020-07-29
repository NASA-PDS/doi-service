import pystache

from pds_doi_core.util.general_util import get_logger
from pds_doi_core.entities.doi import Doi

#from pds_doi_core.outputs.osti_reserve import DOIReserveOstiUtil
from pds_doi_core.outputs.osti_release import DOIReleaseOstiUtil

logger = get_logger(__name__)


class DOIOutputOsti:
    def create_osti_doi_draft_record(self, doi: Doi):
        # The format of 'publication_date' should match the input to 'release' action.
        doi_fields = doi.__dict__
        doi_fields['publication_date'] = doi.publication_date.strftime('%Y-%m-%d')
        doi_fields['keywords'] = "; ".join(doi.keywords)
        renderer = pystache.Renderer()
        return renderer.render_path('config/DOI_template_20200407-mustache.xml', doi_fields)


    def create_osti_doi_reserved_record(self, dois: list):
        doi_fields_list = []
        for doi in dois:
            doi_fields = doi.__dict__
            logger.debug(f"convert datetime {doi_fields['publication_date']}")
            doi_fields['publication_date'] = doi_fields['publication_date'].strftime('%m/%d/%Y')
            doi_fields_list.append(doi_fields)

        renderer = pystache.Renderer()
        return renderer.render_path('config/DOI_IAD2_reserved_template_20200205-mustache.xml', {'dois': doi_fields_list})
