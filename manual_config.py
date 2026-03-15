# -*- coding: utf-8 -*-
"""
手动配置文件生成工具 (manual_config.py) 交互式双语版
功能：运行时先询问文件夹路径，然后遍历文件夹内所有C3D文件，
      对每个文件显示模拟通道列表，让用户手动选择垂直力通道，
      并自动匹配同板的其他分量（Fx, Fy, Mx, My, Mz, COPx, COPy），
      生成按文件的 project_config.json。
使用方式：
    python manual_config.py
    然后按提示输入文件夹路径
"""

import os
import sys
import json
import btk
import numpy as np
import c3d_utils
import re

def clean_path(path):
    return path.strip().lstrip('\u202a').lstrip('\u200e').lstrip('\u200f')

def get_channel_info(acq):
    labels = []
    max_vals = []
    for i in range(acq.GetAnalogs().GetItemNumber()):
        analog = acq.GetAnalog(i)
        label = analog.GetLabel()
        values = analog.GetValues()
        if values.ndim == 2 and values.shape[1] > 1:
            max_val = np.max(np.abs(values))
        else:
            max_val = np.max(np.abs(values.flatten()))
        labels.append(label)
        max_vals.append(max_val)
    return labels, max_vals

def extract_plate_number(label):
    numbers = re.findall(r'\d+', label)
    return numbers[-1] if numbers else None

def main():
    print("手动配置工具（交互式双语版） / Manual Configuration Tool (Interactive Bilingual)")
    folder = input("请输入要处理的文件夹路径: ").strip()
    print("Enter the folder path to process:")
    folder = clean_path(folder)
    if not os.path.isdir(folder):
        print(f"文件夹不存在: {folder} / Folder does not exist: {folder}")
        return

    c3d_files = [f for f in os.listdir(folder) if f.lower().endswith('.c3d')]
    if not c3d_files:
        print("文件夹中没有 .c3d 文件 / No .c3d files in folder")
        return

    try:
        top_n = int(input("请输入要显示的前几个候选通道 (默认 5): ").strip() or "5")
        print(f"Enter number of top candidate channels to display (default 5): {top_n}")
    except:
        top_n = 5

    file_channels = {}
    for filename in sorted(c3d_files):
        file_path = os.path.join(folder, filename)
        print(f"\n处理文件: {filename} / Processing file: {filename}")
        acq = c3d_utils.read_c3d(file_path)
        labels, max_vals = get_channel_info(acq)
        sorted_indices = np.argsort(max_vals)[::-1]

        print(f"模拟通道最大值排序 (前 {top_n}): / Analog channel maximum values (top {top_n}):")
        print("  排名 Rank | 编号 Index | 标签 Label               | 最大值 Max value")
        print("  -----------|------------|--------------------------|--------------")
        for rank, idx in enumerate(sorted_indices[:top_n], start=1):
            print(f"  {rank:4d}      | {idx:4d}      | {labels[idx]:24s} | {max_vals[idx]:8.2f}")

        while True:
            try:
                choice = input("请输入垂直力 (Fz) 通道的编号 (必须选择): ").strip()
                print(f"Enter the index of the vertical force (Fz) channel (required): {choice}")
                idx = int(choice)
                if 0 <= idx < len(labels):
                    fz_label = labels[idx]
                    break
                else:
                    print("编号超出范围，请重新输入。/ Index out of range, please try again.")
            except ValueError:
                print("请输入数字编号。/ Please enter a numeric index.")

        chan = {
            'force_vz': fz_label,
            'force_vx': None,
            'force_vy': None,
            'torque_x': None,
            'torque_y': None,
            'torque_z': None,
            'cop_x': None,
            'cop_y': None
        }

        plate_num = extract_plate_number(fz_label)
        all_labels_set = set(labels)

        if plate_num:
            # 匹配 Fx, Fy, Mx, My, Mz
            candidates = {
                'force_vx': [f'FX{plate_num}', f'Fx{plate_num}'],
                'force_vy': [f'FY{plate_num}', f'Fy{plate_num}'],
                'torque_x': [f'MX{plate_num}', f'Mx{plate_num}'],
                'torque_y': [f'MY{plate_num}', f'My{plate_num}'],
                'torque_z': [f'MZ{plate_num}', f'Mz{plate_num}'],
            }
            for comp, cand_list in candidates.items():
                for cand in cand_list:
                    if cand in all_labels_set:
                        chan[comp] = cand
                        break

            # 匹配 COP X 和 Y
            cop_candidates_x = [
                f'COP{plate_num}.X',
                f'COP{plate_num}_X',
                f'Force.COPx{plate_num}',
                f'COP_X{plate_num}'
            ]
            cop_candidates_y = [
                f'COP{plate_num}.Y',
                f'COP{plate_num}_Y',
                f'Force.COPy{plate_num}',
                f'COP_Y{plate_num}'
            ]
            for cand in cop_candidates_x:
                if cand in all_labels_set:
                    chan['cop_x'] = cand
                    break
            for cand in cop_candidates_y:
                if cand in all_labels_set:
                    chan['cop_y'] = cand
                    break

            print(f"自动匹配结果 / Auto-matched components:")
            print(f"  Fx = {chan['force_vx']}, Fy = {chan['force_vy']}")
            print(f"  Mx = {chan['torque_x']}, My = {chan['torque_y']}, Mz = {chan['torque_z']}")
            print(f"  COPx = {chan['cop_x']}, COPy = {chan['cop_y']}")
        else:
            print("警告：无法从标签中提取板号，其他分量将保持为空。")
            print("Warning: Could not extract plate number from label, other components will be left empty.")

        file_channels[filename] = chan

    config = {'file_channels': file_channels}
    output_path = os.path.join(folder, 'project_config.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    print(f"\n配置文件已生成: {output_path} / Configuration file generated: {output_path}")

if __name__ == '__main__':
    main()