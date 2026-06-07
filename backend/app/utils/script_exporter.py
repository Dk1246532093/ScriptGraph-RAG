"""
剧本导出模块
支持导出为 YAML、JSON、Fountain 等格式
"""

import json
import yaml
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path


class ScriptExporter:
    """剧本导出器"""
    
    @staticmethod
    def to_yaml(
        script_data: List[Dict[str, Any]],
        novel_title: str = "",
        novel_id: str = "",
        script_id: str = "",
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        将剧本导出为 YAML 格式
        
        Args:
            script_data: 剧本数据列表
            novel_title: 小说标题
            novel_id: 小说ID
            script_id: 剧本ID
            metadata: 额外元数据
            
        Returns:
            YAML 格式字符串
        """
        export_data = {
            "script": {
                "metadata": {
                    "title": f"{novel_title} - 剧本",
                    "novel_title": novel_title,
                    "novel_id": novel_id,
                    "script_id": script_id,
                    "export_time": datetime.now().isoformat(),
                    "format_version": "1.0",
                    **(metadata or {})
                },
                "statistics": ScriptExporter._calc_statistics(script_data),
                "scenes": []
            }
        }
        
        # 转换场景数据
        for scene_idx, scene in enumerate(script_data, 1):
            scene_export = {
                "scene_number": scene_idx,
                "scene_id": scene.get("scene_id", ""),
                "title": scene.get("title", ""),
                "location": scene.get("location", ""),
                "summary": scene.get("summary", ""),
                "beats": []
            }
            
            # 转换节拍数据
            for beat_idx, beat in enumerate(scene.get("beats", []), 1):
                beat_export = {
                    "beat_number": beat_idx,
                    "beat_id": beat.get("beat_id", ""),
                    "title": beat.get("title", ""),
                    "theme": beat.get("theme", ""),
                    "location": beat.get("location", ""),
                    "atmosphere": beat.get("atmosphere", ""),
                    "characters": beat.get("characters", []),
                    "lines": []
                }
                
                # 转换台词数据
                for line_idx, line in enumerate(beat.get("script", []), 1):
                    voice = line.get("voice") or {}
                    line_export = {
                        "line_number": line_idx,
                        "character": line.get("character", ""),
                        "expression": line.get("expression", ""),
                        "action": line.get("action", ""),
                        "dialogue": voice.get("text", line.get("text", "")),
                        "voice": {
                            "emotion": voice.get("emotion", ""),
                            "tone": voice.get("tone", "")
                        } if voice else None
                    }
                    # 移除空值
                    line_export = {k: v for k, v in line_export.items() if v}
                    beat_export["lines"].append(line_export)
                
                scene_export["beats"].append(beat_export)
            
            export_data["script"]["scenes"].append(scene_export)
        
        # 导出为 YAML
        return yaml.dump(
            export_data,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
            width=1000
        )
    
    @staticmethod
    def to_json(
        script_data: List[Dict[str, Any]],
        novel_title: str = "",
        novel_id: str = "",
        script_id: str = "",
        metadata: Dict[str, Any] = None
    ) -> str:
        """导出为格式化的 JSON"""
        export_data = {
            "script": {
                "metadata": {
                    "title": f"{novel_title} - 剧本",
                    "novel_title": novel_title,
                    "novel_id": novel_id,
                    "script_id": script_id,
                    "export_time": datetime.now().isoformat(),
                    **(metadata or {})
                },
                "statistics": ScriptExporter._calc_statistics(script_data),
                "scenes": script_data
            }
        }
        return json.dumps(export_data, ensure_ascii=False, indent=2)
    
    @staticmethod
    def to_fountain(
        script_data: List[Dict[str, Any]],
        novel_title: str = ""
    ) -> str:
        """
        导出为 Fountain 格式（剧本行业标准格式）
        """
        lines = []
        
        # 标题页
        lines.append(f"Title: {novel_title}")
        lines.append(f"Credit: 由 ScriptGraph-RAG 生成")
        lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        lines.append("")
        
        # 场景
        for scene in script_data:
            lines.append(f".{scene.get('title', '')}")
            lines.append("")
            
            for beat in scene.get("beats", []):
                lines.append(f"/* {beat.get('title', '')} */")
                lines.append("")
                
                for line in beat.get("script", []):
                    character = line.get("character", "")
                    voice = line.get("voice", {})
                    text = voice.get("text", line.get("text", ""))
                    
                    lines.append(character.upper())
                    lines.append(text)
                    lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def _calc_statistics(script_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算剧本统计信息"""
        scene_count = len(script_data)
        beat_count = sum(len(scene.get("beats", [])) for scene in script_data)
        line_count = sum(
            sum(len(beat.get("script", [])) for beat in scene.get("beats", []))
            for scene in script_data
        )
        
        # 统计角色出场
        character_appearances = {}
        for scene in script_data:
            for beat in scene.get("beats", []):
                for line in beat.get("script", []):
                    char = line.get("character", "")
                    if char:
                        character_appearances[char] = character_appearances.get(char, 0) + 1
        
        return {
            "scene_count": scene_count,
            "beat_count": beat_count,
            "line_count": line_count,
            "character_count": len(character_appearances),
            "character_appearances": character_appearances
        }
    
    @staticmethod
    def save_to_file(
        content: str,
        filepath: Path,
        encoding: str = "utf-8"
    ) -> Path:
        """保存内容到文件"""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, "w", encoding=encoding) as f:
            f.write(content)
        
        return filepath


# 便捷函数
def export_script_to_yaml(script_data: List[Dict[str, Any]], **kwargs) -> str:
    """快捷导出为 YAML"""
    return ScriptExporter.to_yaml(script_data, **kwargs)


def export_script_to_json(script_data: List[Dict[str, Any]], **kwargs) -> str:
    """快捷导出为 JSON"""
    return ScriptExporter.to_json(script_data, **kwargs)


def export_script_to_fountain(script_data: List[Dict[str, Any]], **kwargs) -> str:
    """快捷导出为 Fountain"""
    return ScriptExporter.to_fountain(script_data, **kwargs)
