#!/usr/bin/env python3
import gc, sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from process_pdf_batch import process_one, load_index, save_index, get_indexed_names

STANDARDS = Path("knowledge/standards")
EXTRACTED = Path("knowledge/extracted")
INDEX = Path("knowledge/index.json")

txt_stems = {t.stem for t in EXTRACTED.glob("*.txt")}
missing = sorted([p for p in STANDARDS.glob("*.pdf") if p.stem not in txt_stems])

print(f"Missing: {len(missing)}")

# Process OOM-prone ones first with lower DPI
oom_prone = [p for p in missing if any(x in p.name for x in ["SYT 0608", "SHT3046", "NBT 47041"])]
other = [p for p in missing if p not in oom_prone]
ordered = oom_prone + other

ok_count = 0
fail_count = 0

for pdf_path in ordered:
    safe_name = pdf_path.name.encode("utf-8", errors="replace").decode("ascii", errors="replace")
    print(f"\nProcessing: {safe_name}", flush=True)
    gc.collect()
    dpi = 150 if pdf_path in oom_prone else 200
    print(f"  DPI: {dpi}", flush=True)
    try:
        result = process_one(pdf_path, force_ocr=False, dpi=dpi)
        if result:
            ok_count += 1
            print(f"  ✅ Done", flush=True)
        else:
            fail_count += 1
            print(f"  ❌ Failed", flush=True)
    except Exception as e:
        fail_count += 1
        print(f"  ❌ Error: {e}", flush=True)
    gc.collect()

print(f"\n{'='*60}")
print(f"Results: {ok_count} ok, {fail_count} failed")