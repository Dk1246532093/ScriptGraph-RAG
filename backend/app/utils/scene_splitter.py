"""
分镜处理模块
使用 DeepSeek API 将小说章节内容智能分割成 scenes
"""

import re
import json
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from openai import AsyncOpenAI

from app.core.config import settings


@dataclass
class Scene:
    """场景"""
    scene_id: str
    title: str
    location: str
    characters: List[str]
    content: str
    chapter_id: str
    chapter_title: str


class DeepSeekSceneSplitter:
    """使用 DeepSeek API 进行智能分镜"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_API_BASE
        )
        self.model = "deepseek-v4-flash"  # 使用 DeepSeek V4 Flash 模型
    
    async def split_chapter_with_ai(self, chapter_content: str, chapter_title: str) -> List[Dict[str, Any]]:
        """
        使用 DeepSeek API 将章节内容分割成场景
        """
        if not settings.DEEPSEEK_API_KEY:
            print("WARNING: DEEPSEEK_API_KEY not set, falling back to rule-based splitting")
            return []
        
        # 如果内容太长，分段处理
        max_length = 8000
        if len(chapter_content) > max_length:
            return await self._split_long_chapter(chapter_content, chapter_title)
        
        prompt = f"""请将以下小说章节内容分割成多个场景（scene）。

章节标题：{chapter_title}

章节内容：
{chapter_content}

请分析内容，将故事按场景转换分割。每个场景应包含：
1. 场景标题（简短描述）
2. 地点
3. 出现的角色列表
4. 场景内容摘要（800字以内）
5. 场景在原章节中的大致位置（起始字符位置）
6. 场景在原章节中的大致位置（结束字符位置）

请以 JSON 格式返回，格式如下：
{{
    "scenes": [
        {{
            "title": "场景标题",
            "location": "地点",
            "characters": ["角色1", "角色2"],
            "summary": "场景内容摘要",
            "start_pos": 0,
            "end_pos": 500
        }}
    ]
}}

注意：
- 场景转换通常发生在：地点变化、时间变化、新人物出场、情节转折处
- 每个场景应该有相对完整的情节单元
- 返回有效的 JSON 格式，不要添加其他说明文字"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的小说分镜助手，擅长将小说内容分割成适合改编剧本的场景。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content

            # 解析 JSON
            try:
                result = json.loads(content)
                return result.get("scenes", [])
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}, content: {content[:500]}")
                return []

        except Exception as e:
            print(f"DeepSeek API error: {e}")
            return []
    
    async def _split_long_chapter(self, chapter_content: str, chapter_title: str) -> List[Dict[str, Any]]:
        """处理长章节，分段调用 API"""
        chunk_size = 6000
        overlap = 500
        
        scenes = []
        start = 0
        
        while start < len(chapter_content):
            end = min(start + chunk_size, len(chapter_content))
            chunk = chapter_content[start:end]
            
            chunk_scenes = await self.split_chapter_with_ai(chunk, f"{chapter_title} (片段)")
            
            # 调整位置偏移
            for scene in chunk_scenes:
                scene["start_pos"] = scene.get("start_pos", 0) + start
                scene["end_pos"] = scene.get("end_pos", 0) + start
            
            scenes.extend(chunk_scenes)
            
            if end >= len(chapter_content):
                break
            start = end - overlap
        
        return scenes


# 全局 splitter 实例
_splitter = None

def get_splitter() -> DeepSeekSceneSplitter:
    """获取 splitter 实例（单例模式）"""
    global _splitter
    if _splitter is None:
        _splitter = DeepSeekSceneSplitter()
    return _splitter


async def split_chapter_with_ai(chapter_content: str, chapter_id: str, chapter_title: str) -> List[Scene]:
    """
    使用 AI 将章节内容分割成场景
    """
    splitter = get_splitter()
    
    # 调用 AI 分镜
    ai_scenes = await splitter.split_chapter_with_ai(chapter_content, chapter_title)
    
    if not ai_scenes:
        # AI 失败，回退到规则分镜
        print(f"AI splitting failed for chapter {chapter_title}, using rule-based fallback")
        return split_into_scenes(chapter_content, chapter_id, chapter_title)
    
    # 转换为 Scene 对象
    scenes = []
    for i, ai_scene in enumerate(ai_scenes, 1):
        # 根据 AI 返回的位置提取原始内容
        start_pos = ai_scene.get("start_pos", 0)
        end_pos = ai_scene.get("end_pos", len(chapter_content))
        scene_content = chapter_content[start_pos:end_pos]
        
        scene = Scene(
            scene_id=f"{chapter_id}_scene_{i}",
            title=ai_scene.get("title", f"场景 {i}"),
            location=ai_scene.get("location", "未知地点"),
            characters=ai_scene.get("characters", []),
            content=scene_content if scene_content else ai_scene.get("summary", ""),
            chapter_id=chapter_id,
            chapter_title=chapter_title
        )
        scenes.append(scene)
    
    return scenes


def extract_location(text: str) -> str:
    """
    从文本中提取地点信息（规则方法，用于回退）
    """
    location_patterns = [
        r'在([^，。！？\n]{2,20})(?:里|内|中|上|下|旁|边)?[，。]',
        r'(?:来到|到达|走进|进入|返回|离开|前往|抵达)([^，。！？\n]{2,20})[，。]',
        r'([^，。！？\n]{2,20})(?:之中|之内|之上|之下|旁边|附近)[，。]',
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    
    return "未知地点"


def extract_characters(text: str) -> List[str]:
    """
    从文本中提取人物（规则方法，用于回退）
    """
    character_patterns = [
        r'([\u4e00-\u9fa5]{2,4})(?:说道|说|问|答|想|看着|走向|来到)',
        r'([\u4e00-\u9fa5]{2,4})[，。]',
    ]
    
    characters = set()
    for pattern in character_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if match not in ['这里', '那里', '此时', '此刻', '突然', '只见', '原来', '于是']:
                characters.add(match)
    
    return list(characters)[:5]


def split_into_scenes(chapter_content: str, chapter_id: str, chapter_title: str) -> List[Scene]:
    """
    规则方法：将章节内容分割成多个场景（AI 失败时的回退方案）
    """
    scenes = []
    
    content = chapter_content.strip()
    if not content:
        return scenes
    
    # 按段落分割
    paragraphs = re.split(r'\n\s*\n|\r\n\s*\r\n', content)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    if not paragraphs:
        return scenes
    
    # 场景转换标记
    scene_markers = [
        r'(?:与此同时|另一边|另外一边)',
        r'(?:次日|第二天|几天后|数日后|不久之后|过了一会儿)',
        r'(?:场景转换|镜头切换|画面转到)',
    ]
    
    current_scene_paragraphs = []
    current_scene_index = 1
    
    for i, paragraph in enumerate(paragraphs):
        is_scene_break = False
        
        for marker in scene_markers:
            if re.search(marker, paragraph):
                is_scene_break = True
                break
        
        if len(paragraph) > 200 and current_scene_paragraphs:
            is_scene_break = True
        
        if is_scene_break and current_scene_paragraphs:
            scene_content = '\n\n'.join(current_scene_paragraphs)
            scene = create_scene(
                scene_content, 
                current_scene_index, 
                chapter_id, 
                chapter_title
            )
            scenes.append(scene)
            current_scene_index += 1
            current_scene_paragraphs = []
        
        current_scene_paragraphs.append(paragraph)
    
    if current_scene_paragraphs:
        scene_content = '\n\n'.join(current_scene_paragraphs)
        scene = create_scene(
            scene_content, 
            current_scene_index, 
            chapter_id, 
            chapter_title
        )
        scenes.append(scene)
    
    if len(scenes) == 1 and len(scenes[0].content) > 1000:
        scenes = split_long_scene(scenes[0], chapter_id, chapter_title)
    
    return scenes


def create_scene(content: str, scene_index: int, chapter_id: str, chapter_title: str) -> Scene:
    """创建场景对象"""
    location = extract_location(content[:200])
    characters = extract_characters(content)
    
    return Scene(
        scene_id=f"{chapter_id}_scene_{scene_index}",
        title=f"场景 {scene_index}",
        location=location,
        characters=characters,
        content=content,
        chapter_id=chapter_id,
        chapter_title=chapter_title
    )


def split_long_scene(scene: Scene, chapter_id: str, chapter_title: str) -> List[Scene]:
    """将长场景按字数分割"""
    scenes = []
    content = scene.content
    chunk_size = 800
    
    sentences = re.split(r'([。！？\n])', content)
    sentences = [''.join(sentences[i:i+2]) for i in range(0, len(sentences), 2)]
    sentences = [s.strip() for s in sentences if s.strip()]
    
    current_chunk = []
    current_size = 0
    scene_index = 1
    
    for sentence in sentences:
        if current_size + len(sentence) > chunk_size and current_chunk:
            scene_content = ''.join(current_chunk)
            scenes.append(create_scene(
                scene_content,
                scene_index,
                chapter_id,
                chapter_title
            ))
            scene_index += 1
            current_chunk = []
            current_size = 0
        
        current_chunk.append(sentence)
        current_size += len(sentence)
    
    if current_chunk:
        scene_content = ''.join(current_chunk)
        scenes.append(create_scene(
            scene_content,
            scene_index,
            chapter_id,
            chapter_title
        ))
    
    return scenes


async def process_chapters_to_scenes(chapters: List[Dict[str, Any]]) -> List[Scene]:
    """
    处理多个章节，使用 AI 将所有内容转换为场景列表
    """
    all_scenes = []

    for chapter in chapters:
        chapter_id = chapter.get('id', '')
        chapter_title = chapter.get('title', '')
        content = chapter.get('content', '')

        if not content:
            continue

        # 使用 AI 分镜
        scenes = await split_chapter_with_ai(content, chapter_id, chapter_title)
        all_scenes.extend(scenes)

    # 重新编号场景 ID，统一为 scene_1, scene_2, ... scene_n
    for i, scene in enumerate(all_scenes, 1):
        scene.scene_id = f"scene_{i}"

    return all_scenes


def scenes_to_dict(scenes: List[Scene]) -> List[Dict[str, Any]]:
    """将场景对象列表转换为字典列表"""
    return [
        {
            "scene_id": s.scene_id,
            "title": s.title,
            "location": s.location,
            "characters": s.characters,
            "content": s.content[:500] + "..." if len(s.content) > 500 else s.content,
            "chapter_id": s.chapter_id,
            "chapter_title": s.chapter_title
        }
        for s in scenes
    ]
