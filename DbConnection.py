import psycopg2

class DbConnection:

    def __init__(self, db_config: dict) -> None:

        self.db_config = db_config

    def __enter__(self):

        self.con = psycopg2.connect(**self.db_config)
        self.cur = self.con.cursor()
 
        return self.cur

    def __exit__(self, exc_type, exc_value, exc_trace):
        self.con.commit()
        self.cur.close()
        self.con.close()
