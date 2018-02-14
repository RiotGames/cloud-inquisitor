from sqlservice import SQLClient, declarative_base
from werkzeug.local import LocalProxy

from cloud_inquisitor import app_config

Model = declarative_base()

def get_db_connection():
    return SQLClient({
        'SQL_DATABASE_URI': app_config.database_uri
    }, model_class=Model)

db = LocalProxy(get_db_connection)