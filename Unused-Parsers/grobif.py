from __future__ import annotations

import requests
from pathlib import Path


def main() -> None:
    pdf_path = Path("Meta-Harness_ End-to-End Optimization of Model Harnesses.pdf") 
    if not pdf_path.exists():
        raise FileNotFoundError("PDF not found.")

    # ✅ Output file (native XML)
    out_file = pdf_path.parent / f"{pdf_path.stem}_grobid.xml"

    url = "http://localhost:8070/api/processFulltextDocument"

    print("Running GROBID...\n")

    with open(pdf_path, "rb") as f:
        response = requests.post(
            url,
            files={"input": (pdf_path.name, f, "application/pdf")}
        )

    if response.status_code != 200:
        raise RuntimeError("GROBID failed")

    # ✅ Save native TEI XML
    out_file.write_text(response.text, encoding="utf-8")

    print("\n--- Done ---")
    print(f"Output: {out_file}")


if __name__ == "__main__":
    main()