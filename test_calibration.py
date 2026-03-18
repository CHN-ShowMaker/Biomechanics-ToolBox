# -*- coding: utf-8 -*-
"""
测试力板校准脚本 (双语版)
功能：测试单个C3D文件的力板校准矩阵和力数据，显示所有力板信息。
"""

import btk
import numpy as np
import c3d_utils
import sys
import os

def main():
    if len(sys.argv) < 2:
        print("用法: python test_calibration.py <C3D文件路径>")
        print("Usage: python test_calibration.py <C3D file path>")
        return

    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path} / File does not exist: {file_path}")
        return

    acq = c3d_utils.read_c3d(file_path)
    print(f"分析文件: {file_path} / Analyzing file: {file_path}")

    plates_data, fs = c3d_utils.get_force_data(acq, file_path)
    print(f"采样率: {fs} Hz / Sampling rate: {fs} Hz")
    print(f"检测到力板数量: {len(plates_data)} / Plates detected: {len(plates_data)}")

    for plate_idx, plate_dict in enumerate(plates_data):
        print(f"\n--- 力板 {plate_idx+1} / Plate {plate_idx+1} ---")
        cal, ftype = c3d_utils.get_force_plate_calibration(acq, plate_index=plate_idx)
        print(f"力板类型: {ftype} / Force plate type: {ftype}")
        if cal is not None:
            print("校准矩阵: / Calibration matrix:")
            print(cal)
        else:
            print("无校准矩阵 / No calibration matrix")

        print("各分量最大值: / Component max values:")
        for comp in ['Fx', 'Fy', 'Fz', 'Mx', 'My', 'Mz', 'COPx', 'COPy']:
            print(f"  {comp}: {np.max(plate_dict[comp]):.1f}")

if __name__ == '__main__':
    main()