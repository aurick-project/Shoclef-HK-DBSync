from pymongo import MongoClient, errors


def mongo_connect(url):
    try:
        # connect to MongoDB, change the << MONGODB URL >> to reflect your own connection string
        client = MongoClient(url)

        return client
    except errors.ServerSelectionTimeoutError as err:
        print(err)
        return None
    except Exception as e:
        print(e)
        return None
