"""
剧本生成 API 路由
"""
from fastapi import APIRouter, HTTPException
from typing import List
import uuid
from datetime import datetime

from app.models.script import ScriptGenerateRequest, Script, ScriptConfig
from app.services.novel_service import novel_service

router = APIRouter()


@router.post("/generate", response_model=dict)
async def generate_script(request: ScriptGenerateRequest):
    """
    生成剧本
    
    接收小说ID和章节ID列表，返回剧本生成任务ID
    """
    # 验证小说是否存在
    novel = novel_service.get_novel(request.novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    # 验证章节是否存在
    chapters = novel_service.get_novel_chapters(request.novel_id)
    chapter_ids = [ch.id for ch in chapters]
    invalid_chapters = [cid for cid in request.chapter_ids if cid not in chapter_ids]
    if invalid_chapters:
        raise HTTPException(status_code=400, detail=f"无效的章节ID: {invalid_chapters}")
    
    # 获取选中的章节内容
    selected_chapters = []
    for cid in request.chapter_ids:
        chapter = novel_service.get_chapter(request.novel_id, cid)
        if chapter:
            selected_chapters.append(chapter)
    
    # 生成剧本ID
    script_id = str(uuid.uuid4())
    
    # TODO: 调用AI服务生成剧本
    # 这里先返回任务ID，后续实现异步生成
    
    return {
        "script_id": script_id,
        "novel_id": request.novel_id,
        "novel_title": novel.title,
        "selected_chapters": [
            {"id": ch.id, "title": ch.title} for ch in selected_chapters
        ],
        "config": request.config.dict() if request.config else None,
        "status": "pending",
        "message": "剧本生成任务已创建",
        "created_at": datetime.now().isoformat()
    }


@router.get("/{script_id}", response_model=dict)
async def get_script(script_id: str):
    """
    获取剧本详情
    """
    # TODO: 从存储中获取剧本
    raise HTTPException(status_code=501, detail="功能开发中")


@router.get("/", response_model=List[dict])
async def list_scripts(novel_id: str = None):
    """
    获取剧本列表
    
    可选参数 novel_id 过滤特定小说的剧本
    """
    # TODO: 从存储中获取剧本列表
    return []
