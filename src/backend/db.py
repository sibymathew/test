from tinydb import TinyDB, Query

class Database:

    def __init__(self, db_file):
        self.db_hdlr = TinyDB(db_file)
        self.query_hdlr = Query()

    def insert(self, data):
        self.db_hdlr.insert(data)

    def update(self, data, key_name, key_value):
        self.db_hdlr.update(data, self.query_hdlr[key_name] == (key_value))

    def upsert(self, data, key_name, key_value):
        self.db_hdlr.upsert(data, self.query_hdlr[key_name] == (key_value))

    def search(self, key_name, key_value):
        return self.db_hdlr.search(self.query_hdlr[key_name] == (key_value))

    def count(self, key_name, key_value):
        return self.db_hdlr.count(self.query_hdlr[key_name] == (key_value))

    def length(self):
        return len(self.db_hdlr)

    def all(self):
        return self.db_hdlr.all()

    def delete(self, key_name, key_value):
        doc = self.db_hdlr.get(self.query_hdlr[key_name] == (key_value))
        doc_id = doc.doc_id

        self.db_hdlr.remove(doc_ids=[doc_id])
