"""
TXT 小说解析工具
"""

import re
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class Chapter:
    """章节数据结构"""
    index: int
    title: str
    content: str


def detect_encoding(file_content: bytes) -> str:
    """检测文件编码"""
    # 首先尝试 GBK（中文小说常见编码）
    try:
        decoded = file_content.decode('gbk')
        # 检查是否包含常见中文标点，如果包含则很可能是 GBK
        if any(char in decoded for char in ['。', '，', '：', '；', '？', '！', '、']):
            return 'gbk'
    except UnicodeDecodeError:
        pass
    
    # 尝试 GB2312
    try:
        file_content.decode('gb2312')
        return 'gb2312'
    except UnicodeDecodeError:
        pass
    
    # 尝试 UTF-8
    try:
        file_content.decode('utf-8')
        return 'utf-8'
    except UnicodeDecodeError:
        pass
    
    # 默认使用 GBK 并忽略错误（中文小说更可能是 GBK）
    return 'gbk'


def parse_txt_novel(file_content: bytes) -> List[Chapter]:
    """
    解析 TXT 小说文件，提取章节
    
    支持多种章节标题格式：
    - 第1章 xxx
    - 第一章 xxx
    - 第1节 xxx
    - 1. xxx
    - 第一章
    """
    # 检测编码并解码
    encoding = detect_encoding(file_content)
    print(f"DEBUG: Detected encoding: {encoding}")
    content = file_content.decode(encoding, errors='ignore')
    print(f"DEBUG: Content preview (first 100 chars): {content[:100]}")
    # 常见章节标题正则模式（只匹配单行，不跨行）
    chapter_patterns = [
        r'^\s*第[\d一二三四五六七八九十百千万]+章[^\n]*',  # 第1章 或 第一章（整行）
        r'^\s*第[\d一二三四五六七八九十百千万]+节[^\n]*',  # 第1节 或 第一节
        r'^\s*[\d]+[\.、][^\n]+',  # 1. xxx 或 1、xxx
        r'^\s*[Cc]hapter\s*[\d]+[^\n]*',  # Chapter 1 xxx
    ]
    
    # 合并所有模式
    pattern = '|'.join(f'({p})' for p in chapter_patterns)
    
    # 查找所有章节标题位置
    matches = list(re.finditer(pattern, content, re.MULTILINE))
    
    if not matches:
        # 如果没有找到章节，将整个内容作为第一章
        return [Chapter(index=1, title="正文", content=content.strip())]
    
    chapters = []
    
    for i, match in enumerate(matches):
        # 直接使用匹配到的整行内容作为标题
        title = match.group().strip()
        start_pos = match.end()
        
        # 确定章节内容结束位置
        if i < len(matches) - 1:
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(content)
        
        # 提取章节内容
        chapter_content = content[start_pos:end_pos].strip()
        
        # 清理内容中的多余空行
        chapter_content = re.sub(r'\n{3,}', '\n\n', chapter_content)
        
        chapters.append(Chapter(
            index=i + 1,
            title=title,
            content=chapter_content
        ))
    
    return chapters


def extract_title_from_filename(filename: str) -> str:
    """从文件名提取小说标题"""
    # 移除扩展名
    title = filename.rsplit('.', 1)[0]
    # 移除常见的文件名后缀
    title = re.sub(r'[_-](完本|全集|精校|校对|版)', '', title)
    # 移除作者名（通常在括号中）
    title = re.sub(r'[\(（].*?[\)）]', '', title)
    return title.strip()


def get_novel_preview(content: str, max_length: int = 200) -> str:
    """获取小说预览文本"""
    # 移除章节标题
    text = re.sub(r'第[\d一二三四五六七八九十百千万]+章\s*[^\n]*', '', content)
    # 清理空白
    text = re.sub(r'\s+', '', text)
    # 返回前 max_length 个字符
    return text[:max_length] + '...' if len(text) > max_length else text
