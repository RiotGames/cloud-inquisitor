from sqlservice import SQLClient, declarative_base
from werkzeug.local import LocalProxy

Model = declarative_base()

def get_db_connection():
    return SQLClient({
        'SQL_DATABASE_URI': 'mysql://awsaudits:secretpass@localhost:3306/inquisitor',
        'SQL_POOL_SIZE': 5,
        'SQL_ECHO_POOL': True
    }, model_class=Model)

db = LocalProxy(get_db_connection)