from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Name of this App
    app_name: str
    
    allow_origins: list[str]
    allow_credentials: bool
    allow_methods: list[str]
    allow_headers: list[str]
    
    # Milvus Connection Info
    milvus_host: str
    milvus_port: int
    milvus_user: str
    milvus_password: str
    milvus_db_name: str
    milvus_collection: str

    # Redis
    redis_url: str

    metadb_uri: str
    
    #Hyper Clover X connect info    
    hcx_mode: str
    hcx_app_id: str
    hcx_model_name: str
    hcx_api_base: str
    hcx_clovastudio_api_key: str
    hcx_apigw_api_key: str

    emb_api_base: str
    emb_clovastudio_api_key: str
    emb_apigw_api_key: str
    emb_app_id: str

    callback_url: str
    callback_name: str

    #metadb connect info
    metadb_DRIVER: str
    metadb_HOST: str
    metadb_PORT: int
    metadb_DB: str
    metadb_USER: str
    metadb_PW: str

    ## data mart uri
    data_uri: str
    
    #NCloud Object Storage connect info
    service_name: str
    endpoint_url: str
    region_name: str
    access_key: str
    secret_key: str
    bucket_name: str
    chunk_size: int
    chunk_overlap: int

    _callback: any = None
        
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8')
    
@lru_cache
def get_settings():
    return Settings()