# -*- coding: utf-8 -*-
"""
手动配置文件生成工具 (manual_config.py) 交互式双语版
功能：运行时先询问文件夹路径，然后遍历文件夹内所有C3D文件，
      对每个文件自动检测所有力板，并依次让用户为每个力板选择垂直力通道，
      自动匹配同板的其他分量（Fx, Fy, Mx, My, Mz, COPx, COPy），
      并可指定该力板的侧别（1=左脚，2=右脚），最终生成包含 force_plates 列表的 project_config.json。
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

def detect_plates(acq):
    """
    检测文件中有哪些力板（通过标签中的数字分组，排除力矩通道），
    返回一个字典，键为板号，值为该板的标签列表和最大值列表。
    """
    labels, max_vals = get_channel_info(acq)
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
    return plates_dict

def main():
    print("="*60)
    print("手动配置工具（交互式双语版） / Manual Configuration Tool (Interactive Bilingual)")
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

    try:
        top_n = int(input("请输入要显示的前几个候选通道 (默认 5): ").strip() or "5")
        print(f"Enter number of top candidate channels to display (default 5): {top_n}")
    except:
        top_n = 5

    file_channels = {}
    for filename in sorted(c3d_files):
        file_path = os.path.join(folder, filename)
        print(f"\n{'='*40}")
        print(f"处理文件: {filename} / Processing file: {filename}")
        print(f"{'='*40}")

        try:
            acq = c3d_utils.read_c3d(file_path)
        except Exception as e:
            print(f"读取C3D失败: {e} / Failed to read C3D: {e}")
            continue

        # 检测所有力板
        plates_dict = detect_plates(acq)
        if not plates_dict:
            print("  警告：未检测到任何力板通道，跳过该文件 / Warning: No force plate channels detected, skipping")
            continue

        # 获取所有通道的原始信息（用于显示候选）
        all_labels, all_max_vals = get_channel_info(acq)
        sorted_all_indices = np.argsort(all_max_vals)[::-1]

        print(f"\n所有模拟通道最大值排序 (前 {top_n}): / All analog channels max values (top {top_n}):")
        print("  排名 Rank | 编号 Index | 标签 Label               | 最大值 Max value")
        print("  -----------|------------|--------------------------|--------------")
        for rank, idx in enumerate(sorted_all_indices[:top_n], start=1):
            print(f"  {rank:4d}      | {idx:4d}      | {all_labels[idx]:24s} | {all_max_vals[idx]:8.2f}")

        # 为每个力板让用户选择垂直力通道和侧别
        force_plates = []
        plate_numbers = sorted(plates_dict.keys(), key=lambda x: int(x))
        for plate_num_str in plate_numbers:
            print(f"\n--- 配置力板 {plate_num_str} / Configuring Plate {plate_num_str} ---")
            info = plates_dict[plate_num_str]
            # 显示该板内的候选通道
            print(f"  该力板内的通道 (按最大值排序): / Channels in this plate (sorted by max):")
            plate_indices = info['indices']
            plate_labels = info['labels']
            plate_max_vals = info['max_vals']
            sorted_plate = sorted(zip(plate_indices, plate_labels, plate_max_vals), key=lambda x: x[2], reverse=True)
            for idx_in_plate, label, mv in sorted_plate:
                print(f"    编号 {idx_in_plate:4d}: {label:24s} | 最大值 {mv:8.2f}")

            # 让用户选择垂直力通道编号
            while True:
                try:
                    choice = input(f"请为力板 {plate_num_str} 输入垂直力 (Fz) 通道的编号 (必须选择): ").strip()
                    print(f"Enter the index of the vertical force (Fz) channel for plate {plate_num_str} (required): {choice}")
                    idx = int(choice)
                    if idx in info['indices']:
                        fz_label = all_labels[idx]
                        break
                    else:
                        print("编号不在该力板的通道列表中，请重新输入。/ Index not in this plate's channels, please try again.")
                except ValueError:
                    print("请输入数字编号。/ Please enter a numeric index.")

            # 匹配该板的其它分量
            chan = match_components_for_plate(plate_num_str, info['labels'], fz_label)

            # ========== 修改侧别输入为数字选择 ==========
            print(f"请为力板 {plate_num_str} 指定侧别: 1=左脚 left, 2=右脚 right (直接回车默认为 unknown)")
            print(f"Specify side for plate {plate_num_str}: 1=left, 2=right (Enter for unknown)")
            side_choice = input("请输入数字 / Enter number: ").strip()
            if side_choice == '1':
                chan['side'] = 'left'
            elif side_choice == '2':
                chan['side'] = 'right'
            else:
                chan['side'] = 'unknown'
                print("已设为 unknown / Set to unknown")
            # ===========================================

            force_plates.append(chan)

            print(f"  力板 {plate_num_str} 匹配结果 / Plate {plate_num_str} matched components:")
            print(f"    Fz = {chan['force_vz']}")
            print(f"    Fx = {chan['force_vx']}, Fy = {chan['force_vy']}")
            print(f"    Mx = {chan['torque_x']}, My = {chan['torque_y']}, Mz = {chan['torque_z']}")
            print(f"    COPx = {chan['cop_x']}, COPy = {chan['cop_y']}")
            print(f"    侧别 Side = {chan['side']}")

        # 将该文件的配置存入
        file_channels[filename] = {'force_plates': force_plates}
        print(f"\n文件 {filename} 配置完成，共 {len(force_plates)} 块力板。/ File {filename} configured, {len(force_plates)} plate(s).")

    # 写入配置文件
    config = {'file_channels': file_channels}
    output_path = os.path.join(folder, 'project_config.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"配置文件已生成: {output_path} / Configuration file generated: {output_path}")
    print(f"包含 {len(file_channels)} 个文件的配置。/ Configured {len(file_channels)} files.")

if __name__ == '__main__':
    main()