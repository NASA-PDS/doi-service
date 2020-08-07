

class InputFormatException(Exception):
    pass

class UnknownNodeException(Exception):
    pass

class DuplicatedTitleDOIException(Exception):
    pass

class InvalidDOIException(Exception):
    pass

class IllegalDOIActionException(Exception):
    pass

class UnexpectedDOIActionException(Exception):
    pass

class TitleDoesNotMatchProductTypeException(Exception):
    pass
