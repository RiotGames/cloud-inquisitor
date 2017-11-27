from collections import namedtuple

from sqlalchemy.exc import SQLAlchemyError

from cloud_inquisitor import db
from cloud_inquisitor.schema import ConfigItem, ConfigNamespace


class DBCChoice(dict):
    """Utility class for Choice for `DBConfig`"""


class DBCString(str):
    """Utility class for String values for `DBConfig`"""


class DBCInt(int):
    """Utility class for Integer values for `DBConfig`"""


class DBCFloat(float):
    """Utility class for Float values for `DBConfig`"""


class DBCJSON(dict):
    """Utility class for JSON values for `DBConfig`"""


class DBCArray(list):
    """Utility class for Array values for `DBConfig`"""


class DBConfig(object):
    """Database backed configuration object.

    Styled to work similarly to Flask's builtin config object, with the added feature that it understands
    namespaced configuration items to allow for duplicate names within different scopes.
    """
    __instance = None

    def __new__(cls):
        if not cls.__instance:
            cls.__instance = object.__new__(cls)

        return cls.__instance

    def __init__(self):
        self.__data = {}
        self.reload_data()

    def reload_data(self):
        self.__data = {}
        try:
            for ns in ConfigNamespace.query.all():
                self.__data[ns.namespace_prefix] = {x.key: x.value for x in ns.config_items}

        except SQLAlchemyError as ex:
            print('Failed loading configuration from database: {}'.format(ex))

    def namespace_exists(self, namespace):
        """Checks if a namespace exists

        Args:
            namespace (str): Namespace to check for

        Returns:
            `True` if namespace exists, else `False`
        """

        return namespace in self.__data

    def key_exists(self, namespace, key):
        """Checks a namespace for the existance of a specific key

        Args:
            namespace (str): Namespace to check in
            key (str): Name of the key to check for

        Returns:
            `True` if key exists in the namespace, else `False`
        """

        return namespace in self.__data and key in self.__data[namespace]

    def get(self, key, namespace='default', default=None, as_object=False):
        """Return the value of a key/namespace pair

        Args:
            key (str): Key to return
            namespace (str): Namespace of the key
            default (:obj:`Any`): Optional default value to return, if key was not found
            as_object (bool): If `True` returns the object as a :py:obj:`ConfigItem` object instead of its primitive
            type

        Returns:
            Requested value if found, else default value or `None`
        """

        if namespace in self.__data and key in self.__data[namespace]:
            if as_object:
                return (ConfigItem.query
                    .filter(
                        ConfigItem.namespace_prefix == namespace,
                        ConfigItem.key == key
                    )
                    .first()
                )

            return self.__data[namespace][key]
        else:
            return default

    def set(self, namespace, key, value, description=None):
        """Set (create/update) a configuration item

        Args:
            namespace (`str`): Namespace for the item
            key (`str`): Key of the item
            value (`Any`): Value of the type, must by one of `DBCString`, `DBCFloat`, `DBCInt`, `DBCArray`, `DBCJSON` or
            `bool`
            description (`str`): Description of the configuration item

        Returns:
            `None`
        """

        if isinstance(value, DBCChoice):
            vtype = 'choice'

        elif isinstance(value, DBCString):
            vtype = 'string'

        elif isinstance(value, DBCFloat):
            vtype = 'float'

        elif isinstance(value, DBCInt):
            vtype = 'int'

        elif isinstance(value, DBCArray):
            vtype = 'array'

        elif isinstance(value, DBCJSON):
            vtype = 'json'

        elif isinstance(value, bool):
            vtype = 'bool'

        else:
            raise ValueError('Invalid config item type: {}'.format(type(value)))

        if namespace in self.__data and key in self.__data[namespace]:
            itm = ConfigItem.query.filter(ConfigItem.namespace_prefix == namespace, ConfigItem.key == key).first()
            if not itm:
                raise KeyError(key)

            itm.value = value
            itm.type = vtype
            itm.description = description
        else:
            itm = ConfigItem()
            itm.key = key
            itm.value = value
            itm.type = vtype
            itm.description = description
            itm.namespace_prefix = namespace

        db.session.add(itm)
        db.session.commit()

        if namespace in self.__data:
            self.__data[namespace][key] = value
        else:
            self.__data[namespace] = {key: value}

    def delete(self, namespace, key):
        """Remove a configuration item from the database

        Args:
            namespace (`str`): Namespace of the config item
            key (`str`): Key to delete

        Returns:
            `None`
        """
        if self.key_exists(namespace, key):
            obj = ConfigItem.query.filter(ConfigItem.namespace_prefix == namespace, ConfigItem.key == key).first()
            del self.__data[namespace][key]

            db.session.delete(obj)
            db.session.commit()
        else:
            raise KeyError('{}/{}'.format(namespace, key))


ConfigOption = namedtuple('ConfigOption', ('name', 'default_value', 'type', 'description'))
dbconfig = DBConfig()
