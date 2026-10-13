"""Generate a clearly fictional sample attachment; no patient data."""

from pathlib import Path

from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1]
target = root / "apps/web/public/synthetic-document.png"
target.parent.mkdir(parents=True, exist_ok=True)
image = Image.new("RGB", (1000, 650), "#f6faf8")
draw = ImageDraw.Draw(image)
draw.rectangle((45, 45, 955, 605), fill="white", outline="#b4cfc3", width=3)
for y, text, size in [
    (90, "PEDIATRIC CLINIC - FICTIONAL SAMPLE", 34),
    (160, "Development attachment for Unit 03", 28),
    (245, "No real patient or medical findings are present.", 24),
    (300, "Use this image to try upload, retrieval and withdrawal.", 24),
    (400, "SYNTHETIC DATA ONLY", 34),
    (470, "Not a medical report. Not clinically validated.", 24),
]:
    draw.text((85, y), text, fill="#196f63", font_size=size)
image.save(target)
print("Fictional sample attachment generated.")
