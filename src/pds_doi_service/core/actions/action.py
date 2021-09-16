#
#  Copyright 2020–21 by the California Institute of Technology. ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
"""
=========
action.py
=========

Contains the parent class definition for actions of the Core PDS DOI Service.
"""
import argparse

from pds_doi_service.core.outputs.transaction_builder import TransactionBuilder
from pds_doi_service.core.util.config_parser import DOIConfigUtil
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger(__name__)


def create_parser():
    """Non-object function to be used by sphinx-argparse for documentation"""
    logger.info("parser for sphinx-argparse")
    return DOICoreAction.create_cmd_parser()


class DOICoreAction:
    m_doi_config_util = DOIConfigUtil()

    _name = "unknown"
    _description = "no description"
    _order = 9999999  # used to sort actions in documentation
    _run_arguments: tuple[str, ...]
    _run_arguments = ()

    def __init__(self, db_name=None):
        self._config = self.m_doi_config_util.get_config()
        self.m_transaction_builder = TransactionBuilder(db_name)

    @staticmethod
    def create_cmd_parser():
        """
        Creates an argument parser suitable for use with the action class.
        The appropriate subparsers are added based on the available inheritors
        of DOICoreAction and their associated implementations of add_to_subparser().

        Returns
        -------
        parser : argparse.ArgumentParser
            An argument parser with subparsers for each available action
            subclass.

        """
        parser = argparse.ArgumentParser(
            description="PDS core command for DOI management. " "The available subcommands are:\n",
            formatter_class=argparse.RawTextHelpFormatter,
        )

        subparsers = parser.add_subparsers(dest="subcommand")

        # create subparsers
        action_classes = sorted(DOICoreAction.__subclasses__(), key=lambda c: c._order)

        for cls in action_classes:
            parser.description += f"{cls._name} ({cls._description}),\n"
            add_to_subparser_method = getattr(cls, "add_to_subparser", None)

            if callable(add_to_subparser_method):
                add_to_subparser_method(subparsers)

        return parser

    @classmethod
    def add_to_subparser(cls, subparsers):
        """
        Method for actions to add their own subparser which defines the set
        of command-line arguments specific to the action.

        Inheritors of DOICoreAction must provide an implementation that invokes
        add_parser on the provided subparsers object. The parser returned by
        add_parser can then be used by the action to define its own command-line
        arguments.

        Parameters
        ----------
        subparsers : argparse._SubParsersAction
            The set of subparsers for the action to add its own to.

        """
        return NotImplementedError(
            f"Subclasses of {cls.__class__.__name__} must provide an " f"implementation for add_to_subparser()"
        )

    def parse_arguments(self, kwargs):
        """
        Parsers arguments from the provided keyword dictionary, assigning
        only those arguments that are expected by the action (i.e. defined
        in the _run_arguments attribute list).

        Parameters
        ----------
        kwargs : dict
            Dictionary of arguments to assign to the action class as attributes.

        """
        for kwarg in self._run_arguments:
            if kwarg in kwargs:
                setattr(self, f"_{kwarg}", kwargs[kwarg])

            logger.debug(f"{kwarg} = {getattr(self,  f'_{kwarg}')}")

    def run(self, **kwargs):
        """
        Main entrypoint to the action class.

        Inheritors must provide an implementation that performs the expected
        actions of the class.

        Parameters
        ----------
        kwargs : dict
            Keyword dictionary containing arguments for the action class,
            typically as obtained from the command-line parser.

        Returns
        -------
        result : str
            The result of running the action with the provided arguments.
            Typically this is the text body of a DOI label, or the results of
            a database query operation. As pds_doi_cmd.py prints what is returned
            to it, this value should always be a string (or have a valid string
            representation).

        """
        return NotImplementedError(
            f"Subclasses of {self.__class__.__name__} must provide an " f"implementation for run()"
        )
