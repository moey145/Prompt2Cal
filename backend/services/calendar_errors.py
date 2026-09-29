"""Errors shared by the Google and Outlook calendar services."""


class CalendarNotConnected(Exception):
    """The user has no usable connection to this calendar provider.

    Raised for a missing, expired or unrefreshable token, so endpoints can
    tell the user to reconnect instead of passing on a wrapped technical error.
    """
