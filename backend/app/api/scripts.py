"""
剧本生成 API 路由
"""
from fastapi import APIRouter, HTTPException
from typing import List
import uuid
from datetime import datetime

from app.models.script import ScriptGenerateRequest, Script, ScriptConfig
from app.services.novel_service import novel_service
from app.services.script_service import script_service
from app.utils.scene_splitter import process_chapters_to_scenes, scenes_to_dict

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
            selected_chapters.append({
                "id": chapter.id,
                "title": chapter.title,
                "content": chapter.content
            })
    
    # 生成剧本ID
    script_id = str(uuid.uuid4())
    
    # 创建任务文件夹
    script_service.create_script_task(
        script_id=script_id,
        novel_id=request.novel_id,
        novel_title=novel.title,
        chapter_ids=request.chapter_ids,
        config=request.config.dict() if request.config else None
    )
    
    # 分镜处理：使用 DeepSeek API 将章节内容智能分割成场景
    scenes = await process_chapters_to_scenes(selected_chapters)
    
    # 保存场景到文件
    scenes_dict = scenes_to_dict(scenes)
    script_service.save_scenes(script_id, scenes_dict)
    
    return {
        "script_id": script_id,
        "novel_id": request.novel_id,
        "novel_title": novel.title,
        "selected_chapters": [
            {"id": ch["id"], "title": ch["title"]} for ch in selected_chapters
        ],
        "scenes": scenes_dict,
        "scene_count": len(scenes),
        "config": request.config.dict() if request.config else None,
        "status": "scenes_generated",
        "message": "剧本生成任务已创建，章节已分割为场景",
        "created_at": datetime.now().isoformat()
    }


@router.get("/{script_id}", response_model=dict)
async def get_script(script_id: str):
    """
    获取剧本详情
    """
    task = script_service.get_task(script_id)
    if not task:
        raise HTTPException(status_code=404, detail="剧本任务不存在")
    
    # 读取场景数据
    scenes = []
    scenes_path = script_service.get_task_file(script_id, "scenes.json")
    if scenes_path:
        import json
        with open(scenes_path, 'r', encoding='utf-8') as f:
            scenes_data = json.load(f)
            scenes = scenes_data.get("scenes", [])
    
    return {
        "code": 200,
        "data": {
            "task": task,
            "scenes": scenes,
            "scene_count": len(scenes)
        },
        "message": "success"
    }


@router.get("/", response_model=dict)
async def list_scripts(novel_id: str = None):
    """
    获取剧本列表
    
    可选参数 novel_id 过滤特定小说的剧本
    """
    tasks = script_service.list_tasks(novel_id)
    return {
        "code": 200,
        "data": tasks,
        "message": "success"
    }
