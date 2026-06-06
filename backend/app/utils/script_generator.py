"""
剧本生成模块
使用 DeepSeek API 将场景和 beats 转换成详细剧本格式
"""

import json
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from openai import AsyncOpenAI

from ..core.config import settings


@dataclass
class ScriptLine:
    """剧本台词"""
    character: str
    expression: str
    action: str
    voice_emotion: str
    voice_tone: str
    text: str


@dataclass
class ScriptBeat:
    """剧本 Beat"""
    beat_id: str
    title: str
    theme: str
    location: str
    atmosphere: str
    characters: List[str]
    script: List[ScriptLine]


@dataclass
class ScriptScene:
    """剧本场景"""
    scene_id: str
    title: str
    location: str
    summary: str
    beats: List[ScriptBeat]


class DeepSeekScriptGenerator:
    """使用 DeepSeek API 生成详细剧本"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_API_BASE
        )
        self.model = "deepseek-v4-flash"
    
    async def generate_scene_script_with_ai(
        self,
        scene: Dict[str, Any],
        knowledge_graph: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        为整个场景生成详细剧本（一次性调用AI生成所有beats）
        
        Args:
            scene: 场景数据
            knowledge_graph: 知识图谱数据
        
        Returns:
            生成的场景剧本（包含所有beats）
        """
        if not settings.DEEPSEEK_API_KEY:
            print("WARNING: DEEPSEEK_API_KEY not set")
            return self._create_fallback_scene(scene)
        
        beats = scene.get("beats", [])
        if not beats:
            return self._create_fallback_scene(scene)
        
        # 构建角色信息
        characters_info = self._build_characters_info(scene.get("characters", []), knowledge_graph)
        
        # 构建beats列表
        beats_list = "\n".join([f"{i+1}. {beat}" for i, beat in enumerate(beats)])
        
        prompt = f"""你是一名资深影视编剧，擅长将小说情节转化为专业影视剧本。

请将以下场景的所有 beats 转化为详细的拍摄剧本格式。

====================
场景信息
====================
场景标题：{scene.get("title", "")}
场景地点：{scene.get("location", "")}
戏剧作用：{scene.get("dramatic_purpose", "")}
场景内容片段：
{scene.get("content", "")[:1000]}

====================
角色信息
====================
{characters_info}

====================
场景包含的 Beats（剧情节点）
====================
{beats_list}

====================
输出要求
====================

请生成以下格式的剧本内容，一次性返回该场景的所有 beats：

{{
  "scene_id": "{scene.get("scene_id", "")}",
  "title": "{scene.get("title", "")}",
  "location": "{scene.get("location", "")}",
  "summary": "场景概述",
  "beats": [
    {{
      "beat_id": "beat_1",
      "title": "第一个beat的标题",
      "theme": "主题（如：牺牲、爱情、冲突、逃亡等）",
      "location": "具体地点",
      "atmosphere": "氛围描述（如：悲壮、紧张、温馨、压抑等）",
      "characters": ["出场角色列表"],
      "script": [
        {{
          "character": "角色名",
          "expression": "表情（如：痛苦、坚定、温柔、愤怒等）",
          "action": "动作描述（如：握紧剑柄、回头望去、跌倒在地等）",
          "voice": {{
            "emotion": "情绪（如：决绝、悲伤、愤怒等）",
            "tone": "语气（如：低沉、颤抖、严厉、轻声等）",
            "text": "台词内容（根据小说原文改编，要有画面感）"
          }}
        }}
      ]
    }},
    {{
      "beat_id": "beat_2",
      "title": "第二个beat的标题",
      ...
    }}
  ]
}}

要求：
1. beats 数组包含 {len(beats)} 个元素，对应上面列出的所有剧情节点
2. 每个 beat 的 script 数组包含 3-8 个元素，每个元素是一个角色的台词或动作
3. 台词要有画面感，适合拍摄
4. 动作描述要具体，能指导演员表演
5. 表情和语气要符合角色情绪和场景氛围
6. beats 之间要有合理的过渡，体现剧情的发展
7. 保持忠实于原著情节
8. 只返回 JSON 格式，不要有其他文字
"""

        try:
            print(f"Calling DeepSeek API for scene: {scene.get('title', '')}...")
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一名专业影视编剧，擅长将小说转化为影视剧本。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            print(f"API response received, content length: {len(content) if content else 0}")
            
            if not content:
                print("Warning: Empty response from API")
                return self._create_fallback_scene(scene)
            
            try:
                result = json.loads(content)
                print(f"JSON parsed successfully, beats: {len(result.get('beats', []))}")
                # 确保返回的 beats 数量正确
                if "beats" in result and len(result["beats"]) == len(beats):
                    return result
                else:
                    print(f"Warning: Beats count mismatch, expected {len(beats)}, got {len(result.get('beats', []))}")
                    return self._create_fallback_scene(scene)
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
                return self._create_fallback_scene(scene)

        except Exception as e:
            print(f"DeepSeek API error: {e}")
            import traceback
            traceback.print_exc()
            return self._create_fallback_scene(scene)
    
    def _build_characters_info(self, characters: List[str], knowledge_graph: Dict[str, Any]) -> str:
        """构建角色信息字符串"""
        if not knowledge_graph or "nodes" not in knowledge_graph:
            return "\n".join([f"- {name}" for name in characters])
        
        nodes = knowledge_graph.get("nodes", [])
        char_info_list = []
        
        for char_name in characters:
            # 在知识图谱中查找角色信息
            for node in nodes:
                if node.get("name") == char_name and node.get("type") == "Character":
                    desc = node.get("description", "")
                    char_info_list.append(f"- {char_name}：{desc}")
                    break
            else:
                char_info_list.append(f"- {char_name}")
        
        return "\n".join(char_info_list) if char_info_list else "\n".join([f"- {name}" for name in characters])
    
    def _create_fallback_scene(self, scene: Dict[str, Any]) -> Dict[str, Any]:
        """创建回退的场景剧本（API 失败时使用）"""
        characters = scene.get("characters", [])
        beats = scene.get("beats", [])
        
        fallback_beats = []
        for i, beat_title in enumerate(beats, 1):
            fallback_beats.append({
                "beat_id": f"beat_{i}",
                "title": beat_title,
                "theme": "剧情发展",
                "location": scene.get("location", "未知地点"),
                "atmosphere": "紧张",
                "characters": characters,
                "script": [
                    {
                        "character": characters[0] if characters else "角色A",
                        "expression": "严肃",
                        "action": "环顾四周",
                        "voice": {
                            "emotion": "紧张",
                            "tone": "低沉",
                            "text": "情况紧急，我们必须马上行动。"
                        }
                    }
                ]
            })
        
        return {
            "scene_id": scene.get("scene_id", ""),
            "title": scene.get("title", ""),
            "location": scene.get("location", ""),
            "summary": scene.get("dramatic_purpose", ""),
            "beats": fallback_beats
        }
    
    async def generate_scene_script(
        self,
        scene: Dict[str, Any],
        knowledge_graph: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        为整个场景生成剧本（包含所有 beats）
        
        Args:
            scene: 场景数据
            knowledge_graph: 知识图谱数据
        
        Returns:
            完整的场景剧本
        """
        # 使用 AI 一次性生成整个场景的所有 beats
        return await self.generate_scene_script_with_ai(scene, knowledge_graph)


# 全局生成器实例
_generator = None

def get_generator() -> DeepSeekScriptGenerator:
    """获取生成器实例（单例模式）"""
    global _generator
    if _generator is None:
        _generator = DeepSeekScriptGenerator()
    return _generator


async def generate_script_from_scenes(
    scenes: List[Dict[str, Any]],
    knowledge_graph: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    从场景列表生成完整剧本
    
    Args:
        scenes: 场景数据列表
        knowledge_graph: 知识图谱数据
    
    Returns:
        剧本数据列表
    """
    generator = get_generator()
    
    # 逐个场景生成（避免过多并发）
    script_scenes = []
    for scene in scenes:
        print(f"Generating script for scene: {scene.get('title', '')}...")
        script_scene = await generator.generate_scene_script(scene, knowledge_graph)
        script_scenes.append(script_scene)
    
    return script_scenes


def script_to_dict(script_scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """将剧本对象列表转换为字典列表（备用，实际使用字典直接返回）"""
    # 实际业务逻辑中直接返回字典，此函数保留用于类型兼容
    return script_scenes if isinstance(script_scenes, list) else []
