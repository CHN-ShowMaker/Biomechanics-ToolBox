# -*- coding: utf-8 -*-
"""
C3D文件通用处理函数（含项目配置支持、矩阵校准、多分量数据获取）
版本：3.0 修复版
功能：
    - 读取C3D，自动/手动配置力通道
    - 解析力板校准矩阵（TYPE-2/3/4）
    - 返回校准后的多分量数据字典
    - 保留旧函数 `find_force_channel` 用于兼容
依赖：btk, numpy, scipy, json, os
"""

import btk
import numpy as np
from scipy.signal import butter, filtfilt
import config
import json
import os

# 缓存已加载的项目配置
_config_cache = {}

def get_project_config(c3d_file_path):
    """
    从 C3D 文件所在目录向上查找 project_config.json，返回配置字典。
    如果未找到，返回空字典。
    """
    folder = os.path.dirname(c3d_file_path)
    if folder in _config_cache:
        return _config_cache[folder]

    config_path = os.path.join(folder, 'project_config.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            _config_cache[folder] = config_data
            return config_data
        except Exception as e:
            print(f"读取配置文件失败: {e}")
    _config_cache[folder] = {}
    return {}

def read_c3d(file_path):
    """读取C3D文件，返回acq对象"""
    reader = btk.btkAcquisitionFileReader()
    reader.SetFilename(file_path)
    reader.Update()
    return reader.GetOutput()

def get_force_plate_calibration(acq, plate_index=0):
    """
    解析指定力板的校准矩阵，返回 (cal_matrix, force_plate_type)
    参数：
        acq : btk.btkAcquisition
        plate_index : int, 力板编号（从0开始）
    返回：
        cal_matrix : numpy array, 形状 (6,6) 或 (6,1) 取决于类型；若无法解析返回 None
        force_plate_type : int, 2/3/4；若未知返回 0
    """
    try:
        meta = acq.GetMetaData()
        fp_group = meta.GetChild('FORCE_PLATFORM')  # 使用 GetChild 替代 FindChild 以避免迭代器问题
        if not fp_group:
            return None, 0

        used = fp_group.GetChild('USED').GetInfo().ToDouble()[0]
        if plate_index >= used:
            return None, 0

        types = fp_group.GetChild('TYPE').GetInfo().ToDouble()
        if len(types) <= plate_index:
            return None, 0
        ftype = int(types[plate_index])

        cal_matrix_param = fp_group.GetChild('CAL_MATRIX')
        if not cal_matrix_param:
            return None, ftype

        cal_data = cal_matrix_param.GetInfo().ToDouble()
        dims = cal_matrix_param.GetInfo().GetDimensions()
        if len(dims) == 2 and dims[0] == 6 and dims[1] == 6:
            cal_matrix = np.array(cal_data).reshape(6,6)
        elif len(dims) == 1 and dims[0] == 6:
            cal_matrix = np.diag(cal_data)
        else:
            cal_matrix = None
        return cal_matrix, ftype
    except Exception as e:
        print(f"解析力板校准矩阵失败: {e}")
        return None, 0

def get_force_data(acq, c3d_file_path=None):
    """
    获取校准后的完整力板数据，返回字典，包含以下字段（若缺失则为零数组）：
        'Fx', 'Fy', 'Fz', 'Mx', 'My', 'Mz', 'COPx', 'COPy'
    同时返回采样频率 fs
    优先使用项目配置文件中的通道映射，若未配置则尝试自动识别（仅 Fz）。
    若存在多块力板，默认取第一块（可根据配置扩展）。
    """
    # 默认输出
    frames = acq.GetAnalogFrameNumber()
    fs = acq.GetAnalogFrequency()
    zero_arr = np.zeros(frames)
    result = {
        'Fx': zero_arr.copy(),
        'Fy': zero_arr.copy(),
        'Fz': zero_arr.copy(),
        'Mx': zero_arr.copy(),
        'My': zero_arr.copy(),
        'Mz': zero_arr.copy(),
        'COPx': zero_arr.copy(),
        'COPy': zero_arr.copy()
    }

    # 获取配置文件中的通道映射（如果提供了文件路径）
    config_data = {}
    if c3d_file_path:
        config_data = get_project_config(c3d_file_path)
    channel_map = config_data.get('channels', {})

    # 辅助函数：根据标签获取数据
    analog_labels = []
    analog_values = []
    for i in range(acq.GetAnalogs().GetItemNumber()):
        analog = acq.GetAnalog(i)
        label = analog.GetLabel()
        val = analog.GetValues()
        # 取第一列（如果有多列）
        if val.ndim == 2 and val.shape[1] > 1:
            val = val[:, 0]
        else:
            val = val.flatten()
        analog_labels.append(label)
        analog_values.append(val)

    label_to_idx = {label: idx for idx, label in enumerate(analog_labels)}

    # 定义需要获取的分量及其在配置文件中的键名
    components = [
        ('Fx', 'force_vx'),
        ('Fy', 'force_vy'),
        ('Fz', 'force_vz'),
        ('Mx', 'torque_x'),
        ('My', 'torque_y'),
        ('Mz', 'torque_z'),
        ('COPx', 'cop_x'),
        ('COPy', 'cop_y')
    ]

    # 优先从配置读取（仅当配置值存在且非空）
    for comp, key in components:
        label = channel_map.get(key)
        if label and label in label_to_idx:
            result[comp] = analog_values[label_to_idx[label]]
        elif label:
            print(f"警告：配置中指定的通道 {label} 不存在，{comp} 将保持为零。")
        # 若 label 为 None 或空，则跳过，不警告

    # 自动识别 Fz（如果未配置且当前为零）
    if 'force_vz' not in channel_map or not channel_map.get('force_vz'):
        if np.all(result['Fz'] == 0):
            # 简单自动识别：查找包含 'FZ' 的通道
            for label, idx in label_to_idx.items():
                if 'FZ' in label.upper():
                    result['Fz'] = analog_values[idx]
                    print(f"自动识别垂直力通道: {label}")
                    break

    # ---------- 应用力板校准矩阵（如果存在） ----------
    try:
        cal_matrix, ftype = get_force_plate_calibration(acq, plate_index=0)
        if cal_matrix is not None:
            # 构造原始向量 [Fx, Fy, Fz, Mx, My, Mz]（当前未校准的值）
            raw = np.column_stack([
                result['Fx'],
                result['Fy'],
                result['Fz'],
                result['Mx'],
                result['My'],
                result['Mz']
            ])  # shape (frames, 6)
            # 应用校准矩阵（通常 raw @ cal_matrix.T）
            calibrated = raw @ cal_matrix.T
            result['Fx'] = calibrated[:, 0]
            result['Fy'] = calibrated[:, 1]
            result['Fz'] = calibrated[:, 2]
            result['Mx'] = calibrated[:, 3]
            result['My'] = calibrated[:, 4]
            result['Mz'] = calibrated[:, 5]
            print("应用力板校准矩阵成功")
    except Exception as e:
        print(f"应用力板校准矩阵失败，将使用原始值: {e}")

    return result, fs

# ---------- 保留旧函数 find_force_channel 供兼容 ----------
def find_force_channel(acq, c3d_file_path=None):
    """
    旧版函数，仅返回 (force_data, fs)，其中 force_data 是垂直力的一维数组。
    内部调用 get_force_data 并取 'Fz' 字段。
    """
    data_dict, fs = get_force_data(acq, c3d_file_path)
    return data_dict['Fz'], fs

# ---------- 以下为原有函数（未改动） ----------
def lowpass_filter(data, fs, cutoff=None, order=None):
    """低通滤波，使用config中的默认参数"""
    if cutoff is None:
        cutoff = config.FILTER_CUTOFF
    if order is None:
        order = config.FILTER_ORDER
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low')
    y = filtfilt(b, a, data)
    return y

def detect_gait_events(force, fs):
    """
    步态事件检测：返回 (触地帧列表, 离地帧列表)
    基于 config.GAIT_THRESHOLD_RATIO 动态阈值
    """
    threshold = config.GAIT_THRESHOLD_RATIO * np.max(force)
    above = force > threshold
    hs = np.where(np.diff(above.astype(int)) == 1)[0] + 1
    to = np.where(np.diff(above.astype(int)) == -1)[0] + 1
    return hs, to

def detect_jump_events(force, fs):
    """
    跳跃事件检测：返回 (离地帧, 落地帧, 起跳峰值帧, 落地峰值帧)
    基于 config.JUMP_THRESHOLD_RATIO
    """
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