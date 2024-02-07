from typing import (Any, Dict, Iterator, List, Optional, Literal, Sequence, Tuple, Union,)
from sqlalchemy import URL
 
from langchain.sql_database import (SQLDatabase)
 
def truncate_word(content: Any, *, length: int, suffix: str = "...") -> str:
    if not isinstance(content, str) or length <= 0:
        return content
 
    if len(content) <= length:
        return content
 
    return content[: length - len(suffix)].rsplit(" ", 1)[0] + suffix
 
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

    def run(
        self,
        command: str,
        fetch: Literal["all", "one"] = "all",
        include_columns: bool = False,
    ) -> str:
        """Execute a SQL command and return a string representing the results.
 
        If the statement returns rows, a string of the results is returned.
        If the statement returns no rows, an empty string is returned.
        """
        result = self.db._execute(command, fetch)
 
        res = [
            {
                column: truncate_word(value, length=self.__class__.db._max_string_length)
                for column, value in r.items()
            }
            for r in result
        ]
 
        if not include_columns:
            res = [tuple(row.values()) for row in res]
 
        return res
        
    def get_system(self, id: str) -> tuple:
        query = f"select connect_type, connect_spec from api_system where system_id = {id} and status = 'Y'"
        result = self.run(query, "one")
        if result:
            connect_type, connect_spec = result[0]  # Unpack the first tuple
            return (connect_type, connect_spec)
        else: 
            return None
    
    def get_api(self, id: str) -> tuple:
        query = f"select system_id, api_spec from api_spec where api_id = {id} and status = 'Y'"
        result = self.run(query, "one")
        if result:
            system_id, api_spec = result[0]  # Unpack the first tuple
            return (system_id, api_spec)
        else: 
            return None
    
    def get_prompt(self, id: str) -> str:
        return self.run("select prompt_text from prompt where prompt_id = {id} and status = 'Y'".format(id), "one")
    
    def get_domain_list(self) -> Dict[str, Any]:
        rows = self.run("select domain_id, domain_name, domain_desc from domain", "many")
        return [{"domain_id":row[0], "domain_name":row[3], "domain_desc":row[3]} for row in rows]
 
    
__all__ = ["QueryMetaDB"]