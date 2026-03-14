# -*- coding: utf-8 -*-
"""
中文显示设置模块 (zh_font_finals.py)
功能：解决 matplotlib 中文显示为方块的问题。
使用方法：在需要绘图的脚本开头导入本模块，例如：
    import zh_font_finals
之后所有 matplotlib 绘图将自动支持中文。
注意：需确保主脚本已导入 matplotlib.pyplot as plt（通常在绘图前导入）
"""

import matplotlib.pyplot as plt

# 设置中文字体（优先微软雅黑，备选黑体、楷体）
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'KaiTi']
plt.rcParams['axes.unicode_minus'] = False   # 解决负号显示异常