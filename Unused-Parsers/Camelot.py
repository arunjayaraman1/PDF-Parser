from __future__ import annotations

import os
import sys
import time
from pathlib import Path
import pandas as pd

# Avoid shadowing camelot
THIS_DIR = str(Path(__file__).resolve().parent)
if THIS_DIR in sys.path:
    sys.path.remove(THIS_DIR)

try:
    import camelot
except ModuleNotFoundError as exc:
    raise RuntimeError(
        "camelot-py is not installed. Install with: python -m pip install camelot-py[cv]"
    ) from exc


def _format_duration_sec(total_sec: float) -> tuple[int, float]:
    mins = int(total_sec // 60)
    secs = total_sec - 60 * mins
    return mins, secs


def _camelot_flavor() -> str:
    f = os.environ.get("CAMELOT_FLAVOR", "lattice").strip().lower()
    return f if f in ("lattice", "stream") else "lattice"


def main() -> None:
    pdf_path = Path("Holiday 2026.pdf")
    if not pdf_path.exists():
        raise FileNotFoundError("PDF not found.")

    out_file = pdf_path.parent / f"{pdf_path.stem}_all_tables.csv"

    flavor = _camelot_flavor()
    print(f"Using Camelot flavor: {flavor}")

    t0 = time.perf_counter()

    # 🔥 Extract tables
    tables = camelot.read_pdf(
        str(pdf_path),
        pages="all",
        flavor=flavor,
    )

    if tables.n == 0:
        print("No tables found.")
        return

    final_rows = []

    for i in range(tables.n):
        t = tables[i]
        df = t.df

        # Get page number
        page = getattr(t, "page", i + 1)
        try:
            page = int(page)
        except:
            page = i + 1

        table_id = i + 1

        # ✅ Add clean label row
        label_row = pd.DataFrame([[f"Page {page}, Table {table_id}"]])

        # Reset column names to avoid mismatch
        df.columns = range(df.shape[1])

        final_rows.append(label_row)
        final_rows.append(df)

    # Combine everything
    final_df = pd.concat(final_rows, ignore_index=True)

    # Save CSV
    final_df.to_csv(out_file, index=False, header=False)

    elapsed = time.perf_counter() - t0
    mins, secs = _format_duration_sec(elapsed)

    print("\n--- Done ---")
    print(f"Tables extracted: {tables.n}")
    print(f"Output file: {out_file}")
    print(f"Execution time: {mins} min {secs:.2f} sec")


if __name__ == "__main__":
    main()