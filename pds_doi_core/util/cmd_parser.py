import argparse


def add_default_action_arguments(_parser):
    _parser.add_argument('-c', '--node_id',
                         help='The pds dscipline node in charge of the submission of the DOI',
                         required=True,
                         metavar='"img"')
    _parser.add_argument('-i', '--input',
                         help='A pds4 label local or on http, a xls spreadsheet'
                              ' is also supported to reserve a list of doi',
                         required=True,
                         metavar='input/bundle_in_with_contributors.xml')
    _parser.add_argument('-s', '--submitter_email',
                         help='The email address of the user performing the action for these services',
                         required=False,
                         metavar='"my.email@node.gov"')
    _parser.add_argument('-t', '--target',
                         help='the system target to mint the DOI',
                         required=False,
                         default='osti',
                         metavar='osti')


def create_cmd_parser():
    parser = argparse.ArgumentParser(
        description='Reserve or draft a DOI\n'
                    ' Examples:\n '
                    ' % pds-doi-cmd draft -c img -s Qui.T.Chau@jpl.nasa.gov -i input/bundle_in_with_contributors.xml\n'
                    ' % pds-doi-cmd reserve -c img -i input/DOI_Reserved_GEO_200318.xlsx\n',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    subparsers = parser.add_subparsers(dest='action')
    # create subparsers
    for action_type in ['draft', 'reserve']:
        action_parser = subparsers.add_parser(action_type)
        add_default_action_arguments(action_parser)

    return parser
