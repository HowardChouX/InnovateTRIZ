"""
pytest 配置文件
确保项目根目录在 sys.path 中
"""
import sys
import os

# 将 src 目录和项目根目录添加到 sys.path
# src/ 在前，确保 from config.constants 能解析到 src/config/
# 项目根目录在后，支持 tests/ 内各文件自己的 sys.path.insert
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, "src")
for p in (src_path, project_root):
    if p not in sys.path:
        sys.path.insert(0, p)
