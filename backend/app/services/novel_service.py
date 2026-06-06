"""
小说服务层
"""

import os
import json
import uuid
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from app.core.config import settings
from app.models.novel import Novel, NovelDetail, Chapter
from app.utils.txt_parser import parse_txt_novel, extract_title_from_filename


class NovelService:
    """小说服务"""
    
    def __init__(self):
        self.novels_dir = Path(settings.NOVELS_DIR)
        self.novels_dir.mkdir(parents=True, exist_ok=True)
        
        # 元数据文件放到 novels 目录下
        self.metadata_file = self.novels_dir / "metadata.json"
        self._metadata = self._load_metadata()
    
    def _load_metadata(self) -> dict:
        """加载元数据"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"novels": []}
    
    def _save_metadata(self):
        """保存元数据"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self._metadata, f, ensure_ascii=False, indent=2)
    
    def get_all_novels(self) -> List[Novel]:
        """获取所有小说列表"""
        novels = []
        for novel_data in self._metadata.get("novels", []):
            novels.append(Novel(**novel_data))
        return novels
    
    def get_novel(self, novel_id: str) -> Optional[NovelDetail]:
        """获取小说详情"""
        for novel_data in self._metadata.get("novels", []):
            if novel_data["id"] == novel_id:
                novel = NovelDetail(**novel_data)
                # 加载章节信息
                chapters_file = self.novels_dir / novel_id / "chapters.json"
                if chapters_file.exists():
                    with open(chapters_file, 'r', encoding='utf-8') as f:
                        chapters_data = json.load(f)
                        novel.chapters = [Chapter(**c) for c in chapters_data]
                return novel
        return None
    
    def get_chapter(self, novel_id: str, chapter_id: str) -> Optional[Chapter]:
        """获取章节内容"""
        novel = self.get_novel(novel_id)
        if novel:
            for chapter in novel.chapters:
                if chapter.id == chapter_id:
                    return chapter
        return None
    
    def create_novel(self, title: str, file_content: bytes, filename: str) -> Novel:
        """创建新小说"""
        novel_id = str(uuid.uuid4())
        novel_dir = self.novels_dir / novel_id
        novel_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存原始文件
        file_path = novel_dir / "original.txt"
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # 解析章节（自动检测编码）
        chapters = parse_txt_novel(file_content)
        
        # 保存章节数据
        chapters_data = []
        for i, chapter in enumerate(chapters):
            chapter_id = f"chapter_{i + 1}"
            chapters_data.append({
                "id": chapter_id,
                "title": chapter.title,
                "index": chapter.index,
                "content": chapter.content
            })
        
        chapters_file = novel_dir / "chapters.json"
        with open(chapters_file, 'w', encoding='utf-8') as f:
            json.dump(chapters_data, f, ensure_ascii=False, indent=2)
        
        # 创建小说记录
        now = datetime.now()
        novel_data = {
            "id": novel_id,
            "title": title or extract_title_from_filename(filename),
            "author": None,
            "chapterCount": len(chapters),
            "status": "已解析",
            "createdAt": now.isoformat(),
            "updatedAt": now.isoformat(),
            "filePath": str(file_path)
        }
        
        self._metadata["novels"].append(novel_data)
        self._save_metadata()
        
        return Novel(**novel_data)
    
    def delete_novel(self, novel_id: str) -> bool:
        """删除小说"""
        # 删除文件
        novel_dir = self.novels_dir / novel_id
        if novel_dir.exists():
            import shutil
            shutil.rmtree(novel_dir)
        
        # 删除元数据
        self._metadata["novels"] = [
            n for n in self._metadata["novels"] if n["id"] != novel_id
        ]
        self._save_metadata()
        
        return True


# 单例实例
novel_service = NovelService()
