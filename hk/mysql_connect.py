import mysql.connector
from mysql.connector import Error


def mysql_db_connect(database):
    print()
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


# log db
def mysql_log_connect(database):
    print()
    print('Connect to db %s' % database['logname'], end=' ')

    try:
        connection = mysql.connector.connect(
            host=database['host'],
            database=database['logname'],
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
