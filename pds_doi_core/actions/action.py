import argparse
from pds_doi_core.input.input_util import DOIInputUtil
from pds_doi_core.input.node_util import NodeUtil
from pds_doi_core.input.pds4_util import DOIPDS4LabelUtil
from pds_doi_core.outputs.osti import DOIOutputOsti
from pds_doi_core.outputs.output_util import DOIOutputUtil
from pds_doi_core.outputs.transaction_builder import TransactionBuilder
from pds_doi_core.util.config_parser import DOIConfigUtil
from pds_doi_core.util.general_util import get_logger

logger = get_logger('pds_doi_core.actions.actions')


# non object function to be used by sphynx-argparse for documentation
def create_parser():
    logger.info('parser for sphynx-argparse')
    return DOICoreAction.create_cmd_parser()

class DOICoreAction:
    m_doi_config_util = DOIConfigUtil()
    m_doi_input_util = DOIInputUtil()
    m_doi_output_util = DOIOutputUtil()
    m_doi_pds4_label = DOIPDS4LabelUtil()
    m_doi_output_osti = DOIOutputOsti()
    m_node_util = NodeUtil()

    _name = 'unknown'
    _decription = 'no description'
    _order = 9999999 # used to sort actions in documentation

    def __init__(self, db_name=None):
        self._config = self.m_doi_config_util.get_config()
        # Let each class derived from DOICoreAction parse its own arguments.
        self.m_transaction_builder = TransactionBuilder(db_name)

    def parse_arguments_from_cmd(self, arguments):
        # The 'check' action has no arguments.  This empty function is needed though.
        return 1

    @staticmethod
    def create_cmd_parser():
        parser = argparse.ArgumentParser(
            description='PDS core command for DOI management. The available subcommands are:\n',
            formatter_class=argparse.RawTextHelpFormatter)
        # ArgumentDefaultsHelpFormatter)

        subparsers = parser.add_subparsers(dest='subcommand')

        # create subparsers
        action_classes = sorted(DOICoreAction.__subclasses__(), key=lambda c : c._order)
        for cls in action_classes:
            parser.description += f'{cls._name} ({cls._description}),\n'
            add_to_subparser_method = getattr(cls, "add_to_subparser", None)
            if callable(add_to_subparser_method):
                add_to_subparser_method.__call__(subparsers)

        return parser

# end of class DOICoreAction:
