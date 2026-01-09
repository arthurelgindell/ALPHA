"""
Short-Form Video Production Workflow (LinkedIn/YouTube Shorts)

Pipeline:
1. Strategy (DeepSeek) → Hook, narrative beats, CTA
2. Storyboard (DeepSeek) → Scene breakdown with timing, transitions, text overlays
3. Shot List (Nemotron) → Video prompts per scene, backend selection
4. Video Generation → GAMMA for hero shots, Veo 3.1 for quick turnaround
5. Post-Production (DaVinci Resolve) → Timeline, text, transitions, color
6. Render → /Volumes/STUDIO/VIDEO/

Text Handling: All text via DaVinci Resolve, never baked into video
"""

from pathlib import Path
from typing import List, Optional, Literal
from dataclasses import dataclass
from pydantic import BaseModel, Field
import json

from .base import Workflow, WorkflowResult, WorkflowStatus
from ..llm.router import TaskType
from ..generators.video import VideoBackend
from ..output.manager import OutputType
from ..resolve.controller import ResolveController, ResolveError

# ============================================================================
# Schemas for Structured LLM Output
# ============================================================================

class SceneBeat(BaseModel):
  """Individual scene in the video"""
  scene_number: int = Field(ge=1, le=20)
  duration_seconds: float = Field(ge=1, le=15)
  description: str = Field(max_length=300)
  camera_movement: str = Field(max_length=100)
  text_overlay: Optional[str] = Field(default=None, max_length=100)
  text_position: str = Field(default="bottom-center")
  transition_in: Optional[str] = Field(default=None)
  transition_out: Optional[str] = Field(default=None)
  audio_notes: Optional[str] = Field(default=None, max_length=200)
  is_hero_shot: bool = Field(default=False)

class VideoStoryboard(BaseModel):
  """Complete video storyboard"""
  title: str = Field(max_length=100)
  hook: str = Field(max_length=200, description="Opening hook in first 3 seconds")
  target_duration: int = Field(ge=5, le=60)
  narrative_arc: str = Field(max_length=200)
  target_platform: str = Field(default="linkedin")
  scenes: List[SceneBeat] = Field(min_length=3, max_length=15)
  cta_text: str = Field(max_length=100)
  hashtags: List[str] = Field(max_length=10)

class ShotPrompt(BaseModel):
  """Optimized video generation prompt"""
  scene_number: int
  backend: str = Field(description="gamma-test|gamma-medium|gamma-high|veo-fast")
  prompt: str = Field(description="Five-Part Formula prompt")
  duration: int = Field(ge=2, le=10)
  quality_priority: str = Field(default="balanced")

class ShotList(BaseModel):
  """Complete shot list with prompts"""
  shots: List[ShotPrompt]

# ============================================================================
# Short Video Workflow
# ============================================================================

class ShortVideoWorkflow(Workflow):
  """
  Short-Form Video Production Workflow

  Creates 15-60 second videos for LinkedIn/YouTube Shorts

  Usage:
    workflow = ShortVideoWorkflow(
      brief="The hidden truth about task mining",
      duration=30
    )
    result = workflow.execute()

    if result.success:
      print(f"Video: {result.outputs[0]}")
  """

  def __init__(
    self,
    brief: str,
    duration: int = 30,
    style: str = "documentary",
    platform: Literal["linkedin", "youtube_shorts", "instagram_reels"] = "linkedin",
    use_resolve: bool = True,
    output_dir: Optional[Path] = None
  ):
    super().__init__(brief, style, output_dir)
    self.duration = duration
    self.platform = platform
    self.use_resolve = use_resolve
    self._resolve: Optional[ResolveController] = None

  def plan(self) -> dict:
    """Create video storyboard and shot list using LLM"""
    self._report_progress("Creating storyboard...", 0.1)

    # Phase 1: Storyboard with DeepSeek
    storyboard_prompt = f"""Create a storyboard for a short-form video:

Topic: {self.brief}
Target Duration: {self.duration} seconds
Platform: {self.platform}
Style: {self.style}

Create a compelling video that:
1. Hooks in the first 3 seconds (pattern interrupt)
2. Builds tension through visual storytelling
3. Delivers value through each scene
4. Ends with clear CTA

The video should feel cinematic, not corporate.
Use the Five-Part Formula for each scene:
[Cinematography] + [Subject] + [Action] + [Context] + [Style & Ambiance]

NO text should be baked into video - all text added in post.
"""

    try:
      storyboard = self.router.structured_output(
        task_type=TaskType.STORYBOARD,
        messages=[
          {"role": "system", "content": "You are an expert video director specializing in short-form content for LinkedIn and social media."},
          {"role": "user", "content": storyboard_prompt}
        ],
        response_model=VideoStoryboard
      )
    except Exception as e:
      storyboard = self._fallback_storyboard()

    self._report_progress("Generating shot list...", 0.2)

    # Phase 2: Shot prompts with Nemotron
    shots_request = f"""Generate optimized video generation prompts for this storyboard:

{storyboard.model_dump_json(indent=2)}

For each scene, create a prompt using the Five-Part Formula:
[CINEMATOGRAPHY]: Camera movement, lens, angle, framing
[SUBJECT]: Who/what is in the scene
[ACTION]: What is happening
[CONTEXT]: Setting, time of day, environment
[STYLE & AMBIANCE]: Mood, lighting, color grade

Backend selection:
- gamma-high: Hero shots, quality priority
- gamma-medium: Standard scenes, balanced
- gamma-test: Quick validation, test renders
- veo-fast: Rapid turnaround needed

IMPORTANT: Prompts should NOT include any text - text added in post-production.
"""

    try:
      shot_list = self.router.structured_output(
        task_type=TaskType.SHOT_LIST,
        messages=[
          {"role": "system", "content": "You are an expert at crafting video generation prompts using the Five-Part Formula."},
          {"role": "user", "content": shots_request}
        ],
        response_model=ShotList
      )
    except Exception as e:
      shot_list = self._fallback_shots(storyboard)

    return {
      "storyboard": storyboard.model_dump() if hasattr(storyboard, 'model_dump') else storyboard,
      "shot_list": shot_list.model_dump() if hasattr(shot_list, 'model_dump') else shot_list
    }

  def _fallback_storyboard(self) -> VideoStoryboard:
    """Fallback storyboard when LLM unavailable"""
    scenes_count = max(3, self.duration // 8)
    scenes = []

    for i in range(scenes_count):
      if i == 0:
        desc = "Opening hook shot"
      elif i == scenes_count - 1:
        desc = "Closing CTA shot"
      else:
        desc = f"Content scene {i}"

      scenes.append(SceneBeat(
        scene_number=i + 1,
        duration_seconds=self.duration / scenes_count,
        description=desc,
        camera_movement="static" if i == 0 else "slow dolly",
        is_hero_shot=i == 0
      ))

    return VideoStoryboard(
      title=self.brief[:50],
      hook=self.brief,
      target_duration=self.duration,
      narrative_arc="Hook → Content → CTA",
      target_platform=self.platform,
      scenes=scenes,
      cta_text="Learn more",
      hashtags=["ai", "technology", "professional"]
    )

  def _fallback_shots(self, storyboard) -> ShotList:
    """Fallback shot list when LLM unavailable"""
    shots = []
    for scene in storyboard.scenes if hasattr(storyboard, 'scenes') else []:
      backend = "gamma-high" if scene.is_hero_shot else "gamma-medium"
      shots.append(ShotPrompt(
        scene_number=scene.scene_number,
        backend=backend,
        prompt=f"[CINEMATOGRAPHY]: {scene.camera_movement}. [SUBJECT]: Professional scene. [ACTION]: {scene.description}. [CONTEXT]: Modern environment. [STYLE]: Cinematic, {self.style}.",
        duration=int(scene.duration_seconds),
        quality_priority="quality" if scene.is_hero_shot else "balanced"
      ))
    return ShotList(shots=shots)

  def generate(self, plan: dict) -> List[Path]:
    """Generate video clips for each shot"""
    assets = []
    shots = plan.get("shot_list", {}).get("shots", [])

    for i, shot_data in enumerate(shots):
      scene_num = shot_data.get("scene_number", i + 1)
      self._report_progress(
        f"Generating scene {scene_num}...",
        0.3 + (i / len(shots)) * 0.4
      )

      prompt = shot_data.get("prompt", "")
      backend_str = shot_data.get("backend", "gamma-medium")
      duration = shot_data.get("duration", 5)

      try:
        # Parse backend
        if backend_str.startswith("gamma"):
          quality = backend_str.split("-")[1] if "-" in backend_str else "medium"
          result = self.video_gen.generate_gamma(
            prompt=prompt,
            quality=quality,
            num_frames=duration * 12  # Approximate 12fps
          )
        else:  # veo
          result = self.video_gen.generate_veo(
            prompt=prompt,
            duration=min(duration, 8),
            fast=True
          )

        if result.success and result.path:
          assets.append(result.path)
        else:
          self.result.errors.append(f"Failed to generate scene {scene_num}: {result.error}")

      except Exception as e:
        self.result.errors.append(f"Generation error for scene {scene_num}: {e}")

    return assets

  def assemble(self, assets: List[Path], plan: dict) -> List[Path]:
    """
    Assemble video using DaVinci Resolve

    Or simple concatenation if Resolve unavailable
    """
    self._report_progress("Assembling video...", 0.8)

    storyboard = plan.get("storyboard", {})
    title = storyboard.get("title", self.brief)[:30]

    if self.use_resolve and len(assets) > 0:
      try:
        return self._assemble_with_resolve(assets, plan)
      except ResolveError as e:
        self.result.errors.append(f"Resolve assembly failed: {e}")
        # Fall through to simple assembly

    # Simple assembly: just save assets with proper naming
    return self._simple_assembly(assets, plan)

  def _assemble_with_resolve(self, assets: List[Path], plan: dict) -> List[Path]:
    """Assemble video using DaVinci Resolve"""
    storyboard = plan.get("storyboard", {})
    title = storyboard.get("title", self.brief)[:30]

    self._resolve = ResolveController()
    self._resolve.connect()

    # Create project
    project_name = f"ARTHUR_{title.replace(' ', '_')}"
    self._resolve.create_project(project_name)

    # Create timeline from clips
    self._resolve.create_timeline_from_clips(
      name="Main Timeline",
      clip_paths=assets,
      width=1920,
      height=1080,
      fps=24.0
    )

    # Add text overlays from storyboard
    scenes = storyboard.get("scenes", [])
    for i, scene in enumerate(scenes):
      if scene.get("text_overlay"):
        self._resolve.add_lower_third(
          title=scene["text_overlay"],
          position=(0.1, 0.1),
          clip_index=i
        )

    # Render
    output_filename = self.output_manager.generate_filename(
      output_type=OutputType.VIDEO,
      topic=self.brief[:30],
      style=self.style,
      extension="mp4"
    )
    output_path = self.output_dir / "videos" / output_filename

    self._resolve.render(
      output_path=output_path.parent,
      filename=output_path.stem
    )
    self._resolve.start_render()

    self._resolve.close()

    return [output_path]

  def _simple_assembly(self, assets: List[Path], plan: dict) -> List[Path]:
    """Simple assembly without Resolve - just organize assets"""
    storyboard = plan.get("storyboard", {})

    # Create output folder
    folder_name = self.output_manager.generate_filename(
      output_type=OutputType.VIDEO,
      topic=self.brief[:30],
      style=self.style
    ).replace(".mp4", "")

    output_folder = self.output_dir / "videos" / folder_name
    output_folder.mkdir(parents=True, exist_ok=True)

    # Copy assets with proper naming
    final_outputs = []
    for i, asset in enumerate(assets):
      dest_name = f"scene_{i+1:02d}{asset.suffix}"
      dest_path = output_folder / dest_name
      import shutil
      shutil.copy2(str(asset), str(dest_path))
      final_outputs.append(dest_path)

    # Save assembly instructions
    instructions = {
      "topic": self.brief,
      "style": self.style,
      "duration": self.duration,
      "platform": self.platform,
      "storyboard": storyboard,
      "clips": [str(p) for p in final_outputs],
      "assembly_notes": "Clips should be assembled in Resolve for text overlays and color grading"
    }
    (output_folder / "assembly_instructions.json").write_text(json.dumps(instructions, indent=2))

    return [output_folder]

  def execute(self) -> WorkflowResult:
    """Execute video workflow"""
    return super().execute()
