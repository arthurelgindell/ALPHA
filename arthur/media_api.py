"""
REST API for LanceDB Media Database.

Provides network access to the media database from any node (ALPHA, BETA, GAMMA)
over Tailscale. Runs on ALPHA at port 8422.

Usage:
    # Start server
    python -m arthur.media_api

    # From any node
    curl http://alpha:8422/health
    curl http://alpha:8422/stats
    curl "http://alpha:8422/search/theme?query=neural+network&limit=5"
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import logging
import base64
from datetime import datetime

from arthur.media_db import MediaDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
  title="ARTHUR Media Database API",
  description="REST API for LanceDB media asset database",
  version="1.0.0"
)

# Global database instance (lazy loaded)
_db: Optional[MediaDatabase] = None


def get_db() -> MediaDatabase:
  """Get or create database instance."""
  global _db
  if _db is None:
    logger.info("Initializing MediaDatabase...")
    _db = MediaDatabase()
    logger.info("MediaDatabase ready")
  return _db


# ============================================================
# Request/Response Models
# ============================================================

class AddImageRequest(BaseModel):
  """Request to add an image to the database."""
  image_base64: str  # Base64 encoded image
  filename: str
  source: str
  generation_prompt: Optional[str] = None
  generation_model: Optional[str] = None
  content_type: Optional[str] = None
  subjects: Optional[List[str]] = None
  style_tags: Optional[List[str]] = None
  quality_rating: Optional[int] = None
  episode_assignments: Optional[List[int]] = None


class AddVideoRequest(BaseModel):
  """Request to add a video to the database."""
  video_base64: str  # Base64 encoded video
  filename: str
  source: str
  thumbnail_base64: Optional[str] = None
  generation_prompt: Optional[str] = None
  generation_model: Optional[str] = None
  content_type: Optional[str] = None
  subjects: Optional[List[str]] = None
  style_tags: Optional[List[str]] = None
  quality_rating: Optional[int] = None
  episode_assignments: Optional[List[int]] = None


class RateAssetRequest(BaseModel):
  """Request to rate an asset."""
  asset_id: str
  rating: int
  notes: Optional[str] = None


class AssignEpisodeRequest(BaseModel):
  """Request to assign asset to episode."""
  asset_id: str
  episode: int


class SearchSimilarRequest(BaseModel):
  """Request for image similarity search."""
  image_base64: str  # Base64 encoded reference image
  limit: int = 10
  media_type: Optional[str] = None  # 'image' or 'video'


class AssetResponse(BaseModel):
  """Response with asset metadata (no binary content)."""
  id: str
  filename: str
  source: str
  media_type: str
  width: Optional[int]
  height: Optional[int]
  duration_seconds: Optional[float]
  file_size_bytes: Optional[int]
  format: Optional[str]
  content_type: Optional[str]
  subjects: List[str]
  style_tags: List[str]
  quality_rating: Optional[int]
  quality_notes: Optional[str]
  episode_assignments: List[int]
  use_count: int
  created_at: str


# ============================================================
# Health & Stats Endpoints
# ============================================================

@app.get("/health")
async def health():
  """Health check endpoint."""
  return {
    "status": "healthy",
    "service": "media-db-api",
    "version": "1.0.0",
    "timestamp": datetime.now().isoformat()
  }


@app.get("/stats")
async def stats():
  """Get database statistics."""
  db = get_db()
  return db.stats()


# ============================================================
# Search Endpoints
# ============================================================

@app.get("/search/theme")
async def search_by_theme(
  query: str = Query(..., description="Natural language search query"),
  limit: int = Query(20, description="Maximum results"),
  min_quality: Optional[int] = Query(None, description="Minimum quality rating"),
  media_type: Optional[str] = Query(None, description="Filter: 'image' or 'video'")
):
  """Search assets by natural language theme description.

  Example: /search/theme?query=neural+network+AI&limit=5
  """
  db = get_db()
  # Get more results to account for filtering
  fetch_limit = limit * 5 if media_type else limit
  results = db.find_by_theme(query, limit=fetch_limit, min_quality=min_quality)

  if media_type:
    results = results[results['media_type'] == media_type].head(limit)

  # Convert to list of dicts without binary content
  assets = []
  for _, row in results.iterrows():
    assets.append(_row_to_asset_dict(row))

  return {"query": query, "count": len(assets), "assets": assets}


@app.post("/search/similar")
async def search_similar(request: SearchSimilarRequest):
  """Find visually similar assets to a reference image.

  POST with base64-encoded image.
  """
  db = get_db()

  try:
    image_bytes = base64.b64decode(request.image_base64)
  except Exception as e:
    raise HTTPException(status_code=400, detail=f"Invalid base64 image: {e}")

  results = db.find_similar(image_bytes, limit=request.limit, media_type=request.media_type)

  assets = []
  for _, row in results.iterrows():
    assets.append(_row_to_asset_dict(row))

  return {"count": len(assets), "assets": assets}


@app.get("/search/subject/{subject}")
async def search_by_subject(
  subject: str,
  media_type: Optional[str] = Query(None, description="Filter: 'image' or 'video'")
):
  """Find assets by subject tag.

  Example: /search/subject/mac_studio
  """
  db = get_db()
  results = db.find_by_subject(subject, media_type=media_type)

  assets = []
  for _, row in results.iterrows():
    assets.append(_row_to_asset_dict(row))

  return {"subject": subject, "count": len(assets), "assets": assets}


@app.get("/search/episode/{episode}")
async def search_by_episode(
  episode: int,
  unassigned: bool = Query(False, description="Find unassigned assets instead")
):
  """Find assets assigned to a LinkedIn episode.

  Example: /search/episode/1
  """
  db = get_db()
  results = db.find_for_episode(episode, unassigned_only=unassigned)

  assets = []
  for _, row in results.iterrows():
    assets.append(_row_to_asset_dict(row))

  return {"episode": episode, "unassigned_only": unassigned, "count": len(assets), "assets": assets}


# ============================================================
# Asset Management Endpoints
# ============================================================

@app.get("/asset/{asset_id}")
async def get_asset(asset_id: str):
  """Get asset metadata by ID."""
  db = get_db()
  asset = db.get_asset(asset_id)

  if asset is None:
    raise HTTPException(status_code=404, detail=f"Asset not found: {asset_id}")

  return _row_to_asset_dict(asset)


@app.get("/asset/{asset_id}/content")
async def get_asset_content(asset_id: str):
  """Download actual asset content (image or video bytes).

  Returns binary content with appropriate Content-Type.
  """
  db = get_db()
  asset = db.get_asset(asset_id)

  if asset is None:
    raise HTTPException(status_code=404, detail=f"Asset not found: {asset_id}")

  if asset['media_type'] == 'image':
    content = asset['image']
    content_type = f"image/{asset['format'] or 'png'}"
  else:
    content = asset['video']
    content_type = f"video/{asset['format'] or 'mp4'}"

  if content is None:
    raise HTTPException(status_code=404, detail=f"Asset has no content")

  return Response(
    content=content,
    media_type=content_type,
    headers={"Content-Disposition": f"attachment; filename={asset['filename']}"}
  )


@app.post("/asset/image")
async def add_image(request: AddImageRequest):
  """Add a new image to the database.

  POST with base64-encoded image and metadata.
  """
  db = get_db()

  try:
    image_bytes = base64.b64decode(request.image_base64)
  except Exception as e:
    raise HTTPException(status_code=400, detail=f"Invalid base64 image: {e}")

  # Write to temp file for processing
  import tempfile
  from pathlib import Path

  suffix = Path(request.filename).suffix or '.png'
  with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
    tmp.write(image_bytes)
    tmp_path = tmp.name

  try:
    asset_id = db.add_image(
      tmp_path,
      source=request.source,
      generation_prompt=request.generation_prompt,
      generation_model=request.generation_model,
      content_type=request.content_type,
      subjects=request.subjects,
      style_tags=request.style_tags,
      quality_rating=request.quality_rating,
      episode_assignments=request.episode_assignments
    )
  finally:
    Path(tmp_path).unlink()

  return {"success": True, "asset_id": asset_id}


@app.post("/asset/video")
async def add_video(request: AddVideoRequest):
  """Add a new video to the database.

  POST with base64-encoded video and metadata.
  """
  db = get_db()

  try:
    video_bytes = base64.b64decode(request.video_base64)
  except Exception as e:
    raise HTTPException(status_code=400, detail=f"Invalid base64 video: {e}")

  thumbnail_bytes = None
  if request.thumbnail_base64:
    try:
      thumbnail_bytes = base64.b64decode(request.thumbnail_base64)
    except Exception:
      pass

  # Write to temp file for processing
  import tempfile
  from pathlib import Path

  suffix = Path(request.filename).suffix or '.mp4'
  with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
    tmp.write(video_bytes)
    tmp_path = tmp.name

  try:
    asset_id = db.add_video(
      tmp_path,
      source=request.source,
      generation_prompt=request.generation_prompt,
      generation_model=request.generation_model,
      content_type=request.content_type,
      subjects=request.subjects,
      style_tags=request.style_tags,
      quality_rating=request.quality_rating,
      episode_assignments=request.episode_assignments
    )
  finally:
    Path(tmp_path).unlink()

  return {"success": True, "asset_id": asset_id}


@app.post("/asset/rate")
async def rate_asset(request: RateAssetRequest):
  """Rate an asset's quality (1-10)."""
  db = get_db()

  if not 1 <= request.rating <= 10:
    raise HTTPException(status_code=400, detail="Rating must be 1-10")

  try:
    db.rate_asset(request.asset_id, request.rating, request.notes)
  except ValueError as e:
    raise HTTPException(status_code=404, detail=str(e))

  return {"success": True, "asset_id": request.asset_id, "rating": request.rating}


@app.post("/asset/assign-episode")
async def assign_episode(request: AssignEpisodeRequest):
  """Assign an asset to a LinkedIn episode."""
  db = get_db()

  if not 1 <= request.episode <= 8:
    raise HTTPException(status_code=400, detail="Episode must be 1-8")

  try:
    db.assign_to_episode(request.asset_id, request.episode)
  except ValueError as e:
    raise HTTPException(status_code=404, detail=str(e))

  return {"success": True, "asset_id": request.asset_id, "episode": request.episode}


# ============================================================
# List Endpoints
# ============================================================

@app.get("/assets")
async def list_assets(
  media_type: Optional[str] = Query(None, description="Filter: 'image' or 'video'"),
  source: Optional[str] = Query(None, description="Filter by source"),
  limit: int = Query(100, description="Maximum results"),
  offset: int = Query(0, description="Offset for pagination")
):
  """List all assets with optional filters."""
  db = get_db()
  df = db.assets_table.search().to_pandas()

  if media_type:
    df = df[df['media_type'] == media_type]
  if source:
    df = df[df['source'] == source]

  # Apply pagination
  total = len(df)
  df = df.iloc[offset:offset + limit]

  assets = []
  for _, row in df.iterrows():
    assets.append(_row_to_asset_dict(row))

  return {"total": total, "offset": offset, "limit": limit, "assets": assets}


# ============================================================
# Backup Endpoint
# ============================================================

@app.post("/backup")
async def backup_to_beta():
  """Backup database to /Volumes/MEDIA on BETA."""
  db = get_db()

  try:
    db.backup_to_beta()
    return {"success": True, "message": "Backed up to /Volumes/MEDIA/media_assets.lance"}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Helper Functions
# ============================================================

def _row_to_asset_dict(row) -> dict:
  """Convert pandas row to asset dict without binary content."""
  import pandas as pd

  def safe_int(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
      return None
    return int(val)

  def safe_float(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
      return None
    return float(val)

  def safe_str(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
      return None
    return str(val)

  def safe_list(val):
    import numpy as np
    if val is None:
      return []
    if isinstance(val, float) and pd.isna(val):
      return []
    # Handle numpy arrays
    if isinstance(val, np.ndarray):
      if val.size == 0:
        return []
      val = val.tolist()
    # Handle empty sequences
    try:
      if len(val) == 0:
        return []
    except TypeError:
      return []
    # Convert numpy types to Python native types
    result = []
    for item in val:
      if isinstance(item, (np.integer, np.int32, np.int64)):
        result.append(int(item))
      elif isinstance(item, (np.floating, np.float32, np.float64)):
        result.append(float(item))
      else:
        result.append(item)
    return result

  return {
    "id": row['id'],
    "filename": row['filename'],
    "source": row['source'],
    "media_type": row['media_type'],
    "width": safe_int(row['width']),
    "height": safe_int(row['height']),
    "duration_seconds": safe_float(row['duration_seconds']),
    "file_size_bytes": safe_int(row['file_size_bytes']),
    "format": safe_str(row['format']),
    "content_type": safe_str(row['content_type']),
    "subjects": safe_list(row['subjects']),
    "style_tags": safe_list(row['style_tags']),
    "quality_rating": safe_int(row['quality_rating']),
    "quality_notes": safe_str(row['quality_notes']),
    "episode_assignments": safe_list(row['episode_assignments']),
    "use_count": safe_int(row['use_count']) or 0,
    "created_at": row['created_at'],
  }


# ============================================================
# Main Entry Point
# ============================================================

def main():
  """Run the API server."""
  print("=" * 60)
  print("ARTHUR Media Database API")
  print("=" * 60)
  print(f"Starting server on http://0.0.0.0:8422")
  print(f"Access from any node: http://alpha:8422")
  print()
  print("Endpoints:")
  print("  GET  /health              - Health check")
  print("  GET  /stats               - Database statistics")
  print("  GET  /search/theme?query= - Theme-based search")
  print("  POST /search/similar      - Image similarity search")
  print("  GET  /search/subject/{s}  - Search by subject")
  print("  GET  /search/episode/{n}  - Search by episode")
  print("  GET  /asset/{id}          - Get asset metadata")
  print("  GET  /asset/{id}/content  - Download asset content")
  print("  POST /asset/image         - Add image")
  print("  POST /asset/video         - Add video")
  print("  POST /asset/rate          - Rate asset")
  print("  POST /asset/assign-episode- Assign to episode")
  print("  GET  /assets              - List all assets")
  print("  POST /backup              - Backup to BETA")
  print("=" * 60)

  uvicorn.run(
    "arthur.media_api:app",
    host="0.0.0.0",
    port=8422,
    reload=False,
    log_level="info"
  )


if __name__ == "__main__":
  main()
