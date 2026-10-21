# PhysicE

基于 Python 和 Pygame 的物理运动可视化实验，保留从自由落体到速度、惯性控制的不同版本。

## 开始使用

先准备 Python 3 环境，再执行：

```bash
git clone https://github.com/OGAS-45/PhysicE.git
cd PhysicE
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Windows 可使用 `python -m venv .venv`，在 PowerShell 中通过 `.venv\Scripts\Activate.ps1` 激活环境。

## 选择实验

| 文件 | 版本主题 |
|---|---|
| `1-Free_Fall_Motion.py` | 自由落体 |
| `2-Any_Motion.py` | 运动实验 |
| `3-Any_Motion_with_+V copy.py` | 速度控制版本 |
| `4-Any_Motion_with_inertia_inx.py` | 惯性版本 |

例如：

```bash
python "1-Free_Fall_Motion.py"
python "3-Any_Motion_with_+V copy.py"
```

一次运行一个实验。含空格的文件名需要引号；不同版本的具体操作以脚本实现为准。

## 维护状态

- 本次修正了 README 的代码块、克隆地址和脚本文件名，未修改实验代码或重新验证图形窗口。
- 旧版本脚本作为实验过程保留，不自动删除或覆盖。
- 根目录中的 `.gitingnore` 名称需要另行修正；本次没有将它重命名，也不把它视为有效的 `.gitignore`。
- 历史说明标注 MIT，但当前根目录未见 LICENSE 文件，需维护者确认后补齐，不在文档整理时擅自新增授权。
