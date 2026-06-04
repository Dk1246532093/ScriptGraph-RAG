"""
项目配置
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # 项目信息
    PROJECT_NAME: str = "ScriptGraph-RAG"
    VERSION: str = "0.1.0"
    
    # API 配置
    API_V1_STR: str = "/api/v1"
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # 存储路径
    STORAGE_DIR: str = "storage"
    NOVELS_DIR: str = "storage/novels"
    KG_DIR: str = "storage/knowledge_graph"
    RAG_DIR: str = "storage/rag"
    SCRIPTS_DIR: str = "storage/scripts"
    
    # AI API 配置
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com/v1"
    QWEN_API_KEY: str = ""
    QWEN_API_BASE: str = "https://dashscope.aliyuncs.com/api/v1"
    
    # RAG 配置
    CHUNK_SIZE: int = 1500
    CHUNK_OVERLAP: int = 200
    TOP_K: int = 5
    
    # 向量模型
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    class Config:
        env_file = ".env"


settings = Settings()
