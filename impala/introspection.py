import warnings
from collections import namedtuple

from MySQLdb.constants import FIELD_TYPE
from django.db.backends.base.introspection import BaseDatabaseIntrospection
from django.db.backends.base.introspection import (
    BaseDatabaseIntrospection, FieldInfo, TableInfo,
)
from django.db.models.indexes import Index
from django.utils.datastructures import OrderedSet
from django.utils.deprecation import RemovedInDjango21Warning

FieldInfo = namedtuple('FieldInfo', FieldInfo._fields + ('extra', 'is_unsigned'))
InfoLine = namedtuple('InfoLine', 'col_name data_type max_len num_prec num_scale extra column_default is_unsigned')


class DatabaseIntrospection(BaseDatabaseIntrospection):

    def get_table_list(self, cursor):
        "Returns a list of table names in the current database."
        cursor.execute("SHOW TABLES")

        # 此处需要查出来是表还是试图
        return [TableInfo(row[0], 't' if len(row) <= 1 else {'BASE TABLE': 't', 'VIEW': 'v'}.get(row[1], 't'))
                for row in cursor.fetchall()]

