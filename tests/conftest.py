"""
pytest 配置文件
确保项目根目录在 sys.path 中
"""
import sys
import os

# 将项目根目录添加到 sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
