"""
LLM Router - Intelligent routing between DeepSeek (Strategist) and Nemotron (Executor)

Routing Logic:
  User Brief
      │
      ▼
  ┌─────────────────────────────────────┐
  │ Is this planning/strategy/creative? │
  │ Is there ambiguity to resolve?      │
  │ Does it need multi-step reasoning?  │
  └─────────────────────────────────────┘
      │                    │
     YES                  NO
      │                    │
      ▼                    ▼
  DeepSeek V3.1      Nemotron
  (ALPHA:1234)       (BETA:1234)
"""

from enum import Enum
from typing import Optional, Callable
from openai import OpenAI
from pydantic import BaseModel
import instructor

from .clients import get_strategist, get_executor, check_endpoint
from ..config import ALPHA_LM, BETA_LM

class TaskType(str, Enum):
  """Task types for routing decisions"""
  # Strategist tasks (DeepSeek)
  STRATEGY = "strategy"
  STORYBOARD = "storyboard"
  NARRATIVE = "narrative"
  PLANNING = "planning"
  CREATIVE = "creative"
  AMBIGUOUS = "ambiguous"

  # Executor tasks (Nemotron)
  STRUCTURED_OUTPUT = "structured_output"
  PROMPT_ENGINEERING = "prompt_engineering"
  SHOT_LIST = "shot_list"
  JSON_GENERATION = "json_generation"
  FORMATTING = "formatting"

# Tasks that route to DeepSeek (Strategist)
STRATEGIST_TASKS = {
  TaskType.STRATEGY,
  TaskType.STORYBOARD,
  TaskType.NARRATIVE,
  TaskType.PLANNING,
  TaskType.CREATIVE,
  TaskType.AMBIGUOUS,
}

# Tasks that route to Nemotron (Executor)
EXECUTOR_TASKS = {
  TaskType.STRUCTURED_OUTPUT,
  TaskType.PROMPT_ENGINEERING,
  TaskType.SHOT_LIST,
  TaskType.JSON_GENERATION,
  TaskType.FORMATTING,
}

class LLMRouter:
  """
  Routes requests to appropriate LLM based on task type

  Usage:
    router = LLMRouter()

    # Auto-routing based on task type
    response = router.complete(
      task_type=TaskType.STORYBOARD,
      messages=[{"role": "user", "content": "Create storyboard for..."}]
    )

    # Structured output with Pydantic
    from schemas import VideoScript
    script = router.structured_output(
      task_type=TaskType.STRUCTURED_OUTPUT,
      messages=[...],
      response_model=VideoScript
    )
  """

  def __init__(self, check_availability: bool = True):
    self._strategist: Optional[OpenAI] = None
    self._executor: Optional[OpenAI] = None
    self._strategist_available = False
    self._executor_available = False

    if check_availability:
      self._check_availability()

  def _check_availability(self):
    """Check which endpoints are available"""
    alpha_status = check_endpoint(ALPHA_LM)
    beta_status = check_endpoint(BETA_LM)
    self._strategist_available = alpha_status["available"]
    self._executor_available = beta_status["available"]

  @property
  def strategist(self) -> OpenAI:
    """Get or create strategist client (DeepSeek on ALPHA)"""
    if self._strategist is None:
      self._strategist = get_strategist()
    return self._strategist

  @property
  def executor(self) -> OpenAI:
    """Get or create executor client (Nemotron on BETA)"""
    if self._executor is None:
      self._executor = get_executor()
    return self._executor

  def get_client_for_task(self, task_type: TaskType) -> OpenAI:
    """Route to appropriate client based on task type"""
    if task_type in STRATEGIST_TASKS:
      return self.strategist
    else:
      return self.executor

  def get_role_for_task(self, task_type: TaskType) -> str:
    """Get role name for task type"""
    if task_type in STRATEGIST_TASKS:
      return "strategist"
    else:
      return "executor"

  def complete(
    self,
    task_type: TaskType,
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: int = 4096,
    **kwargs
  ) -> str:
    """
    Complete a chat request, routing to appropriate LLM

    Args:
      task_type: Type of task for routing
      messages: Chat messages
      temperature: Sampling temperature
      max_tokens: Max response tokens

    Returns:
      Response content as string
    """
    client = self.get_client_for_task(task_type)

    response = client.chat.completions.create(
      model="local-model",
      messages=messages,
      temperature=temperature,
      max_tokens=max_tokens,
      **kwargs
    )

    return response.choices[0].message.content

  def structured_output(
    self,
    task_type: TaskType,
    messages: list[dict],
    response_model: type[BaseModel],
    temperature: float = 0.3,  # Lower temp for structured output
    max_retries: int = 3,
    **kwargs
  ) -> BaseModel:
    """
    Get structured output using Instructor library

    Args:
      task_type: Type of task for routing
      messages: Chat messages
      response_model: Pydantic model for response validation
      temperature: Sampling temperature (lower for structured)
      max_retries: Number of retries on validation failure

    Returns:
      Validated Pydantic model instance
    """
    client = self.get_client_for_task(task_type)

    # Wrap client with instructor
    # Use JSON_SCHEMA mode for LM Studio compatibility
    instructor_client = instructor.from_openai(
      client,
      mode=instructor.Mode.JSON_SCHEMA
    )

    return instructor_client.chat.completions.create(
      model="local-model",
      messages=messages,
      response_model=response_model,
      temperature=temperature,
      max_retries=max_retries,
      **kwargs
    )

  def status(self) -> dict:
    """Get status of all endpoints"""
    return {
      "strategist": {
        "name": ALPHA_LM.name,
        "endpoint": ALPHA_LM.base_url,
        "available": self._strategist_available,
        "role": ALPHA_LM.role,
        "description": ALPHA_LM.description
      },
      "executor": {
        "name": BETA_LM.name,
        "endpoint": BETA_LM.base_url,
        "available": self._executor_available,
        "role": BETA_LM.role,
        "description": BETA_LM.description
      }
    }

# ============================================================================
# Convenience Functions
# ============================================================================

def strategize(prompt: str, system_prompt: Optional[str] = None) -> str:
  """
  Quick function for strategic/creative tasks

  Uses DeepSeek V3.1 for complex reasoning
  """
  router = LLMRouter(check_availability=False)
  messages = []

  if system_prompt:
    messages.append({"role": "system", "content": system_prompt})

  messages.append({"role": "user", "content": prompt})

  return router.complete(TaskType.STRATEGY, messages)

def execute(prompt: str, system_prompt: Optional[str] = None) -> str:
  """
  Quick function for structured/execution tasks

  Uses Nemotron for consistent, formatted output
  """
  router = LLMRouter(check_availability=False)
  messages = []

  if system_prompt:
    messages.append({"role": "system", "content": system_prompt})

  messages.append({"role": "user", "content": prompt})

  return router.complete(TaskType.STRUCTURED_OUTPUT, messages)
