"""Why a parse produced no event, so the user is told instead of shown a guess."""


class ParserUnavailable(Exception):
    """The language model could not be reached or gave an unusable reply."""


class NoEventFound(Exception):
    """The text was read, but no event could be found in it."""
