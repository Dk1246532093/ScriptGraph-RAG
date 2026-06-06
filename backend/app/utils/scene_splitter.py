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
    start_text: str
    end_text: str
    beats: List[str]
    dramatic_purpose: str
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
        
        prompt = f"""你是一名专业编剧、影视剧本顾问和叙事结构分析师。

请将以下小说章节内容分析并划分为多个影视场景（Scene）。

章节标题：
{chapter_title}

章节内容：
{chapter_content}

====================
Scene划分原则
====================

Scene（场景）是影视叙事中的完整戏剧单元。

一个Scene必须满足：

- 发生在同一时间段
- 发生在同一地点
- 围绕同一个核心冲突或核心事件
- 具有完整的戏剧过程（开始→发展→结果）

重要：

不要因为字数较长而拆分Scene。

不要因为人物情绪变化而拆分Scene。

不要因为战斗升级而拆分Scene。

不要因为角色做出新决定而拆分Scene。

不要因为剧情进入下一阶段而拆分Scene。

如果事件仍然连续发生在同一时间、同一地点、同一冲突中，则应视为同一个Scene。

例如：

错误：

Scene1：发现追兵
Scene2：开始逃跑
Scene3：李三受伤
Scene4：决定断后
Scene5：装死反击

正确：

Scene1：大漠追杀

因为上述内容属于同一时间、同一地点、同一追杀事件。

====================
仅在以下情况创建新Scene
====================

1. 地点发生变化

例如：

大漠 → 客栈

2. 时间发生明显变化

例如：

白天 → 夜晚

三年前 → 三年后

3. 叙事视角切换到另一组人物

例如：

李文秀逃亡

切换到

追兵营地议事

4. 当前核心冲突结束

并进入新的独立故事阶段

例如：

逃亡结束

进入客栈休整

5. 主角开始执行新的独立行动线

例如：

成功脱险

开始寻找藏宝图

====================
Beat划分原则
====================

Beat（剧情节点）是Scene内部的重要戏剧动作。

一个Scene可以包含多个Beat。

例如：

Scene：大漠追杀

Beat：
- 一家三口逃亡
- 李三中箭
- 红马倒毙
- 追兵逼近
- 李三决定断后
- 装死反击
- 壮烈战死

这些内容属于同一个Scene。

====================
输出要求
====================

请识别本章节中的所有Scene。

每个Scene包含：

- title：场景标题
- location：场景地点
- characters：主要出场人物
- start_text：场景开始的原文（前50字左右，用于定位场景起点）
- end_text：场景结束的原文（后50字左右，用于定位场景终点）
- dramatic_purpose：戏剧作用
- beats：场景内部关键剧情节点列表

返回格式：

{{
  "scenes": [
    {{
      "title": "",
      "location": "",
      "characters": [],
      "start_text": "",
      "end_text": "",
      "dramatic_purpose": "",
      "beats": [
        ""
      ]
    }}
  ]
}}

要求：

- Scene数量尽可能少且合理
- 每个Scene必须是完整戏剧单元
- 不允许按字数切分
- 不允许按段落切分
- 优先遵循影视剧本结构
- beats数量不限
- 仅返回JSON
"""

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
        # AI 返回 start_text 和 end_text
        start_text = ai_scene.get("start_text", "")
        end_text = ai_scene.get("end_text", "")
        
        # 根据 start_text 和 end_text 从章节内容中提取完整片段
        full_content = extract_scene_content(chapter_content, start_text, end_text)
        
        scene = Scene(
            scene_id=f"{chapter_id}_scene_{i}",
            title=ai_scene.get("title", f"场景 {i}"),
            location=ai_scene.get("location", "未知地点"),
            characters=ai_scene.get("characters", []),
            start_text=start_text,
            end_text=end_text,
            beats=ai_scene.get("beats", []),
            dramatic_purpose=ai_scene.get("dramatic_purpose", ""),
            chapter_id=chapter_id,
            chapter_title=chapter_title
        )
        scenes.append(scene)
        
        # 将完整内容保存到场景对象的一个额外属性中（用于后续存储）
        scene.full_content = full_content
    
    return scenes


def extract_scene_content(chapter_content: str, start_text: str, end_text: str) -> str:
    """
    根据开始文本和结束文本，从章节内容中提取完整场景
    """
    if not start_text or not end_text:
        return chapter_content
    
    # 清理文本（去除多余空格和换行）用于匹配
    def clean_text(text: str) -> str:
        return ' '.join(text.split())
    
    chapter_clean = clean_text(chapter_content)
    start_clean = clean_text(start_text)
    end_clean = clean_text(end_text)
    
    # 查找开始位置
    start_idx = chapter_clean.find(start_clean)
    if start_idx == -1:
        # 如果精确匹配失败，尝试只匹配前20个字符
        start_partial = clean_text(start_text[:20])
        start_idx = chapter_clean.find(start_partial)
    
    if start_idx == -1:
        # 还是找不到，返回整个章节
        return chapter_content
    
    # 查找结束位置（从开始位置之后查找）
    search_from = start_idx + len(start_clean)
    end_idx = chapter_clean.find(end_clean, search_from)
    
    if end_idx == -1:
        # 如果精确匹配失败，尝试只匹配后20个字符
        end_partial = clean_text(end_text[-20:])
        end_idx = chapter_clean.find(end_partial, search_from)
    
    # 将清理后的开始索引映射回原始文本
    original_start = find_original_position(chapter_content, chapter_clean, start_idx)
    
    if end_idx == -1:
        # 找不到结束位置，返回从开始到章节末尾
        return chapter_content[original_start:]
    
    # 提取完整内容（包括结束文本）
    end_idx += len(end_clean)
    
    # 将清理后的结束索引映射回原始文本
    original_end = find_original_position(chapter_content, chapter_clean, end_idx)
    
    return chapter_content[original_start:original_end]


def find_original_position(original: str, cleaned: str, cleaned_pos: int) -> int:
    """
    将清理后文本的位置映射回原始文本的位置
    """
    original_pos = 0
    cleaned_count = 0
    
    for char in original:
        if cleaned_count >= cleaned_pos:
            break
        if not char.isspace() or (original_pos > 0 and original[original_pos-1:original_pos+1] == '\n\n'):
            # 保留段落分隔
            cleaned_count += 1
        original_pos += 1
    
    return original_pos


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
    """创建场景对象（规则分镜回退时使用）"""
    location = extract_location(content[:200])
    characters = extract_characters(content)
    
    # 提取开头和结尾文本
    start_text = content[:100] if len(content) > 100 else content
    end_text = content[-100:] if len(content) > 100 else content
    
    return Scene(
        scene_id=f"{chapter_id}_scene_{scene_index}",
        title=f"场景 {scene_index}",
        location=location,
        characters=characters,
        start_text=start_text,
        end_text=end_text,
        beats=[],
        dramatic_purpose="",
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
    result = []
    for s in scenes:
        scene_dict = {
            "scene_id": s.scene_id,
            "title": s.title,
            "location": s.location,
            "characters": s.characters,
            "start_text": s.start_text,
            "end_text": s.end_text,
            "beats": s.beats,
            "dramatic_purpose": s.dramatic_purpose,
            "chapter_id": s.chapter_id,
            "chapter_title": s.chapter_title
        }
        # 如果有完整内容，也添加到字典中
        if hasattr(s, 'full_content') and s.full_content:
            scene_dict["content"] = s.full_content
        result.append(scene_dict)
    return result
