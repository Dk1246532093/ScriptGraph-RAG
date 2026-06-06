"""
剧本生成 API 路由
"""
from fastapi import APIRouter, HTTPException
from typing import List
import uuid
import json
from datetime import datetime
from pathlib import Path

from app.models.script import ScriptGenerateRequest, Script, ScriptConfig
from app.services.novel_service import novel_service
from app.services.script_service import script_service
from app.utils.scene_splitter import process_chapters_to_scenes, scenes_to_dict
from app.utils.script_generator import generate_script_from_scenes

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
    
    # 知识图谱抽取：从章节原文中抽取三层知识图谱（人物、地点、事件）
    kg_path = await script_service.generate_and_save_knowledge_graph(
        script_id, selected_chapters
    )
    
    # 读取保存的知识图谱数据
    kg_data = {}
    if kg_path.exists():
        with open(kg_path, 'r', encoding='utf-8') as f:
            kg_file_content = json.load(f)
            kg_data = kg_file_content.get("data", {})
    
    # 生成详细剧本：根据场景和知识图谱生成完整剧本
    print(f"Generating final script for {script_id}...")
    try:
        script_data = await generate_script_from_scenes(scenes_dict, kg_data)
        print(f"Script generated: {len(script_data)} scenes")
    except Exception as e:
        print(f"Error generating script: {e}")
        import traceback
        traceback.print_exc()
        script_data = []
    
    # 保存剧本
    if script_data:
        save_path = script_service.save_script(script_id, script_data)
        print(f"Script saved to: {save_path}")
    else:
        print("Warning: No script data to save")
    
    # 统计剧本信息
    total_beats = sum(len(scene.get("beats", [])) for scene in script_data)
    total_lines = sum(
        sum(len(beat.get("script", [])) for beat in scene.get("beats", []))
        for scene in script_data
    )
    
    return {
        "script_id": script_id,
        "novel_id": request.novel_id,
        "novel_title": novel.title,
        "selected_chapters": [
            {"id": ch["id"], "title": ch["title"]} for ch in selected_chapters
        ],
        "scenes": scenes_dict,
        "scene_count": len(scenes),
        "knowledge_graph": kg_data,
        "kg_node_count": len(kg_data.get("nodes", [])),
        "kg_edge_count": len(kg_data.get("edges", [])),
        "script": script_data,
        "script_scene_count": len(script_data),
        "script_beat_count": total_beats,
        "script_line_count": total_lines,
        "config": request.config.dict() if request.config else None,
        "status": "completed",
        "message": "剧本生成完成，包含场景分割、知识图谱和详细剧本",
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
    
    # 读取知识图谱数据
    kg_data = {}
    kg_path = script_service.get_task_file(script_id, "knowledge_graph.json")
    if kg_path:
        import json
        with open(kg_path, 'r', encoding='utf-8') as f:
            kg_file_content = json.load(f)
            kg_data = kg_file_content.get("data", {})
    
    return {
        "code": 200,
        "data": {
            "task": task,
            "scenes": scenes,
            "scene_count": len(scenes),
            "knowledge_graph": kg_data,
            "kg_node_count": len(kg_data.get("nodes", [])),
            "kg_edge_count": len(kg_data.get("edges", []))
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





@router.get("/{script_id}/script", response_model=dict)
async def get_script_content(script_id: str):
    """
    获取已生成的剧本内容
    
    Args:
        script_id: 剧本任务ID
    
    Returns:
        剧本内容
    """
    task = script_service.get_task(script_id)
    if not task:
        raise HTTPException(status_code=404, detail="剧本任务不存在")
    
    script_path = script_service.get_task_file(script_id, "script.json")
    if not script_path:
        raise HTTPException(status_code=404, detail="剧本尚未生成")
    
    with open(script_path, 'r', encoding='utf-8') as f:
        script_file_content = json.load(f)
        script_data = script_file_content.get("data", [])
    
    return {
        "code": 200,
        "data": {
            "script_id": script_id,
            "scenes": script_data,
            "scene_count": len(script_data)
        },
        "message": "success"
    }
