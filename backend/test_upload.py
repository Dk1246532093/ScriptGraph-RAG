"""
测试文件上传接口
"""

import requests

# 创建测试文件
with open('test_novel.txt', 'w', encoding='utf-8') as f:
    f.write("第一章 测试\n\n这是第一章的内容。\n\n第二章 测试2\n\n这是第二章的内容。")

# 测试上传
url = "http://localhost:8000/api/v1/novels/upload"

with open('test_novel.txt', 'rb') as f:
    files = {'file': ('test_novel.txt', f, 'text/plain')}
    data = {'title': '测试小说'}
    
    response = requests.post(url, files=files, data=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
