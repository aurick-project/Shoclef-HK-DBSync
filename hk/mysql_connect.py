import mysql.connector
from mysql.connector import Error
import datetime


# log db
def mysql_db_connect(database):
    print('Connect to db %s' % database['dbname'], end=' ')

    try:
        connection = mysql.connector.connect(
            host=database['host'],
            database=database['dbname'],
            user=database['username'],
            password=database['password'],
            port=int(database['port'])
        )
        if connection.is_connected():
            print('| OK')
            return connection
        else:
            print('| FAIL')
            return None
    except Error as e:
        print('| FAIL')
        print(str(e))
    return None


# delete connection
def mysql_db_close(connection, cursor=None):
    if connection.is_connected:
        if cursor:
            cursor.close()
        connection.close()
        print("MySQL connection was closed")


def mysql_select_table(cursor, table, select='*', where=None, order_by=None, group_by=None, fetch='all', fetch_num=10):
    """

    :param cursor: db cursor
    :param table: string table name
    :param select: string '*' or 'a AS aa, b, c'
    :param where: string None or 'a="AAA" OR b="BBB"'
    :param order_by: string None or 'a DESC, b'
    :param group_by: string None or 'a'
    :param fetch: string 'all', 'one', 'many'
    :param fetch_num: integer if fetch='many' get fetch_num rows
    :return: array db rows
    """

    query = "SELECT %s FROM %s" % (select, table)

    if where:
        query += " WHERE %s" % where

    if group_by:
        query += " GROUP BY %s" % group_by

    if order_by:
        query += " ORDER BY %s" % order_by
    try:
        cursor.execute(query)
        if fetch == 'all':
            return cursor.fetchall()
        elif fetch == 'one':
            return cursor.fetchone()
        else:
            return cursor.fetchmany(fetch_num)
    except Error as e:
        print('select query failed %s' % query)
        print(e)
        return []


def mysql_insert_table(db, cursor, table, data):
    """
    :param db: mysql db
    :param cursor: mysql db cursor
    :param table: string table name
    :param data: list {'a':'A', 'b':'B',...}
    :return: int inserted row id or None
    """
    query_fields = ''
    query_values = ''
    for field in data.keys():
        query_fields += '%s,' % field
        if isinstance(data[field], str):
            query_values += '"%s",' % data[field].replace('"', '\\"')
        elif isinstance(data[field], type(None)):
            query_values += 'NULL,'
        elif isinstance(data[field], datetime.datetime):
            query_values += '"%s",' % data[field].strftime('%Y-%m-%d %H:%M:%S')
        else:
            query_values += '%s,' % data[field]
    query_fields = query_fields[:-1]
    query_values = query_values[:-1]

    query = 'INSERT INTO %s(%s) VALUES (%s)' % (table, query_fields, query_values)
    print('insert into %s' % table, end=' ')
    try:
        cursor.execute(query)
        db.commit()
        print('| OK id=%s' % cursor.lastrowid)
        return cursor.lastrowid
    except Error as e:
        print('| FAIL')
        print(query)
        print(str(e))
        return -1


def mysql_update_table(db, cursor, table, data, where=''):
    """

    :param db: mysql db
    :param cursor: mysql db cursor
    :param table: str table name
    :param data: list {'a':'A', 'b':'B'...}
    :param where: string "id='111' AND del='true'"
    :return: boolean True or False
    """
    query_where = ''
    if where != '':
        query_where = 'WHERE ' + where
    query_update = ''
    for field in data.keys():
        if isinstance(data[field], str):
            query_update += '%s="%s",' % (field, data[field].replace('"', '\\"'))
        elif isinstance(data[field], type(None)):
            query_update += '%s=NULL,' % field
        else:
            query_update += '%s="%s",' % (field, data[field])
    query_update = query_update[:-1]
    query = "UPDATE %s SET %s %s" % (table, query_update, query_where)
    try:
        cursor.execute(query)
        db.commit()
        return True
    except Error as e:
        print('update failed %s' % query)
        print(e)
        return False


def mysql_delete_table(db, cursor, table, where=''):
    """

    :param db:
    :param cursor:
    :param table:
    :param where: 'id=1 AND added>"2000-01-01"'
    :return:
    """
    if where == '':
        query = 'TRUNCATE %s' % table
    else:
        query = 'DELETE FROM %s WHERE %s' % (table, where)
    try:
        cursor.execute(query)
        db.commit()
        return True
    except Error as e:
        print('delete failed %s' % query)
        print(e)
        return False
