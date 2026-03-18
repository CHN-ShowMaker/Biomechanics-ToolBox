# -*- coding: utf-8 -*-
"""
自动配置文件生成工具 (auto_config.py) 交互式双语版
功能：运行时先询问文件夹路径，然后自动为文件夹内所有C3D文件配置多力板通道
      （排除力矩通道），自动检测每个力板的垂直力通道，并匹配同板的其他分量，
      生成包含 force_plates 列表的 project_config.json。
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
    """获取所有模拟通道的标签和最大值"""
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
    """从标签中提取数字后缀"""
    numbers = re.findall(r'\d+', label)
    return numbers[-1] if numbers else None

def match_components_for_plate(plate_num, labels_in_plate, fz_label):
    """
    为指定力板匹配其他分量（Fx, Fy, Mx, My, Mz, COPx, COPy）
    返回该板的通道映射字典（包含 plate_id 和所有分量）
    """
    chan = {
        'plate_id': int(plate_num),
        'force_vz': fz_label,
        'force_vx': None,
        'force_vy': None,
        'torque_x': None,
        'torque_y': None,
        'torque_z': None,
        'cop_x': None,
        'cop_y': None
    }
    labels_set = set(labels_in_plate)
    # 候选列表
    candidates = {
        'force_vx': [f'FX{plate_num}', f'Fx{plate_num}'],
        'force_vy': [f'FY{plate_num}', f'Fy{plate_num}'],
        'torque_x': [f'MX{plate_num}', f'Mx{plate_num}'],
        'torque_y': [f'MY{plate_num}', f'My{plate_num}'],
        'torque_z': [f'MZ{plate_num}', f'Mz{plate_num}'],
        'cop_x': [f'COP{plate_num}.X', f'COP{plate_num}_X', f'Force.COPx{plate_num}', f'COP_X{plate_num}'],
        'cop_y': [f'COP{plate_num}.Y', f'COP{plate_num}_Y', f'Force.COPy{plate_num}', f'COP_Y{plate_num}']
    }
    for comp, cand_list in candidates.items():
        for cand in cand_list:
            if cand in labels_set:
                chan[comp] = cand
                break
    return chan

def main():
    print("="*60)
    print("自动配置工具（交互式双语版） / Auto Configuration Tool (Interactive Bilingual)")
    print("="*60)

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
        print(f"\n处理文件: {filename} / Processing: {filename}")

        try:
            acq = c3d_utils.read_c3d(file_path)
        except Exception as e:
            print(f"读取C3D失败: {e} / Failed to read C3D: {e}")
            continue

        labels, max_vals = get_channel_info(acq)

        # 按板号分组（排除力矩通道）
        plates_dict = {}
        for idx, label in enumerate(labels):
            if is_momentum(label):
                continue
            plate_num = extract_plate_number(label)
            if plate_num is None:
                continue
            if plate_num not in plates_dict:
                plates_dict[plate_num] = {'indices': [], 'labels': [], 'max_vals': []}
            plates_dict[plate_num]['indices'].append(idx)
            plates_dict[plate_num]['labels'].append(label)
            plates_dict[plate_num]['max_vals'].append(max_vals[idx])

        if not plates_dict:
            print("  警告：未找到任何带数字后缀的非力矩通道，跳过该文件 / Warning: No plate-numbered non-momentum channels found, skipping")
            continue

        # 为每个力板生成配置
        force_plates = []
        for plate_num_str, info in plates_dict.items():
            # 在该板内选择最大值最大的通道作为垂直力通道
            best_idx_in_plate = info['indices'][np.argmax(info['max_vals'])]
            fz_label = labels[best_idx_in_plate]
            # 匹配其他分量
            chan = match_components_for_plate(plate_num_str, info['labels'], fz_label)
            force_plates.append(chan)

        # 输出检测结果
        print(f"  检测到 {len(force_plates)} 块力板 / Detected {len(force_plates)} force plate(s):")
        for i, plate in enumerate(force_plates):
            print(f"    力板 {plate['plate_id']}: Fz = {plate['force_vz']}, Fx = {plate['force_vx']}, Fy = {plate['force_vy']}, "
                  f"Mx = {plate['torque_x']}, My = {plate['torque_y']}, Mz = {plate['torque_z']}, "
                  f"COPx = {plate['cop_x']}, COPy = {plate['cop_y']}")

        file_channels[filename] = {'force_plates': force_plates}

    # 写入配置文件
    config = {'file_channels': file_channels}
    output_path = os.path.join(folder, 'project_config.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

    print(f"\n配置文件已生成: {output_path} / Configuration file generated: {output_path}")
    print("包含以下文件的配置: / Configured files:", list(file_channels.keys()))

if __name__ == '__main__':
    main()