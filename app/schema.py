from pydantic import BaseModel, Field
from typing import Optional

# Main Query For Assistant
class AssistantQueryItem(BaseModel):
    query: str
    
    default_threshold: Optional[float] = None
    domain_threshold: Optional[float] = Field(None, alias="domainThreshold")
    api_threshold: Optional[float] = Field(None, alias="apiThreshold")
    chunk_text_threshold: Optional[float] = Field(None, alias="chunkTextThreshold")

    class Config:
        allow_population_by_field_name = True

    @property
    def thresholds(self):
        return {
            "domain_desc": self.domain_threshold or self.default_threshold,
            "api_desc": self.api_threshold or self.default_threshold,
            "chunk_text": self.chunk_text_threshold or self.default_threshold,
        }

class DomainItem(BaseModel):
    pk: int
    text: str
    
class ApiDescItem(BaseModel):
    collection_name: str
    text: str
    api_id: int
    domain_id: int