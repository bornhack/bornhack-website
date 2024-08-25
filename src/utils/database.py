from django.db.models import Func
from django.db.models import IntegerField


class CastToInteger(Func):
    """Trying to use a GIST index in postgres over a BooleanField will not work:

        django.db.utils.ProgrammingError: data type boolean has no default operator class for access method "gist"
        HINT:  You must specify an operator class for the index or define a default operator class for the data type.

    This class can be use to cast the bool to int in the constraint, making it work.
    https://docs.djangoproject.com/en/3.0/ref/models/expressions/#func-expressions
    """

    function = "CAST"
    output_field = IntegerField()
    template = "%(function)s(%(expressions)s AS int)"
