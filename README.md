# blockMesh-gui

OpenFOAM blockMeshDict GUI Generator / OpenFOAM blockMeshDict 可视化生成工具

**Version / 版本**: v1.0.0

---

## Features / 功能

### 🎨 Visual Input / 可视化输入
Interactive GUI for mesh configuration with real-time preview.  
交互式网格配置界面，支持实时预览。

- Set domain bounds and cell counts visually  
  可视化设置计算域范围和网格数量
- Configure boundary conditions for all 6 faces  
  配置 6 个面的边界条件
- Multi-segment support in X/Y/Z directions  
  支持 X/Y/Z 三方向多段网格

### 📋 Template System / 模板系统
Built-in templates for common CFD cases.  
内置常用 CFD 案例模板。

- Quick load preset configurations  
  快速加载预设配置
- Export/import custom templates (YAML)  
  导出/导入自定义模板（YAML 格式）
- Save time on repetitive setups  
  节省重复配置时间

### 👁️ Simple Visualization / 简单可视化
3D mesh preview with boundary face coloring.  
3D 网格预览，边界面上色显示。

- Rotate and zoom to inspect mesh structure  
  旋转缩放查看网格结构
- Color-coded boundary faces  
  边界条件颜色区分
- Segment markers with cell count labels  
  分段标记和网格数量标注

---

## Installation / 安装

```bash
# Clone repository / 克隆仓库
git clone https://github.com/YOUR_USERNAME/blockMesh-gui.git
cd blockMesh-gui

# Install dependencies / 安装依赖
pip install -r requirements.txt
```

**Requirements / 依赖**:
- Python 3.8+
- PyQt6
- PyYAML
- matplotlib

---

## Usage / 使用方法

```bash
# Run from project root / 从项目根目录运行
python run.py
```

### Quick Start / 快速开始

1. **Load a template / 加载模板**  
   Select from dropdown → Click "Load"  
   从下拉菜单选择 → 点击 "Load"

2. **Configure mesh / 配置网格**  
   - Set domain bounds (min/max)  
     设置计算域范围
   - Enable segments for multi-block mesh  
     启用分段创建多块网格
   - Adjust cell counts per segment  
     调整每段网格数量

3. **Preview / 预览**  
   Click "Preview" to see 3D visualization and blockMeshDict content  
   点击 "Preview" 查看 3D 可视化和文本内容

4. **Generate / 生成**  
   Click "Generate" to save blockMeshDict file  
   点击 "Generate" 保存 blockMeshDict 文件

---

## Project Structure / 项目结构

```
blockMesh-gui/
├── src/                    # Source code / 源代码
│   ├── core/               # Data models & generator / 数据模型和生成器
│   ├── gui/                # PyQt6 interface / PyQt6 界面
│   └── utils/              # Config I/O, visualization / 配置 IO、可视化
├── templates/              # Preset templates / 预设模板
├── run.py                  # Launch script / 启动脚本
├── requirements.txt        # Python dependencies / Python 依赖
└── README.md               # This file / 本文件
```

---

## Screenshots / 截图

![blockMesh-gui Screenshot](https://raw.githubusercontent.com/balabibo/imageForGit/main/blockMesh-gui.png)

*Main interface with 3D visualization / 主界面带 3D 可视化*

---

## License / 许可证

MIT License - See [LICENSE](LICENSE) file for details.  
MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

## Contributing / 贡献

Issues and pull requests are welcome!  
欢迎提交 Issue 和 Pull Request！

---

**Made by balabibo with OpenClaw 🤖**  
**by balabibo with OpenClaw 制作**

Made with ❤️ for the OpenFOAM community  
为 OpenFOAM 社区制作
