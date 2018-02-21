import logging
import uuid
from base64 import b64decode
from datetime import datetime
from enum import Enum
from json import JSONDecoder, JSONEncoder

from markupsafe import Markup
from werkzeug.http import parse_date

import cloud_inquisitor.schema
from cloud_inquisitor.database import Model

log = logging.getLogger('JSON')


class InquisitorJSONEncoder(JSONEncoder):
    """Custom JSON encoding function.

    This class will check if the object being serialized has a function called `to_json()`, and call it if available,
    as well as adding a type-hint value to the output dict (`__type` key/value pair)
    """

    def default(self, obj):
        """Default object encoder function

        Args:
            obj (:obj:`Any`): Object to be serialized

        Returns:
            JSON string
        """
        if isinstance(obj, datetime):
            return obj.isoformat()

        if issubclass(obj.__class__, Enum.__class__):
            return obj.value

        to_json = getattr(obj, 'to_json', None)
        if to_json:
            out = obj.to_json()
            if issubclass(obj.__class__, Model):
                out.update({'__type': obj.__class__.__name__})

            return out

        return JSONEncoder.default(self, obj)


class InquisitorJSONDecoder(JSONDecoder):
    """Custom JSON decoding class

    This class will attempt to convert object serialized by :obj:`InquisitorJSONEncoder` back into Python objects, using
    the type-hinting done by the encoder.
    """

    def __init__(self, *, object_hook=None, parse_float=None, parse_int=None,
                 parse_constant=None, strict=True, object_pairs_hook=None):
        """Initialize the class, overriding the object hook

        Args:
            object_hook:
            parse_float:
            parse_int:
            parse_constant:
            strict:
            object_pairs_hook:
        """
        try:
            super().__init__(
                object_hook=self.object_hook,
                parse_float=parse_float,
                parse_int=parse_int,
                parse_constant=parse_constant,
                strict=strict,
                object_pairs_hook=object_pairs_hook
            )
        except Exception:
            log.exception('Failed loading JSON data')

    @staticmethod
    def object_hook(obj):
        """Checks to see if the `__type`-hinting field is available in the object being de-serialized. If present, and
        the class referenced has a `from_json` function it will return the generated object, else a standard dic
        will be returned

        Args:
            obj: Object to be deserialized

        Returns:
            Deserialized object or regular python objec
        """
        try:
            if '__type' in obj:
                obj_type = obj['__type']
                cls = getattr(cloud_inquisitor.schema, obj_type)
                if hasattr(cls, 'from_json'):
                    return cls.from_json(obj)

            key, value = next(iter(obj.items()))
            if key == ' t':
                return tuple(value)
            elif key == ' u':
                return uuid.UUID(value)
            elif key == ' b':
                return b64decode(value)
            elif key == ' m':
                return Markup(value)
            elif key == ' d':
                return parse_date(value)

            return obj
        except Exception:
            log.exception('Error during data deserialization')
