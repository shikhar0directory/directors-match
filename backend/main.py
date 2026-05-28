from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn, shutil, os, random, json
import numpy as np
from database import init_db, get_all_locations

app = FastAPI(
    title="Directors Match API",
    description="AI-powered cinematic location scouting — Sage University Bhopal",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("images", exist_ok=True)
app.mount("/images", StaticFiles(directory="images"), name="images")

model       = None
faiss_index = None
index_ids   = []

def load_ai():
    global model, faiss_index, index_ids
    try:
        import faiss
        from sentence_transformers import SentenceTransformer
        import sqlite3

        print("🤖 Loading AI model...")
        model = SentenceTransformer("clip-ViT-B-32")
        print("✅ AI model loaded!")

        conn = sqlite3.connect("directors_match.db")
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT location_id, vector FROM image_vectors WHERE vector IS NOT NULL"
        ).fetchall()
        conn.close()

        if not rows:
            print("⚠️  No vectors found — run vector_gen.py first!")
            return

        vectors   = []
        index_ids = []

        for row in rows:
            try:
                vec = np.array(json.loads(row["vector"]), dtype=np.float32)
                vectors.append(vec)
                index_ids.append(row["location_id"])
            except Exception as e:
                print(f"   Skip vector: {e}")

        if not vectors:
            print("⚠️  No valid vectors!")
            return

        dim         = len(vectors[0])
        faiss_index = faiss.IndexFlatIP(dim)

        matrix = np.stack(vectors)
        norms  = np.linalg.norm(matrix, axis=1, keepdims=True)
        matrix = matrix / (norms + 1e-8)

        faiss_index.add(matrix)
        print(f"✅ FAISS index built with {len(vectors)} vectors!")
        print("🎬 Real AI matching ACTIVE!")

    except Exception as e:
        print(f"⚠️  AI loading failed: {e}")
        model = None
        faiss_index = None

@app.on_event("startup")
def startup():
    init_db()
    print("✅ Database ready.")
    load_ai()

@app.get("/")
def root():
    ai_active = model is not None and faiss_index is not None
    return {
        "status":      "running",
        "project":     "Directors Match",
        "version":     "2.0.0",
        "ai_matching": "CLIP+FAISS ACTIVE" if ai_active else "Random (run vector_gen.py)"
    }

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    allowed = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed:
        raise HTTPException(400, "Only JPG, PNG or WEBP images allowed.")
    path = f"images/{file.filename}"
    with open(path, "wb") as buf:
        shutil.copyfileobj(file.file, buf)
    return {"success": True, "filename": file.filename, "path": path}

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    save_path = f"images/query_{file.filename}"
    content   = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    locs = get_all_locations()
    if not locs:
        raise HTTPException(404, "No locations in database.")

    if model is not None and faiss_index is not None and index_ids:
        try:
            import faiss
            from PIL import Image as PILImage

            query_img = PILImage.open(save_path).convert("RGB")
            query_vec = model.encode(query_img).astype(np.float32)
            query_vec = query_vec / (np.linalg.norm(query_vec) + 1e-8)
            query_vec = query_vec.reshape(1, -1)

            k            = min(4, faiss_index.ntotal)
            scores, idxs = faiss_index.search(query_vec, k)

            results = []
            for score, idx in zip(scores[0], idxs[0]):
                if idx < 0 or idx >= len(index_ids):
                    continue
                loc_id = index_ids[idx]
                loc    = next((l for l in locs if l["id"] == loc_id), None)
                if not loc:
                    continue
                tags      = [t.strip() for t in loc["tags"].split(",")] if loc["tags"] else []
                match_pct = int(50 + (float(score) * 49))
                match_pct = max(50, min(99, match_pct))
                results.append({
                    "id":          loc["id"],
                    "name":        loc["name"],
                    "area":        loc["area"],
                    "image_url":   f"http://localhost:8000/images/{loc['image_path']}",
                    "tags":        tags,
                    "crowd_level": loc["crowd_level"],
                    "cam_iso":     loc.get("cam_iso", ""),
                    "cam_ss":      loc.get("cam_ss", ""),
                    "cam_ap":      loc.get("cam_ap", ""),
                    "cam_focal":   loc.get("cam_focal", ""),
                    "cam_ev":      loc.get("cam_ev", ""),
                    "cam_wb":      loc.get("cam_wb", ""),
                    "match":       match_pct,
                })

            results.sort(key=lambda x: x["match"], reverse=True)
            return {
                "success":           True,
                "matching_mode":     "CLIP + FAISS — Real AI Visual Similarity",
                "matched_locations": results
            }

        except Exception as e:
            print(f"AI matching error: {e}")

    sample  = random.sample(locs, min(4, len(locs)))
    results = []
    for loc in sample:
        tags = [t.strip() for t in loc["tags"].split(",")] if loc["tags"] else []
        results.append({
            "id":          loc["id"],
            "name":        loc["name"],
            "area":        loc["area"],
            "image_url":   f"http://localhost:8000/images/{loc['image_path']}",
            "tags":        tags,
            "crowd_level": loc["crowd_level"],
            "cam_iso":     loc.get("cam_iso", ""),
            "cam_ss":      loc.get("cam_ss", ""),
            "cam_ap":      loc.get("cam_ap", ""),
            "cam_focal":   loc.get("cam_focal", ""),
            "cam_ev":      loc.get("cam_ev", ""),
            "cam_wb":      loc.get("cam_wb", ""),
            "match":       random.randint(70, 99),
        })
    results.sort(key=lambda x: x["match"], reverse=True)
    return {
        "success":           True,
        "matching_mode":     "Random fallback",
        "matched_locations": results
    }

@app.get("/locations")
def locations():
    locs   = get_all_locations()
    result = []
    for loc in locs:
        tags = [t.strip() for t in loc["tags"].split(",")] if loc["tags"] else []
        result.append({
            "id":          loc["id"],
            "name":        loc["name"],
            "area":        loc["area"],
            "image_url":   f"http://localhost:8000/images/{loc['image_path']}",
            "tags":        tags,
            "crowd_level": loc["crowd_level"],
            "cam_iso":     loc.get("cam_iso", ""),
            "cam_ss":      loc.get("cam_ss", ""),
            "cam_ap":      loc.get("cam_ap", ""),
            "cam_focal":   loc.get("cam_focal", ""),
            "cam_ev":      loc.get("cam_ev", ""),
            "cam_wb":      loc.get("cam_wb", ""),
        })
    return {"success": True, "total": len(result), "locations": result}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
