#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#

# This file DOIWebServer.py is the web server for DOI services.
#
# pip install -r requirements.txt
# export FLASK_APP=DOIWebServer.py
# python3 -m flask run
#
# Example from curl:
#
# curl "http://127.0.0.1:5000/create_osti_label?target_url="https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml"&contributor='Cartography+and+Imaging+Sciences+Discipline'" 
#
# A valid XML text will be returned.  A redirect can be done to capture the output with '> my_out.xml'
#
# Notes:
#
#   1. Value for target_url keyword must be enclosed in single or double quotes.
#   2. Value for contributor keyword cannot have spaces and they must be replaced with '+' or %20

from flask import Flask;
from flask import request;

app = Flask(__name__)
@app.route('/')

@app.route('/')
def index():
    return('Index Page')

@app.route('/hello')
def hello():
    return('Hello, World!');

@app.route('/create_osti_label/<myurl>',methods=['GET','POST'])
def create_osti_label(myurl):
    if request.method == 'POST':
        my_file = request.files['the_file']
    #from DOICoreServices import DOICoreServices;
    #doiCoreServices = DOICoreServices() 
    #contributor_value = 'Cartography and Imaging Sciences Discipline'
    #target_url = 'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml'
    #o_doi_label = doiCoreServices.CreateDOILabel(target_url,contributor_value);
    #return(o_doi_label);
    return('Hello, World from create_osti_label!,method=' + request.method + " myurl [" + myurl + "]");

@app.route('/create_osti_label')
def create_osti_label_2():
    function_name = 'create_osti_label_2:'
    if request.method == 'POST':
        my_file = request.files['the_file']
    # Get the target_url and remove any single or double quotes.
    target_url        = request.args.get('target_url',default='target_url_zzz',type=str);
    target_url        = target_url.replace('"','').replace("'",'');
    # If the value contains single or double quotes, remove them.
    contributor_value = request.args.get('contributor',default='contributor_zzz',type=str);
    print(function_name,"contributor_value",contributor_value);
    contributor_value = contributor_value.replace('%20',' ').replace('%27','');   # Replace %20 with ' ', and replace "'" with ''
    print(function_name,"contributor_value",contributor_value);
    from pds_doi_core.cmd.DOICoreServices import DOICoreServices;
    doiCoreServices = DOICoreServices() 
    #contributor_value = 'Cartography and Imaging Sciences Discipline'
    #target_url = 'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml'
    o_doi_label = doiCoreServices.CreateDOILabel(target_url,contributor_value);
    return(o_doi_label);
    #return('Hello, World from create_osti_label_2!,method=' + request.method + " target_url [" + target_url + "] contributor_value [" + contributor_value);


@app.route('/reserve_osti_label')
def reserve_osti_label():
    function_name = 'reserve_osti_label:'
    if request.method == 'POST':
        my_file = request.files['the_file']
    # Get the target_url and remove any single or double quotes.
    target_url        = request.args.get('target_url',default='target_url_zzz',type=str);
    target_url        = target_url.replace('"','').replace("'",'');
    # If the value contains single or double quotes, remove them.
    contributor_value = request.args.get('contributor',default='contributor_zzz',type=str);
    print(function_name,"contributor_value",contributor_value);
    contributor_value = contributor_value.replace('%20',' ').replace('%27','');   # Replace %20 with ' ', and replace "'" with ''
    print(function_name,"contributor_value",contributor_value);
    from pds_doi_core.cmd.DOICoreServices import DOICoreServices;
    doiCoreServices = DOICoreServices()
    #contributor_value = 'Cartography and Imaging Sciences Discipline'
    #target_url = 'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml'
    #print(function_name,"target_url",target_url);
    publisher_value = 'dummy_publisher_value';
    #print(function_name,"contributor_value",contributor_value);
    o_doi_label = doiCoreServices.reserve_doi_label(target_url, publisher_value, contributor_value);
    #o_doi_label = 'hello_world'
    #print(function_name,"o_doi_label",o_doi_label);

    return(o_doi_label);
    #return('Hello, World from create_osti_label_2!,method=' + request.method + " target_url [" + target_url + "] contributor_value [" + contributor_value);



#def hello_world():
#    return('Hello, World!');
