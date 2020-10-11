import mysql.connector
from mysql.connector import Error


# log db
def mysql_db_connect(database):
    print()
    print('Connect to db %s' % database['dbname'], end=' ')

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


# delete connection
def mysql_db_close(connection):
    if connection.is_connected:
        connection.close()
        print("MySQL connection was closed")
