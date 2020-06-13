from pds_doi_core.input.input_util import DOIInputUtil
from pds_doi_core.input.node_util import NodeUtil
from pds_doi_core.input.pds4_util import DOIPDS4LabelUtil
from pds_doi_core.outputs.osti import DOIOutputOsti
from pds_doi_core.outputs.output_util import DOIOutputUtil
from pds_doi_core.outputs.transaction_builder import TransactionBuilder
from pds_doi_core.util.config_parser import DOIConfigUtil
from pds_doi_core.util.general_util import get_logger

logger = get_logger('pds_doi_core.actions.actions')


class DOICoreAction:
    m_doi_config_util = DOIConfigUtil()
    m_doi_input_util = DOIInputUtil()
    m_doi_output_util = DOIOutputUtil()
    m_doi_pds4_label = DOIPDS4LabelUtil()
    m_doi_output_osti = DOIOutputOsti()
    m_transaction_builder = TransactionBuilder()
    m_node_util = NodeUtil()

    def __init__(self):
        self._config = self.m_doi_config_util.get_config()


