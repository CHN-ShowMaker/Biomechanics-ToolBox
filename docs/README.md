## `docs/README.md`（中英双语完整版）

```
# Biomechanics Toolbox 详细使用说明 / Detailed Documentation

本文件夹包含工具箱的详细文档。以下是各个主要脚本的功能简介及基本用法。
This folder contains detailed documentation of the toolbox. Below is a brief introduction and basic usage of each main script.
```
---

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

---

## 通道配置工具 / Channel Configuration Tools

- **`manual_config.py`**  
  手动为每个文件选择垂直力通道，并自动匹配同板的其他分量（Fx, Fy, Mx, My, Mz, COPx, COPy）。运行时首先提示输入文件夹路径，然后逐个文件显示前 N 个候选通道（按最大值排序），用户输入编号后，程序自动根据板号匹配其他分量。  
  Manually select the vertical force channel per file, and automatically match other components (Fx, Fy, Mx, My, Mz, COPx, COPy) based on plate number. The script first prompts for the folder path, then for each file it shows the top candidate channels (sorted by maximum value); after user input, it automatically matches other components.

- **`auto_config.py`**  
  全自动配置。运行时首先提示输入文件夹路径，然后自动排除力矩通道（标签含 MX/MY/MZ），选择剩余通道中最大值最大的作为垂直力，并根据板号匹配其他分量，直接生成配置文件。无需用户干预。  
  Fully automatic configuration. The script first prompts for the folder path, then automatically excludes moment channels (labels containing MX/MY/MZ), selects the channel with the highest maximum among the remaining as vertical force, and matches other components based on plate number. No further user interaction required.

---

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
  
---

## 使用流程 / Typical Workflow

1. **准备数据**：将所有 C3D 文件放入一个文件夹（如 `data/`）。  
   Place your C3D files in a folder (e.g., `data/`).

2. **通道配置**：根据数据规范程度选择手动或自动配置。  
   - 手动：`python manual_config.py` → 输入文件夹路径 → 按提示为每个文件选择垂直力通道。  
   - 自动：`python auto_config.py` → 输入文件夹路径 → 等待自动完成。  
   Configure channels according to data regularity, either manually or automatically:
     - Manual: `python manual_config.py` → enter folder path → select vertical force channel for each file.
     - Automatic: `python auto_config.py` → enter folder path → wait for completion.

3. **（可选）特征提取**：运行 `action_features.py --plot data/` 查看力曲线和特征值，辅助判断动作类型。  
   (Optional) Run `action_features.py --plot data/` to inspect force curves and features, helping you determine the movement type.

4. **批量处理**：运行 `batch_process_by_type.py`，输入文件夹和动作类型，等待处理完成。  
   Run `batch_process_by_type.py`, enter folder path and movement type, and wait for completion.

5. **查看结果**：在时间戳文件夹中找到图片、OpenSim 文件、本次汇总 Excel；累积 Excel 位于原文件夹中。  
   Locate results in the timestamped folder (images, OpenSim files, summary Excel); cumulative Excel files are in the original data folder.

6. **（可选）统计分析**：运行 `stat_analysis.py` 对累积 Excel 进行统计检验。  
   (Optional) Run `stat_analysis.py` to perform statistical tests on cumulative Excel.

7. **（可选）图像拟合**：运行 `average_curve_interactive.py` 对多次试验取平均曲线。  
   (Optional) Run `average_curve_interactive.py` to generate mean curves from multiple trials.

---

## 常见问题 / Frequently Asked Questions

### 1. 如何选择正确的力通道？ / How to select the correct force channel?
- 先用 `auto_config.py` 尝试自动配置。如果结果合理（力值几百到几千N），则可直接使用。
- 如果自动配置不合理，或你想精细控制，用 `manual_config.py` 手动选择。程序会显示前 N 个候选通道（按最大值排序），你只需输入编号，其他分量会自动匹配。
- 还可以先运行 `action_features.py --plot` 查看波形，辅助判断。

- First try automatic configuration with `auto_config.py`. If the results are reasonable (force values in the hundreds to thousands of N), you can use it directly.
- If automatic configuration is unsatisfactory or you need precise control, use `manual_config.py` to manually select the vertical force channel. The program will display the top N candidate channels (sorted by maximum value); after you enter the index, other components are automatically matched.
- You can also run `action_features.py --plot` first to inspect the waveforms, which aids in decision making.

### 2. 自动配置时如何排除力矩通道？ / How are moment channels excluded during automatic configuration?
`auto_config.py` 会自动识别标签中含 `MX`, `MY`, `MZ` 的通道并将其排除，避免将大数值的力矩误认为力。

`auto_config.py` automatically identifies channels with labels containing `MX`, `MY`, or `MZ` and excludes them, preventing large moment values from being mistaken as forces.

### 3. 配置文件 `project_config.json` 的格式是什么？ / What is the format of the configuration file `project_config.json`?
```json
{
    "file_channels": {
        "filename1.c3d": {
            "force_vz": "Fz2",
            "force_vx": "Fx2",
            "force_vy": "Fy2",
            "torque_x": "Mx2",
            "torque_y": "My2",
            "torque_z": "Mz2",
            "cop_x": "COP2.X",
            "cop_y": "COP2.Y"
        },
        "filename2.c3d": { ... }
    }
}
```
未找到的分量会保留为 null。
Components that are not found remain as null.

### 4. 为什么我的力值只有几十N，或达到几万N？ / Why are my force values only tens of N, or as high as tens of thousands of N?
几十N：通常是因为选择了错误的通道（例如加速度计），或数据本身需要校准矩阵。请用 `check_forceplate.py` 检查力板类型和校准矩阵。

几万N：几乎肯定是误选了力矩通道（Mx/My/Mz），请用 `auto_config.py` 重新配置（它会自动排除力矩通道），或手动选择正确的力通道。

Tens of N: usually caused by selecting the wrong channel (e.g., an accelerometer) or because the data itself requires a calibration matrix. Use `check_forceplate.py` to inspect the force plate type and calibration matrix.

Tens of thousands of N: almost certainly due to mistakenly selecting a moment channel (Mx/My/Mz). Reconfigure with `auto_config.py` (which automatically excludes moment channels) or manually select the correct force channel.

### 5. 如何处理文件间通道不一致？ / How to handle inconsistent channels across files?
使用 `manual_config.py` 或 `auto_config.py` 都会生成按文件配置的 `project_config.json`，每个文件可独立指定通道，完美解决通道不一致问题。
Both `manual_config.py` and `auto_config.py` generate a per‑file configuration in `project_config.json`, allowing each file to specify its own channels independently, perfectly solving the problem of channel inconsistency across files.

### 6. 如何导出 OpenSim 文件？ / How to export OpenSim files?
批量处理时会自动调用 `c3d_to_opensim_finals.py` 生成 `.trc` 和 `.mot` 文件，保存在时间戳文件夹的 opensim_files/ 子目录中。你可以在 OpenSim 中直接使用这些文件。
During batch processing, `c3d_to_opensim_finals.py` is automatically called to generate `.trc` and `.mot` files, which are saved in the opensim_files/ subfolder of the timestamped output folder. These files can be directly used in OpenSim.

本文档会持续更新。如有疑问，欢迎在 GitHub Issues 中提出。
This document is continuously updated. If you have any questions, feel free to open an issue on GitHub.
