import os
import shutil
from pathlib import Path

import opendataloader_pdf
import pypdf

input_path = os.environ.get("OPENDATALOADER_SOURCE")
if not input_path:
    raise ValueError("OPENDATALOADER_SOURCE not set")

pdf_path = Path(input_path).resolve()
stem = pdf_path.stem

pdf_reader = pypdf.PdfReader(input_path)
total_pages = len(pdf_reader.pages)

opendataloader_pdf.convert(
    input_path=input_path,
    output_dir="output",
    format=["markdown", "json"],
    markdown_page_separator=f"--- Page %page-number% / {total_pages} ---",
)

extracted_dir = Path(f"{stem}_extracted")
extracted_dir.mkdir(parents=True, exist_ok=True)

md_file = Path(f"output/{stem}.md")
if md_file.exists():
    content = md_file.read_text(encoding="utf-8")
    output_file = extracted_dir / "extracted.md"
    output_file.write_text(content, encoding="utf-8")

images_dir = Path(f"output/{stem}_images")
if images_dir.exists():
    dest_images = extracted_dir / f"{stem}_images"
    if dest_images.exists():
        shutil.copytree(images_dir, dest_images, dirs_exist_ok=True)
    else:
        shutil.copytree(images_dir, dest_images)

json_file = Path(f"output/{stem}.json")
if json_file.exists():
    (extracted_dir / "extracted.json").write_text(
        json_file.read_text(encoding="utf-8"), encoding="utf-8"
    )