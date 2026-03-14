# -*- coding: utf-8 -*-
"""
C3D文件通用处理函数（含项目配置支持、矩阵校准、多分量数据获取）
版本：3.0 双语版
功能：
    - 读取C3D，自动/手动配置力通道
    - 解析力板校准矩阵（TYPE-2/3/4）
    - 返回校准后的多分量数据字典
    - 支持 project_config.json（全局）和 file_channels.json（按文件覆盖）
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
    从 C3D 文件所在目录向上查找 project_config.json，以及 file_channels.json（按文件名覆盖）。
    返回配置字典。
    """
    folder = os.path.dirname(c3d_file_path)
    if folder in _config_cache:
        return _config_cache[folder]

    config_data = {}

    # 读取 project_config.json（全局配置）
    proj_path = os.path.join(folder, 'project_config.json')
    if os.path.exists(proj_path):
        try:
            with open(proj_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            print(f"[配置 Config] 加载全局配置文件: {proj_path} / Loaded global config file: {proj_path}")
        except Exception as e:
            print(f"[配置 Config] 读取 project_config.json 失败: {e} / Failed to read project_config.json: {e}")

    # 读取 file_channels.json（按文件覆盖）
    file_path = os.path.join(folder, 'file_channels.json')
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
            file_channels = file_config.get('file_channels', {})
            filename = os.path.basename(c3d_file_path)
            if filename in file_channels and file_channels[filename]:
                if 'channels' not in config_data:
                    config_data['channels'] = {}
                for key, value in file_channels[filename].items():
                    if value is not None:
                        config_data['channels'][key] = value
                print(f"[配置 Config] 应用按文件配置: {filename} -> {config_data['channels']} / Applied per-file config: {filename} -> {config_data['channels']}")
            else:
                print(f"[配置 Config] 文件中没有 {filename} 的配置 / No config for {filename} in file")
        except Exception as e:
            print(f"[配置 Config] 读取 file_channels.json 失败: {e} / Failed to read file_channels.json: {e}")
    else:
        print(f"[配置 Config] 未找到 file_channels.json，使用全局配置 / No file_channels.json found, using global config")

    _config_cache[folder] = config_data
    return config_data

def read_c3d(file_path):
    """读取C3D文件，返回acq对象 / Read C3D file and return acq object"""
    reader = btk.btkAcquisitionFileReader()
    reader.SetFilename(file_path)
    reader.Update()
    return reader.GetOutput()

def get_force_plate_calibration(acq, plate_index=0):
    """
    解析指定力板的校准矩阵，返回 (cal_matrix, force_plate_type)
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
        print(f"解析力板校准矩阵失败: {e} / Failed to parse force plate calibration matrix: {e}")
        return None, 0

def get_force_data(acq, c3d_file_path=None):
    """
    获取校准后的完整力板数据，返回字典和采样频率。
    优先使用项目配置文件中的通道映射，若未配置则尝试自动识别（仅 Fz）。
    对于多列模拟通道，取第一列作为代表（假设单分量）。
    """
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

    # 获取配置文件中的通道映射
    config_data = {}
    if c3d_file_path:
        config_data = get_project_config(c3d_file_path)
    channel_map = config_data.get('channels', {})
    print(f"[力数据 Force Data] 使用的通道映射: {channel_map} / Channel mapping used: {channel_map}")

    # 构建标签到数据的映射（保留原始多维数组）
    analog_data = {}
    for i in range(acq.GetAnalogs().GetItemNumber()):
        analog = acq.GetAnalog(i)
        label = analog.GetLabel()
        values = analog.GetValues()  # 可能为 (frames, 1) 或 (frames, 多列)
        analog_data[label] = values

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

    # 从配置中读取各分量
    for comp, key in components:
        label = channel_map.get(key)
        if label and label in analog_data:
            data = analog_data[label]
            if data.ndim == 2 and data.shape[1] > 1:
                # 多列数据：取第一列作为该分量的值（假设分量对应第一列）
                result[comp] = data[:, 0]
                print(f"[力数据 Force Data] {comp} 从通道 {label} 取第一列，最大值: {np.max(result[comp]):.1f} / {comp} from channel {label} (first column), max: {np.max(result[comp]):.1f}")
            else:
                result[comp] = data.flatten()
                print(f"[力数据 Force Data] {comp} 从通道 {label} 读取，最大值: {np.max(result[comp]):.1f} / {comp} from channel {label}, max: {np.max(result[comp]):.1f}")
        elif label:
            print(f"[力数据 Force Data] 警告：配置中指定的通道 {label} 不存在，{comp} 将保持为零。 / Warning: Channel {label} specified in config does not exist. {comp} will remain zero.")

    # 自动识别 Fz（如果未配置且当前为零）
    if 'force_vz' not in channel_map or not channel_map.get('force_vz'):
        if np.all(result['Fz'] == 0):
            for label, data in analog_data.items():
                if 'FZ' in label.upper():
                    if data.ndim == 2 and data.shape[1] > 1:
                        result['Fz'] = data[:, 0]  # 同样取第一列
                    else:
                        result['Fz'] = data.flatten()
                    print(f"[力数据 Force Data] 自动识别垂直力通道: {label} / Automatically identified vertical force channel: {label}")
                    break

    # 应用力板校准矩阵（如果存在）
    try:
        cal_matrix, ftype = get_force_plate_calibration(acq, plate_index=0)
        if cal_matrix is not None:
            raw = np.column_stack([
                result['Fx'],
                result['Fy'],
                result['Fz'],
                result['Mx'],
                result['My'],
                result['Mz']
            ])
            calibrated = raw @ cal_matrix.T
            result['Fx'] = calibrated[:, 0]
            result['Fy'] = calibrated[:, 1]
            result['Fz'] = calibrated[:, 2]
            result['Mx'] = calibrated[:, 3]
            result['My'] = calibrated[:, 4]
            result['Mz'] = calibrated[:, 5]
            print(f"[力数据 Force Data] 应用力板校准矩阵成功，Fz 最大值变为: {np.max(result['Fz']):.1f} / Force plate calibration matrix applied, Fz max: {np.max(result['Fz']):.1f}")
        else:
            print(f"[力数据 Force Data] 无校准矩阵，使用原始值 / No calibration matrix, using raw values")
    except Exception as e:
        print(f"[力数据 Force Data] 应用力板校准矩阵失败，将使用原始值: {e} / Failed to apply calibration matrix, using raw values: {e}")

    return result, fs

# ---------- 保留旧函数 find_force_channel 供兼容 ----------
def find_force_channel(acq, c3d_file_path=None):
    data_dict, fs = get_force_data(acq, c3d_file_path)
    return data_dict['Fz'], fs

# ---------- 以下为原有函数（未改动） ----------
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