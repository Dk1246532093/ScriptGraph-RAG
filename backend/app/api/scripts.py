"""
剧本生成 API 路由
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, AsyncGenerator
import uuid
import json
from datetime import datetime
from pathlib import Path
import asyncio

from app.models.script import ScriptGenerateRequest, Script, ScriptConfig
from app.services.novel_service import novel_service
from app.services.script_service import script_service
from app.utils.scene_splitter import process_chapters_to_scenes, scenes_to_dict
from app.utils.script_generator import generate_script_from_scenes, generate_script_from_scenes_stream

router = APIRouter()


def sse_event(event: str, data: dict) -> str:
    """生成 SSE 事件格式"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/generate", response_model=dict)
async def generate_script(request: ScriptGenerateRequest):
    """
    生成剧本（非流式）
    
    接收小说ID和章节ID列表，返回完整剧本生成结果
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


async def generate_script_stream_generator(request: ScriptGenerateRequest) -> AsyncGenerator[str, None]:
    """
    生成剧本的流式生成器
    
    通过 SSE 实时返回每个阶段的进度和结果
    """
    try:
        # 1. 验证阶段
        yield sse_event("progress", {
            "stage": "validating",
            "message": "正在验证小说和章节...",
            "progress": 5
        })
        await asyncio.sleep(0.1)
        
        # 验证小说是否存在
        novel = novel_service.get_novel(request.novel_id)
        if not novel:
            yield sse_event("error", {"message": "小说不存在"})
            return
        
        # 验证章节是否存在
        chapters = novel_service.get_novel_chapters(request.novel_id)
        chapter_ids = [ch.id for ch in chapters]
        invalid_chapters = [cid for cid in request.chapter_ids if cid not in chapter_ids]
        if invalid_chapters:
            yield sse_event("error", {"message": f"无效的章节ID: {invalid_chapters}"})
            return
        
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
        
        yield sse_event("progress", {
            "stage": "initialized",
            "message": "验证完成，开始生成任务...",
            "progress": 10,
            "script_id": script_id
        })
        
        # 创建任务文件夹
        script_service.create_script_task(
            script_id=script_id,
            novel_id=request.novel_id,
            novel_title=novel.title,
            chapter_ids=request.chapter_ids,
            config=request.config.dict() if request.config else None
        )
        
        # 2. 场景分割阶段
        yield sse_event("progress", {
            "stage": "scene_splitting",
            "message": "正在使用 DeepSeek API 智能分割场景...",
            "progress": 20
        })
        
        scenes = await process_chapters_to_scenes(selected_chapters)
        scenes_dict = scenes_to_dict(scenes)
        script_service.save_scenes(script_id, scenes_dict)
        
        yield sse_event("scenes_ready", {
            "message": f"场景分割完成，共 {len(scenes)} 个场景",
            "progress": 40,
            "scene_count": len(scenes),
            "scenes": scenes_dict
        })
        
        # 3. 知识图谱抽取阶段
        yield sse_event("progress", {
            "stage": "knowledge_graph",
            "message": "正在抽取三层知识图谱（人物、地点、事件）...",
            "progress": 50
        })
        
        kg_path = await script_service.generate_and_save_knowledge_graph(
            script_id, selected_chapters
        )
        
        kg_data = {}
        if kg_path.exists():
            with open(kg_path, 'r', encoding='utf-8') as f:
                kg_file_content = json.load(f)
                kg_data = kg_file_content.get("data", {})
        
        yield sse_event("knowledge_graph_ready", {
            "message": f"知识图谱抽取完成，共 {len(kg_data.get('nodes', []))} 个节点，{len(kg_data.get('edges', []))} 条关系",
            "progress": 70,
            "kg_node_count": len(kg_data.get("nodes", [])),
            "kg_edge_count": len(kg_data.get("edges", [])),
            "knowledge_graph": kg_data
        })
        
        # 4. 剧本生成阶段（流式）
        yield sse_event("progress", {
            "stage": "script_generating",
            "message": f"正在生成剧本，共 {len(scenes_dict)} 个场景...",
            "progress": 75
        })
        
        script_data = []
        total_beats = 0
        total_lines = 0
        
        try:
            # 使用流式生成器，每完成一个场景就发送给前端
            async for scene_result in generate_script_from_scenes_stream(scenes_dict, kg_data):
                scene_script = scene_result["scene"]
                scene_index = scene_result["index"]
                total_scenes = scene_result["total"]
                scene_progress = scene_result["progress_percent"]
                
                script_data.append(scene_script)
                
                # 计算当前场景的节拍和台词数
                scene_beats = len(scene_script.get("beats", []))
                scene_lines = sum(
                    len(beat.get("script", [])) for beat in scene_script.get("beats", [])
                )
                total_beats += scene_beats
                total_lines += scene_lines
                
                # 发送单个场景完成的事件
                yield sse_event("scene_generated", {
                    "message": f"场景 {scene_index + 1}/{total_scenes} 生成完成: {scene_script.get('title', '')}",
                    "progress": 75 + int(scene_progress * 0.2),  # 75%~95%
                    "scene_index": scene_index,
                    "total_scenes": total_scenes,
                    "scene": scene_script,
                    "scene_beats": scene_beats,
                    "scene_lines": scene_lines,
                    "accumulated_beats": total_beats,
                    "accumulated_lines": total_lines
                })
                
                print(f"[Stream] Scene {scene_index + 1}/{total_scenes} sent to client")
            
            print(f"Script generated: {len(script_data)} scenes")
            
        except Exception as e:
            print(f"Error generating script: {e}")
            import traceback
            traceback.print_exc()
            yield sse_event("error", {"message": f"剧本生成失败: {str(e)}"})
            return
        
        # 保存剧本
        if script_data:
            save_path = script_service.save_script(script_id, script_data)
            print(f"Script saved to: {save_path}")
        
        yield sse_event("script_ready", {
            "message": f"剧本生成完成，共 {len(script_data)} 个场景，{total_beats} 个节拍",
            "progress": 95,
            "script_scene_count": len(script_data),
            "script_beat_count": total_beats,
            "script_line_count": total_lines
        })
        
        # 5. 完成阶段
        yield sse_event("completed", {
            "message": "剧本生成全部完成！",
            "progress": 100,
            "script_id": script_id,
            "novel_id": request.novel_id,
            "novel_title": novel.title,
            "selected_chapters": [
                {"id": ch["id"], "title": ch["title"]} for ch in selected_chapters
            ],
            "scene_count": len(scenes),
            "kg_node_count": len(kg_data.get("nodes", [])),
            "kg_edge_count": len(kg_data.get("edges", [])),
            "script_scene_count": len(script_data),
            "script_beat_count": total_beats,
            "script_line_count": total_lines,
            "status": "completed",
            "created_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Stream error: {e}")
        import traceback
        traceback.print_exc()
        yield sse_event("error", {"message": f"生成过程出错: {str(e)}"})


@router.post("/generate/stream")
async def generate_script_stream(request: ScriptGenerateRequest):
    """
    流式生成剧本
    
    通过 SSE 实时返回生成进度，前端可以按阶段展示：
    - progress: 进度更新（stage: validating/scene_splitting/knowledge_graph/script_generating）
    - scenes_ready: 场景分割完成
    - knowledge_graph_ready: 知识图谱抽取完成
    - script_ready: 剧本生成完成
    - completed: 全部完成
    - error: 发生错误
    
    前端使用 EventSource 接收：
    ```javascript
    const eventSource = new EventSource('/api/scripts/generate/stream');
    eventSource.addEventListener('progress', (e) => { ... });
    eventSource.addEventListener('scenes_ready', (e) => { ... });
    eventSource.addEventListener('completed', (e) => { ... });
    ```
    """
    return StreamingResponse(
        generate_script_stream_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用 Nginx 缓冲
        }
    )


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


from fastapi.responses import PlainTextResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
from app.utils.script_exporter import ScriptExporter, export_script_to_yaml, export_script_to_fountain


class ScriptExportRequest(BaseModel):
    """剧本导出请求"""
    script_data: List[dict]  # 剧本数据
    novel_title: Optional[str] = ""  # 小说标题
    novel_id: Optional[str] = ""  # 小说ID
    format: str = "yaml"  # 导出格式
    download: bool = False  # 是否下载


@router.post("/export")
async def export_script_from_data(request: ScriptExportRequest):
    """
    从传入的剧本数据导出为指定格式
    
    支持前端修改剧本后实时导出
    
    Args:
        request: 导出请求，包含剧本数据和元数据
    
    Returns:
        导出的剧本内容
    """
    script_data = request.script_data
    
    if not script_data:
        raise HTTPException(status_code=400, detail="剧本数据不能为空")
    
    # 根据格式导出
    format = request.format.lower()
    script_id = str(uuid.uuid4())[:8]  # 生成临时ID用于文件名
    
    if format == "yaml":
        content = export_script_to_yaml(
            script_data,
            novel_title=request.novel_title,
            novel_id=request.novel_id,
            script_id=script_id
        )
        media_type = "application/x-yaml"
        file_ext = "yaml"
    
    elif format == "json":
        content = ScriptExporter.to_json(
            script_data,
            novel_title=request.novel_title,
            novel_id=request.novel_id,
            script_id=script_id
        )
        media_type = "application/json"
        file_ext = "json"
    
    elif format == "fountain":
        content = export_script_to_fountain(
            script_data,
            novel_title=request.novel_title
        )
        media_type = "text/plain"
        file_ext = "fountain"
    
    else:
        raise HTTPException(status_code=400, detail=f"不支持的导出格式: {format}")
    
    if request.download:
        # 生成文件名
        safe_title = request.novel_title.replace(" ", "_").replace("/", "_") if request.novel_title else "script"
        filename = f"{safe_title}_script.{file_ext}"
        
        # 保存到临时文件
        temp_path = Path(f"storage/exports/{script_id}.{file_ext}")
        ScriptExporter.save_to_file(content, temp_path)
        
        return FileResponse(
            temp_path,
            media_type=media_type,
            filename=filename
        )
    else:
        return PlainTextResponse(
            content=content,
            media_type=media_type
        )


@router.get("/{script_id}/export")
async def export_script(
    script_id: str,
    format: str = "yaml",
    download: bool = False
):
    """
    从已保存的剧本任务导出为指定格式
    
    Args:
        script_id: 剧本任务ID
        format: 导出格式，支持 yaml/json/fountain
        download: 是否作为文件下载
    
    Returns:
        导出的剧本内容
    """
    # 验证剧本存在
    task = script_service.get_task(script_id)
    if not task:
        raise HTTPException(status_code=404, detail="剧本任务不存在")
    
    # 读取剧本数据
    script_path = script_service.get_task_file(script_id, "script.json")
    if not script_path:
        raise HTTPException(status_code=404, detail="剧本尚未生成")
    
    with open(script_path, 'r', encoding='utf-8') as f:
        script_file_content = json.load(f)
        script_data = script_file_content.get("data", [])
    
    if not script_data:
        raise HTTPException(status_code=404, detail="剧本内容为空")
    
    # 获取元数据
    novel_title = task.get("novel_title", "")
    novel_id = task.get("novel_id", "")
    
    # 根据格式导出
    format = format.lower()
    
    if format == "yaml":
        content = export_script_to_yaml(
            script_data,
            novel_title=novel_title,
            novel_id=novel_id,
            script_id=script_id
        )
        media_type = "application/x-yaml"
        file_ext = "yaml"
    
    elif format == "json":
        content = ScriptExporter.to_json(
            script_data,
            novel_title=novel_title,
            novel_id=novel_id,
            script_id=script_id
        )
        media_type = "application/json"
        file_ext = "json"
    
    elif format == "fountain":
        content = export_script_to_fountain(
            script_data,
            novel_title=novel_title
        )
        media_type = "text/plain"
        file_ext = "fountain"
    
    else:
        raise HTTPException(status_code=400, detail=f"不支持的导出格式: {format}")
    
    if download:
        # 生成文件名
        safe_title = novel_title.replace(" ", "_").replace("/", "_") if novel_title else "script"
        filename = f"{safe_title}_script.{file_ext}"
        
        # 保存到临时文件
        temp_path = Path(f"storage/exports/{script_id}.{file_ext}")
        ScriptExporter.save_to_file(content, temp_path)
        
        return FileResponse(
            temp_path,
            media_type=media_type,
            filename=filename
        )
    else:
        return PlainTextResponse(
            content=content,
            media_type=media_type
        )
