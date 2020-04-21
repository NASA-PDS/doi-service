from flask import Flask
from flask_restplus import Api, Resource, fields

flask_app = Flask(__name__)
app = Api(app=flask_app)

name_space = app.namespace('dois', description='PDS DOI Core function restFull API')

doi_summary = app.model('doi_summary', {
    'id': fields.String,
    'status': fields.String,
    'owner': fields.String,
    'date': fields.DateTime(dt_format='rfc822'),
})

doi_record = app.inherit('doi_record', doi_summary, {
    'record': fields.String,
    'message': fields.String
})


@name_space.route("/")
class MainClass(Resource):

    @app.marshal_with(doi_summary, as_list=True)
    @app.doc(description="list the DOI of the user",
             responses={200: 'OK', 500: 'Internal error'}
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
                 'node': 'pds node in charge of the dataset',
                 'status': '"reserved" | "draft"',
                 'format': '"PDS4" | "Json" | "csv" | "xls" ',
                 'url': 'url of the resource to be loaded (optional)'
             })
    def post(self):
        return {
            "status": "To be implemented"
        }


@name_space.route('/<id>', doc={'params':{'id': 'The DOI identifier (without the prefix)'}})
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
                 'node': 'pds node in charge of the dataset',
                 'status': '"reserved" | "draft"',
                 'format': '"PDS4" | "Json"',
                 'url': 'url of the resource to be loaded (optional)'
             }
             )
    def put(self):
        return {
            "status": "To be implemented"
        }


@name_space.route('/<id>/release', doc={'params':{'id': 'The DOI identifier (without the prefix)'}})
class DoiClass(Resource):

    @app.marshal_with(doi_record, envelope='resource')
    @app.doc(description="release a DOI record",
             responses={200: 'OK', 400: 'Can not be released', 404: 'Not existing', 500: 'Internal error'})
    def get(self):
        return {
            "status": "To be implemented"
        }


@name_space.route('/<id>/deactivate', doc={'params':{'id': 'The DOI identifier (without the prefix)'}})
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