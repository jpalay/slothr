# change this for production servers probably
SECRET_KEY = 'DEVELOPMENT SECRET KEY'

DATABASE = {
    'host': 'localhost',
    'port': 3306,
    'name': 'slothr',
    'user': 'root',
    'password': ''
}

try:
    from local_settings import *
except ImportError:
    pass
