# -*- coding: utf-8 -*-
"""
交互式力板检测脚本 (check_forceplate_interactive.py)
功能：遍历指定文件夹内所有C3D文件，显示每个文件的力板类型、校准矩阵、
      处理后的Fz最大值，以及原始通道的最大值（用于对比）。
使用方法：
    python check_forceplate_interactive.py
    然后按提示输入文件夹路径。
"""

import os
import sys
import btk
import numpy as np
import c3d_utils

def clean_path(path):
    """清理路径中的不可见字符"""
    return path.strip().lstrip('\u202a').lstrip('\u200e').lstrip('\u200f')

def get_raw_channel_max(acq, label):
    """获取指定模拟通道的原始数据最大值（绝对值）"""
    for i in range(acq.GetAnalogs().GetItemNumber()):
        analog = acq.GetAnalog(i)
        if analog.GetLabel() == label:
            values = analog.GetValues()
            if values.ndim == 2 and values.shape[1] > 1:
                # 取所有列的最大绝对值
                return np.nanmax(np.abs(values))
            else:
                return np.nanmax(np.abs(values.flatten()))
    return None

def main():
    print("力板校准检测工具（交互式）")
    folder = input("请输入包含C3D文件的文件夹路径: ").strip()
    folder = clean_path(folder)
    if not os.path.isdir(folder):
        print("文件夹不存在或路径无效。")
        return

    c3d_files = [f for f in os.listdir(folder) if f.lower().endswith('.c3d')]
    if not c3d_files:
        print("文件夹中没有C3D文件。")
        return

    print(f"\n共找到 {len(c3d_files)} 个C3D文件，开始分析...\n")

    for filename in sorted(c3d_files):
        file_path = os.path.join(folder, filename)
        print(f"文件: {filename}")
        try:
            acq = c3d_utils.read_c3d(file_path)

            # 获取力板校准信息
            cal, ftype = c3d_utils.get_force_plate_calibration(acq, plate_index=0)
            print(f"  力板类型: {ftype}")
            if cal is not None:
                # 简化显示：只打印前几行或对角线
                if cal.shape == (6,6):
                    print(f"  校准矩阵 (对角线): {np.diag(cal)}")
                else:
                    print(f"  校准矩阵: {cal}")
            else:
                print("  校准矩阵: 无 (可能为 TYPE-2 预缩放)")

            # 获取处理后的力数据（已应用校准）
            force_dict, fs = c3d_utils.get_force_data(acq, file_path)
            fz_calibrated = np.max(force_dict['Fz'])
            print(f"  校准后 Fz 最大值: {fz_calibrated:.1f} N")

            # 获取配置文件中的通道映射（用于获取原始通道值）
            config_data = c3d_utils.get_project_config(file_path)
            channel_map = config_data.get('channels', {})
            fz_label = channel_map.get('force_vz')
            if fz_label:
                raw_max = get_raw_channel_max(acq, fz_label)
                if raw_max is not None:
                    print(f"  原始通道 ({fz_label}) 最大值: {raw_max:.1f}")
                else:
                    print(f"  原始通道 {fz_label} 未找到")
            else:
                print("  未配置垂直力通道，跳过原始值对比")

        except Exception as e:
            print(f"  处理出错: {e}")
        print("-" * 40)

if __name__ == '__main__':
    main()