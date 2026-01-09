"""
LanceDB-powered multi-modal media asset database.

Stores actual images and videos (not just file paths) with CLIP embeddings
for visual similarity search. Database lives on BETA at /Volumes/MEDIA.

Usage:
    from arthur.media_db import MediaDatabase

    db = MediaDatabase()
    db.add_image("/path/to/image.jpg", source="midjourney")
    similar = db.find_similar(reference_image_bytes)
    themed = db.find_by_theme("dramatic tech workspace")
"""

import lancedb
from lancedb.pydantic import LanceModel, Vector
from pathlib import Path
from typing import Optional, List
import uuid
from datetime import datetime
from PIL import Image
import io
import subprocess
import logging

logger = logging.getLogger(__name__)

# Database location - local for atomic operations, backup to /Volumes/MEDIA
# SMB mounts don't support atomic rename operations that LanceDB requires
DEFAULT_DB_PATH = "/Users/arthurdell/ARTHUR/media_assets.lance"
BACKUP_DB_PATH = "/Volumes/MEDIA/media_assets.lance"


class MediaAsset(LanceModel):
  """Schema for media assets stored in LanceDB."""

  # Identity
  id: str
  filename: str

  # Actual content stored as bytes
  image: Optional[bytes] = None
  video: Optional[bytes] = None
  thumbnail: Optional[bytes] = None

  # CLIP embedding for visual similarity search (512-dim for ViT-B-32)
  vector: Vector(512)

  # Generation metadata
  source: str  # 'midjourney' | 'gemini' | 'press_kit' | 'gamma' | 'screen_capture'
  generation_prompt: Optional[str] = None
  generation_model: Optional[str] = None
  generation_time_seconds: Optional[float] = None
  generation_cost_usd: Optional[float] = None

  # Technical specs
  width: Optional[int] = None
  height: Optional[int] = None
  duration_seconds: Optional[float] = None
  file_size_bytes: Optional[int] = None
  format: Optional[str] = None

  # Content classification
  media_type: str  # 'image' | 'video'
  content_type: Optional[str] = None  # 'product_hero' | 'workspace' | 'concept' | etc.
  subjects: List[str] = []  # ['mac_studio', 'dgx_spark']
  style_tags: List[str] = []  # ['cinematic', 'minimal', 'dramatic']

  # Quality rating (1-10)
  quality_rating: Optional[int] = None
  quality_notes: Optional[str] = None

  # Usage tracking
  episode_assignments: List[int] = []  # [1, 2, 8] for LinkedIn episodes
  use_count: int = 0
  created_at: str
  last_used_at: Optional[str] = None


class LinkedInProject(LanceModel):
  """Schema for LinkedIn project tracking."""

  id: str
  project_name: str
  theme: str
  asset_ids: List[str] = []
  created_at: str
  published_at: Optional[str] = None
  engagement_likes: int = 0
  engagement_comments: int = 0
  engagement_shares: int = 0


class MediaDatabase:
  """LanceDB-powered multi-modal media asset database."""

  def __init__(self, db_path: str = DEFAULT_DB_PATH):
    """Initialize database connection.

    Args:
        db_path: Path to LanceDB database file. Defaults to /Volumes/MEDIA/media_assets.lance
    """
    self.db_path = Path(db_path)
    self.db = lancedb.connect(str(db_path))
    self._clip_model = None
    self._clip_preprocess = None
    self._tokenizer = None
    self._init_tables()

  def _init_tables(self):
    """Initialize database tables if they don't exist."""
    import pyarrow as pa

    existing_tables = self.db.table_names()

    if "assets" not in existing_tables:
      logger.info("Creating assets table with proper schema...")
      # Define schema explicitly to avoid null type issues
      schema = pa.schema([
        pa.field("id", pa.string()),
        pa.field("filename", pa.string()),
        pa.field("image", pa.large_binary()),  # For storing image bytes
        pa.field("video", pa.large_binary()),  # For storing video bytes
        pa.field("thumbnail", pa.large_binary()),  # For storing thumbnail bytes
        pa.field("vector", pa.list_(pa.float32(), 512)),  # CLIP embedding
        pa.field("source", pa.string()),
        pa.field("generation_prompt", pa.string()),
        pa.field("generation_model", pa.string()),
        pa.field("generation_time_seconds", pa.float64()),
        pa.field("generation_cost_usd", pa.float64()),
        pa.field("width", pa.int32()),
        pa.field("height", pa.int32()),
        pa.field("duration_seconds", pa.float64()),
        pa.field("file_size_bytes", pa.int64()),
        pa.field("format", pa.string()),
        pa.field("media_type", pa.string()),
        pa.field("content_type", pa.string()),
        pa.field("subjects", pa.list_(pa.string())),
        pa.field("style_tags", pa.list_(pa.string())),
        pa.field("quality_rating", pa.int32()),
        pa.field("quality_notes", pa.string()),
        pa.field("episode_assignments", pa.list_(pa.int32())),
        pa.field("use_count", pa.int32()),
        pa.field("created_at", pa.string()),
        pa.field("last_used_at", pa.string()),
      ])
      # Create empty table with schema
      empty_table = pa.table({f.name: pa.array([], type=f.type) for f in schema})
      self.assets_table = self.db.create_table("assets", data=empty_table, mode="overwrite")
    else:
      self.assets_table = self.db.open_table("assets")

    if "projects" not in existing_tables:
      logger.info("Creating projects table...")
      projects_schema = pa.schema([
        pa.field("id", pa.string()),
        pa.field("project_name", pa.string()),
        pa.field("theme", pa.string()),
        pa.field("asset_ids", pa.list_(pa.string())),
        pa.field("created_at", pa.string()),
        pa.field("published_at", pa.string()),
        pa.field("engagement_likes", pa.int32()),
        pa.field("engagement_comments", pa.int32()),
        pa.field("engagement_shares", pa.int32()),
      ])
      empty_projects = pa.table({f.name: pa.array([], type=f.type) for f in projects_schema})
      self.projects_table = self.db.create_table("projects", data=empty_projects, mode="overwrite")
    else:
      self.projects_table = self.db.open_table("projects")

  def _get_clip_model(self):
    """Lazy-load CLIP model for embeddings."""
    if self._clip_model is None:
      import open_clip
      import torch

      logger.info("Loading CLIP model (ViT-B-32)...")
      self._clip_model, _, self._clip_preprocess = open_clip.create_model_and_transforms(
        'ViT-B-32', pretrained='openai'
      )
      self._tokenizer = open_clip.get_tokenizer('ViT-B-32')

      # Use MPS if available (Apple Silicon)
      if torch.backends.mps.is_available():
        self._clip_model = self._clip_model.to('mps')
        logger.info("CLIP model loaded on MPS (Apple Silicon)")
      else:
        logger.info("CLIP model loaded on CPU")

    return self._clip_model, self._clip_preprocess, self._tokenizer

  def _get_image_embedding(self, img: Image.Image) -> list:
    """Generate CLIP embedding for an image."""
    import torch

    model, preprocess, _ = self._get_clip_model()
    device = 'mps' if torch.backends.mps.is_available() else 'cpu'

    # Preprocess and get embedding
    image_tensor = preprocess(img).unsqueeze(0).to(device)

    with torch.no_grad():
      embedding = model.encode_image(image_tensor)
      embedding = embedding / embedding.norm(dim=-1, keepdim=True)  # Normalize

    return embedding.cpu().numpy().flatten().tolist()

  def _get_text_embedding(self, text: str) -> list:
    """Generate CLIP embedding for text (for text-to-image search)."""
    import torch

    model, _, tokenizer = self._get_clip_model()
    device = 'mps' if torch.backends.mps.is_available() else 'cpu'

    # Tokenize and get embedding
    text_tokens = tokenizer([text]).to(device)

    with torch.no_grad():
      embedding = model.encode_text(text_tokens)
      embedding = embedding / embedding.norm(dim=-1, keepdim=True)  # Normalize

    return embedding.cpu().numpy().flatten().tolist()

  def _extract_video_thumbnail(self, video_path: str) -> Optional[bytes]:
    """Extract thumbnail from video using ffmpeg."""
    try:
      import tempfile
      with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        tmp_path = tmp.name

      # Extract frame at 1 second
      result = subprocess.run([
        'ffmpeg', '-i', video_path,
        '-ss', '00:00:01',
        '-vframes', '1',
        '-y', tmp_path
      ], capture_output=True, timeout=30)

      if result.returncode == 0 and Path(tmp_path).exists():
        with open(tmp_path, 'rb') as f:
          thumbnail_bytes = f.read()
        Path(tmp_path).unlink()
        return thumbnail_bytes
    except Exception as e:
      logger.warning(f"Failed to extract thumbnail: {e}")

    return None

  def add_image(
    self,
    image_path: str,
    source: str,
    generation_prompt: str = None,
    generation_model: str = None,
    content_type: str = None,
    subjects: List[str] = None,
    style_tags: List[str] = None,
    quality_rating: int = None,
    episode_assignments: List[int] = None,
    **kwargs
  ) -> str:
    """Add image to database with auto-generated CLIP embedding.

    Args:
        image_path: Path to image file
        source: Origin of image ('midjourney', 'gemini', 'press_kit', etc.)
        generation_prompt: The prompt used to generate (if AI-generated)
        generation_model: Model used ('midjourney-v6.1', 'nano-banana-pro', etc.)
        content_type: Type of content ('product_hero', 'workspace', 'concept')
        subjects: List of subjects in image (['mac_studio', 'dgx_spark'])
        style_tags: Style descriptors (['cinematic', 'minimal'])
        quality_rating: Quality score 1-10
        episode_assignments: LinkedIn episode numbers [1, 2, 8]

    Returns:
        Asset ID (UUID)
    """
    path = Path(image_path)
    if not path.exists():
      raise FileNotFoundError(f"Image not found: {image_path}")

    # Read image bytes
    with open(path, 'rb') as f:
      image_bytes = f.read()

    # Open image for embedding and metadata
    img = Image.open(io.BytesIO(image_bytes))
    width, height = img.size

    # Generate CLIP embedding
    logger.info(f"Generating embedding for {path.name}...")
    embedding = self._get_image_embedding(img)

    # Determine format
    fmt = path.suffix.lower().lstrip('.')
    if fmt == 'jpg':
      fmt = 'jpeg'

    asset_id = str(uuid.uuid4())

    asset_data = {
      "id": asset_id,
      "filename": path.name,
      "image": image_bytes,
      "video": None,
      "thumbnail": None,
      "vector": embedding,
      "source": source,
      "generation_prompt": generation_prompt,
      "generation_model": generation_model,
      "generation_time_seconds": kwargs.get('generation_time_seconds'),
      "generation_cost_usd": kwargs.get('generation_cost_usd'),
      "width": width,
      "height": height,
      "duration_seconds": None,
      "file_size_bytes": len(image_bytes),
      "format": fmt,
      "media_type": "image",
      "content_type": content_type,
      "subjects": subjects or [],
      "style_tags": style_tags or [],
      "quality_rating": quality_rating,
      "quality_notes": kwargs.get('quality_notes'),
      "episode_assignments": episode_assignments or [],
      "use_count": 0,
      "created_at": datetime.now().isoformat(),
      "last_used_at": None,
    }

    self.assets_table.add([asset_data])
    logger.info(f"Added image: {path.name} (id={asset_id[:8]}...)")

    return asset_id

  def add_video(
    self,
    video_path: str,
    source: str,
    generation_prompt: str = None,
    generation_model: str = None,
    content_type: str = None,
    subjects: List[str] = None,
    style_tags: List[str] = None,
    quality_rating: int = None,
    episode_assignments: List[int] = None,
    **kwargs
  ) -> str:
    """Add video to database with thumbnail-based CLIP embedding.

    Args:
        video_path: Path to video file
        source: Origin of video ('gamma', 'gemini_veo', 'wan26', etc.)
        generation_prompt: The prompt used to generate
        generation_model: Model used ('hunyuanvideo-1.5', 'veo-3.1', etc.)
        content_type: Type of content ('reveal', 'animation', 'workflow')
        subjects: List of subjects (['mac_studio', 'neural_network'])
        style_tags: Style descriptors (['cinematic', 'abstract'])
        quality_rating: Quality score 1-10
        episode_assignments: LinkedIn episode numbers [1, 2, 8]

    Returns:
        Asset ID (UUID)
    """
    path = Path(video_path)
    if not path.exists():
      raise FileNotFoundError(f"Video not found: {video_path}")

    # Read video bytes
    with open(path, 'rb') as f:
      video_bytes = f.read()

    # Extract thumbnail for embedding
    logger.info(f"Extracting thumbnail from {path.name}...")
    thumbnail_bytes = self._extract_video_thumbnail(str(path))

    # Generate embedding from thumbnail
    embedding = [0.0] * 512  # Default if no thumbnail
    if thumbnail_bytes:
      img = Image.open(io.BytesIO(thumbnail_bytes))
      embedding = self._get_image_embedding(img)
    else:
      logger.warning(f"Could not extract thumbnail for {path.name}, using zero embedding")

    # Get video duration using ffprobe
    duration = None
    try:
      result = subprocess.run([
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(path)
      ], capture_output=True, text=True, timeout=30)
      if result.returncode == 0:
        duration = float(result.stdout.strip())
    except Exception as e:
      logger.warning(f"Could not get video duration: {e}")

    fmt = path.suffix.lower().lstrip('.')
    asset_id = str(uuid.uuid4())

    asset_data = {
      "id": asset_id,
      "filename": path.name,
      "image": None,
      "video": video_bytes,
      "thumbnail": thumbnail_bytes,
      "vector": embedding,
      "source": source,
      "generation_prompt": generation_prompt,
      "generation_model": generation_model,
      "generation_time_seconds": kwargs.get('generation_time_seconds'),
      "generation_cost_usd": kwargs.get('generation_cost_usd'),
      "width": kwargs.get('width'),
      "height": kwargs.get('height'),
      "duration_seconds": duration,
      "file_size_bytes": len(video_bytes),
      "format": fmt,
      "media_type": "video",
      "content_type": content_type,
      "subjects": subjects or [],
      "style_tags": style_tags or [],
      "quality_rating": quality_rating,
      "quality_notes": kwargs.get('quality_notes'),
      "episode_assignments": episode_assignments or [],
      "use_count": 0,
      "created_at": datetime.now().isoformat(),
      "last_used_at": None,
    }

    self.assets_table.add([asset_data])
    dur_str = f"{duration:.1f}s" if duration else "unknown"
    logger.info(f"Added video: {path.name} (id={asset_id[:8]}..., duration={dur_str})")

    return asset_id

  def find_similar(self, reference_image: bytes, limit: int = 10, media_type: str = None):
    """Find visually similar assets to a reference image.

    Args:
        reference_image: Image bytes to search for
        limit: Maximum results to return
        media_type: Filter by 'image' or 'video' (None for both)

    Returns:
        pandas DataFrame of matching assets
    """
    img = Image.open(io.BytesIO(reference_image))
    embedding = self._get_image_embedding(img)

    query = self.assets_table.search(embedding).limit(limit)

    if media_type:
      query = query.where(f"media_type = '{media_type}'")

    return query.to_pandas()

  def find_by_theme(self, theme_description: str, limit: int = 20, min_quality: int = None):
    """Find assets matching a text description using CLIP text-to-image.

    Args:
        theme_description: Natural language description (e.g., "dramatic tech workspace")
        limit: Maximum results to return
        min_quality: Minimum quality rating filter

    Returns:
        pandas DataFrame of matching assets
    """
    embedding = self._get_text_embedding(theme_description)

    query = self.assets_table.search(embedding).limit(limit)

    if min_quality is not None:
      query = query.where(f"quality_rating >= {min_quality}")

    return query.to_pandas()

  def find_by_subject(self, subject: str, media_type: str = None) -> list:
    """Find all assets containing a specific subject.

    Args:
        subject: Subject to search for (e.g., 'mac_studio')
        media_type: Filter by 'image' or 'video'

    Returns:
        pandas DataFrame of matching assets
    """
    # LanceDB array contains query
    query = self.assets_table.search().where(f"array_contains(subjects, '{subject}')")

    if media_type:
      query = query.where(f"media_type = '{media_type}'")

    return query.to_pandas()

  def find_for_episode(self, episode: int, unassigned_only: bool = False):
    """Find assets assigned to or suitable for a specific episode.

    Args:
        episode: Episode number (1-8)
        unassigned_only: If True, find assets NOT yet assigned to this episode

    Returns:
        pandas DataFrame of matching assets
    """
    if unassigned_only:
      return self.assets_table.search().where(
        f"NOT array_contains(episode_assignments, {episode})"
      ).to_pandas()
    else:
      return self.assets_table.search().where(
        f"array_contains(episode_assignments, {episode})"
      ).to_pandas()

  def rate_asset(self, asset_id: str, rating: int, notes: str = None):
    """Rate an asset's quality (1-10).

    Args:
        asset_id: Asset UUID
        rating: Quality score 1-10
        notes: Optional quality notes
    """
    if not 1 <= rating <= 10:
      raise ValueError("Rating must be between 1 and 10")

    self.assets_table.update(
      where=f"id = '{asset_id}'",
      values={"quality_rating": rating, "quality_notes": notes}
    )
    logger.info(f"Rated asset {asset_id[:8]}... as {rating}/10")

  def assign_to_episode(self, asset_id: str, episode: int):
    """Assign an asset to a LinkedIn episode.

    Args:
        asset_id: Asset UUID
        episode: Episode number (1-8)
    """
    # Get current assignments
    result = self.assets_table.search().where(f"id = '{asset_id}'").limit(1).to_pandas()
    if len(result) == 0:
      raise ValueError(f"Asset not found: {asset_id}")

    current = result.iloc[0]['episode_assignments']
    if episode not in current:
      current.append(episode)
      self.assets_table.update(
        where=f"id = '{asset_id}'",
        values={"episode_assignments": current}
      )
      logger.info(f"Assigned asset {asset_id[:8]}... to Episode {episode}")

  def get_asset(self, asset_id: str):
    """Get a single asset by ID.

    Returns:
        pandas Series of asset data, or None if not found
    """
    result = self.assets_table.search().where(f"id = '{asset_id}'").limit(1).to_pandas()
    return result.iloc[0] if len(result) > 0 else None

  def get_image_bytes(self, asset_id: str) -> Optional[bytes]:
    """Retrieve actual image content from database."""
    asset = self.get_asset(asset_id)
    return asset['image'] if asset is not None else None

  def get_video_bytes(self, asset_id: str) -> Optional[bytes]:
    """Retrieve actual video content from database."""
    asset = self.get_asset(asset_id)
    return asset['video'] if asset is not None else None

  def export_asset(self, asset_id: str, output_path: str):
    """Export an asset from database to file.

    Args:
        asset_id: Asset UUID
        output_path: Path to save the file
    """
    asset = self.get_asset(asset_id)
    if asset is None:
      raise ValueError(f"Asset not found: {asset_id}")

    if asset['media_type'] == 'image':
      content = asset['image']
    else:
      content = asset['video']

    if content is None:
      raise ValueError(f"Asset {asset_id} has no content")

    with open(output_path, 'wb') as f:
      f.write(content)

    logger.info(f"Exported {asset['filename']} to {output_path}")

  def import_directory(
    self,
    dir_path: str,
    source: str,
    recursive: bool = True,
    content_type: str = None,
    subjects: List[str] = None,
    style_tags: List[str] = None
  ) -> int:
    """Bulk import all images/videos from a directory.

    Args:
        dir_path: Directory to import from
        source: Source identifier for all imports
        recursive: Whether to search subdirectories
        content_type: Optional content type for all imports
        subjects: Optional subjects for all imports
        style_tags: Optional style tags for all imports

    Returns:
        Number of assets imported
    """
    path = Path(dir_path)
    if not path.exists():
      raise FileNotFoundError(f"Directory not found: {dir_path}")

    pattern = '**/*' if recursive else '*'

    image_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.gif'}
    video_extensions = {'.mp4', '.mov', '.webm', '.avi'}

    count = 0
    for file in path.glob(pattern):
      if not file.is_file():
        continue

      suffix = file.suffix.lower()

      try:
        if suffix in image_extensions:
          self.add_image(
            str(file),
            source=source,
            content_type=content_type,
            subjects=subjects,
            style_tags=style_tags
          )
          count += 1
        elif suffix in video_extensions:
          self.add_video(
            str(file),
            source=source,
            content_type=content_type,
            subjects=subjects,
            style_tags=style_tags
          )
          count += 1
      except Exception as e:
        logger.error(f"Failed to import {file}: {e}")

    logger.info(f"Imported {count} assets from {dir_path}")
    return count

  def stats(self) -> dict:
    """Get database statistics.

    Returns:
        Dictionary of stats (counts, sizes, etc.)
    """
    df = self.assets_table.search().to_pandas()

    if len(df) == 0:
      return {
        "total_assets": 0,
        "images": 0,
        "videos": 0,
        "total_size_mb": 0,
        "sources": {},
        "avg_quality": None,
        "rated_count": 0,
        "unrated_count": 0,
      }

    images = df[df['media_type'] == 'image']
    videos = df[df['media_type'] == 'video']

    total_size = df['file_size_bytes'].sum()
    sources = df['source'].value_counts().to_dict()

    rated = df[df['quality_rating'].notna()]
    avg_quality = rated['quality_rating'].mean() if len(rated) > 0 else None

    return {
      "total_assets": len(df),
      "images": len(images),
      "videos": len(videos),
      "total_size_mb": round(total_size / (1024 * 1024), 2),
      "sources": sources,
      "avg_quality": round(avg_quality, 1) if avg_quality else None,
      "rated_count": len(rated),
      "unrated_count": len(df) - len(rated),
    }

  def backup_to_beta(self, dest_path: str = BACKUP_DB_PATH):
    """Backup database to /Volumes/MEDIA on BETA.

    LanceDB requires atomic file operations that SMB mounts don't support,
    so we run locally and sync to BETA for backup.

    Args:
        dest_path: Destination path (default: /Volumes/MEDIA/media_assets.lance)
    """
    import shutil

    src = Path(self.db_path)
    dest = Path(dest_path)

    if not src.exists():
      raise FileNotFoundError(f"Source database not found: {src}")

    # Ensure destination directory exists
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Copy entire directory (LanceDB is a directory, not a file)
    if dest.exists():
      shutil.rmtree(dest)
    shutil.copytree(src, dest)

    logger.info(f"Backed up database to {dest}")


# CLI interface
def main():
  """CLI entry point for media_db commands."""
  import argparse
  import json

  parser = argparse.ArgumentParser(description="LanceDB Media Asset Database")
  subparsers = parser.add_subparsers(dest='command', help='Commands')

  # Import command
  import_parser = subparsers.add_parser('import', help='Import directory')
  import_parser.add_argument('path', help='Directory to import')
  import_parser.add_argument('--source', required=True, help='Source identifier')
  import_parser.add_argument('--content-type', help='Content type')
  import_parser.add_argument('--subjects', nargs='+', help='Subject tags')
  import_parser.add_argument('--styles', nargs='+', help='Style tags')

  # Search command
  search_parser = subparsers.add_parser('search', help='Search by theme')
  search_parser.add_argument('query', help='Theme description')
  search_parser.add_argument('--limit', type=int, default=20, help='Max results')
  search_parser.add_argument('--min-quality', type=int, help='Minimum quality rating')

  # Similar command
  similar_parser = subparsers.add_parser('similar', help='Find similar images')
  similar_parser.add_argument('image', help='Reference image path')
  similar_parser.add_argument('--limit', type=int, default=10, help='Max results')

  # Rate command
  rate_parser = subparsers.add_parser('rate', help='Rate an asset')
  rate_parser.add_argument('asset_id', help='Asset ID')
  rate_parser.add_argument('--rating', type=int, required=True, help='Rating 1-10')
  rate_parser.add_argument('--notes', help='Quality notes')

  # Export command
  export_parser = subparsers.add_parser('export', help='Export asset to file')
  export_parser.add_argument('asset_id', help='Asset ID')
  export_parser.add_argument('--output', required=True, help='Output path')

  # Stats command
  subparsers.add_parser('stats', help='Show database stats')

  args = parser.parse_args()

  # Set up logging
  logging.basicConfig(level=logging.INFO, format='%(message)s')

  db = MediaDatabase()

  if args.command == 'import':
    count = db.import_directory(
      args.path,
      source=args.source,
      content_type=args.content_type,
      subjects=args.subjects,
      style_tags=args.styles
    )
    print(f"Imported {count} assets")

  elif args.command == 'search':
    results = db.find_by_theme(
      args.query,
      limit=args.limit,
      min_quality=args.min_quality
    )
    for _, row in results.iterrows():
      print(f"{row['id'][:8]}... | {row['filename']} | {row['source']} | Q:{row['quality_rating'] or 'N/A'}")

  elif args.command == 'similar':
    with open(args.image, 'rb') as f:
      ref_bytes = f.read()
    results = db.find_similar(ref_bytes, limit=args.limit)
    for _, row in results.iterrows():
      print(f"{row['id'][:8]}... | {row['filename']} | {row['source']} | Q:{row['quality_rating'] or 'N/A'}")

  elif args.command == 'rate':
    db.rate_asset(args.asset_id, args.rating, args.notes)
    print(f"Rated {args.asset_id[:8]}... as {args.rating}/10")

  elif args.command == 'export':
    db.export_asset(args.asset_id, args.output)
    print(f"Exported to {args.output}")

  elif args.command == 'stats':
    stats = db.stats()
    print(json.dumps(stats, indent=2))

  else:
    parser.print_help()


if __name__ == "__main__":
  main()
