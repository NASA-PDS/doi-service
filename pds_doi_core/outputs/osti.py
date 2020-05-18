import pystache


def create_osti_doi_record(doi_fields):
    doi_fields['publication_date'] = doi_fields['publication_date'].strftime('%m/%d/%Y')
    doi_fields['keywords'] = "; ".join(doi_fields['keywords'])
    renderer = pystache.Renderer()
    return renderer.render_path('config/DOI_template_20200407-mustache.xml', doi_fields)