# Lab Report Craft

通用大学物理/工程实验报告写作工作流 Skill，覆盖从讲义解析、数据审阅、处理分析、可视化、LaTeX 排版到多轮审校的全流程。

- 📖 [项目背景与适用场景](docs/project-context.md)
- 🛠️ [常见使用流程](docs/common-workflows.md)
- 🔧 [问题排查指南](docs/troubleshooting.md)
- 🤖 [AI Agent 入口文档](AGENTS.md)

本 Skill 在长输出、低成本的模型环境下创立并验证。此类环境单次输出 token 量大，但推理深度和代码能力有限，偶有低级错误。因此工作流以**流程冗余和强制校验**为主要防御手段，通过数值管线、多方交叉验证、逐页逐图逐句审查等机制保障输出准确性。

---

## 文件结构

| 文件 | 用途 |
|------|------|
| `SKILL.md` | 工作流总纲。八阶段速览 + 核心原则 + 资源索引 |
| `references/workflow.md` | 八阶段详解，含每个阶段的操作步骤与提问触发点 |
| `references/checklist.md` | 写作自检 + 七维排查 + 逐页逐图逐句检查 + 教师评审清单 |
| `references/practical-guide.md` | 数据处理、可视化、LaTeX 排版、素材搜集、手写识别的代码示例与规范 |
| `references/ask-user-guide.md` | 不确定时提问指南，含 16 个触发点的标准提问模板 |
| `assets/template.tex` | 通用 ctexart 实验报告 LaTeX 模板 |
| `assets/scripts/compile_report.py` | LaTeX 自动编译（多次编译直到交叉引用稳定） |
| `assets/scripts/pdf_to_png.py` | PDF 转 PNG 验证（检查渲染质量） |
| `assets/scripts/extract_figures_from_pdf.py` | 从讲义/论文 PDF 提取图片（处理透明通道） |
| `assets/scripts/check_numerical_pipeline.py` | 扫描手动输入数值，检查数值管线完整性 |
| `assets/scripts/validate_report.py` | 综合验证（图片存在性+数值管线+编译） |

---

## 使用方式

1. 在对话中提供实验讲义和数据文件的路径（或直接上传）
2. （可选）指定 `assets/template.tex` 的自定义模板路径
3. 指示 Agent 生成实验报告，例如：

```
实验讲义在 [路径]，数据在 [路径]，按模板生成实验报告。
```

Agent 自动加载 `SKILL.md`，按八阶段工作流执行，各阶段自动查阅 `references/` 下的对应参考文件。

---

## 核心原则

1. **讲义驱动**：实验讲义的明确要求是最高准则
2. **全局返工**：发现问题回到源头阶段重新执行，不是单步修补
3. **不确定时提问**：遇到模糊、不一致、讲义未明确的内容必须停下来向用户提问，严禁推测
4. **预防胜于检查**：写的时候就对，不要指望审校兜底
5. **数值管线**：正文中每个数值来自脚本输出的唯一来源（`params.tex` + `\newcommand`），禁止手动输入
6. **手写数据多方验证**：至少两种独立方法交叉验证，存疑必问
7. **逐页逐图逐句审校**：七维排查（粗筛）+ 逐页逐图逐句（精筛）+ 独立教师 Agent 交叉审核
