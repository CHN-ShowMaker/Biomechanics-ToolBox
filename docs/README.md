# Biomechanics Toolbox 详细使用说明 / Detailed Documentation

本文件夹包含工具箱的详细文档。以下是各个主要脚本的功能简介及基本用法。
This folder contains detailed documentation of the toolbox. Below is a brief introduction and basic usage of each main script.

## 核心工具模块 / Core Utility Modules

- **`c3d_utils.py`**  
  C3D 文件读写、力通道识别、校准矩阵应用、多分量力数据获取。被其他所有分析脚本依赖。  
  C3D file I/O, force channel identification, calibration matrix application, and multi‑component force data acquisition. Depended on by all analysis scripts.

- **`plot_utils.py`**  
  统一绘图函数，设置中文字体，绘制力‑时间曲线并标记事件。  
  Unified plotting functions, set Chinese fonts, plot force‑time curves with event markers.

- **`excel_utils.py`**  
  将分析结果追加到 Excel 累积文件。  
  Append analysis results to cumulative Excel files.

- **`config.py`**  
  全局配置文件，可调整滤波频率、阈值比例、OpenSim 导出开关等。  
  Global configuration file – adjust filter cutoff, threshold ratios, OpenSim export switch, etc.

## 通道配置工具 / Channel Configuration Tools

- **`configure.py`**  
  交互式手动配置通道，生成 `project_config.json`（适用于所有文件通道一致的情况）。  
  Interactive manual channel configuration, generates `project_config.json` (when channel assignments are consistent across files).

- **`auto_configure.py`**  
  自动为每个文件推荐垂直力通道，生成 `file_channels.json`（适用于文件间通道不一致的情况）。  
  Automatically recommend vertical force channels per file, generates `file_channels.json` (when channel assignments vary between files).

- **`suggest_channel.py`**  
  分析第一个 C3D 文件，显示前 N 个最大值通道并生成波形图，辅助人工选择力通道。  
  Analyze the first C3D file, display the top N channels by maximum value, and generate waveform plots to assist manual channel selection.

## 特征提取与动作分析 / Feature Extraction & Movement Analysis

- **`action_features.py`**  
  提取力信号特征（最小值、最大值、峰数量、最长腾空时间、腾空次数），生成归一化曲线图，辅助判断动作类型。  
  Extract force signal features (minimum, maximum, number of peaks, max flight duration, flight count), generate normalized curves to aid movement type identification.

- **`gait_analysis_finals.py`**  
  步态分析：检测触地/离地事件，计算平均支撑时间、峰值力，生成力曲线图，导出 OpenSim 文件。  
  Gait analysis: detect foot strike/toe‑off events, compute mean stance time and peak force, generate force curves, export OpenSim files.

- **`run_single_leg_jump_finals.py`**  
  跑动单腿跳分析：检测腾空、起跳蹬伸峰、落地冲击，计算腾空时间，生成曲线图，导出 OpenSim 文件。  
  Running single‑leg jump analysis: detect flight, takeoff push‑off peak, landing impact, compute flight time, generate plots, export OpenSim files.

- **`run_double_leg_jump_finals.py`**  
  跑动双腿跳分析：检测腾空、起跳合力峰、落地冲击，计算腾空时间，生成曲线图，导出 OpenSim 文件。  
  Running double‑leg jump analysis: detect flight, takeoff resultant peak, landing impact, compute flight time, generate plots, export OpenSim files.

- **`jump_analysis_finals.py`**  
  原地纵跳分析：检测腾空、起跳峰值、落地冲击，计算腾空时间，生成曲线图，导出 OpenSim 文件。  
  Countermovement jump analysis: detect flight, takeoff peak, landing impact, compute flight time, generate plots, export OpenSim files.

- **`cutting_analysis_finals.py`**  
  侧切动作分析：检测冲击峰，计算峰值力、冲量，生成曲线图，导出 OpenSim 文件。  
  Cutting movement analysis: detect impact peak, compute peak force and impulse, generate plots, export OpenSim files.

## 批量处理与调度 / Batch Processing & Scheduling

- **`batch_process_by_type.py`**  
  批量处理主脚本。输入文件夹路径和动作类型，自动调用对应的分析脚本处理所有 C3D 文件，并整理输出。  
  Main batch processing script. Input folder path and movement type, automatically call the corresponding analysis script for all C3D files, and organize outputs.

## 统计分析 / Statistical Analysis

- **`stat_analysis_interactive.py`**  
  交互式统计分析。读取累积 Excel，进行 t 检验、方差分析、相关分析，生成统计图表和报告。  
  Interactive statistical analysis. Read cumulative Excel, perform t‑tests, ANOVA, correlation, generate statistical plots and reports.

## 图像拟合 / Curve Averaging

- **`average_curve_interactive.py`**  
  读取归一化曲线文件（`.npy`），计算平均曲线和标准差带，绘制典型曲线图。  
  Read normalized curve files (`.npy`), compute mean curve and standard deviation band, generate typical curve plots.

## 诊断工具 / Diagnostic Tools

- **`check_forceplate_interactive.py`**  
  检查 C3D 文件的力板类型、校准矩阵和原始值，帮助定位数据问题。  
  Check force plate type, calibration matrix, and raw values of C3D files to help diagnose data issues.

- **`test_calibration.py`**  
  简单测试脚本，输出指定文件的校准矩阵和力数据。  
  Simple test script to output calibration matrix and force data for a given file.

## OpenSim 导出 / OpenSim Export

- **`c3d_to_opensim_finals.py`**  
  将 C3D 文件转换为 OpenSim 所需的 `.trc`（标记点轨迹）和 `.mot`（地面反作用力）文件。  
  Convert C3D files to OpenSim format (`.trc` for marker trajectories, `.mot` for ground reaction forces).

## 常见问题 / Frequently Asked Questions

### 1. 如何选择正确的力通道？ / How to select the correct force channel?
- 先运行 `suggest_channel.py` 查看候选通道波形，确定垂直力通道编号。  
  First run `suggest_channel.py` to view candidate channel waveforms and determine the vertical force channel index.
- 如果所有文件通道一致，用 `configure.py` 手动配置；如果不一致，用 `auto_configure.py` 自动生成按文件配置。  
  If channel assignments are consistent across files, use `configure.py` for manual configuration; if they vary, use `auto_configure.py` to generate per‑file configuration.

### 2. 批量处理时如何指定动作类型？ / How to specify movement type during batch processing?
- 运行 `batch_process_by_type.py`，按提示输入动作类型代码：  
  Run `batch_process_by_type.py` and enter the movement type code when prompted:
  - `gait`：步态 / gait
  - `single_jump`：跑动单腿跳 / running single‑leg jump
  - `double_jump`：跑动双腿跳 / running double‑leg jump
  - `cmj`：原地纵跳 / countermovement jump
  - `cut`：侧切 / cutting

### 3. 结果文件保存在哪里？ / Where are the result files saved?
- 每次运行 `batch_process_by_type.py` 会在数据文件夹下生成一个时间戳文件夹（如 `output_20250314_...`），其中包含：  
  Each run of `batch_process_by_type.py` creates a timestamped folder (e.g., `output_20250314_...`) in the data folder, containing:
  - `images/`：力曲线图 / force curve plots
  - `opensim_files/`：按文件分类的 `.trc`/`.mot` 文件 / `.trc`/`.mot` files organized by file
  - `动作类型_汇总.xlsx`：本次运行的指标汇总表 / summary Excel for this run
- 同时，指标会追加到数据文件夹下的累积 Excel（如 `步态分析累计版.xlsx`）。  
  Metrics are also appended to cumulative Excel files in the data folder (e.g., `步态分析累计版.xlsx`).

---

本文档会持续更新。如有疑问，欢迎在 GitHub Issues 中提出。  
This document is continuously updated. If you have any questions, feel free to open an issue on GitHub.
