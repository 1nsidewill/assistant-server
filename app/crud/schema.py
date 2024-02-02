from pydantic import BaseModel

class DomainItem(BaseModel):
    pk: int
    text: str