"""
TRIZ应用常量定义
"""

# 应用信息
APP_NAME = "TRIZ-AI"
APP_VERSION = "0.2.0"
APP_AUTHOR = "TRIZ"

# 矩阵类型
MATRIX_39 = "39"
MATRIX_48 = "48"
MATRIX_TYPES = [MATRIX_39, MATRIX_48]

# 从triz_constants导入统一数据
# 39矩阵参数（与MATRIX_39键保持一致）
from data.triz_constants import ENGINEERING_PARAMETERS as ENGINEERING_PARAMETERS_39
# 40发明原理（唯一数据源）
from data.triz_constants import PRINCIPLE_NAMES as INVENTIVE_PRINCIPLES

# 原理分类
PRINCIPLE_CATEGORIES = {
    "物理": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        13,
        14,
        15,
        17,
        18,
        19,
        20,
        27,
        28,
        29,
        30,
        31,
        37,
    ],
    "化学": [35, 36, 38, 39, 40],
    "几何": [1, 2, 3, 4, 7, 14, 17, 31],
    "时间": [9, 10, 11, 16, 19, 20, 21, 34],
    "系统": [6, 23, 24, 25, 26, 32, 33],
}

# AI配置
DEFAULT_AI_MODEL = "deepseek-chat"
DEEPSEEK_API_BASE = "https://api.deepseek.com"
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"

# 解决方案配置
MAX_SOLUTIONS = 20

# 颜色配置
COLORS = {
    "primary": "#2196F3",  # 蓝色
    "secondary": "#4CAF50",  # 绿色
    "accent": "#FF9800",  # 橙色
    "error": "#F44336",  # 红色
    "warning": "#FFC107",  # 黄色
    "success": "#4CAF50",  # 绿色
    "info": "#2196F3",  # 蓝色
    "background": "#FFFFFF",  # 白色
    "surface": "#F5F5F5",  # 浅灰色
    "text_primary": "#212121",  # 深灰色
    "text_secondary": "#757575",  # 中灰色
}

# 原理分类颜色
CATEGORY_COLORS = {
    "物理": "#2196F3",
    "化学": "#4CAF50",
    "几何": "#FF9800",
    "时间": "#9C27B0",
    "系统": "#607D8B",
}

# 图标
ICONS = {
    "ai": "🤖",
    "matrix": "📊",
    "parameter": "⚙️",
    "solution": "💡",
    "history": "📈",
    "export": "📤",
    "settings": "⚙️",
    "help": "❓",
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
}
