"""
Impala backend for django.

Requires impyla: https://github.com/cloudera/impyla
"""
from __future__ import unicode_literals

from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.base.features import BaseDatabaseFeatures


from django.core.exceptions import ImproperlyConfigured

try:
    from impala import dbapi as Database
except ImportError as exc:
    raise ImproperlyConfigured("Error loading impyla module: %s" % exc)

from .client import DatabaseClient
from .creation import DatabaseCreation
from .introspection import DatabaseIntrospection
from .schema import DatabaseSchemaEditor
from .operations import DatabaseOperations
from .validation import DatabaseValidation


DatabaseError = Database.DatabaseError
IntegrityError = Database.IntegrityError

try:
    from impala.hiveserver2 import HiveServer2Cursor
except ImportError as exc:
    raise ImproperlyConfigured("Error loading impyla module: %s" % exc)


class ImpalaCursor(HiveServer2Cursor):
    """
    Cursor Wrapper
    """

    def _escape_args(self, args):
        _args = []
        for value in args:
            if value is None:
                _args.append('NULL')
            elif isinstance(value, basestring):
                _args.append(
                    "'%s'" % Database._escape(value))
            else:
                _args.append(str(value))
        return tuple(_args)

    def execute(self, query, args=None):
        if args:
            query = query % self._escape_args(args)
        if query[-1] == ';':
            query = query[:-1]

        super(ImpalaCursor, self).execute(query)


Database.Cursor = ImpalaCursor


class DatabaseFeatures(BaseDatabaseFeatures):
    can_return_id_from_insert = False
    has_real_datatype = True
    supports_nullable_unique_constraints = False
    supports_partially_nullable_unique_constraints = False
    supports_timezones = False
    supports_transactions = False

    def _supports_transactions(self):
        return False


class DatabaseWrapper(BaseDatabaseWrapper):
    vendor = 'impala'
    display_name = 'Impala'
    operators = {
        'exact': '= %s',
        'iexact': 'LIKE %s',
        'contains': 'LIKE %s',
        'icontains': 'LIKE %s',
        'regex': 'REGEXP %s',
        'iregex': 'REGEXP %s',
        'gt': '> %s',
        'gte': '>= %s',
        'lt': '< %s',
        'lte': '<= %s',
        'startswith': 'LIKE %s',
        'endswith': 'LIKE %s',
        'istartswith': 'LIKE %s',
        'iendswith': 'LIKE %s',
    }

    Database = Database
    SchemaEditorClass = DatabaseSchemaEditor
    # Classes instantiated in __init__().
    client_class = DatabaseClient
    creation_class = DatabaseCreation
    features_class = DatabaseFeatures
    introspection_class = DatabaseIntrospection
    ops_class = DatabaseOperations
    validation_class = DatabaseValidation

    # def __init__(self, *args, **kwargs):
    #     super(DatabaseWrapper, self).__init__(*args, **kwargs)
    #
    #     self.features = DatabaseFeatures(self)
    #     self.ops = DatabaseOperations(self)
    #     self.client = DatabaseClient(self)
    #     self.creation = DatabaseCreation(self)
    #     self.introspection = DatabaseIntrospection(self)
    #     self.validation = DatabaseValidation(self)

    def get_connection_params(self):
        settings_dict = self.settings_dict
        if settings_dict['NAME'] == '':
            raise ImproperlyConfigured(
                "settings.DATABASES is improperly configured. "
                "Please supply the NAME value.")

        conn_params = {}
        conn_params.update(settings_dict['OPTIONS'])
        if 'autocommit' in conn_params:
            del conn_params['autocommit']
        if 'isolation_level' in conn_params:
            del conn_params['isolation_level']
        if settings_dict['USER']:
            conn_params['ldap_user'] = settings_dict['USER']
        if settings_dict['PASSWORD']:
            conn_params['ldap_password'] = settings_dict['PASSWORD']
        if settings_dict['HOST']:
            conn_params['host'] = settings_dict['HOST']
        if settings_dict['PORT']:
            conn_params['port'] = settings_dict['PORT']
        if settings_dict['DATABASE']:
            conn_params['database'] = settings_dict['DATABASE']
        return conn_params

    def get_new_connection(self, conn_params):
        return Database.connect(**conn_params)

    def init_connection_state(self):
        # XXX:
        pass

    def create_cursor(self, name=None):
        # XXX:
        cursor = self.connection.cursor()
        cursor.execute('USE %s' % (self.settings_dict['DATABASE'] or 'default'))
        return cursor

    def _set_autocommit(self, autocommit):
        pass

    def is_usable(self):
        try:
            self.connection.ping()
        except Database.Error:
            return False
        else:
            return True

    def _start_transaction_under_autocommit(self):
        pass

    def schema_editor(self, *args, **kwargs):
        return DatabaseSchemaEditor(self, *args, **kwargs)
