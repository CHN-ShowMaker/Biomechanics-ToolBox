# -*- coding: utf-8 -*-
"""
交互式图像拟合脚本
根据提示输入包含 _curve.npy 文件的文件夹路径，自动计算平均曲线并绘图。
"""

import numpy as np
import glob
import matplotlib.pyplot as plt
import os
import plot_utils

def clean_path(path):
    return path.strip().lstrip('\u202a').lstrip('\u200e').lstrip('\u200f')

def main():
    plot_utils.setup_chinese_font()
    print("="*50)
    print("交互式图像拟合脚本（平均曲线）")
    print("="*50)

    folder = input("请输入包含 *_curve.npy 文件的文件夹路径: ").strip()
    folder = clean_path(folder)
    if not os.path.isdir(folder):
        print("文件夹不存在，请检查路径。")
        return

    # 查找所有曲线文件
    curve_files = glob.glob(os.path.join(folder, '*_curve.npy'))
    if not curve_files:
        print(f"在 {folder} 中没有找到任何 *_curve.npy 文件。")
        return

    print(f"找到 {len(curve_files)} 条曲线。")

    # 读取所有曲线
    curves = []
    for f in curve_files:
        curve = np.load(f)
        curves.append(curve)

    curves = np.array(curves)

    # 计算平均和标准差
    mean_curve = np.mean(curves, axis=0)
    std_curve = np.std(curves, axis=0)

    # 时间轴
    x = np.linspace(0, 100, len(mean_curve))

    # 绘图
    plt.figure(figsize=(8, 5))
    plt.plot(x, mean_curve, 'b-', linewidth=2, label='平均')
    plt.fill_between(x, mean_curve - std_curve, mean_curve + std_curve,
                     alpha=0.3, color='b', label='±1 标准差')
    plt.xlabel('归一化时间 (%)')
    plt.ylabel('垂直力 (N)')
    plt.title(f'平均力曲线 (n={len(curves)})')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # 保存图片
    output_name = input("请输入输出图片文件名 (默认 average_curve.png): ").strip()
    if not output_name:
        output_name = 'average_curve.png'
    output_path = os.path.join(folder, output_name)
    plt.savefig(output_path, dpi=300)
    print(f"平均曲线图已保存至：{output_path}")
    plt.show()

if __name__ == '__main__':
    main()