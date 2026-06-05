"""
小说相关 API 路由
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List

from app.models.novel import Novel, NovelDetail, Chapter
from app.services.novel_service import novel_service

router = APIRouter()


@router.get("/novels", response_model=dict)
async def get_novels():
    """获取小说列表"""
    novels = novel_service.get_all_novels()
    return {"code": 200, "data": novels, "message": "success"}


@router.post("/novels/upload", response_model=dict)
async def upload_novel(
    title: str = Form(default=""),
    file: UploadFile = File(default=None)
):
    """上传小说文件"""
    print(f"DEBUG: title='{title}', file={file}")
    # 检查参数
    if not title or not title.strip():
        print("DEBUG: title check failed")
        raise HTTPException(status_code=400, detail="请输入小说标题")
    if not file:
        print("DEBUG: file check failed")
        raise HTTPException(status_code=400, detail="请选择文件")
    
    # 检查文件类型（不区分大小写）
    if not file.filename.lower().endswith('.txt'):
        raise HTTPException(status_code=400, detail="只支持 TXT 格式文件")
    
    # 读取文件内容
    content = await file.read()
    
    print(f"DEBUG: Read {len(content)} bytes from file")
    print(f"DEBUG: First 100 bytes (raw): {content[:100]}")
    
    # 尝试用不同编码解码前100字节
    for enc in ['utf-8', 'gbk', 'gb2312']:
        try:
            decoded = content[:100].decode(enc)
            print(f"DEBUG: Decoded with {enc}: {decoded[:50]}")
            break
        except:
            pass
    
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="文件内容为空")
    
    try:
        # 创建小说
        novel = novel_service.create_novel(
            title=title,
            file_content=content,
            filename=file.filename
        )
        return {"code": 200, "data": novel, "message": "上传成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析失败: {str(e)}")


@router.get("/novels/{novel_id}", response_model=dict)
async def get_novel_detail(novel_id: str):
    """获取小说详情"""
    novel = novel_service.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    return {"code": 200, "data": novel, "message": "success"}


@router.get("/novels/{novel_id}/chapters", response_model=dict)
async def get_novel_chapters(novel_id: str):
    """获取小说章节列表"""
    novel = novel_service.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    # 只返回章节基本信息，不包含内容
    chapters = [{"id": c.id, "title": c.title, "index": c.index} for c in novel.chapters]
    return {"code": 200, "data": chapters, "message": "success"}


@router.get("/novels/{novel_id}/chapters/{chapter_id}", response_model=dict)
async def get_chapter_content(novel_id: str, chapter_id: str):
    """获取章节内容"""
    chapter = novel_service.get_chapter(novel_id, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    return {"code": 200, "data": chapter, "message": "success"}


@router.delete("/novels/{novel_id}", response_model=dict)
async def delete_novel(novel_id: str):
    """删除小说"""
    success = novel_service.delete_novel(novel_id)
    if not success:
        raise HTTPException(status_code=404, detail="小说不存在")
    return {"code": 200, "data": None, "message": "删除成功"}
