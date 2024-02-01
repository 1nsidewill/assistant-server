from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str
    milvus_host: str
    milvus_port: int
    milvus_user: str
    milvus_password: str
    milvus_db_name: str
    milvus_collection: str

    redis_url: str

    metadb_uri: str
    
    hcx_api_base: str
    hcx_clovastudio_api_key: str
    hcx_apigw_api_key: str

    emb_api_base: str
    emb_clovastudio_api_key: str
    emb_apigw_api_key: str
    emb_app_id: str

    callback_url: str
    callback_name: str
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8')

    _callback: any = None

@lru_cache
def get_settings():
    return Settings()