import os
import torch
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

fname = "Meta-Harness.pdf"
output_dir = "marker_output"

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Load models (no options allowed in your version)
model_dict = create_model_dict()

converter = PdfConverter(artifact_dict=model_dict)

# ✅ ONLY THIS (no flags)
rendered = converter(fname)

full_text, _, images = text_from_rendered(rendered)

os.makedirs(output_dir, exist_ok=True)

for img_name, img_obj in images.items():
    img_obj.save(os.path.join(output_dir, img_name))

with open(os.path.join(output_dir, "output.txt"), "w", encoding="utf-8") as f:
    f.write(full_text)

print(f"✅ Done! {len(images)} images saved.")