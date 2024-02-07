from typing import (Any, Dict, Iterator, List, Optional, Sequence, Tuple, Union,)
from sqlalchemy import URL

from langchain.sql_database import SQLDatabase

class QueryMetaDB:

    db: SQLDatabase = None

    def __init__(self):
        if self.__class__.db is None:
            from app.config import get_settings
            conf = get_settings()
            url_object = URL.create(
                drivername=conf.metadb_DRIVER,
                username=conf.metadb_USER,
                password=conf.metadb_PW,  # plain (unescaped) text
                host=conf.metadb_HOST,
                port=conf.metadb_PORT,
                database=conf.metadb_DB,
            ) 
            self.__class__.db = SQLDatabase.from_uri(database_uri=url_object)

    def get_system(self, id: str) -> str:
        return self.db.run("select connect_type, connect_spec from api_system where system_id = {id} and status = 'Y'".format(id), "one")
    
    def get_api(self, id: str) -> str:
        return self.db.run("select system_id, api_spec from api_spec where api_id = {id} and status = 'Y'".format(id), "one")
    
    def get_prompt(self, id: str) -> str:
        return self.db.run("select prompt_text from prompt where prompt_id = {id} and status = 'Y'".format(id), "one")
    
    def get_domain_list(self) -> Dict[str, Any]:
        rows = self.db.run("select domain_id, domain_name, domain_desc from domain", "many")
        return [{"domain_id":row[0], "domain_name":row[3], "domain_desc":row[3]} for row in rows]

    
__all__ = ["QueryMetaDB"]