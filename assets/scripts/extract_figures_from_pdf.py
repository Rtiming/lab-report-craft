#!/usr/bin/env python3
"""
从 PDF 提取图片脚本

实验讲义/论文中常有需要的原理图/示意图。此脚本提供两种提取方式：
1. 提取 PDF 中嵌入的图片对象（保留原始分辨率）
2. 截取 PDF 页面区域（处理透明通道、裁剪空白边距）

透明通道问题：部分 PDF 提取的图片含透明背景，在 LaTeX 白色背景下显示为黑底。
此脚本自动检测并将透明通道转为白色背景。

用法:
    # 提取 PDF 中所有嵌入的图片
    python3 extract_figures_from_pdf.py lecture.pdf

    # 截取指定页面区域（用于从论文页面中截取 figure）
    python3 extract_figures_from_pdf.py paper.pdf --page 3 --crop --output figure.png

    # 批量处理：提取所有嵌入图片到指定目录
    python3 extract_figures_from_pdf.py lecture.pdf -o assets/extracted/
"""

import argparse
import io
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
    from PIL import Image
    import numpy as np
except ImportError as e:
    print(f"❌ 缺少依赖: {e}\n   pip install PyMuPDF Pillow numpy", file=sys.stderr)
    sys.exit(1)


def extract_embedded_images(pdf_path: Path, output_dir: Path, min_size: int = 100):
    """提取 PDF 中嵌入的图片对象"""
    doc = fitz.open(str(pdf_path))
    output_dir.mkdir(parents=True, exist_ok=True)
    extracted = []

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        img_list = page.get_images(full=True)

        for img_idx, img in enumerate(img_list, start=1):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            ext = base_image["ext"]

            # 跳过太小的图片（通常是图标、装饰元素）
            try:
                pil_img = Image.open(io.BytesIO(image_bytes))
                if pil_img.width < min_size or pil_img.height < min_size:
                    continue
            except Exception:
                continue

            # 处理透明通道
            pil_img = handle_transparency(pil_img)

            out_path = output_dir / f"{pdf_path.stem}_p{page_idx}_img{img_idx}.png"
            pil_img.save(str(out_path), "PNG")
            extracted.append(out_path)
            print(f"✅ {out_path.name} ({pil_img.width}x{pil_img.height})")

    doc.close()
    print(f"\n共提取 {len(extracted)} 张图片到: {output_dir}")
    return extracted


def handle_transparency(img: Image.Image) -> Image.Image:
    """
    处理透明通道。
    部分 PDF 提取的图片含透明背景（RGBA），在白色背景下显示为黑底。
    转换为 RGB，透明部分填充白色。
    """
    if img.mode == "RGBA":
        # 创建白色背景
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])  # 使用 alpha 通道作为 mask
        return background
    elif img.mode == "P":
        # 调色板模式，先转 RGBA 再处理
        img = img.convert("RGBA")
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])
        return background
    elif img.mode != "RGB":
        return img.convert("RGB")
    return img


def crop_page_region(pdf_path: Path, page_num: int, output_path: Path, dpi: int = 300):
    """
    截取 PDF 页面，自动裁剪空白边距（基于连通区域分析）。
    适用于从论文/讲义页面中截取 figure 区域。
    """
    doc = fitz.open(str(pdf_path))
    if page_num >= len(doc):
        print(f"❌ 页码 {page_num} 超出范围 (共 {len(doc)} 页)", file=sys.stderr)
        sys.exit(1)

    page = doc[page_num]
    scale = dpi / 72
    mat = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=mat)

    # 转为 PIL Image
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    doc.close()

    # 自动裁剪空白边距
    img_cropped = auto_crop_white_margin(img, threshold=250)

    img_cropped.save(str(output_path), "PNG")
    print(f"✅ {output_path} (原始 {img.width}x{img.height} → 裁剪后 {img_cropped.width}x{img_cropped.height})")
    return output_path


def auto_crop_white_margin(img: Image.Image, threshold: int = 250) -> Image.Image:
    """
    基于连通区域分析裁剪白色边距。
    找出非白色内容的边界框，裁剪掉周围的空白。
    """
    arr = np.array(img)

    # 转换为灰度，找出非白色像素
    if len(arr.shape) == 3:
        gray = np.mean(arr, axis=2)
    else:
        gray = arr

    # 非白色像素的掩码
    mask = gray < threshold

    if not np.any(mask):
        return img  # 全白，不裁剪

    # 找出非白色区域的边界
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    top = np.argmax(rows)
    bottom = len(rows) - np.argmax(rows[::-1])
    left = np.argmax(cols)
    right = len(cols) - np.argmax(cols[::-1])

    # 留一点边距（10 像素）
    margin = 10
    top = max(0, top - margin)
    bottom = min(img.height, bottom + margin)
    left = max(0, left - margin)
    right = min(img.width, right + margin)

    return img.crop((left, top, right, bottom))


def main():
    parser = argparse.ArgumentParser(description="从 PDF 提取图片")
    parser.add_argument("pdf", help="输入 PDF 文件路径")
    parser.add_argument("-o", "--output", help="输出目录/文件路径")
    parser.add_argument("--page", "-p", type=int, help="截取指定页面（从 0 开始）")
    parser.add_argument("--crop", "-c", action="store_true", help="自动裁剪空白边距")
    parser.add_argument("--dpi", type=int, default=300, help="截图 DPI (默认 300)")
    parser.add_argument("--min-size", type=int, default=100, help="提取嵌入图片的最小尺寸 (默认 100)")
    args = parser.parse_args()

    pdf_path = Path(args.pdf).resolve()
    if not pdf_path.exists():
        print(f"❌ 文件不存在: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    if args.page is not None:
        # 截取页面模式
        if args.output:
            output_path = Path(args.output).resolve()
        else:
            output_path = pdf_path.parent / f"{pdf_path.stem}_p{args.page}_cropped.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        crop_page_region(pdf_path, args.page, output_path, dpi=args.dpi)
    else:
        # 提取嵌入图片模式
        if args.output:
            output_dir = Path(args.output).resolve()
        else:
            output_dir = pdf_path.parent / f"{pdf_path.stem}_extracted"
        extract_embedded_images(pdf_path, output_dir, min_size=args.min_size)


if __name__ == "__main__":
    main()
