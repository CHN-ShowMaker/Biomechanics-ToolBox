# -*- coding: utf-8 -*-
"""
C3D文件通用处理函数（含项目配置支持、矩阵校准、多分量数据获取）
版本：4.0 多力板支持版
依赖：btk, numpy, scipy, json, os, re
"""

import btk
import numpy as np
from scipy.signal import butter, filtfilt
import config
import json
import os
import re

# ========== C3D 文件读取 ==========

def read_c3d(file_path):
    """读取C3D文件，返回acq对象"""
    reader = btk.btkAcquisitionFileReader()
    reader.SetFilename(file_path)
    reader.Update()
    return reader.GetOutput()

# ========== 配置文件读取与解析 ==========

def get_project_config(c3d_file_path):
    """
    从 C3D 文件所在目录向上查找 project_config.json，
    返回配置字典，格式为 {'plates': [ ... ]}，每个元素是一个力板的通道映射。
    兼容旧格式（单板字典），自动转换为新格式。
    """
    folder = os.path.dirname(c3d_file_path)
    config_path = os.path.join(folder, 'project_config.json')
    plates_config = []
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            file_channels = config_data.get('file_channels', {})
            filename = os.path.basename(c3d_file_path)
            if filename in file_channels:
                entry = file_channels[filename]
                # 检查是否为新格式（包含 force_plates 键）
                if 'force_plates' in entry:
                    plates_config = entry['force_plates']
                else:
                    # 旧格式：单个板字典，转换为列表，默认板号为1
                    plate = {'plate_id': 1, **entry}
                    plates_config = [plate]
                    print(f"检测到旧版配置文件，已自动转换为单力板配置（板号1）。/ Old config detected, converted to single-plate (plate 1).")
        except Exception as e:
            print(f"读取配置文件失败: {e} / Failed to read config: {e}")
    return {'plates': plates_config}

# ========== 力板自动检测（无配置时使用）==========

def _extract_plate_number(label):
    """从标签中提取数字后缀，返回数字字符串或None"""
    numbers = re.findall(r'\d+', label)
    return numbers[-1] if numbers else None

def _match_components_for_plate(plate_num, labels_in_plate):
    """
    根据板号和在当前板内出现的标签列表，匹配各分量。
    返回一个字典，包含该板的通道映射（plate_id, force_vz, force_vx, ...）。
    """
    chan = {
        'plate_id': int(plate_num),
        'force_vz': None,
        'force_vx': None,
        'force_vy': None,
        'torque_x': None,
        'torque_y': None,
        'torque_z': None,
        'cop_x': None,
        'cop_y': None
    }
    # 候选模式列表
    candidates = {
        'force_vx': [f'FX{plate_num}', f'Fx{plate_num}'],
        'force_vy': [f'FY{plate_num}', f'Fy{plate_num}'],
        'torque_x': [f'MX{plate_num}', f'Mx{plate_num}'],
        'torque_y': [f'MY{plate_num}', f'My{plate_num}'],
        'torque_z': [f'MZ{plate_num}', f'Mz{plate_num}'],
        'cop_x': [f'COP{plate_num}.X', f'COP{plate_num}_X', f'Force.COPx{plate_num}', f'COP_X{plate_num}'],
        'cop_y': [f'COP{plate_num}.Y', f'COP{plate_num}_Y', f'Force.COPy{plate_num}', f'COP_Y{plate_num}']
    }
    labels_set = set(labels_in_plate)
    for comp, cand_list in candidates.items():
        for cand in cand_list:
            if cand in labels_set:
                chan[comp] = cand
                break
    return chan

def auto_detect_plates(acq):
    """
    从 acq 对象中自动检测所有力板，返回板配置列表。
    每个配置包含 plate_id 及各分量标签。
    """
    # 获取所有模拟通道的标签和最大值
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

    # 按板号分组
    plates_dict = {}  # key: 板号, value: {'indices': [...], 'labels': [...], 'max_vals': [...]}
    for idx, label in enumerate(labels):
        plate_num = _extract_plate_number(label)
        if plate_num is None:
            continue  # 无数字的通道忽略（可能不是力板通道）
        if plate_num not in plates_dict:
            plates_dict[plate_num] = {'indices': [], 'labels': [], 'max_vals': []}
        plates_dict[plate_num]['indices'].append(idx)
        plates_dict[plate_num]['labels'].append(label)
        plates_dict[plate_num]['max_vals'].append(max_vals[idx])

    if not plates_dict:
        print("自动检测：未找到任何带数字后缀的通道，无法识别力板。/ Auto detect: No plate-numbered channels found.")
        return []

    plates_config = []
    for plate_num_str, info in plates_dict.items():
        # 在该板内选择最大值最大的通道作为垂直力通道
        best_idx_in_plate = info['indices'][np.argmax(info['max_vals'])]
        fz_label = labels[best_idx_in_plate]

        # 生成该板的通道映射
        chan = _match_components_for_plate(plate_num_str, info['labels'])
        chan['force_vz'] = fz_label  # 设置垂直力通道
        plates_config.append(chan)

    print(f"自动检测到 {len(plates_config)} 块力板。/ Auto-detected {len(plates_config)} force plate(s).")
    return plates_config

# ========== 力板校准矩阵获取 ==========

def get_force_plate_calibration(acq, plate_index):
    """
    获取指定索引（0-based）力板的校准矩阵和类型。
    返回 (cal_matrix, ftype)，若无校准矩阵则 cal_matrix=None。
    """
    try:
        meta = acq.GetMetaData()
        fp_group = meta.GetChild('FORCE_PLATFORM')
        if not fp_group:
            return None, 0
        used = fp_group.GetChild('USED').GetInfo().ToDouble()[0]
        if plate_index >= used:
            return None, 0
        types = fp_group.GetChild('TYPE').GetInfo().ToDouble()
        if len(types) <= plate_index:
            return None, 0
        ftype = int(types[plate_index])

        # 获取校准矩阵参数（可能为6x6矩阵或6个对角元素）
        cal_matrix_param = fp_group.GetChild('CAL_MATRIX')
        if not cal_matrix_param:
            return None, ftype
        cal_data = cal_matrix_param.GetInfo().ToDouble()
        dims = cal_matrix_param.GetInfo().GetDimensions()
        if len(dims) == 2 and dims[0] == 6 and dims[1] == 6:
            # 完整6x6矩阵
            cal_matrix = np.array(cal_data).reshape(6, 6)
        elif len(dims) == 1 and dims[0] == 6:
            # 对角矩阵（6个元素）
            cal_matrix = np.diag(cal_data)
        else:
            cal_matrix = None
        return cal_matrix, ftype
    except Exception as e:
        print(f"解析力板校准矩阵失败 (板索引 {plate_index}): {e} / Failed to parse calibration matrix (plate {plate_index}): {e}")
        return None, 0

# ========== 获取所有力板数据 ==========

def get_force_data(acq, c3d_file_path=None):
    """
    返回 (plates_data, fs)
    plates_data: 列表，每个元素是一个字典，包含该力板的 Fx, Fy, Fz, Mx, My, Mz, COPx, COPy
    fs: 采样率 (Hz)
    """
    frames = acq.GetAnalogFrameNumber()
    fs = acq.GetAnalogFrequency()
    zero_arr = np.zeros(frames)

    # 获取配置文件（若有）
    config_data = {}
    if c3d_file_path:
        config_data = get_project_config(c3d_file_path)
    plates_config = config_data.get('plates', [])

    # 若没有配置，则自动检测
    if not plates_config:
        print("未找到配置文件或配置为空，尝试自动检测力板。/ No config found, attempting auto-detection.")
        plates_config = auto_detect_plates(acq)
        if not plates_config:
            print("自动检测失败，将返回空数据。/ Auto-detection failed, returning empty data.")
            return [], fs

    # 构建标签到数据的映射（一次读取，避免重复）
    analog_data = {}
    for i in range(acq.GetAnalogs().GetItemNumber()):
        analog = acq.GetAnalog(i)
        label = analog.GetLabel()
        values = analog.GetValues()
        # 确保数据是一维
        if values.ndim == 2 and values.shape[1] > 1:
            # 多列数据取第一列（常见情况）
            analog_data[label] = values[:, 0]
        else:
            analog_data[label] = values.flatten()

    plates_data = []
    for plate_cfg in plates_config:
        plate_id = plate_cfg.get('plate_id', 1)
        # 初始化该板的数据字典
        plate_dict = {comp: zero_arr.copy() for comp in ['Fx', 'Fy', 'Fz', 'Mx', 'My', 'Mz', 'COPx', 'COPy']}

        # 分量与配置键的对应
        comp_map = [
            ('Fx', 'force_vx'),
            ('Fy', 'force_vy'),
            ('Fz', 'force_vz'),
            ('Mx', 'torque_x'),
            ('My', 'torque_y'),
            ('Mz', 'torque_z'),
            ('COPx', 'cop_x'),
            ('COPy', 'cop_y')
        ]

        # 根据配置填充
        for comp, key in comp_map:
            label = plate_cfg.get(key)
            if label and label in analog_data:
                plate_dict[comp] = analog_data[label]

        # 应用该板的校准矩阵
        try:
            # 注意：plate_index 从0开始，假设配置中的 plate_id 从1开始且与文件顺序一致
            cal_matrix, ftype = get_force_plate_calibration(acq, plate_index=plate_id-1)
            if cal_matrix is not None:
                # 构建原始6分量矩阵
                raw = np.column_stack([
                    plate_dict['Fx'],
                    plate_dict['Fy'],
                    plate_dict['Fz'],
                    plate_dict['Mx'],
                    plate_dict['My'],
                    plate_dict['Mz']
                ])
                calibrated = raw @ cal_matrix.T
                plate_dict['Fx'] = calibrated[:, 0]
                plate_dict['Fy'] = calibrated[:, 1]
                plate_dict['Fz'] = calibrated[:, 2]
                plate_dict['Mx'] = calibrated[:, 3]
                plate_dict['My'] = calibrated[:, 4]
                plate_dict['Mz'] = calibrated[:, 5]
                print(f"[力板 {plate_id}] 应用校准矩阵成功，Fz 最大值: {np.max(plate_dict['Fz']):.1f} N / Calibrated, Fz max: {np.max(plate_dict['Fz']):.1f} N")
            else:
                print(f"[力板 {plate_id}] 无校准矩阵，使用原始值 / No calibration matrix, using raw values")
        except Exception as e:
            print(f"[力板 {plate_id}] 校准失败: {e}，使用原始值 / Calibration failed, using raw values")

        plates_data.append(plate_dict)

    return plates_data, fs

# ========== 兼容旧函数 ==========

def find_force_channel(acq, c3d_file_path=None):
    """
    兼容旧版，返回第一个力板的垂直力数据。
    """
    plates_data, fs = get_force_data(acq, c3d_file_path)
    if plates_data:
        return plates_data[0]['Fz'], fs
    else:
        return np.array([]), fs

# ========== 信号处理 ==========

def lowpass_filter(data, fs, cutoff=None, order=None):
    if cutoff is None:
        cutoff = config.FILTER_CUTOFF
    if order is None:
        order = config.FILTER_ORDER
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low')
    y = filtfilt(b, a, data)
    return y

# ========== 事件检测 ==========

def detect_gait_events(force, fs):
    threshold = config.GAIT_THRESHOLD_RATIO * np.max(force)
    above = force > threshold
    hs = np.where(np.diff(above.astype(int)) == 1)[0] + 1
    to = np.where(np.diff(above.astype(int)) == -1)[0] + 1
    return hs, to

def detect_jump_events(force, fs):
    threshold = config.JUMP_THRESHOLD_RATIO * np.max(force)
    in_flight = force < threshold
    flight_starts = np.where(np.diff(in_flight.astype(int)) == 1)[0] + 1
    flight_ends = np.where(np.diff(in_flight.astype(int)) == -1)[0] + 1
    if len(flight_starts) == 0 or len(flight_ends) == 0:
        return None, None, None, None
    takeoff = flight_starts[0]
    landing = flight_ends[0]
    pre_window = min(config.JUMP_PRE_WINDOW, takeoff)
    pre_seg = force[takeoff - pre_window : takeoff]
    takeoff_peak_frame = takeoff - pre_window + np.argmax(pre_seg)
    post_window = min(config.JUMP_POST_WINDOW, len(force) - landing)
    post_seg = force[landing : landing + post_window]
    landing_peak_frame = landing + np.argmax(post_seg)
    return takeoff, landing, takeoff_peak_frame, landing_peak_frame