# -*- coding: utf-8 -*-
"""
自动配置文件生成工具 (auto_config.py) 交互式双语版
功能：运行时先询问文件夹路径，然后自动为文件夹内所有C3D文件配置垂直力通道
      （排除力矩通道），并自动匹配同板的其他分量（Fx, Fy, Mx, My, Mz, COPx, COPy），
      直接生成 project_config.json。
使用方式：
    python auto_config.py
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
    """清理路径中的不可见字符 / Clean invisible characters from path"""
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

def is_momentum(label):
    """判断是否为力矩通道（根据常见力矩关键词）"""
    upper = label.upper()
    return any(kw in upper for kw in ['MX', 'MY', 'MZ'])

def extract_plate_number(label):
    numbers = re.findall(r'\d+', label)
    return numbers[-1] if numbers else None

def main():
    print("自动配置工具（交互式双语版） / Auto Configuration Tool (Interactive Bilingual)")
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

    file_channels = {}
    for filename in sorted(c3d_files):
        file_path = os.path.join(folder, filename)
        print(f"\n处理: {filename} / Processing: {filename}")
        acq = c3d_utils.read_c3d(file_path)
        labels, max_vals = get_channel_info(acq)

        candidate_indices = [i for i, label in enumerate(labels) if not is_momentum(label)]
        if not candidate_indices:
            print(f"警告: {filename} 中未找到非力矩通道，跳过 / Warning: No non‑momentum channels found in {filename}, skipping")
            continue

        best_idx = max(candidate_indices, key=lambda i: max_vals[i])
        fz_label = labels[best_idx]

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
            print(f"  Fz = {chan['force_vz']}")
            if chan['force_vx']: print(f"  Fx = {chan['force_vx']}")
            if chan['force_vy']: print(f"  Fy = {chan['force_vy']}")
            if chan['torque_x']: print(f"  Mx = {chan['torque_x']}")
            if chan['torque_y']: print(f"  My = {chan['torque_y']}")
            if chan['torque_z']: print(f"  Mz = {chan['torque_z']}")
            if chan['cop_x']: print(f"  COPx = {chan['cop_x']}")
            if chan['cop_y']: print(f"  COPy = {chan['cop_y']}")
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