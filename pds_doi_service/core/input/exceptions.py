

class InputFormatException(Exception):
    pass


class UnknownNodeException(Exception):
    pass


class UnknownLIDVIDException(Exception):
    pass


class NoTransactionHistoryForLIDVIDException(Exception):
    pass


class DuplicatedTitleDOIException(Exception):
    pass


class IllegalDOIActionException(Exception):
    pass


class UnexpectedDOIActionException(Exception):
    pass


class TitleDoesNotMatchProductTypeException(Exception):
    pass


class CriticalDOIException(Exception):
    pass


class WarningDOIException(Exception):
    pass


class SiteURLNotExistException(Exception):
    pass

