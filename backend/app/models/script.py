"""
剧本数据模型
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ScriptConfig(BaseModel):
    """剧本生成配置"""
    style: Optional[str] = None  # 剧本风格：wuxia/modern/fantasy/mystery
    characters: Optional[str] = None  # 角色设定
    requirements: Optional[str] = None  # 特殊要求


class ScriptGenerateRequest(BaseModel):
    """剧本生成请求"""
    novel_id: str
    chapter_ids: List[str]
    config: Optional[ScriptConfig] = None


class ScriptScene(BaseModel):
    """剧本场景"""
    scene_id: str
    title: str
    location: str
    characters: List[str]
    content: str


class Script(BaseModel):
    """剧本"""
    id: str
    novel_id: str
    novel_title: str
    title: str
    chapter_ids: List[str]
    scenes: List[ScriptScene]
    config: Optional[ScriptConfig] = None
    status: str  # pending/generating/completed/failed
    created_at: datetime
    updated_at: datetime
