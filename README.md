# Biomechanics-ToolBox
Python tools for C3D data processing in biomechanics
# Biomechanics Toolbox / 生物力学工具箱

[中文](#chinese-version) | [English](#english-version)

---

## Chinese Version

### 简介
一套用于运动生物力学 C3D 数据处理的 Python 工具。支持步态、单腿跳、双腿跳、原地纵跳、侧切五种动作分析，具备批量处理、特征提取、统计分析和 OpenSim 文件导出功能。

### 功能
- 读取 C3D 文件，自动识别力通道
- 支持五种动作类型：步态、单腿跳、双腿跳、原地纵跳、侧切
- 批量处理文件夹内所有 C3D 文件
- 生成力‑时间曲线和归一化曲线
- 导出 OpenSim 格式文件（`.trc`、`.mot`）
- 提取特征（峰值力、腾空时间、冲量等）
- 交互式统计分析（t 检验、方差分析、相关分析）
- 按文件配置通道（解决数据不一致问题）

### 安装
```bash
# 克隆仓库
git clone https://github.com/CHN-ShowMaker/Biomechanics-ToolBox.git
cd Biomechanics-ToolBox

# 创建 conda 环境（推荐）
conda create -n bio python=3.9
conda activate bio
pip install -r requirements.txt
快速开始
将 C3D 文件放入一个文件夹。

（可选）配置通道：

bash
python configure.py <文件夹路径>
运行批量处理：

bash
python batch_process_by_type.py
结果保存在时间戳文件夹中（如 output_20250314_...）。

文档
详细使用说明请参考 docs/ 文件夹。

许可证
本项目采用 MIT 许可证 – 详见 LICENSE 文件。

引用
如果您在研究中使用了本工具箱，请引用：

text

English Version
Introduction
A Python toolbox for automated processing of C3D files in biomechanics. It supports gait, single-leg jump, double-leg jump, countermovement jump, and cutting movement analysis, with batch processing, feature extraction, statistical analysis, and OpenSim file export.

Features
Read C3D files, automatically identify force channels

Support five movement types: gait, single-leg jump, double-leg jump, countermovement jump, cutting

Batch process all C3D files in a folder

Generate force‑time curves and normalized curves

Export OpenSim files (.trc, .mot)

Extract features (peak force, flight time, impulse, etc.)

Interactive statistical analysis (t‑test, ANOVA, correlation)

Per‑file channel configuration (solves data inconsistency issues)

Installation
bash
# Clone the repository
git clone https://github.com/CHN-ShowMaker/Biomechanics-ToolBox.git
cd Biomechanics-ToolBox

# Create conda environment (recommended)
conda create -n bio python=3.9
conda activate bio
pip install -r requirements.txt
Quick Start
Put your C3D files in one folder.

(Optional) Configure channels:

bash
python configure.py <folder_path>
Run batch processing:

bash
python batch_process_by_type.py
Results are saved in a timestamped folder (e.g., output_20250314_...).

Documentation
For detailed usage, see docs/.

License
This project is licensed under the MIT License - see the LICENSE file for details.

Citation
If you use this toolbox in your research, please cite:

text
