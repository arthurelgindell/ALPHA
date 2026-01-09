"""
Base Workflow Classes
Foundation for all production workflows
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Any, Callable
import logging
import traceback

from ..llm.router import LLMRouter, TaskType
from ..generators.image import ImageGenerator
from ..generators.video import VideoGenerator
from ..output.manager import OutputManager
from ..config import PATHS

logger = logging.getLogger(__name__)

class WorkflowStatus(str, Enum):
  """Status of workflow execution"""
  PENDING = "pending"
  PLANNING = "planning"
  GENERATING = "generating"
  ASSEMBLING = "assembling"
  RENDERING = "rendering"
  COMPLETED = "completed"
  FAILED = "failed"

@dataclass
class WorkflowResult:
  """Result of workflow execution"""
  success: bool
  status: WorkflowStatus
  outputs: List[Path] = field(default_factory=list)
  errors: List[str] = field(default_factory=list)
  metadata: dict = field(default_factory=dict)
  started_at: Optional[datetime] = None
  completed_at: Optional[datetime] = None

  @property
  def duration(self) -> Optional[float]:
    """Execution duration in seconds"""
    if self.started_at and self.completed_at:
      return (self.completed_at - self.started_at).total_seconds()
    return None

class Workflow(ABC):
  """
  Base class for all production workflows

  Subclasses implement specific workflows like:
  - CarouselWorkflow
  - ShortVideoWorkflow
  - LongVideoWorkflow
  - BatchWorkflow

  Usage:
    workflow = CarouselWorkflow(brief="AI Skills Premium")
    result = workflow.execute()

    if result.success:
      print(f"Outputs: {result.outputs}")
  """

  def __init__(
    self,
    brief: str,
    style: str = "professional",
    output_dir: Optional[Path] = None
  ):
    self.brief = brief
    self.style = style
    self.output_dir = output_dir or PATHS.project_root

    # Initialize components
    self.router = LLMRouter(check_availability=False)
    self.image_gen = ImageGenerator()
    self.video_gen = VideoGenerator()
    self.output_manager = OutputManager()

    # State
    self.status = WorkflowStatus.PENDING
    self.result = WorkflowResult(
      success=False,
      status=WorkflowStatus.PENDING,
      started_at=None
    )

    # Progress callbacks
    self._progress_callbacks: List[Callable] = []

  def on_progress(self, callback: Callable[[str, float], None]):
    """Register progress callback"""
    self._progress_callbacks.append(callback)

  def _report_progress(self, message: str, progress: float = 0.0):
    """Report progress to callbacks"""
    for callback in self._progress_callbacks:
      try:
        callback(message, progress)
      except:
        pass
    logger.info(f"[{progress*100:.0f}%] {message}")

  def _update_status(self, status: WorkflowStatus):
    """Update workflow status"""
    self.status = status
    self.result.status = status

  @abstractmethod
  def plan(self) -> dict:
    """
    Planning phase - create content plan using LLM

    Returns:
      Planning data dict (schema varies by workflow type)
    """
    pass

  @abstractmethod
  def generate(self, plan: dict) -> List[Path]:
    """
    Generation phase - create media assets

    Args:
      plan: Output from plan() phase

    Returns:
      List of generated file paths
    """
    pass

  @abstractmethod
  def assemble(self, assets: List[Path], plan: dict) -> List[Path]:
    """
    Assembly phase - combine assets into final outputs

    Args:
      assets: Generated asset paths
      plan: Original plan

    Returns:
      List of final output paths
    """
    pass

  def execute(self) -> WorkflowResult:
    """
    Execute complete workflow

    Returns:
      WorkflowResult with outputs and metadata
    """
    self.result.started_at = datetime.now()

    try:
      # Phase 1: Planning
      self._update_status(WorkflowStatus.PLANNING)
      self._report_progress("Planning content strategy...", 0.1)
      plan = self.plan()
      self.result.metadata["plan"] = plan

      # Phase 2: Generation
      self._update_status(WorkflowStatus.GENERATING)
      self._report_progress("Generating media assets...", 0.3)
      assets = self.generate(plan)
      self.result.metadata["assets"] = [str(p) for p in assets]

      # Phase 3: Assembly
      self._update_status(WorkflowStatus.ASSEMBLING)
      self._report_progress("Assembling final output...", 0.7)
      outputs = self.assemble(assets, plan)
      self.result.outputs = outputs

      # Complete
      self._update_status(WorkflowStatus.COMPLETED)
      self._report_progress("Workflow complete!", 1.0)
      self.result.success = True

    except Exception as e:
      self._update_status(WorkflowStatus.FAILED)
      self.result.errors.append(str(e))
      self.result.errors.append(traceback.format_exc())
      logger.error(f"Workflow failed: {e}")

    self.result.completed_at = datetime.now()
    return self.result

  def validate_infrastructure(self) -> dict:
    """
    Validate required infrastructure is available

    Returns:
      Dict with component availability status
    """
    from ..llm.clients import check_all_endpoints

    status = {
      "llm": check_all_endpoints(),
      "gamma": self.video_gen.check_gamma(),
      "studio": self.output_manager.studio_available()
    }

    return status
