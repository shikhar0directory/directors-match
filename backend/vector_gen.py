"""
Directors Match — Vector Generator
Ek baar run karo — saari campus photos ke vectors ban jayenge
Phir main.py real similarity matching karega
"""

import os
import json
import sqlite3
import numpy as np
from PIL import Image
from sentence_transformers import SentenceTransformer

DB_PATH    = "directors_match.db"
IMG_FOLDER = "images"

print("🎬 Directors Match — Vector Generator")
print("=" * 45)
print("Loading AI model... (pehli baar thoda time lagega)")

# CLIP-based vision model load karo
model = SentenceTransformer("clip-ViT-B-32")
print("✅ AI model loaded!")
print()

# Database connect karo
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur  = conn.cursor()

# Saari locations fetch karo
locations = cur.execute("SELECT * FROM locations").fetchall()
print(f"📍 {len(locations)} locations mili database mein")
print()

success = 0
failed  = 0

for loc in locations:
    img_path = os.path.join(IMG_FOLDER, loc["image_path"])

    if not os.path.exists(img_path):
        print(f"  ⚠️  Image nahi mili: {loc['image_path']} — skip kar rahe hain")
        failed += 1
        continue

    try:
        # Image load karo
        img = Image.open(img_path).convert("RGB")

        # Vector generate karo
        vector = model.encode(img)

        # Vector store karo database mein
        vector_json = json.dumps(vector.tolist())

        # Pehle purana vector delete karo agar hai
        cur.execute(
            "DELETE FROM image_vectors WHERE location_id = ?",
            (loc["id"],)
        )

        # Naya vector insert karo
        cur.execute(
            "INSERT INTO image_vectors (location_id, vector) VALUES (?, ?)",
            (loc["id"], vector_json)
        )

        print(f"  ✅ {loc['name']}")
        success += 1

    except Exception as e:
        print(f"  ❌ Error {loc['name']}: {e}")
        failed += 1

conn.commit()
conn.close()

print()
print("=" * 45)
print(f"✅ Done! {success} vectors generated")
if failed > 0:
    print(f"⚠️  {failed} images skip hui (file missing)")
print()
print("Ab python3 main.py run karo — real AI matching shuru ho jayegi!")
