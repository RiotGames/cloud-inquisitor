from sqlservice import SQLClient, declarative_base

Model = declarative_base()

def get_db_connection():
    return SQLClient({
        'SQL_DATABASE_URI': 'mysql://awsaudits:secretpass@localhost:3306/inquisitor',
    }, model_class=Model)