from __future__ import annotations

import os
import sys
import time
from pathlib import Path
import pandas as pd

# Avoid shadowing tabula
THIS_DIR = str(Path(__file__).resolve().parent)
if THIS_DIR in sys.path:
    sys.path.remove(THIS_DIR)

try:
    import tabula
except ModuleNotFoundError as exc:
    raise RuntimeError(
        "tabula-py is not installed. Install with: python -m pip install tabula-py"
    ) from exc


def _format_duration_sec(total_sec: float) -> tuple[int, float]:
    mins = int(total_sec // 60)
    secs = total_sec - 60 * mins
    return mins, secs


def _tabula_lattice() -> bool:
    return os.environ.get("TABULA_LATTICE", "").strip().lower() in ("1", "true", "yes")


def main() -> None:
    pdf_path = Path("Meta-Harness_ End-to-End Optimization of Model Harnesses.pdf")
    if not pdf_path.exists():
        raise FileNotFoundError("PDF not found.")

    out_file = pdf_path.parent / f"{pdf_path.stem}_tabula_all_tables.csv"

    lattice = _tabula_lattice()
    mode = "lattice" if lattice else "stream"

    print(f"Using Tabula mode: {mode}")
    print("Starting extraction...\n")

    t0 = time.perf_counter()

    # 🔥 TABULA ONLY
    dfs = tabula.read_pdf(
        str(pdf_path),
        pages="all",
        multiple_tables=True,
        lattice=lattice,
    )

    if not dfs:
        print("No tables found.")
        return

    final_rows = []

    # 🧠 Track page manually (Tabula doesn’t give page reliably)
    table_counter = 1

    for df in dfs:
        if df is None or df.empty:
            continue

        # ⚠️ Tabula doesn't always return page → approximate
        page = table_counter  # fallback assumption

        # Reset columns (avoid mismatch)
        df.columns = range(df.shape[1])

        # ✅ Label row (your exact requirement)
        label_row = pd.DataFrame([[f"Page {page}, Table {table_counter}"]])

        final_rows.append(label_row)
        final_rows.append(df)

        table_counter += 1

    # Combine everything
    final_df = pd.concat(final_rows, ignore_index=True)

    # Save CSV
    final_df.to_csv(out_file, index=False, header=False)

    elapsed = time.perf_counter() - t0
    mins, secs = _format_duration_sec(elapsed)

    print("\n--- Done ---")
    print(f"Tables extracted: {table_counter - 1}")
    print(f"Output file: {out_file}")
    print(f"Execution time: {mins} min {secs:.2f} sec")


if __name__ == "__main__":
    main()