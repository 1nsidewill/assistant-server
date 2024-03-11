from pydantic import BaseModel, Field, validator
from typing import Optional, Required

# Main Query For Assistant
class AssistantQueryItem(BaseModel):
    query: str
    
    # HCX Options
    rag_top_k: Optional[int] = Field(default=3)
    max_tokens: Optional[int] = Field(default=2048)
    
    default_threshold: float = 0.3
    domain_threshold: Optional[float] = 0
    api_threshold: Optional[float] = 0.8
    chunk_text_threshold: Optional[float] = 0

    aadObjectId: Optional[str] = None
    
    class Config:
        allow_population_by_field_name = True

    @property
    def thresholds(self):
        # Check each threshold individually, fall back to default_threshold if None
        return {
            "domain_desc": self.domain_threshold if self.domain_threshold != 0 else self.default_threshold,
            "api_desc": self.api_threshold if self.api_threshold != 0 else self.default_threshold,
            "chunk_text": self.chunk_text_threshold if self.chunk_text_threshold != 0 else self.default_threshold,
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

class DomainDescItem(BaseModel):
    collection_name: str
    text: str
    domain_id: int
    name: str