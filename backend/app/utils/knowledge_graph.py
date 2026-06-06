"""
知识图谱抽取模块
从小说内容中抽取人物、地点及它们之间的关系
"""

import json
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from openai import AsyncOpenAI

from ..core.config import settings


@dataclass
class Character:
    """人物节点"""
    id: str
    name: str
    type: str = "Character"
    description: Optional[str] = None  # 人物简介


@dataclass
class Location:
    """地点节点"""
    id: str
    name: str
    type: str = "Location"
    description: Optional[str] = None


@dataclass
class Edge:
    """关系边"""
    source: str          # 起始节点ID
    target: str          # 目标节点ID
    relation: str        # 关系类型
    description: str     # 关系描述（如"白马李三是李文秀的父亲"）
    category: str = "character"
    bidirectional: bool = False  # 是否为双向关系


@dataclass
class KnowledgeGraph:
    """知识图谱"""
    nodes: List[Any]
    edges: List[Edge]


class KnowledgeGraphExtractor:
    """使用 DeepSeek API 抽取知识图谱"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_API_BASE
        )
        self.model = "deepseek-v4-flash"
    
    async def extract_from_chapters(
        self, 
        chapters: List[Dict[str, Any]]
    ) -> KnowledgeGraph:
        """
        从完整章节文本中抽取知识图谱（人物、地点、关系）
        
        Args:
            chapters: 章节列表，每个章节包含 id, title, content
            
        Returns:
            KnowledgeGraph 对象
        """
        if not settings.DEEPSEEK_API_KEY:
            print("WARNING: DEEPSEEK_API_KEY not set, returning empty knowledge graph")
            return KnowledgeGraph(nodes=[], edges=[])
        
        # 构建完整章节文本用于AI抽取
        chapters_text = self._prepare_chapters_text(chapters)
        
        # 调用 AI 抽取
        kg_data = await self._extract_with_ai(chapters_text)
        
        return kg_data
    
    def _prepare_chapters_text(self, chapters: List[Dict[str, Any]]) -> str:
        """准备完整章节文本用于抽取"""
        parts = []
        for ch in chapters:
            chapter_id = ch.get("id", "")
            title = ch.get("title", "")
            content = ch.get("content", "")
            
            parts.append(f"""
【章节: {title}】
章节ID: {chapter_id}

{content}
""")
        return "\n".join(parts)
    
    async def _extract_with_ai(self, chapters_text: str) -> KnowledgeGraph:
        """使用 AI 抽取知识图谱"""
        
        # 限制文本长度
        max_length = 12000
        if len(chapters_text) > max_length:
            chapters_text = chapters_text[:max_length] + "\n...[内容截断]"
        
        prompt = f"""从小说文本中抽取知识图谱，包含人物、地点节点及它们之间的关系。

小说内容：
{chapters_text}

节点定义：
- Character: 人物，包含 id, name, type="Character", description（人物简介）
- Location: 地点，包含 id, name, type="Location", description（地点描述）

关系定义：
- spouse: 夫妻（双向）
- parent_of: 父母→子女（单向：父母指向子女）
- child_of: 子女→父母（单向）
- sworn_brother: 结义兄弟（双向）
- master_of: 师父→徒弟（单向）
- disciple_of: 徒弟→师父（单向）
- same_master: 同门（双向）
- former_lovers: 曾有感情（双向）
- rescuer_of: 救助者→被救者（单向）
- guardian_of: 监护人→被监护人（单向）
- enemy_of: 仇敌（双向）
- friend_of: 朋友（双向）
- appears_in: 人物出现在地点（单向）

注意：
1. spouse、sworn_brother、same_master、former_lovers、enemy_of、friend_of 是双向关系，bidirectional=true
2. 每条边必须包含 description 字段，用自然语言描述关系，如"白马李三是李文秀的父亲"、"李三和上官虹是夫妻"

输出JSON格式：
{{
  "characters": [
    {{"id": "C001", "name": "李文秀", "type": "Character", "description": "白马李三之女"}},
    {{"id": "C002", "name": "白马李三", "type": "Character", "description": "李文秀之父"}},
    {{"id": "C003", "name": "上官虹", "type": "Character", "description": "李三之妻"}}
  ],
  "locations": [
    {{"id": "L001", "name": "大漠", "type": "Location", "description": "西域大漠"}}
  ],
  "edges": [
    {{"source": "C002", "target": "C001", "relation": "parent_of", "description": "白马李三是李文秀的父亲", "category": "character", "bidirectional": false}},
    {{"source": "C002", "target": "C003", "relation": "spouse", "description": "白马李三和上官虹是夫妻", "category": "character", "bidirectional": true}},
    {{"source": "C002", "target": "L001", "relation": "appears_in", "description": "白马李三在大漠被追杀", "category": "character_location", "bidirectional": false}}
  ]
}}

要求：
1. parent_of 方向必须是父母→子女
2. edges 的 source/target 必须对应存在的节点id
3. 只返回JSON，不要其他文字"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的小说知识图谱抽取助手。只抽取人物和地点两类节点及它们的关系。注意parent_of关系方向是父母指向子女。只输出JSON。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=6000,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            
            if not content:
                print("ERROR: Empty response from API")
                return KnowledgeGraph(nodes=[], edges=[])
            
            try:
                result = json.loads(content)
                return self._parse_kg_result(result)
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}, content: {content[:500]}")
                return KnowledgeGraph(nodes=[], edges=[])

        except Exception as e:
            print(f"DeepSeek API error: {e}")
            return KnowledgeGraph(nodes=[], edges=[])
    
    def _parse_kg_result(self, result: Dict[str, Any]) -> KnowledgeGraph:
        """解析 AI 返回的结果，构建 KnowledgeGraph"""
        nodes = []
        edges = []
        
        # 解析人物
        for char_data in result.get("characters", []):
            char = Character(
                id=char_data.get("id", ""),
                name=char_data.get("name", ""),
                type="Character",
                description=char_data.get("description")
            )
            nodes.append(char)
        
        # 解析地点
        for loc_data in result.get("locations", []):
            loc = Location(
                id=loc_data.get("id", ""),
                name=loc_data.get("name", ""),
                type="Location",
                description=loc_data.get("description")
            )
            nodes.append(loc)
        
        # 解析所有关系边
        for edge_data in result.get("edges", []):
            edge = Edge(
                source=edge_data.get("source", ""),
                target=edge_data.get("target", ""),
                relation=edge_data.get("relation", ""),
                description=edge_data.get("description", ""),
                category=edge_data.get("category", "character"),
                bidirectional=edge_data.get("bidirectional", False)
            )
            edges.append(edge)
        
        return KnowledgeGraph(nodes=nodes, edges=edges)


def kg_to_dict(kg: KnowledgeGraph) -> Dict[str, List[Dict[str, Any]]]:
    """将 KnowledgeGraph 转换为字典格式"""
    nodes = []
    for node in kg.nodes:
        node_dict = asdict(node)
        node_dict = {k: v for k, v in node_dict.items() if v is not None}
        nodes.append(node_dict)
    
    edges = []
    for edge in kg.edges:
        edge_dict = asdict(edge)
        edges.append(edge_dict)
    
    return {
        "nodes": nodes,
        "edges": edges
    }


# 全局抽取器实例
_extractor = None

def get_extractor() -> KnowledgeGraphExtractor:
    """获取抽取器实例（单例模式）"""
    global _extractor
    if _extractor is None:
        _extractor = KnowledgeGraphExtractor()
    return _extractor


async def extract_knowledge_graph(
    chapters: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    从章节原文中抽取知识图谱（便捷函数）
    
    Args:
        chapters: 章节列表，每个章节包含 id, title, content
        
    Returns:
        包含 nodes 和 edges 的字典
    """
    extractor = get_extractor()
    kg = await extractor.extract_from_chapters(chapters)
    return kg_to_dict(kg)
