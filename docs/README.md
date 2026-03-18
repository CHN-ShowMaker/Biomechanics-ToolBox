## `docs/README.md`（中英双语完整版）

```
# Biomechanics Toolbox 详细使用说明 / Detailed Documentation

本文件夹包含工具箱的详细文档。以下是各个主要脚本的功能简介及基本用法。
This folder contains detailed documentation of the toolbox. Below is a brief introduction and basic usage of each main script.
```
---

## 核心工具模块 / Core Utility Modules

- **`c3d_utils.py`**  
  C3D 文件读写、力通道识别、校准矩阵应用、多分量数据获取。支持多力板自动检测和配置，为每块力板独立应用校准矩阵。被其他所有分析脚本依赖。  
  C3D file I/O, force channel identification, calibration matrix application, and multi‑component force data acquisition. Supports automatic detection and configuration of multiple force plates, applying calibration matrices independently to each plate. Depended on by all analysis scripts.
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
  手动为每个文件配置所有检测到的力板。运行后首先提示输入文件夹路径，然后对每个文件自动检测所有力板，并依次为每块力板显示该板内的候选通道（按最大值排序）。用户选择垂直力通道编号后，可指定侧别（1=左脚，2=右脚），程序自动匹配同板的其他分量（Fx, Fy, Mx, My, Mz, COPx, COPy）。最终生成包含多力板配置的 `project_config.json`。  
  Manually configure all detected force plates per file. After prompting for the folder path, the script automatically detects all force plates in each file and displays the candidate channels within each plate (sorted by maximum value). After the user selects the vertical force channel index and specifies the side (1=left, 2=right), the program automatically matches other components (Fx, Fy, Mx, My, Mz, COPx, COPy) for that plate. Finally, a `project_config.json` with multi‑plate configuration is generated.

- **`auto_config.py`**  
  全自动配置多力板。运行时首先提示输入文件夹路径，然后自动排除力矩通道（标签含 MX/MY/MZ），根据标签中的数字后缀将所有通道按板号分组。对每组（即每块力板）选择最大值最大的通道作为垂直力，并自动匹配该板的其他分量（Fx, Fy, Mx, My, Mz, COPx, COPy），直接生成包含多力板配置的 `project_config.json`。无需用户干预。  
  Fully automatic multi‑plate configuration. After prompting for the folder path, the script automatically excludes moment channels (labels containing MX/MY/MZ) and groups remaining channels by plate number (based on trailing digits). For each plate, it selects the channel with the highest maximum as the vertical force and automatically matches other components (Fx, Fy, Mx, My, Mz, COPx, COPy). A `project_config.json` with multi‑plate configuration is generated without any user intervention.

---

## 特征提取与动作分析 / Feature Extraction & Movement Analysis

- **`action_features.py`**  
  提取力信号特征（最小值、最大值、峰数量、最长腾空时间、腾空次数），生成归一化曲线图，辅助判断动作类型。  
  Extract force signal features (minimum, maximum, number of peaks, max flight duration, flight count), generate normalized curves to aid movement type identification.

- **`gait_analysis_finals.py`**  
  步态分析：支持多块力板，根据配置中的侧别自动分配左右脚。对每块力板独立检测触地/离地事件，计算平均支撑时间、峰值力，生成力曲线图并按侧别分类保存至 `images/left|right|unknown/`，归一化曲线保存至 `curves/left|right|unknown/`。累积 Excel 中每块力板单独一行，便于左右脚比较。自动导出 OpenSim 文件。  
  Gait analysis: supports multiple force plates, automatically assigns left/right based on side configuration. For each plate, independently detects foot strike/toe‑off events, computes mean stance time and peak force, generates force plots saved in `images/left|right|unknown/`, and normalized curves saved in `curves/left|right|unknown/`. Each plate is written as a separate row in the cumulative Excel, facilitating left/right comparisons. Automatically exports OpenSim files.

- **`run_single_leg_jump_finals.py`**  
  跑动单腿跳分析：检测腾空、起跳蹬伸峰、落地冲击，计算腾空时间，生成曲线图，导出 OpenSim 文件。  
  Running single‑leg jump analysis: detect flight, takeoff push‑off peak, landing impact, compute flight time, generate plots, export OpenSim files.
  累积 Excel 中每块力板单独一行，包含侧别和板号信息，图片和曲线按侧别分类保存。
Each plate is written as a separate row in the cumulative Excel, including side and plate number; images and curves are saved in side‑specific subfolders.

- **`run_double_leg_jump_finals.py`**  
  跑动双腿跳分析：检测腾空、起跳合力峰、落地冲击，计算腾空时间，生成曲线图，导出 OpenSim 文件。  
  Running double‑leg jump analysis: detect flight, takeoff resultant peak, landing impact, compute flight time, generate plots, export OpenSim files.
  累积 Excel 中每块力板单独一行，包含侧别和板号信息，图片和曲线按侧别分类保存。
Each plate is written as a separate row in the cumulative Excel, including side and plate number; images and curves are saved in side‑specific subfolders.

- **`jump_analysis_finals.py`**  
  原地纵跳分析：检测腾空、起跳峰值、落地冲击，计算腾空时间，生成曲线图，导出 OpenSim 文件。  
  Countermovement jump analysis: detect flight, takeoff peak, landing impact, compute flight time, generate plots, export OpenSim files.
  累积 Excel 中每块力板单独一行，包含侧别和板号信息，图片和曲线按侧别分类保存。
Each plate is written as a separate row in the cumulative Excel, including side and plate number; images and curves are saved in side‑specific subfolders.

- **`cutting_analysis_finals.py`**  
  侧切动作分析：检测冲击峰，计算峰值力、冲量，生成曲线图，导出 OpenSim 文件。  
  Cutting movement analysis: detect impact peak, compute peak force and impulse, generate plots, export OpenSim files.
  累积 Excel 中每块力板单独一行，包含侧别和板号信息，图片和曲线按侧别分类保存。
Each plate is written as a separate row in the cumulative Excel, including side and plate number; images and curves are saved in side‑specific subfolders.
  
---

## 使用流程 / Typical Workflow

1. **准备数据**：将所有 C3D 文件放入一个文件夹（如 `data/`）。  
   Place your C3D files in a folder (e.g., `data/`).

2. **通道配置**：根据数据规范程度选择手动或自动配置。工具箱会自动检测多块力板。  
   - 手动：`python manual_config.py` → 输入文件夹路径 → 按提示为每个文件依次为每块检测到的力板选择垂直力通道，并可指定侧别（1=左脚，2=右脚）。  
   - 自动：`python auto_config.py` → 输入文件夹路径 → 程序自动检测所有力板并完成配置，生成 `project_config.json`。  
   Configure channels according to data regularity. The toolbox automatically detects multiple force plates.
     - Manual: `python manual_config.py` → enter folder path → for each detected force plate, select the vertical force channel and optionally specify the side (1=left, 2=right).
     - Automatic: `python auto_config.py` → enter folder path → the program automatically detects all plates and creates `project_config.json`.

3. **（可选）特征提取**：运行 `action_features.py --plot data/` 查看力曲线和特征值，辅助判断动作类型。  
   (Optional) Run `action_features.py --plot data/` to inspect force curves and features, helping you determine the movement type.

4. **批量处理**：运行 `batch_process_by_type.py`，输入文件夹和动作类型，等待处理完成。对于步态，图片和曲线将按侧别分类保存至 `images/left|right|unknown/` 和 `curves/left|right|unknown/`；累积 Excel 中每块力板单独一行，包含侧别和板号信息。  
   Run `batch_process_by_type.py`, enter folder path and movement type, and wait for completion. For gait, images and curves are saved in `images/left|right|unknown/` and `curves/left|right|unknown/` according to side. Each plate is written as a separate row in the cumulative Excel, including side and plate number.

5. **查看结果**：在时间戳文件夹中找到图片、OpenSim 文件、本次汇总 Excel；累积 Excel 位于原文件夹中。  
   Locate results in the timestamped folder (images, OpenSim files, summary Excel); cumulative Excel files are in the original data folder.

6. **（可选）统计分析**：运行 `stat_analysis.py` 对累积 Excel 进行统计检验。  
   (Optional) Run `stat_analysis.py` to perform statistical tests on cumulative Excel.
   根目录中提供了示例累积 Excel 文件 gait_cumulative_example.xlsx，可直接用于测试统计分析功能。
The root directory contains an example cumulative Excel file gait_cumulative_example.xlsx that you can use to test the statistical analysis features.

8. **（可选）图像拟合**：运行 `average_curve_interactive.py` 对多次试验取平均曲线。  
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
新版配置文件支持多力板，每个文件可包含多个力板的配置，格式如下：
```json
{
    "file_channels": {
        "filename.c3d": {
            "force_plates": [
                {
                    "plate_id": 1,
                    "force_vz": "Fz1",
                    "force_vx": "Fx1",
                    ...
                },
                {
                    "plate_id": 2,
                    "force_vz": "Fz2",
                    ...
                }
            ]
        }
    }
}
```
旧版单力板格式仍可被自动识别并转换为多板格式。
The new configuration format supports multiple force plates. An example with two plates is shown above. Legacy single‑plate format is still recognized and automatically converted.
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
text
### 7. 如何处理包含多块力板的 C3D 文件？ / How to handle C3D files with multiple force plates?
工具箱会自动检测多块力板。在手动配置时，`manual_config.py` 会为每个文件列出所有检测到的力板，并允许您为每块力板单独选择通道和侧别。自动配置时，`auto_config.py` 会根据通道标签中的数字后缀自动分组并为每块力板生成配置。所有分析脚本均支持多板数据，累积 Excel 中每块力板独立成行。

The toolbox automatically detects multiple force plates. During manual configuration, `manual_config.py` lists all detected plates for each file and lets you configure each plate separately (channel selection and side). During automatic configuration, `auto_config.py` groups channels by trailing digits and generates per‑plate configurations. All analysis scripts support multi‑plate data, with each plate written as a separate row in the cumulative Excel.

本文档会持续更新。如有疑问，欢迎在 GitHub Issues 中提出。
This document is continuously updated. If you have any questions, feel free to open an issue on GitHub.
