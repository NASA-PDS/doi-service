from pds_doi_service.core.outputs.schemaentities.rights import Rights


class DOIDataCiteRights(Rights):
    @classmethod
    def get_label_mappings(cls):
        return {
            "text": "rights",
            "uri": "rightsUri",
            "identifier": "rightsIdentifier",
            "identifier_scheme": "rightsIdentifierScheme",
            "scheme_uri": "schemeUri",
            "language": "lang",
        }
