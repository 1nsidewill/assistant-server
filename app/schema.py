from pydantic import BaseModel, Field, validator
from typing import Optional

# Main Query For Assistant
class AssistantQueryItem(BaseModel):
    query: str
    
    rag_top_k: Optional[int] = 3
    
    default_threshold: Optional[float] = None
    domain_threshold: Optional[float] = Field(None)
    api_threshold: Optional[float] = Field(None)
    chunk_text_threshold: Optional[float] = Field(None)

    class Config:
        allow_population_by_field_name = True

    @property
    def thresholds(self):
        # Check each threshold individually, fall back to default_threshold if None
        return {
            "domain_desc": self.domain_threshold if self.domain_threshold is not None else self.default_threshold,
            "api_desc": self.api_threshold if self.api_threshold is not None else self.default_threshold,
            "chunk_text": self.chunk_text_threshold if self.chunk_text_threshold is not None else self.default_threshold,
        }

    @validator('default_threshold', always=True)
    def check_thresholds(cls, v, values):
        if v is None and (values.get('domain_threshold') is None and values.get('api_threshold') is None and values.get('chunk_text_threshold') is None):
            raise ValueError('default_threshold must be set if domain_threshold, api_threshold, and chunk_text_threshold are not provided.')
        return v

class DomainItem(BaseModel):
    pk: int
    text: str
    
class ApiDescItem(BaseModel):
    collection_name: str
    text: str
    api_id: int
    domain_id: int