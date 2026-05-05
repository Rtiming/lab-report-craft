# 实验报告实操指南

**从实战中沉淀的系统性经验。按操作场景组织，写作和审校时直接查阅。**

---

## 目录

- [1. 数据处理](#1-数据处理)
  - [1.1 常见数据格式读取](#11-常见数据格式读取)
  - [1.2 磁滞回线参数提取](#12-磁滞回线参数提取)
  - [1.3 定标数据处理](#13-定标数据处理)
  - [1.4 手写数据识别](#14-手写数据识别)
- [2. 数据可视化](#2-数据可视化)
  - [2.1 图表类型选择](#21-图表类型选择)
  - [2.2 配色与样式](#22-配色与样式)
  - [2.3 参数框与图例布局](#23-参数框与图例布局)
  - [2.4 数学符号规范](#24-数学符号规范)
  - [2.5 matplotlib mathtext 陷阱](#25-matplotlib-mathtext-陷阱)
  - [2.6 输出格式与验证](#26-输出格式与验证)
- [3. LaTeX 排版](#3-latex-排版)
  - [3.1 模板结构与关键配置](#31-模板结构与关键配置)
  - [3.2 数值管线](#32-数值管线)
  - [3.3 单位排版](#33-单位排版)
  - [3.4 公式排版](#34-公式排版)
  - [3.5 图片插入](#35-图片插入)
  - [3.6 表格排版](#36-表格排版)
  - [3.7 参考文献](#37-参考文献)
  - [3.8 交叉引用常见坑](#38-交叉引用常见坑)
- [4. 素材搜集与裁剪](#4-素材搜集与裁剪)
  - [4.1 原理图来源](#41-原理图来源)
  - [4.2 截图硬性规范](#42-截图硬性规范)
  - [4.3 从 PDF 提取图片](#43-从-pdf-提取图片)
  - [4.4 连通区域分析裁剪](#44-连通区域分析裁剪)
- [5. 快速命令索引](#5-快速命令索引)

---

## 1. 数据处理

### 1.1 常见数据格式读取

```python
import numpy as np
import pandas as pd

# 纯文本单列
data = np.loadtxt('data.txt')           # 默认 UTF-8/ASCII
# 编码异常时：np.loadtxt('data.txt', encoding='utf-8') 或 'gbk'

# CSV 带表头多列
df = pd.read_csv('data.csv', skiprows=3)  # 跳过仪器信息行
freq = df['Freq'].values
cap = df['Ciss'].values

# .xy 文件（纯文本两列，通常无表头）
data = np.loadtxt('Fe.xy')
H_raw, J_raw = data[:, 0], data[:, 1]

# ASCII 不规则格式（手动解析）
with open('data.txt') as f:
    data = [float(line.strip()) for line in f if line.strip()]
```

### 1.2 磁滞回线参数提取

**饱和磁矩 $J_s$**：取正负高场区平均值，再取平均
```python
mask_pos = H > 0.85 * H_max
mask_neg = H < -0.85 * H_max
Js = (abs(np.mean(J[mask_pos])) + abs(np.mean(J[mask_neg]))) / 2
```

**剩余磁矩 $J_r$**：$H \approx 0$ 时的最大 $|J|$
```python
threshold = max(H_max * 0.02, 50)   # |H| < 2% Hmax 或 50 Oe
mask = np.abs(H) < threshold
Jr = np.max(np.abs(J[mask]))
```

**矫顽力 $H_c$（关键：必须分离升支/降支）**

**严禁全数据 bin 平均**——升支/降支混叠会导致正负 $J$ 抵消，$H_c$ 严重偏低。

```python
max_idx = np.argmax(H)
min_idx = np.argmin(H)

# 降支: H 从 max 降到 min
H_desc = H[max_idx:min_idx+1]
J_desc = J[max_idx:min_idx+1]

# 升支: H 从 min 升到 end 再连到 max
H_asc = np.concatenate([H[min_idx:], H[:max_idx+1]])
J_asc = np.concatenate([J[min_idx:], J[:max_idx+1]])

# 分别线性拟合求过零点
hcs = []
for H_b, J_b in [(H_desc, J_desc), (H_asc, J_asc)]:
    mask = np.abs(H_b) < 500
    a, b = np.polyfit(H_b[mask], J_b[mask], 1)
    hcs.append(abs(-b / a))

Hc = np.mean(hcs)        # 取两支平均
uncertainty = abs(hcs[0] - hcs[1]) / 2   # 用两支差异估计不确定度
```

**注意**：升支和降支求得的 $H_c$ 通常有差异，要在报告中说明原因（扫描滞后、磁历史等）。

### 1.3 定标数据处理

**标准样品替代法**：
1. 用标准样品（如 Ni）的已知饱和磁矩 $J_{s,0}$ 定标 Y 轴
2. 定标常数 $K_y = J_{s,0} / V_{sat}$
3. **必须反测验证**：用 $K_y$ 反算标准样品的 $J_s$，与标称值对比
4. 在报告中说明偏差来源（读数差异、增益档位变化、鞍部定位差异等）

### 1.4 手写数据识别

**这是最高风险环节之一。** 手写数字的误识别率极高，且错误往往隐蔽。

#### 易混淆字符清单

| 易混淆字符 | 误判风险 | 典型案例 |
|-----------|---------|---------|
| **0 ↔ 6** | 极高 | "0.234" 被识别为 "6.234" |
| **1 ↔ 7** | 极高 | "1.5" 被识别为 "7.5"，偏差 400% |
| **3 ↔ 8** | 中高 | "3.14" 被识别为 "8.14" |
| **5 ↔ 6** | 中 | "5" 被识别为 "6" |
| **2 ↔ 7** | 中 | "2.0" 被识别为 "7.0" |
| **小数点位置** | 极高 | "1.23" vs "12.3" vs "123"，偏差可达 100 倍 |
| **正负号** | 高 | 负号被忽略，或污渍被误认为负号 |
| **逗号 ↔ 小数点** | 中高 | 手写逗号和小数点难以区分 |
| **上标/下标** | 中 | "10⁻³" 被识别为 "10³"，偏差 10⁶ 倍 |

#### 多工具独立识别方法

**步骤1：多工具识别**
```python
# 方法1: OCR
import pytesseract
from PIL import Image
img = Image.open('handwritten_data.jpg')
text1 = pytesseract.image_to_string(img, lang='eng')

# 方法2: 人工逐字录入（放大图片后逐行录入）
# 方法3: 不同 OCR 引擎交叉验证
```

**步骤2：交叉比对 + 重点复核**
- 对比两种方法结果，标记不一致处
- 对易混淆字符人工放大复核

**步骤3：物理合理性校验**
- 与讲义预期数量级对比
- 检查同一列数据数量级是否一致
- 检查有无非物理值

**铁律**：任何不确定的数值必须停止处理，向用户提问确认。严禁在存疑未解决的情况下继续数据处理。

**提问模板**：
```
手写数据识别中发现存疑之处，请您核对原始记录后确认：

第5行：两种识别结果分别为 "6.789" 和 "0.789"，
       原始手写数字首位是 6 还是 0？

第12行：数值为 "1.23" 还是 "12.3"？小数点位置不太清晰。

请直接回复确认后的正确数值，或提供该页更清晰的照片。
```

---

## 2. 数据可视化

### 2.1 图表类型选择

| 数据/分析目标 | 推荐图表类型 |
|-------------|------------|
| 单组数据分布 + 拟合 | 直方图 / 散点图 + 拟合曲线 |
| 需要展示拟合质量 | 主图 + 残差图（双面板） |
| 多组数据对比 | 重叠曲线 / 多子图 |
| 扫描/校准数据 | 折线图 + 关键区域标注 |
| 时序数据 | 时间序列图 |
| 二维关系 | 散点图 + 线性拟合 |
| 多参数对比 | 柱状图 / 分组柱状图 |

**多子图布局**：
```python
# 横排（3 个样品对比）
fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))

# 竖排（sharex 统一 x 轴）
fig, axes = plt.subplots(3, 1, figsize=(7, 9), sharex=True)
```

### 2.2 配色与样式

```python
COLOR_DATA  = '#2E5C8A'   # 数据点：深蓝（冷色）
COLOR_FIT   = '#D9534F'   # 拟合曲线：暖红（暖色）
COLOR_REF   = '#5CB85C'   # 标准值/参考线：绿色
COLOR_GRID  = '#E0E0E0'   # 网格线：浅灰
COLOR_RESID = '#6C4C9A'   # 残差：紫色

# 全局样式
plt.rcParams['font.sans-serif'] = ['Hiragino Sans GB', 'PingFang HK', 'Heiti TC']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150

# 边框
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(True, linestyle='--', alpha=0.4, color=COLOR_GRID)
```

**中文字体自动检测**：
```python
import matplotlib.font_manager as fm
chinese_fonts = ['SimHei', 'STHeiti', 'PingFang SC',
                 'Hiragino Sans GB', 'WenQuanYi Micro Hei',
                 'Noto Sans CJK SC']
available = [f.name for f in fm.fontManager.ttflist]
selected = next((f for f in chinese_fonts if f in available), None)

if selected:
    plt.rcParams['font.sans-serif'] = [selected, 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
```

### 2.3 参数框与图例布局

**核心原则：参数框/图例绝对禁止与任何数据点或拟合曲线重叠。**

**默认布局（右侧有空白时）**：
```python
# 参数框放右上角
param_text = (
    f"$J_s = {Js:.4f}~\\mathrm{{emu}}$\n"
    f"$J_r = {Jr:.4f}~\\mathrm{{emu}}$\n"
    f"$H_c = {Hc:.0f}~\\mathrm{{Oe}}$"
)
ax.text(0.96, 0.96, param_text, transform=ax.transAxes,
        fontsize=9, verticalalignment='top', horizontalalignment='right',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                  alpha=0.9, edgecolor='gray'), zorder=3)
```

**防截断要点**：
- `x = 0.96`（不要 0.98，留右边距）
- `fontsize = 9`（不要太大）
- `pad=0.3`（减小 padding）

**回退方案**（数据占满右侧时）：
1. 参数框移至 `upper left`
2. 图例移至 `lower left`
3. 参数框放图外（`bbox_to_anchor=(1.02, 1)`）
4. 增大 figure 尺寸（`figsize=(8, 6)`）

**避障检查清单（保存图片前必须执行）**：
- [ ] 参数框四角坐标是否避开了所有数据点？
- [ ] 参数框是否与拟合曲线/误差棒重叠？
- [ ] 图例是否与任何数据点/曲线/标题重叠？
- [ ] 若默认位置被占，是否已按回退方案调整？
- [ ] **保存图片后，放大检查确认无重叠**

### 2.4 数学符号规范

图中所有数学符号必须使用 LaTeX/MathText 原生命令：

| 错误写法 | 正确写法 |
|---------|---------|
| `chi^2_nu` | `$\chi^2_\nu$` |
| `tau = 2.20 us` | `$\tau = 2.20~\mathrm{\mu s}$` |
| `+/-` | `$\pm$` |
| `A = 7073.1 +- 85.3` | `$A = 7073.1 \pm 85.3$` |

### 2.5 matplotlib mathtext 陷阱

matplotlib 的 mathtext **不是完整 LaTeX**。

**绝对禁止**：
```python
# $$ 双美元 + \n 导致解析崩溃
param_text = (
    f"$J_s = {Js:.4f}~\\mathrm{{emu}}$$\n"   # 错误！
    f"$J_r = {Jr:.4f}~\\mathrm{{emu}}$$\n"
    f"$H_c = {Hc:.0f}~\\mathrm{{Oe}}$"
)
# 结果：$J_s = 0.3996~\mathrm{emu}$$ 原样显示为乱码
```

**正确做法**：每行独立单行 mathtext
```python
param_text = (
    f"$J_s = {Js:.4f}~\\mathrm{{emu}}$\n"
    f"$J_r = {Jr:.4f}~\\mathrm{{emu}}$\n"
    f"$H_c = {Hc:.0f}~\\mathrm{{Oe}}$"
)
```

**关键规则**：
1. 每行必须是完整独立的 `$...$`
2. 用 `\n` 分隔多行，matplotlib `Text` 对象会正确换行
3. 位置预留边距：`x < 0.98`
4. 生成后必须直接查看图片文件

### 2.6 输出格式与验证

**优先矢量图**：
```python
plt.savefig('figure.pdf', format='pdf', bbox_inches='tight')
plt.savefig('figure.png', dpi=300, bbox_inches='tight')
```

**必须验证**（PDF 嵌入 LaTeX 后看起来正常 ≠ 实际渲染正确）：
```bash
# PDF 转 PNG 查看
python3 -c "import fitz; doc=fitz.open('figure.pdf'); \
             doc[0].get_pixmap(dpi=200).save('check.png')"
```

检查项：
- 无乱码（`$`、换行、反斜杠 mathrm 原样显示）
- 无重叠（参数框不压数据）
- 无截断（包括参数框边缘）
- 标签清晰（缩小后仍可读）

---

## 3. LaTeX 排版

### 3.1 模板结构与关键配置

```latex
\documentclass[UTF8,a4paper,12pt]{ctexart}
\usepackage[top=2.45cm,bottom=2.45cm,left=2.55cm,right=2.55cm]{geometry}
\usepackage{amsmath,amsfonts,amssymb}
\usepackage{siunitx}
\usepackage{booktabs}
\usepackage{graphicx}
\usepackage{float}
\usepackage{hyperref}
\usepackage{caption}

\linespread{1.32}
\setlength{\parindent}{2em}

% 防 overfull
\tolerance=1200
\emergencystretch=3em

% 超链接打印友好
\hypersetup{colorlinks=true,linkcolor=black,citecolor=black,urlcolor=black}

% 章节样式
\ctexset{
  section={format=\large\bfseries, beforeskip=1.2ex, afterskip=0.8ex},
  subsection={format=\normalsize\bfseries, beforeskip=0.8ex, afterskip=0.4ex}
}
```

### 3.2 数值管线（铁律）

**正文中每个数值必须来自脚本输出的唯一来源。**

Python 脚本生成宏定义文件：
```python
# scripts/process_data.py
with open("results/params.tex", "w") as f:
    f.write(f"\\newcommand{{\\valJs}}{{{Js:.4f}}}\\n")
    f.write(f"\\newcommand{{\\valJr}}{{{Jr:.4f}}}\\n")
    f.write(f"\\newcommand{{\\valHc}}{{{Hc:.0f}}}\\n")
```

LaTeX 中引用：
```latex
% 导言区加载
\input{results/params.tex}

% 正文中使用
Fe 的饱和磁矩 $J_s = \valJs$ emu，矫顽力 $H_c = \valHc$ Oe。
```

**严禁**：
```latex
% 错误：手动输入数值，极易与脚本输出不一致
Fe 的饱和磁矩 $J_s = 0.3996$ emu，$H_c = 50$ Oe。
```

**唯一例外**：讲义给定的标准值、仪器参数等固定值，可在注释中标注来源后手动输入。

### 3.3 单位排版

```latex
\usepackage{siunitx}
\DeclareSIUnit\emu{emu}
\DeclareSIUnit\Oe{Oe}

\SI{9.98}{Oe/mV}              % 带数值的单位
\si{emu/cm^3}                 % 纯单位
\num{4.5e2}                   % 科学计数法
\SI{2.2045 \pm 0.0215}{\micro\second}   % 带误差
```

### 3.4 公式排版

```latex
% 独立编号公式
\begin{equation}
  N(t) = A \exp\!\left(-\frac{t}{\tau}\right) + C
  \label{eq:exp-model}
\end{equation}

% 无编号对齐
\begin{align*}
  \tau_{1} &= (1.644 \pm 0.137)\,\mathrm{\mu s}, \\
  \tau_{2} &= (2.2045 \pm 0.0215)\,\mathrm{\mu s}.
\end{align*}

% 行内
$\tau = 2.197\,\mathrm{\mu s}$
```

### 3.5 图片插入

```latex
\begin{figure}[htbp]
  \centering
  \includegraphics[width=0.85\textwidth]{figures/result.pdf}
  \caption{µ子衰变时间分布及指数拟合曲线。图中参数框给出拟合结果，
           绿色虚线标注 PDG 2024 标准值。数据来源：137 h 累计测量。}
  \label{fig:lifetime}
\end{figure}
```

- `[htbp]` 允许浮动；如需强制固定用 `[H]`（需 `\usepackage{float}`）
- `width=0.85\textwidth` 比固定宽度更稳健
- `\caption` 在前，`\label` 在后（否则引用编号可能错）

### 3.6 表格排版

```latex
\begin{table}[htbp]
\centering
\caption{三种样品的磁学参数}
\label{tab:params}
\begin{tabular}{cccc}
\toprule
样品 & $J_s$ (\si{emu}) & $J_r$ (\si{emu}) & $H_c$ (\si{Oe}) \\
\midrule
Fe & $0.400\pm0.005$ & $0.097\pm0.003$ & $50\pm35$ \\
Ni & $0.320\pm0.005$ & $0.037\pm0.003$ & $193\pm60$ \\
\bottomrule
\end{tabular}
\end{table}
```

- 用 `booktabs` 的 `\toprule/\midrule/\bottomrule`，不用 `\hline`
- 不确定度统一用 `\pm`
- 表格过宽时用 `\small` 缩小字号

### 3.7 参考文献

```latex
\begin{thebibliography}{9}
\bibitem{ref1} 中国科学技术大学物理实验教学中心,
    振动样品磁强计测磁性质, 实验讲义, 2026.
\bibitem{ref2} D. Jiles, \textit{Introduction to Magnetism and Magnetic Materials},
    2nd ed., CRC Press, p. 98 (1998).
\bibitem{ref3} D. Chen \textit{et al.}, ``Large anomalous Hall effect
    in the kagome ferromagnet LiMn$_6$Sn$_6$,''
    \textit{Phys. Rev. B} \textbf{103}, 144410 (2021).
\end{thebibliography}
```

**检查幽灵文献**：
```bash
grep -o '\\cite{[^}]*}' report.tex | sort | uniq
```

### 3.8 交叉引用常见坑

| 错误 | 原因 | 修复 |
|------|------|------|
| `??` 显示 | 标签未定义或编译次数不足 | 编译两次；检查 `\label{}` 是否在 `\caption{}` 之后 |
| `Figure~\ref{}` 换行断开 | `~` 是非断行空格 | 确保 `Figure~` 和 `\ref` 在同一行 |
| 引用跳号 | 标签重复 | 全文搜索确保每个 `\label{}` 唯一 |
| 图片模糊 | DPI 过低 | `savefig.dpi=300` |
| 图片有黑底 | PDF 提取的图片含透明通道 | 从 PDF 页面截图而非提取 embedded image |
| 编译报错 `Undefined control sequence` | 缺少宏包 | 检查是否加载 `amsmath` 等 |

---

## 4. 素材搜集与裁剪

### 4.1 原理图来源

**严禁用 matplotlib、TikZ 自行绘制原理图/示意图。**

| 来源类型 | 具体渠道 |
|---------|---------|
| 实验讲义 | 实验指导书、课程 PPT（首选） |
| 教材/专著 | Kittel《固体物理导论》等 |
| 学术论文 | arXiv、Google Scholar |
| 开放教育资源 | NDE-ED.org、HyperPhysics、Wikipedia |
| 仪器厂商手册 | Lake Shore、Quantum Design 等官网 |

### 4.2 截图硬性规范

1. **只裁剪图本身**，严禁包含正文段落、公式、页眉页脚、页码
2. 从 PDF/论文截图时，**必须用图像分析方法**精确提取 figure 区域
3. 裁剪后验证：图中是否混入不属于该图的文字？
4. 无法获得干净的图时，宁可不用

### 4.3 从 PDF 提取图片

```python
import fitz
doc = fitz.open('source.pdf')
for page in doc:
    images = page.get_images()
    for img_index, img in enumerate(images):
        xref = img[0]
        pix = fitz.Pixmap(doc, xref)
        if pix.n > 4:   # CMYK 转 RGB
            pix = fitz.Pixmap(fitz.csRGB, pix)
        pix.save(f'extracted_{img_index}.png')
```

**注意**：提取的 embedded image 可能有透明通道问题（PDF 黑底变透明）。在白色背景上打开验证。

### 4.4 连通区域分析裁剪

```python
import cv2
import numpy as np

img = cv2.imread('page.png', cv2.IMREAD_GRAYSCALE)
_, binary = cv2.threshold(img, 200, 255, cv2.THRESH_BINARY_INV)
contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# 找到最大连通区域
largest = max(contours, key=cv2.contourArea)
x, y, w, h = cv2.boundingRect(largest)
cropped = img[y:y+h, x:x+w]
```

---

## 5. 快速命令索引

```bash
# LaTeX 编译
xelatex -interaction=nonstopmode report.tex

# 提取 PDF 文本
pdftotext report.pdf - | head -n 100

# 检查参考文献引用
grep -o '\\cite{[^}]*}' report.tex | sort | uniq

# PDF 图转 PNG 查看
python3 -c "import fitz; doc=fitz.open('figure.pdf'); \
             doc[0].get_pixmap(dpi=200).save('check.png')"

# 检查 overfull hbox
grep -i "overfull" report.log

# 统计字数
pdftotext report.pdf - | wc -m
```
