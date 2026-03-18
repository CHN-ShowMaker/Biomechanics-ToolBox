##  `README.md`（中英双语完整版）

```
# Biomechanics Toolbox / 生物力学工具箱

[中文](#chinese) | [English](#english)

---
```
## Chinese

### 简介
一套用于运动生物力学 C3D 数据处理的 Python 工具。支持步态、单腿跳、双腿跳、原地纵跳、侧切五种动作分析，具备批量处理、特征提取、统计分析和 OpenSim 文件导出功能。工具箱采用模块化设计，提供手动和自动两种配置方式，可适应不同格式的 C3D 文件。

### 主要功能
- **读取 C3D 文件**，自动识别力通道（支持按文件独立配置）
- **支持五种动作类型**：步态（gait）、单腿跳（single‑leg jump）、双腿跳（double‑leg jump）、原地纵跳（countermovement jump, CMJ）、侧切（cutting）
- **批量处理**：一键处理文件夹内所有 C3D 文件，生成力曲线图、OpenSim 文件、汇总 Excel
- **特征提取**：峰值力、腾空时间、支撑时间、冲量等
- **交互式统计分析**：t 检验、方差分析、相关分析，自动生成统计图表
- **图像拟合**：对多次试验的归一化曲线求平均，绘制带标准差带的典型曲线
- **OpenSim 导出**：自动生成 `.trc`（标记点轨迹）和 `.mot`（地面反作用力）文件
- **高级配置**：
  - **手动配置**（`manual_config.py`）：运行后交互式输入文件夹路径，为每个文件自动检测所有力板，然后依次为每块力板选择垂直力通道，并指定侧别（1=左脚，2=右脚），自动匹配同板的其他分量（Fx, Fy, Mx, My, Mz, COPx, COPy）
  - **自动配置**（`auto_config.py`）：运行后交互式输入文件夹路径，自动检测所有力板，为每块力板选择最大值最大的通道作为垂直力，并匹配其他分量，一键生成配置文件
- **多语言输出**：所有脚本输出均为中英双语，便于国际用户
- **多力板支持**：自动检测任意数量的力板，并为每块力板独立配置通道（Fx, Fy, Fz, Mx, My, Mz, COPx, COPy）
- **侧别配置**：在手动配置时可为每块力板指定侧别（1=左脚，2=右脚），步态分析自动按侧别输出左右脚分离的结果
- **长格式累积输出**：每个力板单独一行写入累积 Excel，包含文件名、动作类型、侧别、板号及各动作指标，便于直接导入统计软件进行分组比较
- **图片和曲线自动分类**：力曲线图和归一化曲线按侧别（left/right/unknown）保存在 `images/` 和 `curves/` 子文件夹中

### 安装
```bash
# 克隆仓库
git clone https://github.com/CHN-ShowMaker/Biomechanics-ToolBox.git
cd Biomechanics-ToolBox

# 创建 conda 环境（推荐）
conda create -n bio python=3.9
conda activate bio
pip install -r requirements.txt
```
## 示例数据

本仓库的 `Sample03/` 文件夹中提供了示例C3D文件，你可以直接用它们来测试工具箱的流程。

对于多力板测试，我们建议使用包含两块力板的步态数据（可自行生成或从公开数据集中获取）。

此外，仓库根目录下还提供了一个示例累积 Excel 文件 gait_cumulative_example.xlsx，你可以直接用 stat_analysis.py 进行统计分析，体验工具箱的统计功能。

### 快速开始
1. **准备数据**：将 C3D 文件放入一个文件夹，例如 `data/`。
2. **配置通道**（根据数据规范程度选择）：
   - 手动配置（逐个文件确认）：
     ```bash
     python manual_config.py
      ```
     然后按提示输入文件夹路径，并依次为每个检测到的力板选择垂直力通道编号，同时指定侧别（1=左脚，2=右脚，直接回车为 unknown）。
   - 自动配置（一键完成）：
     ```bash
     python auto_config.py
     ```
     然后按提示输入文件夹路径，程序自动完成所有配置。
3. **批量处理**：
   ```bash
   python batch_process_by_type.py
   ```
   输入文件夹路径和动作类型（gait/single_jump/double_jump/cmj/cut），结果保存在时间戳文件夹（如 `output_20250315_...`）中。
   > 对于步态，图片和曲线将按侧别分类保存。
4. **（可选）特征提取**：
   ```bash
   python action_features.py --plot data/
   ```
5. **（可选）统计分析**：
   ```bash
   python stat_analysis.py
   ```
6. **（可选）图像拟合**：
   ```bash
   python average_curve_interactive.py
   ```

### 文档
详细使用说明请参考 [docs/](docs/) 文件夹。

### 许可证
本项目采用 MIT 许可证 – 详见 [LICENSE](LICENSE) 文件。

### 引用
如果您在研究中使用了本工具箱，请引用：
```
[引用信息 – 发表后添加]
```

---

## English

### Introduction
A Python toolbox for automated processing of C3D files in biomechanics. It supports analysis of five movement types (gait, single‑leg jump, double‑leg jump, countermovement jump, cutting), with batch processing, feature extraction, statistical analysis, and OpenSim file export. The toolbox is modular and offers both manual and automatic configuration modes to handle various C3D data formats.

### Features
- **Read C3D files**, automatically identify force channels (per‑file configuration supported)
- **Five movement types**: gait, single‑leg jump, double‑leg jump, countermovement jump (CMJ), cutting
- **Batch processing**: process all C3D files in a folder with one command, generate force‑time plots, OpenSim files, summary Excel
- **Feature extraction**: peak force, flight time, stance time, impulse, etc.
- **Interactive statistical analysis**: t‑test, ANOVA, correlation, generate publication‑ready plots
- **Curve averaging**: average normalized curves from multiple trials with standard deviation bands
- **OpenSim export**: automatically create `.trc` (marker trajectories) and `.mot` (ground reaction forces) files
- **Advanced configuration**:
  - **Manual configuration** (`manual_config.py`): run the script, enter folder path interactively; the script automatically detects all force plates in each file and lets you select the vertical force channel and side (1=left, 2=right) for each plate; other components (Fx, Fy, Mx, My, Mz, COPx, COPy) are automatically matched based on plate number.
  - **Automatic configuration** (`auto_config.py`): run the script, enter folder path interactively; the program automatically detects all force plates, selects the channel with the highest maximum as the vertical force for each plate, and matches all other components.
- **Bilingual output**: all script messages are in both Chinese and English for international accessibility
- **Multi‑force plate support**: automatically detect any number of force plates and configure each plate independently (Fx, Fy, Fz, Mx, My, Mz, COPx, COPy)
- **Side configuration**: during manual configuration, assign a side (1=left, 2=right) to each plate; gait analysis automatically outputs left/right separated results
- **Long‑format cumulative output**: each force plate is written as a separate row in the cumulative Excel, including filename, movement type, side, plate number, and all metrics – ready for direct import into statistical software for group comparisons
- **Automatic image and curve sorting**: force plots and normalized curves are saved in `images/` and `curves/` subfolders categorized by side (left/right/unknown)

### Installation
```bash
# Clone the repository
git clone https://github.com/CHN-ShowMaker/Biomechanics-ToolBox.git
cd Biomechanics-ToolBox

# Create conda environment (recommended)
conda create -n bio python=3.9
conda activate bio
pip install -r requirements.txt
```

## Example Data

The `Sample03/` folder in this repository contains three sample C3D files that you can use to test the toolbox workflow.

For multi‑force plate tests, we recommend using gait data containing two force plates (can be generated or obtained from public datasets).

Additionally, an example cumulative Excel file gait_cumulative_example.xlsx is provided in the root directory. You can directly use it with stat_analysis.py to explore the statistical analysis features.

### Quick Start
1. **Prepare data**: place your C3D files in a folder, e.g., `data/`.
2. **Configure channels** (choose according to data regularity):
   - Manual configuration (interactive per file):
     ```bash
     python manual_config.py
     ```
     Then follow the prompts to enter the folder path. For each detected force plate, select the vertical force channel index and specify the side (1=left, 2=right, Enter for unknown).
   - Automatic configuration (one‑click):
     ```bash
     python auto_config.py
     ```
     Then follow the prompt to enter folder path; the program will handle everything automatically.
3. **Batch processing**:
   ```bash
   python batch_process_by_type.py
   ```
   Enter folder path and movement type (gait/single_jump/double_jump/cmj/cut). Results are saved in a timestamped folder (e.g., `output_20250315_...`).
   > For gait, images and curves are sorted by side.
4. **(Optional) Feature extraction**:
   ```bash
   python action_features.py --plot data/
   ```
5. **(Optional) Statistical analysis**:
   ```bash
   python stat_analysis.py
   ```
6. **(Optional) Curve averaging**:
   ```bash
   python average_curve_interactive.py
   ```

### Documentation
For detailed usage, see the [docs/](docs/) folder.

### License
This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

### Citation
If you use this toolbox in your research, please cite:
```
[Citation – to be added after publication]
```
