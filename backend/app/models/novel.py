"""
小说数据模型
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class Chapter(BaseModel):
    """章节模型"""
    id: str
    title: str
    index: int
    content: Optional[str] = None


class Novel(BaseModel):
    """小说模型"""
    id: str
    title: str
    author: Optional[str] = None
    chapterCount: int
    status: str = "已上传"
    createdAt: datetime
    updatedAt: datetime
    filePath: str


class NovelDetail(Novel):
    """小说详情"""
    chapters: List[Chapter] = []
