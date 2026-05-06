#!/usr/bin/env python3
"""
PDF 转 PNG 验证脚本

将 PDF 报告或 PDF 图片转换为 PNG，用于直接目视检查渲染质量。
解决"PDF 缩略图看起来正常，实际嵌入后乱码/截断"的问题。

用法:
    # 转换单张 PDF 图片（常用于检查 matplotlib 输出的 figure.pdf）
    python3 pdf_to_png.py figure.pdf

    # 转换整份报告的所有页面
    python3 pdf_to_png.py report.pdf --all-pages

    # 指定输出目录
    python3 pdf_to_png.py figure.pdf -o check/

    # 指定 DPI（默认 200，报告审查建议 >= 150）
    python3 pdf_to_png.py figure.pdf --dpi 300
"""

import argparse
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("❌ 需要 PyMuPDF: pip install PyMuPDF", file=sys.stderr)
    sys.exit(1)


def pdf_page_to_png(pdf_path: Path, page_num: int = 0, dpi: int = 200, output_path: Path = None) -> Path:
    """将 PDF 单页转为 PNG"""
    doc = fitz.open(str(pdf_path))
    if page_num >= len(doc):
        print(f"❌ 页码 {page_num} 超出范围 (共 {len(doc)} 页)", file=sys.stderr)
        sys.exit(1)

    page = doc[page_num]
    # DPI 转缩放因子: 72 dpi 是 PDF 默认，所以 scale = dpi / 72
    scale = dpi / 72
    mat = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=mat)

    if output_path is None:
        stem = pdf_path.stem
        output_path = pdf_path.parent / f"{stem}_p{page_num}_{dpi}dpi.png"

    pix.save(str(output_path))
    doc.close()
    print(f"✅ {output_path} ({pix.width}x{pix.height}, {dpi} DPI)")
    return output_path


def pdf_all_pages_to_png(pdf_path: Path, dpi: int = 200, output_dir: Path = None):
    """将 PDF 所有页面转为 PNG"""
    doc = fitz.open(str(pdf_path))
    if output_dir is None:
        output_dir = pdf_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    page_count = len(doc)
    for i in range(page_count):
        page = doc[i]
        scale = dpi / 72
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat)
        out = output_dir / f"{pdf_path.stem}_p{i}_{dpi}dpi.png"
        pix.save(str(out))
        print(f"✅ {out.name} ({pix.width}x{pix.height})")

    doc.close()
    print(f"\n共 {page_count} 页，输出到: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="PDF 转 PNG 验证脚本")
    parser.add_argument("pdf", help="输入 PDF 文件路径")
    parser.add_argument("-o", "--output", help="输出文件/目录路径")
    parser.add_argument("--dpi", type=int, default=200, help="输出 DPI (默认 200)")
    parser.add_argument("--page", "-p", type=int, default=0, help="要转换的页码 (默认 0)")
    parser.add_argument("--all-pages", "-a", action="store_true", help="转换所有页面")
    args = parser.parse_args()

    pdf_path = Path(args.pdf).resolve()
    if not pdf_path.exists():
        print(f"❌ 文件不存在: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    if args.all_pages:
        output_dir = Path(args.output).resolve() if args.output else None
        pdf_all_pages_to_png(pdf_path, dpi=args.dpi, output_dir=output_dir)
    else:
        output_path = Path(args.output).resolve() if args.output else None
        pdf_page_to_png(pdf_path, page_num=args.page, dpi=args.dpi, output_path=output_path)


if __name__ == "__main__":
    main()
