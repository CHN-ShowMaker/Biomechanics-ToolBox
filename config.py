# -*- coding: utf-8 -*-
"""
配置文件，集中管理所有可调参数
"""

# 滤波参数
FILTER_CUTOFF = 50          # 低通滤波截止频率 (Hz)
FILTER_ORDER = 4            # 滤波器阶数

# 力通道识别关键词
FORCE_KEYWORDS = ['FZ', 'VGRF', 'Force.Fz']  # 用于自动识别垂直力通道

# 跳跃检测参数
JUMP_THRESHOLD_RATIO = 0.1  # 腾空阈值 = 最大力 × 该比例
JUMP_PRE_WINDOW = 200        # 离地前搜索起跳峰的窗口（帧数）
JUMP_POST_WINDOW = 200       # 落地后搜索落地峰的窗口（帧数）
MIN_FLIGHT_DURATION = 0.05   # 最小腾空时间（秒），用于判断是否为跳跃

# 步态检测参数
GAIT_THRESHOLD_RATIO = 0.1   # 触地/离地阈值比例（相对于最大力）
MIN_STANCE_DURATION = 0.1    # 最小支撑时间（秒），用于过滤噪声

# OpenSim导出控制
EXPORT_OPENSIM = True       # 全局开关：是否导出 OpenSim 文件

# 阈值参数
GAIT_THRESHOLD_RATIO = 0.1      # 步态触地/离地阈值比例
JUMP_THRESHOLD_RATIO = 0.1      # 跳跃腾空阈值比例
FORCE_THRESHOLD = 20             # 腾空绝对阈值 (N)，用于动作预测