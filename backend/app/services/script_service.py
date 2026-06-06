"""
剧本存储服务
管理剧本生成任务的存储
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..core.config import settings
from ..utils.knowledge_graph import extract_knowledge_graph


class ScriptService:
    """剧本服务"""
    
    def __init__(self):
        self.result_dir = Path(settings.STORAGE_DIR) / "result"
        self.result_dir.mkdir(parents=True, exist_ok=True)
    
    def create_script_task(self, script_id: str, novel_id: str, novel_title: str, 
                          chapter_ids: List[str], config: Optional[Dict[str, Any]] = None) -> Path:
        """
        创建剧本任务文件夹
        
        Returns:
            任务文件夹路径
        """
        task_dir = self.result_dir / script_id
        task_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建任务元数据
        task_meta = {
            "script_id": script_id,
            "novel_id": novel_id,
            "novel_title": novel_title,
            "chapter_ids": chapter_ids,
            "config": config,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "files": {}
        }
        
        # 保存任务元数据
        meta_path = task_dir / "task.json"
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(task_meta, f, ensure_ascii=False, indent=2)
        
        return task_dir
    
    def save_scenes(self, script_id: str, scenes: List[Dict[str, Any]]) -> Path:
        """
        保存分镜场景
        
        Returns:
            场景文件路径
        """
        task_dir = self.result_dir / script_id
        task_dir.mkdir(parents=True, exist_ok=True)
        
        scenes_path = task_dir / "scenes.json"
        with open(scenes_path, 'w', encoding='utf-8') as f:
            json.dump({
                "script_id": script_id,
                "scenes": scenes,
                "scene_count": len(scenes),
                "saved_at": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        
        # 更新任务元数据
        self._update_task_meta(script_id, {
            "files.scenes": str(scenes_path.relative_to(self.result_dir)),
            "status": "scenes_generated"
        })
        
        return scenes_path
    
    async def generate_and_save_knowledge_graph(
        self, 
        script_id: str, 
        chapters: List[Dict[str, Any]]
    ) -> Path:
        """
        从章节原文中抽取知识图谱并保存
        
        Args:
            script_id: 剧本任务ID
            chapters: 章节列表，每个章节包含 id, title, content
            
        Returns:
            图谱文件路径
        """
        # 抽取知识图谱
        kg_data = await extract_knowledge_graph(chapters)
        
        # 保存到文件
        return self.save_knowledge_graph(script_id, kg_data)
    
    def save_knowledge_graph(self, script_id: str, kg_data: Dict[str, Any]) -> Path:
        """
        保存知识图谱
        
        Returns:
            图谱文件路径
        """
        task_dir = self.result_dir / script_id
        task_dir.mkdir(parents=True, exist_ok=True)
        
        kg_path = task_dir / "knowledge_graph.json"
        with open(kg_path, 'w', encoding='utf-8') as f:
            json.dump({
                "script_id": script_id,
                "data": kg_data,
                "saved_at": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        
        # 更新任务元数据
        self._update_task_meta(script_id, {
            "files.knowledge_graph": str(kg_path.relative_to(self.result_dir)),
            "status": "kg_generated"
        })
        
        return kg_path
    
    def save_script(self, script_id: str, script_data: Dict[str, Any]) -> Path:
        """
        保存剧本 JSON
        
        Returns:
            剧本文件路径
        """
        task_dir = self.result_dir / script_id
        task_dir.mkdir(parents=True, exist_ok=True)
        
        script_path = task_dir / "script.json"
        with open(script_path, 'w', encoding='utf-8') as f:
            json.dump({
                "script_id": script_id,
                "data": script_data,
                "saved_at": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        
        # 更新任务元数据
        self._update_task_meta(script_id, {
            "files.script": str(script_path.relative_to(self.result_dir)),
            "status": "script_generated"
        })
        
        return script_path
    
    def save_yaml(self, script_id: str, yaml_content: str) -> Path:
        """
        保存 YAML 剧本
        
        Returns:
            YAML 文件路径
        """
        task_dir = self.result_dir / script_id
        task_dir.mkdir(parents=True, exist_ok=True)
        
        yaml_path = task_dir / "script.yaml"
        with open(yaml_path, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        
        # 更新任务元数据
        self._update_task_meta(script_id, {
            "files.yaml": str(yaml_path.relative_to(self.result_dir)),
            "status": "completed"
        })
        
        return yaml_path
    
    def get_task(self, script_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务信息
        """
        meta_path = self.result_dir / script_id / "task.json"
        if not meta_path.exists():
            return None
        
        with open(meta_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_task_file(self, script_id: str, filename: str) -> Optional[Path]:
        """
        获取任务文件路径
        """
        file_path = self.result_dir / script_id / filename
        if file_path.exists():
            return file_path
        return None
    
    def list_tasks(self, novel_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出所有任务
        
        Args:
            novel_id: 可选，过滤特定小说的任务
        """
        tasks = []
        
        if not self.result_dir.exists():
            return tasks
        
        for task_dir in self.result_dir.iterdir():
            if task_dir.is_dir():
                meta_path = task_dir / "task.json"
                if meta_path.exists():
                    with open(meta_path, 'r', encoding='utf-8') as f:
                        task = json.load(f)
                        if novel_id is None or task.get("novel_id") == novel_id:
                            tasks.append(task)
        
        # 按创建时间倒序
        tasks.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return tasks
    
    def _update_task_meta(self, script_id: str, updates: Dict[str, Any]):
        """
        更新任务元数据
        """
        meta_path = self.result_dir / script_id / "task.json"
        if not meta_path.exists():
            return
        
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        
        # 处理嵌套更新（如 "files.scenes"）
        for key, value in updates.items():
            if "." in key:
                parts = key.split(".")
                target = meta
                for part in parts[:-1]:
                    if part not in target:
                        target[part] = {}
                    target = target[part]
                target[parts[-1]] = value
            else:
                meta[key] = value
        
        meta["updated_at"] = datetime.now().isoformat()
        
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)


# 全局服务实例
script_service = ScriptService()
