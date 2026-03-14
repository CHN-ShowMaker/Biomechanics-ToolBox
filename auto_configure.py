# -*- coding: utf-8 -*-
"""
自动通道配置工具 (auto_configure.py) 交互式版
功能：遍历文件夹内所有C3D文件，对每个文件自动推荐力通道（垂直力），
      生成一个汇总的 file_channels.json 文件，供后续按文件读取。
使用方式：
    1. 命令行参数：python auto_configure.py <文件夹路径> [--force]
    2. 无参数运行：进入交互模式，提示输入文件夹路径和是否强制覆盖
"""

import os
import sys
import argparse
import json
import btk
import numpy as np

def clean_path(path):
    """清理路径中的不可见字符"""
    return path.strip().lstrip('\u202a').lstrip('\u200e').lstrip('\u200f')

def get_channel_stats(c3d_file):
    """分析单个C3D文件，返回各模拟通道的最大绝对值及其标签"""
    reader = btk.btkAcquisitionFileReader()
    reader.SetFilename(c3d_file)
    reader.Update()
    acq = reader.GetOutput()

    analog_labels = []
    analog_max = []
    for i in range(acq.GetAnalogs().GetItemNumber()):
        analog = acq.GetAnalog(i)
        values = analog.GetValues()
        if values.ndim == 2 and values.shape[1] > 1:
            max_val = np.nanmax(np.abs(values))
        else:
            max_val = np.nanmax(np.abs(values.flatten()))
        analog_labels.append(analog.GetLabel())
        analog_max.append(max_val)
    sorted_indices = np.argsort(analog_max)[::-1]
    return analog_labels, analog_max, sorted_indices

def recommend_channels(analog_labels, analog_max, sorted_indices):
    """
    根据最大值排序，为各分量推荐通道。
    目前仅推荐垂直力（Fz）：取最大值最大的通道作为候选。
    其他分量暂不自动推荐（留空），但可后续手动补充。
    """
    top_idx = sorted_indices[0]
    force_vz = analog_labels[top_idx] if not np.isnan(analog_max[top_idx]) else None
    return {
        'force_vz': force_vz,
        'force_vx': None,
        'force_vy': None,
        'torque_x': None,
        'torque_y': None,
        'torque_z': None,
        'cop_x': None,
        'cop_y': None
    }

def run_auto_configure(folder_path, force=False):
    """核心处理函数，生成 file_channels.json"""
    folder_path = os.path.normpath(folder_path)
    if not os.path.isdir(folder_path):
        print(f"文件夹不存在: {folder_path}")
        return

    c3d_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.c3d')]
    if not c3d_files:
        print("文件夹中没有C3D文件")
        return

    output_path = os.path.join(folder_path, 'file_channels.json')
    if os.path.exists(output_path) and not force:
        print(f"配置文件已存在: {output_path}，如需重新生成请使用 --force 或在交互时选择覆盖")
        return

    file_channels = {}
    for filename in c3d_files:
        file_path = os.path.join(folder_path, filename)
        print(f"处理: {filename}")
        try:
            labels, max_vals, sorted_idx = get_channel_stats(file_path)
            rec = recommend_channels(labels, max_vals, sorted_idx)
            file_channels[filename] = rec
        except Exception as e:
            print(f"  失败: {e}")
            file_channels[filename] = None

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({'file_channels': file_channels}, f, indent=4, ensure_ascii=False)
    print(f"配置文件已生成: {output_path}")

def main():
    parser = argparse.ArgumentParser(description='自动通道配置工具（交互式）', add_help=False)
    parser.add_argument('folder', nargs='?', help='包含C3D文件的文件夹路径')
    parser.add_argument('--force', action='store_true', help='强制重新生成配置文件')
    args, remaining = parser.parse_known_args()

    if args.folder is None:
        # 交互模式
        print("自动通道配置工具（交互式）")
        folder = input("请输入包含C3D文件的文件夹路径: ").strip()
        folder = clean_path(folder)
        if not os.path.isdir(folder):
            print("文件夹不存在或路径无效。")
            return
        force_choice = input("是否强制覆盖已存在的配置文件？(y/n, 默认 n): ").strip().lower()
        force = force_choice == 'y'
        run_auto_configure(folder, force)
    else:
        # 命令行模式
        folder = clean_path(args.folder)
        run_auto_configure(folder, args.force)

if __name__ == '__main__':
    main()