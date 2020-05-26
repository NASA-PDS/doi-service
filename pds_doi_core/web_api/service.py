from flask import Flask
from flask import request
from flask_restplus import Api, Resource, fields
from pds_doi_core.util.general_util import get_logger

logger = get_logger()

flask_app = Flask(__name__)
app = Api(app=flask_app)

name_space = app.namespace('dois', description='PDS DOI Core function restFull API')


doi_summary = app.model('doi_summary', {
    'doi': fields.String,
    'lid' : fields.String,
    'vid' : fields.String,
    'submitter': fields.String,
    'status': fields.String,
    'creation_date': fields.String,
    'update_date': fields.DateTime(dt_format='rfc822'),
})

doi_record = app.inherit('doi_record', doi_summary, {
    'record': fields.String,
    'message': fields.String
})


@name_space.route("/")
class MainClass(Resource):

    @app.marshal_with(doi_summary, as_list=True)
    @app.doc(description="list the DOIs",
             responses={200: 'OK', 500: 'Internal error'},
             params={
                 "submitter": "the submitter of the doi identifier, filter the DOIs (optional)",
                 "node" : "the node which is cited as contributor of the DOI, filter the DOIs (optional), "
                          " use pds steward ids see "
                          " https://pds.nasa.gov/datastandards/documents/dd/current/PDS4_PDS_DD_1D00.html#d5e72146",
                 "lid" : "pds identifier, filter the DOIs (optional)",
                 "vid": "pds version, filter the DOIs (optional)"
             }
             )
    def get(self):
        return {
            "status": "To Be Implemented"
        }

    @app.marshal_with(doi_record)
    @app.doc(description="submit a DOI as reserved or draft, the payload is the record to be submitted."
                         "You can upload information in different formats: PDS4 label, csv or xls."
                         "You can also read csv/xls client side and submit DOI request line by line in a Json object.",
             responses={200: 'Success', 201: "Success", 400: 'Invalid Argument', 500: 'Internal error'},
             params={
                 'node': "the node which is cited as contributor of the DOI, filter the DOIs (optional), "
                         " use pds steward ids see "
                         " https://pds.nasa.gov/datastandards/documents/dd/current/PDS4_PDS_DD_1D00.html#d5e72146",
                 'action': '"reserve" | "draft"',
                 'format': '"pds4" | "json" | "csv" | "xls" ',
                 'url': 'url of the resource to be loaded (optional)'
             })
    def post(self):

        logger.info(f"post request parameters: {request.args}")
        logger.info(f"post request parameters: {request.args['node']}")
        logger.info(f"post request content: {request.data}")

        return {
            "status": "To be implemented"
        }


@name_space.route('/<doi_prefix>/<doi_suffix>', doc={'params':{'doi_prefix': 'The prefix of the DOI identifier',
                                                               'doi_suffix': 'The suffix of the DOI identifier'}})
class DoiClass(Resource):

    @app.marshal_with(doi_record, envelope='resource')
    @app.doc(description="get a DOI record",
             responses={200: 'OK', 404: 'Not existing', 500: 'Internal error'})
    def get(self):
        return {
            "status": "To be implemented"
        }

    @app.marshal_with(doi_record, envelope='resource')
    @app.doc(description="update a DOI record. ",
             responses={200: 'OK', 400: 'Invalid Argument', 404: 'Not existing', 500: 'Internal error'},
             params={
                 'submitter' : "the submitter of the doi identifier",
                 'node': 'pds node in charge of the dataset, '
                 ' use pds steward id see '
                 ' https://pds.nasa.gov/datastandards/documents/dd/current/PDS4_PDS_DD_1D00.html#d5e72146',
                 'format': '"pds4" | "json"',
                 'url': 'url of the resource to be loaded (optional)'
             }
             )
    def put(self):
        return {
            "status": "To be implemented"
        }


@name_space.route('/<doi_prefix>/<doi_suffix>/release', doc={'params': {
                                                                    'doi_prefix': 'The prefix of the DOI identifier',
                                                                    'doi_suffix': 'The suffix of the DOI identifier'}})
class DoiClass(Resource):

    @app.marshal_with(doi_record, envelope='resource')
    @app.doc(description="release a DOI record",
             responses={200: 'OK', 400: 'Can not be released', 404: 'Not existing', 500: 'Internal error'})
    def get(self):
        return {
            "status": "To be implemented"
        }


@name_space.route('/<doi_prefix>/<doi_suffix>/deactivate', doc={'params': {
                                                                    'doi_prefix': 'The prefix of the DOI identifier',
                                                                    'doi_suffix': 'The suffix of the DOI identifier'}})
class DoiClass(Resource):

    @app.marshal_with(doi_record, envelope='resource')
    @app.doc(description="deactivate a DOI record",
             responses={200: 'OK', 400: 'Can not be deactivated', 404: 'Not existing', 500: 'Internal error'})
    def get(self):
        return {
            "status": "To be implemented"
        }


def main():
    flask_app.run()


if __name__ == "__main__":
    main()