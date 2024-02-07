from pydantic import BaseModel

class DomainItem(BaseModel):
    pk: int
    text: str
    
class ApiDescItem(BaseModel):
    collection_name: str
    text: str
    api_id: int
    domain_id: int