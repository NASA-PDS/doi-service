import argparse
import pyclbr
from pds_doi_core.actions import DOICoreAction
from pds_doi_core.actions import *


def add_default_action_arguments(_parser,action_type):
    _parser.add_argument('-c', '--node-id',
                         help='The pds discipline node in charge of the submission of the DOI',
                         required=True,
                         metavar='"img"')
    _parser.add_argument('-i', '--input',
                         help='A pds4 label local or on http, a xls spreadsheet, a database file'
                              ' is also supported to reserve a list of doi',
                         required=True,
                         metavar='input/bundle_in_with_contributors.xml')
    _parser.add_argument('-s', '--submitter-email',
                         help='The email address of the user performing the action for these services',
                         required=True,
                         metavar='"my.email@node.gov"')
    _parser.add_argument('-t', '--target',
                         help='the system target to mint the DOI',
                         required=False,
                         default='osti',
                         metavar='osti')



