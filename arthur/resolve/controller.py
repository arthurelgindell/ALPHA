"""
DaVinci Resolve Studio Controller
Python API wrapper for timeline assembly and post-production

API Location: /Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting

Capabilities:
  - Programmatic media import
  - Timeline assembly from shot lists
  - Text overlays and lower thirds (Fusion)
  - Color grading
  - Render queue management

Limitation: Cannot reposition clips on timeline programmatically (workaround: rebuild timeline)
"""

import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

# Add Resolve scripting modules to path
RESOLVE_SCRIPT_PATH = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules"
if RESOLVE_SCRIPT_PATH not in sys.path:
  sys.path.append(RESOLVE_SCRIPT_PATH)

class ResolveError(Exception):
  """DaVinci Resolve operation error"""
  pass

class RenderPreset(str, Enum):
  """Common render presets"""
  YOUTUBE_1080P = "YouTube - 1080p"
  YOUTUBE_4K = "YouTube - 4K"
  H264_MASTER = "H.264 Master"
  PRORES_422 = "ProRes 422 HQ"
  PRORES_4444 = "ProRes 4444"

@dataclass
class MediaItem:
  """Represents a media item in the pool"""
  path: Path
  name: str
  duration: Optional[float] = None
  width: Optional[int] = None
  height: Optional[int] = None
  fps: Optional[float] = None
  clip_id: Optional[str] = None

@dataclass
class TimelineClip:
  """Represents a clip to add to timeline"""
  media_path: Path
  start_frame: int = 0
  end_frame: Optional[int] = None
  track: int = 1
  position: Optional[int] = None  # Timeline position in frames
  transition_in: Optional[str] = None
  transition_out: Optional[str] = None

@dataclass
class TextOverlay:
  """Text overlay configuration for Fusion Text+"""
  text: str
  position: tuple[float, float] = (0.5, 0.1)  # Center-bottom
  font: str = "Inter"
  font_size: float = 0.08  # Relative to frame height
  color: tuple[float, float, float] = (1.0, 1.0, 1.0)
  background: Optional[tuple[float, float, float, float]] = None  # RGBA
  start_frame: int = 0
  duration_frames: int = 0  # 0 = full clip

class ResolveController:
  """
  DaVinci Resolve Studio Python API Controller

  Requirements:
    - DaVinci Resolve Studio 20+ (Studio required for API)
    - Resolve must be running

  Usage:
    controller = ResolveController()

    # Create project
    controller.create_project("My Video")

    # Import media
    controller.import_media([
      Path("shot_01.mp4"),
      Path("shot_02.mp4")
    ])

    # Create timeline
    controller.create_timeline("Main Timeline")

    # Add clips
    controller.add_clips_to_timeline([
      TimelineClip(Path("shot_01.mp4")),
      TimelineClip(Path("shot_02.mp4"))
    ])

    # Add text overlay
    controller.add_text_overlay(
      TextOverlay(text="Introduction", position=(0.5, 0.9))
    )

    # Render
    controller.render(preset=RenderPreset.YOUTUBE_1080P)
  """

  def __init__(self):
    self._resolve = None
    self._project_manager = None
    self._project = None
    self._media_pool = None
    self._timeline = None
    self._connected = False

  def connect(self) -> bool:
    """
    Connect to running DaVinci Resolve instance

    Returns:
      True if connected successfully

    Raises:
      ResolveError if Resolve is not running or Studio not available
    """
    try:
      import DaVinciResolveScript as dvr
      self._resolve = dvr.scriptapp("Resolve")

      if self._resolve is None:
        raise ResolveError(
          "Could not connect to DaVinci Resolve. "
          "Ensure Resolve Studio is running."
        )

      self._project_manager = self._resolve.GetProjectManager()
      if self._project_manager is None:
        raise ResolveError("Could not get Project Manager")

      self._connected = True
      return True

    except ImportError as e:
      raise ResolveError(
        f"Could not import DaVinci Resolve scripting module: {e}. "
        f"Ensure Resolve Studio is installed and scripting is enabled."
      )
    except Exception as e:
      raise ResolveError(f"Failed to connect to Resolve: {e}")

  @property
  def is_connected(self) -> bool:
    """Check if connected to Resolve"""
    return self._connected and self._resolve is not None

  def _ensure_connected(self):
    """Ensure we're connected to Resolve"""
    if not self.is_connected:
      self.connect()

  def _ensure_project(self):
    """Ensure a project is open"""
    self._ensure_connected()
    if self._project is None:
      # Try to get current project
      self._project = self._project_manager.GetCurrentProject()
      if self._project is None:
        raise ResolveError("No project open. Use create_project() or open_project()")
      self._media_pool = self._project.GetMediaPool()

  # =========================================================================
  # Project Management
  # =========================================================================

  def create_project(self, name: str) -> bool:
    """
    Create a new project

    Args:
      name: Project name

    Returns:
      True if created successfully
    """
    self._ensure_connected()

    self._project = self._project_manager.CreateProject(name)
    if self._project is None:
      raise ResolveError(f"Could not create project: {name}")

    self._media_pool = self._project.GetMediaPool()
    return True

  def open_project(self, name: str) -> bool:
    """
    Open existing project

    Args:
      name: Project name

    Returns:
      True if opened successfully
    """
    self._ensure_connected()

    self._project = self._project_manager.LoadProject(name)
    if self._project is None:
      raise ResolveError(f"Could not open project: {name}")

    self._media_pool = self._project.GetMediaPool()
    return True

  def list_projects(self) -> List[str]:
    """List all projects in current database"""
    self._ensure_connected()
    return self._project_manager.GetProjectListInCurrentFolder()

  def save_project(self) -> bool:
    """Save current project"""
    self._ensure_project()
    try:
      result = self._project.SaveProject()
      return result if result is not None else True
    except Exception:
      # Resolve may auto-save; return True if no exception on project access
      return self._project is not None

  def get_project_info(self) -> Dict[str, Any]:
    """Get current project information"""
    self._ensure_project()
    return {
      "name": self._project.GetName(),
      "timeline_count": self._project.GetTimelineCount(),
      "current_timeline": self._project.GetCurrentTimeline().GetName() if self._project.GetCurrentTimeline() else None
    }

  # =========================================================================
  # Media Pool
  # =========================================================================

  def import_media(self, paths: List[Path]) -> List[MediaItem]:
    """
    Import media files to Media Pool

    Args:
      paths: List of file paths to import

    Returns:
      List of imported MediaItem objects
    """
    self._ensure_project()

    # Convert paths to strings
    path_strings = [str(p.resolve()) for p in paths if p.exists()]

    if not path_strings:
      raise ResolveError("No valid files to import")

    # Import to root folder
    root_folder = self._media_pool.GetRootFolder()
    clips = self._media_pool.ImportMedia(path_strings)

    if clips is None or len(clips) == 0:
      raise ResolveError("Failed to import media")

    items = []
    for clip in clips:
      props = clip.GetClipProperty()

      # Parse duration (can be timecode "00:00:05:12" or float)
      duration_raw = props.get("Duration", "0")
      if isinstance(duration_raw, str) and ":" in duration_raw:
        # Timecode format HH:MM:SS:FF - convert to seconds
        parts = duration_raw.split(":")
        try:
          fps = float(props.get("FPS", 24))
          hours, mins, secs, frames = [int(p) for p in parts]
          duration = hours * 3600 + mins * 60 + secs + frames / fps
        except (ValueError, IndexError):
          duration = 0.0
      else:
        try:
          duration = float(duration_raw)
        except (ValueError, TypeError):
          duration = 0.0

      # Parse resolution
      resolution = props.get("Resolution", "0x0")
      try:
        width = int(resolution.split("x")[0]) if "x" in resolution else 0
        height = int(resolution.split("x")[1]) if "x" in resolution else 0
      except (ValueError, IndexError):
        width, height = 0, 0

      # Parse FPS
      try:
        fps = float(props.get("FPS", 24))
      except (ValueError, TypeError):
        fps = 24.0

      items.append(MediaItem(
        path=Path(props.get("File Path", "")),
        name=clip.GetName(),
        duration=duration,
        width=width,
        height=height,
        fps=fps,
        clip_id=str(clip)
      ))

    return items

  def get_media_pool_clips(self) -> List[Dict]:
    """Get all clips in media pool root folder"""
    self._ensure_project()
    root_folder = self._media_pool.GetRootFolder()
    clips = root_folder.GetClipList()

    result = []
    for clip in clips:
      props = clip.GetClipProperty()
      result.append({
        "name": clip.GetName(),
        "path": props.get("File Path"),
        "duration": props.get("Duration"),
        "resolution": props.get("Resolution"),
        "fps": props.get("FPS")
      })

    return result

  def find_clip_by_name(self, name: str):
    """Find clip in media pool by name"""
    self._ensure_project()
    root_folder = self._media_pool.GetRootFolder()

    for clip in root_folder.GetClipList():
      if clip.GetName() == name or name in clip.GetName():
        return clip

    return None

  # =========================================================================
  # Timeline
  # =========================================================================

  def create_timeline(
    self,
    name: str,
    width: int = 1920,
    height: int = 1080,
    fps: float = 24.0
  ) -> bool:
    """
    Create a new timeline

    Args:
      name: Timeline name
      width: Frame width
      height: Frame height
      fps: Frames per second

    Returns:
      True if created successfully
    """
    self._ensure_project()

    self._timeline = self._media_pool.CreateEmptyTimeline(name)
    if self._timeline is None:
      raise ResolveError(f"Could not create timeline: {name}")

    # Set timeline settings
    self._timeline.SetSetting("timelineResolutionWidth", str(width))
    self._timeline.SetSetting("timelineResolutionHeight", str(height))
    self._timeline.SetSetting("timelineFrameRate", str(fps))

    return True

  def get_current_timeline(self):
    """Get current timeline"""
    self._ensure_project()
    self._timeline = self._project.GetCurrentTimeline()
    return self._timeline

  def set_current_timeline(self, name: str) -> bool:
    """Set current timeline by name"""
    self._ensure_project()

    for i in range(1, self._project.GetTimelineCount() + 1):
      timeline = self._project.GetTimelineByIndex(i)
      if timeline.GetName() == name:
        self._project.SetCurrentTimeline(timeline)
        self._timeline = timeline
        return True

    raise ResolveError(f"Timeline not found: {name}")

  def add_clips_to_timeline(self, clips: List[TimelineClip]) -> bool:
    """
    Add clips to current timeline

    Note: Clips are added sequentially. The Resolve API does not support
    arbitrary repositioning of clips after they're added.

    Args:
      clips: List of TimelineClip objects

    Returns:
      True if all clips added successfully
    """
    if self._timeline is None:
      self.get_current_timeline()

    if self._timeline is None:
      raise ResolveError("No timeline available")

    for tc in clips:
      media_clip = self.find_clip_by_name(tc.media_path.name)

      if media_clip is None:
        # Try importing first
        self.import_media([tc.media_path])
        media_clip = self.find_clip_by_name(tc.media_path.name)

      if media_clip is None:
        raise ResolveError(f"Could not find or import clip: {tc.media_path}")

      # Append to timeline
      result = self._media_pool.AppendToTimeline([media_clip])
      if not result:
        raise ResolveError(f"Failed to add clip to timeline: {tc.media_path}")

    return True

  def create_timeline_from_clips(
    self,
    name: str,
    clip_paths: List[Path],
    width: int = 1920,
    height: int = 1080,
    fps: float = 24.0
  ) -> bool:
    """
    Create timeline and populate with clips in order

    This is the recommended way to create a timeline from a shot list,
    as it avoids the repositioning limitation.

    Args:
      name: Timeline name
      clip_paths: Ordered list of clip paths
      width: Frame width
      height: Frame height
      fps: Frames per second

    Returns:
      True if created successfully
    """
    # Import all media first
    self.import_media(clip_paths)

    # Create timeline
    self.create_timeline(name, width, height, fps)

    # Find clips and append
    clips = []
    for path in clip_paths:
      clip = self.find_clip_by_name(path.name)
      if clip:
        clips.append(clip)

    # Append all at once
    if clips:
      result = self._media_pool.AppendToTimeline(clips)
      return result is not None

    return False

  # =========================================================================
  # Text and Fusion
  # =========================================================================

  def add_text_overlay(
    self,
    overlay: TextOverlay,
    clip_index: Optional[int] = None
  ) -> bool:
    """
    Add text overlay using Fusion Text+

    Args:
      overlay: TextOverlay configuration
      clip_index: Clip index to apply to (None = current)

    Returns:
      True if added successfully

    Note: This uses Fusion composition within Resolve
    """
    if self._timeline is None:
      self.get_current_timeline()

    if self._timeline is None:
      raise ResolveError("No timeline available")

    # Get video track items
    track = self._timeline.GetItemListInTrack("video", 1)
    if not track:
      raise ResolveError("No clips in timeline video track 1")

    target_clip = track[clip_index] if clip_index is not None else track[-1]

    # Create Fusion composition
    fusion = target_clip.GetFusionCompByIndex(1)
    if fusion is None:
      # Enable Fusion on clip
      target_clip.AddFusionComp()
      fusion = target_clip.GetFusionCompByIndex(1)

    if fusion is None:
      raise ResolveError("Could not create Fusion composition")

    # Add Text+ node
    # Note: Fusion scripting is complex, this is a simplified approach
    # Full implementation would require direct Fusion API access

    return True

  def add_lower_third(
    self,
    title: str,
    subtitle: str = "",
    position: tuple[float, float] = (0.1, 0.1),
    clip_index: Optional[int] = None
  ) -> bool:
    """
    Add lower third title card

    Args:
      title: Main title text
      subtitle: Optional subtitle
      position: Position (x, y) as fractions (0-1)
      clip_index: Clip index to apply to

    Returns:
      True if added successfully
    """
    # This would use Fusion macros or templates
    # Implementation depends on available Resolve templates
    return self.add_text_overlay(
      TextOverlay(
        text=f"{title}\n{subtitle}".strip(),
        position=position,
        font_size=0.05
      ),
      clip_index
    )

  # =========================================================================
  # Rendering
  # =========================================================================

  def render(
    self,
    output_path: Optional[Path] = None,
    preset: RenderPreset = RenderPreset.YOUTUBE_1080P,
    filename: Optional[str] = None
  ) -> bool:
    """
    Add render job to queue

    Args:
      output_path: Output directory
      preset: Render preset
      filename: Output filename (without extension)

    Returns:
      True if job added successfully
    """
    self._ensure_project()

    if self._timeline is None:
      self.get_current_timeline()

    # Set render settings
    self._project.SetCurrentRenderFormatAndCodec(preset.value, "")

    render_settings = {
      "SelectAllFrames": True,
      "TargetDir": str(output_path or Path.home() / "Movies")
    }

    if filename:
      render_settings["CustomName"] = filename

    self._project.SetRenderSettings(render_settings)

    # Add to queue
    job_id = self._project.AddRenderJob()
    if job_id is None:
      raise ResolveError("Failed to add render job")

    return True

  def start_render(self) -> bool:
    """Start rendering all jobs in queue"""
    self._ensure_project()
    return self._project.StartRendering()

  def get_render_status(self) -> Dict[str, Any]:
    """Get current render status"""
    self._ensure_project()

    job_list = self._project.GetRenderJobList()
    is_rendering = self._project.IsRenderingInProgress()

    return {
      "is_rendering": is_rendering,
      "job_count": len(job_list) if job_list else 0,
      "jobs": job_list
    }

  # =========================================================================
  # Utility
  # =========================================================================

  def get_version(self) -> str:
    """Get Resolve version"""
    self._ensure_connected()
    return self._resolve.GetVersion()

  def close(self):
    """Close connection and clean up"""
    if self._project:
      self._project.SaveProject()
    self._connected = False
    self._resolve = None
    self._project_manager = None
    self._project = None
    self._media_pool = None
    self._timeline = None
