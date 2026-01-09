"""
Output Manager
Handles naming conventions, metadata generation, and storage management

Naming Pattern: {type}_{topic}_{style}_{date}_{sequence}.{ext}

Examples:
  img_ai-workplace-surveillance_editorial_20250104_001.png
  vid_sun-microsystems-legacy_cinematic_20250104_001.mp4
  carousel_ai-workplace-transformation_20250104_001/
"""

from pathlib import Path
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Optional, Literal
import json
import re
import shutil

from ..config import PATHS

class OutputType(str, Enum):
  """Types of output files"""
  IMAGE = "img"
  VIDEO = "vid"
  CAROUSEL = "carousel"
  PROJECT = "project"

@dataclass
class OutputMetadata:
  """Metadata for generated outputs"""
  filename: str
  output_type: OutputType
  topic: str
  style: str
  created_at: str
  prompt: str
  model: str
  backend: str
  duration: Optional[float] = None  # For videos
  resolution: Optional[str] = None
  sequence: int = 1
  project_id: Optional[str] = None
  tags: list[str] = field(default_factory=list)

  def to_dict(self) -> dict:
    """Convert to dictionary for JSON serialization"""
    d = asdict(self)
    d["output_type"] = self.output_type.value
    return d

  def to_json(self) -> str:
    """Convert to JSON string"""
    return json.dumps(self.to_dict(), indent=2)

  @classmethod
  def from_dict(cls, data: dict) -> "OutputMetadata":
    """Create from dictionary"""
    data["output_type"] = OutputType(data["output_type"])
    return cls(**data)

def slugify(text: str) -> str:
  """Convert text to URL-friendly slug"""
  # Lowercase
  text = text.lower()
  # Replace spaces and underscores with hyphens
  text = re.sub(r'[\s_]+', '-', text)
  # Remove non-alphanumeric except hyphens
  text = re.sub(r'[^a-z0-9-]', '', text)
  # Remove multiple consecutive hyphens
  text = re.sub(r'-+', '-', text)
  # Remove leading/trailing hyphens
  text = text.strip('-')
  return text

def generate_filename(
  output_type: OutputType,
  topic: str,
  style: str,
  sequence: int = 1,
  extension: str = None,
  date: datetime = None
) -> str:
  """
  Generate self-documenting filename

  Pattern: {type}_{topic}_{style}_{date}_{sequence}.{ext}

  Args:
    output_type: Type of output (img, vid, carousel)
    topic: Content topic
    style: Visual style
    sequence: Sequence number (001, 002, etc.)
    extension: File extension (auto-determined if None)
    date: Date for filename (defaults to now)

  Returns:
    Formatted filename
  """
  if date is None:
    date = datetime.now()

  date_str = date.strftime("%Y%m%d")
  topic_slug = slugify(topic)[:40]  # Limit length
  style_slug = slugify(style)[:20]

  # Default extensions
  if extension is None:
    extension = {
      OutputType.IMAGE: "png",
      OutputType.VIDEO: "mp4",
      OutputType.CAROUSEL: "",  # Carousels are folders
      OutputType.PROJECT: "drp"  # DaVinci Resolve project
    }.get(output_type, "")

  filename = f"{output_type.value}_{topic_slug}_{style_slug}_{date_str}_{sequence:03d}"

  if extension:
    filename += f".{extension}"

  return filename

def create_metadata(
  filename: str,
  output_type: OutputType,
  topic: str,
  style: str,
  prompt: str,
  model: str,
  backend: str,
  duration: Optional[float] = None,
  resolution: Optional[str] = None,
  sequence: int = 1,
  project_id: Optional[str] = None,
  tags: Optional[list[str]] = None
) -> OutputMetadata:
  """Create metadata object for output"""
  return OutputMetadata(
    filename=filename,
    output_type=output_type,
    topic=topic,
    style=style,
    created_at=datetime.now().isoformat(),
    prompt=prompt,
    model=model,
    backend=backend,
    duration=duration,
    resolution=resolution,
    sequence=sequence,
    project_id=project_id,
    tags=tags or []
  )

class OutputManager:
  """
  Manages output files, naming, and storage

  Usage:
    manager = OutputManager()

    # Generate filename
    filename = manager.generate_filename(
      OutputType.VIDEO,
      topic="task mining expose",
      style="documentary"
    )

    # Save with metadata
    output_path = manager.save_output(
      source_path=Path("/tmp/video.mp4"),
      output_type=OutputType.VIDEO,
      topic="task mining expose",
      style="documentary",
      prompt="A documentary shot...",
      model="HunyuanVideo-1.5",
      backend="GAMMA"
    )

    # Sync to STUDIO volume
    manager.sync_to_studio()
  """

  def __init__(self, base_path: Optional[Path] = None):
    self.base_path = base_path or PATHS.project_root
    self._sequence_cache: dict[str, int] = {}

  def _get_output_dir(self, output_type: OutputType) -> Path:
    """Get output directory for type"""
    dirs = {
      OutputType.IMAGE: PATHS.images_dir,
      OutputType.VIDEO: PATHS.videos_dir,
      OutputType.CAROUSEL: PATHS.carousels_dir,
      OutputType.PROJECT: PATHS.project_root / "projects"
    }
    output_dir = dirs.get(output_type, PATHS.project_root / "outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

  def _get_next_sequence(self, prefix: str, output_dir: Path) -> int:
    """Get next sequence number for prefix in directory"""
    cache_key = f"{output_dir}:{prefix}"

    if cache_key in self._sequence_cache:
      self._sequence_cache[cache_key] += 1
      return self._sequence_cache[cache_key]

    # Find existing files with this prefix
    pattern = f"{prefix}_*"
    existing = list(output_dir.glob(pattern))

    if not existing:
      self._sequence_cache[cache_key] = 1
      return 1

    # Extract sequence numbers
    sequences = []
    for path in existing:
      match = re.search(r'_(\d{3})\.[^.]+$', path.name)
      if match:
        sequences.append(int(match.group(1)))

    next_seq = max(sequences, default=0) + 1
    self._sequence_cache[cache_key] = next_seq
    return next_seq

  def generate_filename(
    self,
    output_type: OutputType,
    topic: str,
    style: str,
    extension: str = None,
    auto_sequence: bool = True
  ) -> str:
    """
    Generate filename with auto-sequencing

    Args:
      output_type: Type of output
      topic: Content topic
      style: Visual style
      extension: File extension
      auto_sequence: Automatically increment sequence

    Returns:
      Generated filename
    """
    output_dir = self._get_output_dir(output_type)
    date_str = datetime.now().strftime("%Y%m%d")
    topic_slug = slugify(topic)[:40]
    style_slug = slugify(style)[:20]

    prefix = f"{output_type.value}_{topic_slug}_{style_slug}_{date_str}"

    if auto_sequence:
      sequence = self._get_next_sequence(prefix, output_dir)
    else:
      sequence = 1

    return generate_filename(
      output_type=output_type,
      topic=topic,
      style=style,
      sequence=sequence,
      extension=extension
    )

  def save_output(
    self,
    source_path: Path,
    output_type: OutputType,
    topic: str,
    style: str,
    prompt: str,
    model: str,
    backend: str,
    duration: Optional[float] = None,
    resolution: Optional[str] = None,
    tags: Optional[list[str]] = None,
    move: bool = False
  ) -> tuple[Path, OutputMetadata]:
    """
    Save output with proper naming and metadata

    Args:
      source_path: Source file path
      output_type: Type of output
      topic: Content topic
      style: Visual style
      prompt: Generation prompt
      model: Model used
      backend: Backend used
      duration: Duration for videos
      resolution: Resolution string
      tags: Optional tags
      move: Move instead of copy

    Returns:
      Tuple of (output_path, metadata)
    """
    output_dir = self._get_output_dir(output_type)
    extension = source_path.suffix.lstrip('.')

    filename = self.generate_filename(
      output_type=output_type,
      topic=topic,
      style=style,
      extension=extension
    )

    output_path = output_dir / filename

    # Copy or move file
    if move:
      shutil.move(str(source_path), str(output_path))
    else:
      shutil.copy2(str(source_path), str(output_path))

    # Create metadata
    metadata = create_metadata(
      filename=filename,
      output_type=output_type,
      topic=topic,
      style=style,
      prompt=prompt,
      model=model,
      backend=backend,
      duration=duration,
      resolution=resolution,
      tags=tags
    )

    # Save metadata sidecar
    metadata_path = output_path.with_suffix(output_path.suffix + '.json')
    metadata_path.write_text(metadata.to_json())

    return output_path, metadata

  def create_carousel_folder(
    self,
    topic: str,
    style: str
  ) -> Path:
    """
    Create carousel folder with proper naming

    Returns:
      Path to carousel folder
    """
    folder_name = self.generate_filename(
      output_type=OutputType.CAROUSEL,
      topic=topic,
      style=style
    )

    carousel_path = PATHS.carousels_dir / folder_name
    carousel_path.mkdir(parents=True, exist_ok=True)

    return carousel_path

  def studio_available(self) -> bool:
    """Check if STUDIO volume is mounted"""
    return PATHS.studio_mount.exists() and PATHS.studio_mount.is_dir()

  def sync_to_studio(
    self,
    output_type: Optional[OutputType] = None,
    since: Optional[datetime] = None
  ) -> list[Path]:
    """
    Sync outputs to STUDIO volume on BETA

    Args:
      output_type: Only sync specific type (None = all)
      since: Only sync files created after this time

    Returns:
      List of synced paths
    """
    if not self.studio_available():
      raise RuntimeError("STUDIO volume not mounted. Mount BETA storage first.")

    synced = []
    types_to_sync = [output_type] if output_type else list(OutputType)

    for otype in types_to_sync:
      source_dir = self._get_output_dir(otype)
      dest_dir = {
        OutputType.IMAGE: PATHS.studio_images,
        OutputType.VIDEO: PATHS.studio_video,
        OutputType.CAROUSEL: PATHS.studio_carousels,
        OutputType.PROJECT: PATHS.studio_mount / "PROJECTS"
      }.get(otype)

      if dest_dir is None:
        continue

      dest_dir.mkdir(parents=True, exist_ok=True)

      for source_file in source_dir.iterdir():
        if source_file.is_file():
          # Check modification time if since specified
          if since and datetime.fromtimestamp(source_file.stat().st_mtime) < since:
            continue

          dest_file = dest_dir / source_file.name

          # Only copy if newer or doesn't exist
          if not dest_file.exists() or source_file.stat().st_mtime > dest_file.stat().st_mtime:
            try:
              # Try copy2 first (preserves metadata)
              shutil.copy2(str(source_file), str(dest_file))
            except OSError:
              # Fall back to basic copy for SMB/network shares
              shutil.copy(str(source_file), str(dest_file))
            synced.append(dest_file)

    return synced

  def list_outputs(
    self,
    output_type: Optional[OutputType] = None,
    days: int = 7,
    limit: int = 50
  ) -> list[dict]:
    """
    List recent outputs

    Args:
      output_type: Filter by type
      days: Only show outputs from last N days
      limit: Maximum number of results

    Returns:
      List of output info dicts
    """
    outputs = []
    cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
    types_to_check = [output_type] if output_type else list(OutputType)

    for otype in types_to_check:
      output_dir = self._get_output_dir(otype)

      for path in output_dir.iterdir():
        if path.is_file() and not path.suffix == '.json':
          mtime = path.stat().st_mtime
          if mtime >= cutoff:
            # Try to load metadata
            meta_path = path.with_suffix(path.suffix + '.json')
            metadata = None
            if meta_path.exists():
              try:
                metadata = json.loads(meta_path.read_text())
              except:
                pass

            outputs.append({
              "path": str(path),
              "filename": path.name,
              "type": otype.value,
              "size_mb": path.stat().st_size / 1024 / 1024,
              "created": datetime.fromtimestamp(mtime).isoformat(),
              "metadata": metadata
            })

    # Sort by creation time, newest first
    outputs.sort(key=lambda x: x["created"], reverse=True)

    return outputs[:limit]
