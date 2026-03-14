# -*- coding: utf-8 -*-
"""
交互式项目配置工具 (configure.py)  v3.0
功能：扫描指定文件夹中的C3D文件，让用户手动配置所有力通道映射，
      并保存为 project_config.json 到该文件夹，供后续批量处理使用。
特性：
    - 支持配置所有分量：Fx, Fy, Fz, Mx, My, Mz, COPx, COPy
    - 支持跳过任意分量（留空）
    - 集成通道推荐（调用 suggest_channel 模块，可选）
"""

import os
import json
import btk
import glob
import sys
import numpy as np
from pathlib import Path

# 尝试导入通道推荐模块（可选）
try:
    from suggest_channel import get_first_c3d, compute_channel_stats
    HAS_SUGGEST = True
except ImportError:
    HAS_SUGGEST = False
    print("提示：未找到 suggest_channel 模块，将无法使用通道推荐功能。")

def clean_path(path):
    """清理路径中的不可见字符"""
    return path.strip().lstrip('\u202a').lstrip('\u200e').lstrip('\u200f')

def get_input_int(prompt, default=None, allow_none=False):
    """获取整数输入"""
    while True:
        val = input(prompt).strip()
        if val == '' and default is not None:
            return default
        if val == '' and allow_none:
            return None
        try:
            return int(val)
        except:
            print("请输入有效数字。")

def get_input_float(prompt, default=None):
    val = input(prompt).strip()
    if val == '' and default is not None:
        return default
    try:
        return float(val)
    except:
        print("请输入有效数字。")
        return get_input_float(prompt, default)

def get_input_bool(prompt, default='n'):
    val = input(prompt).strip().lower()
    if val == '':
        return default == 'y'
    return val.startswith('y')

def select_channel(analog_labels, channel_type, required=False, suggested_idx=None):
    """交互式选择通道，返回通道名称（字符串）或 None（如果跳过）"""
    print(f"\n可用模拟通道（用于{channel_type}）：")
    for idx, label in enumerate(analog_labels):
        suggestion = " (推荐)" if idx == suggested_idx else ""
        print(f"  {idx}: {label}{suggestion}")
    if required:
        prompt = f"请选择{channel_type}通道的编号（必须选择）"
    else:
        prompt = f"请选择{channel_type}通道的编号（留空跳过）"
    if suggested_idx is not None:
        prompt += f" [推荐 {suggested_idx}]: "
    else:
        prompt += ": "
    while True:
        choice = input(prompt).strip()
        if choice == '' and suggested_idx is not None and not required:
            # 用户回车且推荐存在且非必须，返回推荐
            return analog_labels[suggested_idx]
        if choice == '' and not required:
            return None
        try:
            idx = int(choice)
            if 0 <= idx < len(analog_labels):
                return analog_labels[idx]
            else:
                print("编号超出范围，请重新输入。")
        except:
            print("请输入数字编号。")

def configure_project(folder_path):
    """交互式配置，生成 project_config.json"""
    folder_path = clean_path(folder_path)
    if not os.path.isdir(folder_path):
        print("文件夹不存在，请检查路径。")
        return

    # 获取该文件夹下所有C3D文件
    c3d_files = glob.glob(os.path.join(folder_path, '*.c3d'))
    if not c3d_files:
        print("该文件夹下没有找到 .c3d 文件。")
        return

    # 取第一个文件作为代表
    first_file = c3d_files[0]
    print(f"使用文件 {os.path.basename(first_file)} 作为模板进行配置。")

    # ---------- 询问是否进行通道推荐 ----------
    do_suggest = False
    if HAS_SUGGEST:
        ans = input("\n是否进行通道推荐（分析数据中最大值最大的通道作为垂直力候选）？(y/n, 默认 n): ").strip().lower()
        do_suggest = ans == 'y'

    # 如果启用推荐，计算推荐通道（用于垂直力）
    suggested_idx = None
    if do_suggest:
        try:
            print("正在分析数据，请稍候...")
            _, max_vals, _, sorted_indices, _ = compute_channel_stats(first_file)
            if len(sorted_indices) > 0:
                # 找到第一个非NaN的有效通道作为推荐
                for idx in sorted_indices:
                    if not np.isnan(max_vals[idx]):
                        suggested_idx = idx
                        break
                if suggested_idx is not None:
                    print(f"\n推荐：通道 {suggested_idx}，最大值为 {max_vals[suggested_idx]:.2f}")
                else:
                    print("未找到有效通道，无法推荐。")
            else:
                print("无法获取通道推荐。")
        except Exception as e:
            print(f"通道推荐失败: {e}")

    # 读取C3D获取模拟通道列表
    try:
        reader = btk.btkAcquisitionFileReader()
        reader.SetFilename(first_file)
        reader.Update()
        acq = reader.GetOutput()
    except Exception as e:
        print(f"读取C3D失败: {e}")
        return

    analog_labels = []
    for i in range(acq.GetAnalogs().GetItemNumber()):
        analog = acq.GetAnalog(i)
        analog_labels.append(analog.GetLabel())

    if not analog_labels:
        print("该文件没有模拟通道（力板数据）。")
        return

    print("\n模拟通道列表：")
    for idx, label in enumerate(analog_labels):
        print(f"  {idx}: {label}")

    # 交互选择各通道
    config = {}
    config['channels'] = {}

    print("\n请指定力通道（如果某个分量不存在，留空跳过）。")
    config['channels']['force_vz'] = select_channel(analog_labels, '垂直力 (Fz)', required=True, suggested_idx=suggested_idx)
    config['channels']['force_vx'] = select_channel(analog_labels, '前后力 (Fx)', required=False)
    config['channels']['force_vy'] = select_channel(analog_labels, '侧向力 (Fy)', required=False)
    config['channels']['torque_x'] = select_channel(analog_labels, '力矩 X (Mx)', required=False)
    config['channels']['torque_y'] = select_channel(analog_labels, '力矩 Y (My)', required=False)
    config['channels']['torque_z'] = select_channel(analog_labels, '力矩 Z (Mz)', required=False)
    config['channels']['cop_x'] = select_channel(analog_labels, '压力中心 X (COPx)', required=False)
    config['channels']['cop_y'] = select_channel(analog_labels, '压力中心 Y (COPy)', required=False)

    # 滤波参数
    print("\n设置滤波参数（默认值来自 config.py，可修改）")
    from config import FILTER_CUTOFF, FILTER_ORDER
    config['filter'] = {}
    config['filter']['cutoff'] = get_input_float(f"滤波截止频率 (Hz) (默认 {FILTER_CUTOFF}): ", default=FILTER_CUTOFF)
    config['filter']['order'] = get_input_int(f"滤波器阶数 (默认 {FILTER_ORDER}): ", default=FILTER_ORDER)

    # 阈值参数
    print("\n设置阈值参数（可选，留空使用 config.py 默认）")
    from config import GAIT_THRESHOLD_RATIO, JUMP_THRESHOLD_RATIO, FORCE_THRESHOLD
    config['thresholds'] = {}
    config['thresholds']['gait_threshold_ratio'] = get_input_float(f"步态阈值比例 (默认 {GAIT_THRESHOLD_RATIO}): ", default=GAIT_THRESHOLD_RATIO)
    config['thresholds']['jump_threshold_ratio'] = get_input_float(f"跳跃阈值比例 (默认 {JUMP_THRESHOLD_RATIO}): ", default=JUMP_THRESHOLD_RATIO)
    config['thresholds']['force_threshold'] = get_input_float(f"腾空阈值 (N) (默认 {FORCE_THRESHOLD}): ", default=FORCE_THRESHOLD)

    # OpenSim导出开关
    from config import EXPORT_OPENSIM
    config['export_opensim'] = get_input_bool(f"是否导出OpenSim文件？(y/n, 默认 {'y' if EXPORT_OPENSIM else 'n'}): ", default='y' if EXPORT_OPENSIM else 'n')

    # 保存配置文件
    config_path = os.path.join(folder_path, 'project_config.json')
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    print(f"\n配置已保存至: {config_path}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # 如果提供了命令行参数，直接作为文件夹路径
        folder = clean_path(sys.argv[1])
        configure_project(folder)
    else:
        # 交互模式
        folder = input("请输入要配置的文件夹路径: ").strip()
        folder = clean_path(folder)
        configure_project(folder)