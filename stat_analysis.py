# -*- coding: utf-8 -*-
"""
交互式统计分析脚本 (修复小样本和文件关闭问题)
运行后根据提示输入文件路径、指标列名、分组列名等，自动进行统计检验并生成图表。
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os
from statsmodels.stats.multicomp import pairwise_tukeyhsd
import sys
import io
import plot_utils

def clean_path(path):
    """清理路径中的不可见字符"""
    return path.strip().lstrip('\u202a').lstrip('\u200e').lstrip('\u200f')

def get_input(prompt, default=None):
    """获取用户输入，可带默认值"""
    if default:
        value = input(f"{prompt} (默认: {default}): ").strip()
        if value == '':
            value = default
    else:
        value = input(f"{prompt}: ").strip()
    return value

def main():
    # 设置中文字体
    plot_utils.setup_chinese_font()

    print("="*50)
    print("交互式统计分析脚本")
    print("="*50)

    # 获取文件路径
    file_path = get_input("请输入Excel文件路径")
    file_path = clean_path(file_path)
    if not os.path.exists(file_path):
        print("文件不存在，请检查路径。")
        return

    # 读取数据
    try:
        df = pd.read_excel(file_path)
        print(f"成功读取数据，共 {len(df)} 行，列名：{list(df.columns)}")
    except Exception as e:
        print(f"读取文件失败：{e}")
        return

    # 获取指标列名
    print("\n可用列名：", list(df.columns))
    metric_col = get_input("请输入要分析的指标列名")
    if metric_col not in df.columns:
        print(f"错误：列 '{metric_col}' 不存在。")
        return

    # 获取分组列名
    group_col = get_input("请输入分组列名（用于比较的组别）")
    if group_col not in df.columns:
        print(f"错误：列 '{group_col}' 不存在。")
        return

    # 相关分析选项
    do_corr = get_input("是否进行相关分析？(y/n)", default='n').lower()
    corr_x, corr_y = None, None
    if do_corr == 'y':
        corr_x = get_input("请输入相关分析的X列名")
        corr_y = get_input("请输入相关分析的Y列名")
        if corr_x not in df.columns or corr_y not in df.columns:
            print("相关分析列名不存在，跳过相关分析。")
            corr_x = corr_y = None

    # 输出目录
    output_dir = get_input("请输入输出目录（默认为当前目录下的 stat_results）", default='./stat_results')
    output_dir = clean_path(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    # 设置日志
    log_path = os.path.join(output_dir, 'analysis_log.txt')
    log_file = open(log_path, 'w', encoding='utf-8')
    original_stdout = sys.stdout  # 保存原始标准输出

    class Tee:
        def __init__(self, *files):
            self.files = files
        def write(self, obj):
            for f in self.files:
                f.write(obj)
                f.flush()
        def flush(self):
            for f in self.files:
                f.flush()

    sys.stdout = Tee(sys.stdout, log_file)
    print(f"日志文件已创建：{log_path}")

    # 去除缺失值
    df_clean = df[[metric_col, group_col]].dropna()
    if len(df_clean) < len(df):
        print(f"警告：已删除 {len(df)-len(df_clean)} 行包含缺失值的数据。")

    groups = df_clean[group_col].unique()
    print(f"分组情况：{groups}")

    # 检查每组样本量
    group_sizes = df_clean.groupby(group_col)[metric_col].count()
    min_group_size = group_sizes.min()
    if min_group_size < 2:
        print(f"警告：某些组样本量不足（最小样本量 = {min_group_size}），无法进行统计检验。只输出描述统计和图表。")
        perform_test = False
    else:
        perform_test = True

    # 根据组数选择检验
    if len(groups) == 2:
        group1 = df_clean[df_clean[group_col] == groups[0]][metric_col]
        group2 = df_clean[df_clean[group_col] == groups[1]][metric_col]

        print(f"\n组 {groups[0]} 描述统计：")
        print(group1.describe())
        print(f"\n组 {groups[1]} 描述统计：")
        print(group2.describe())

        if perform_test:
            # 正态性检验
            if len(group1) < 5000:
                stat1, p1 = stats.shapiro(group1)
                normal1 = p1 > 0.05
            else:
                normal1 = True
            if len(group2) < 5000:
                stat2, p2 = stats.shapiro(group2)
                normal2 = p2 > 0.05
            else:
                normal2 = True

            if not (normal1 and normal2):
                print("数据不符合正态分布，使用 Mann-Whitney U 检验")
                u_stat, p_value = stats.mannwhitneyu(group1, group2, alternative='two-sided')
                test_name = 'Mann-Whitney U'
                effect_size = u_stat / (len(group1)*len(group2))
            else:
                # 方差齐性检验
                levene_stat, levene_p = stats.levene(group1, group2)
                equal_var = levene_p > 0.05
                t_stat, p_value = stats.ttest_ind(group1, group2, equal_var=equal_var)
                test_name = '独立样本t检验' + (' (Welch校正)' if not equal_var else '')
                # Cohen's d
                mean1, mean2 = group1.mean(), group2.mean()
                std1, std2 = group1.std(), group2.std()
                pooled_std = np.sqrt(((len(group1)-1)*std1**2 + (len(group2)-1)*std2**2) / (len(group1)+len(group2)-2))
                effect_size = (mean1 - mean2) / pooled_std

            print(f"\n{test_name} 结果：")
            print(f"统计量 = {t_stat if 't' in test_name else u_stat:.4f}, p = {p_value:.4f}")
            print(f"效应量 = {effect_size:.4f}")
        else:
            print("样本量不足，跳过统计检验。")

        # 箱线图（即使样本量不足也绘制，但可能显示简单）
        plt.figure(figsize=(6,4))
        sns.boxplot(data=df_clean, x=group_col, y=metric_col)
        plt.title(f'{metric_col} 分组箱线图')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'boxplot.png'), dpi=300)
        plt.show()

    elif len(groups) >= 3:
        data_groups = [df_clean[df_clean[group_col] == g][metric_col] for g in groups]

        print("\n各组的描述统计：")
        print(df_clean.groupby(group_col)[metric_col].describe())

        if perform_test:
            # 方差齐性检验
            levene_stat, levene_p = stats.levene(*data_groups)
            print(f"\n方差齐性检验 (Levene)：统计量 = {levene_stat:.4f}, p = {levene_p:.4f}")

            # 单因素方差分析
            f_stat, p_value = stats.f_oneway(*data_groups)
            print(f"\n单因素方差分析结果：F = {f_stat:.4f}, p = {p_value:.4f}")

            if p_value < 0.05:
                tukey = pairwise_tukeyhsd(df_clean[metric_col], df_clean[group_col], alpha=0.05)
                print("\n事后检验 (Tukey HSD)：")
                print(tukey)
                tukey_summary = pd.DataFrame(data=tukey.summary().data[1:], columns=tukey.summary().data[0])
                tukey_summary.to_excel(os.path.join(output_dir, 'tukey_results.xlsx'), index=False)
        else:
            print("样本量不足，跳过统计检验。")

        # 箱线图
        plt.figure(figsize=(8,5))
        sns.boxplot(data=df_clean, x=group_col, y=metric_col)
        plt.title(f'{metric_col} 分组箱线图')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'boxplot.png'), dpi=300)
        plt.show()

        # 小提琴图
        plt.figure(figsize=(8,5))
        sns.violinplot(data=df_clean, x=group_col, y=metric_col)
        plt.title(f'{metric_col} 分组小提琴图')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'violinplot.png'), dpi=300)
        plt.show()
    else:
        print("分组数不足，无法进行组间比较。")

    # 相关分析
    if corr_x and corr_y:
        if corr_x in df.columns and corr_y in df.columns:
            corr_data = df[[corr_x, corr_y]].dropna()
            if len(corr_data) > 0:
                r, p_corr = stats.pearsonr(corr_data[corr_x], corr_data[corr_y])
                print(f"\n相关分析：{corr_x} 与 {corr_y}")
                print(f"Pearson r = {r:.4f}, p = {p_corr:.4f}")
                plt.figure(figsize=(5,4))
                sns.scatterplot(data=corr_data, x=corr_x, y=corr_y)
                plt.title(f'{corr_x} vs {corr_y} (r={r:.2f})')
                plt.tight_layout()
                plt.savefig(os.path.join(output_dir, 'scatter.png'), dpi=300)
                plt.show()
            else:
                print("相关分析：数据缺失，无法计算。")
        else:
            print("相关分析：指定的列不存在。")

    # 保存描述统计
    desc_stats = df_clean.groupby(group_col)[metric_col].describe()
    desc_stats.to_excel(os.path.join(output_dir, 'descriptive_stats.xlsx'))

    # 恢复标准输出并关闭日志文件
    sys.stdout = original_stdout
    log_file.close()
    print(f"\n所有结果已保存至目录：{output_dir}")

if __name__ == '__main__':
    main()