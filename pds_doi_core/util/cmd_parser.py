import argparse


def add_default_action_arguments(_parser):
    _parser.add_argument('-c', '--contributor',
                         help='The pds dscipline node in charge of the submission of the DOI',
                         required=True,
                         metavar='"Cartography and Imaging Sciences Discipline"')
    _parser.add_argument('-i', '--input',
                         help='A pds4 label local or on http, a xls spreadsheet'
                              ' is also supported to reserve a list of doi',
                         required=True,
                         metavar='input/bundle_in_with_contributors.xml')
    _parser.add_argument('-t', '--target',
                         help='the system target to mint the DOI',
                         required=False,
                         default='osti',
                         metavar='osti')


def create_cmd_parser():
    parser = argparse.ArgumentParser(
        description='Reserve or draft a DOI\n'
                    ' Examples:\n '
                    ' % pds-doi-cmd draft -c "Cartography and Imaging Sciences Discipline" -i input/bundle_in_with_contributors.xml\n'
                    ' % pds-doi-cmd reserve -c "Cartography and Imaging Sciences Discipline" -i input/DOI_Reserved_GEO_200318.xlsx\n',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    subparsers = parser.add_subparsers(dest='action')
    # create subparsers
    for action_type in ['draft', 'reserve']:
        action_parser = subparsers.add_parser(action_type)
        add_default_action_arguments(action_parser)

    return parser
