"""
OpenAI-compatible LM Studio clients
Both ALPHA (DeepSeek) and BETA (Nemotron) expose OpenAI-compatible APIs
"""

from openai import OpenAI
from typing import Optional, Generator
import httpx
from ..config import ALPHA_LM, BETA_LM, VISION_ALPHA, LMStudioEndpoint

def _create_client(endpoint: LMStudioEndpoint, timeout: float = 120.0) -> OpenAI:
  """Create OpenAI client for LM Studio endpoint"""
  return OpenAI(
    base_url=endpoint.base_url,
    api_key="lm-studio",  # LM Studio ignores API key
    timeout=timeout,
    http_client=httpx.Client(timeout=timeout)
  )

def get_strategist(timeout: float = 120.0) -> OpenAI:
  """
  Get DeepSeek V3.1 client (ALPHA)
  Use for: Strategy, planning, complex reasoning, storyboarding
  """
  return _create_client(ALPHA_LM, timeout)

def get_executor(timeout: float = 60.0) -> OpenAI:
  """
  Get Nemotron client (BETA)
  Use for: Structured output, prompt engineering, task execution
  """
  return _create_client(BETA_LM, timeout)


def get_vision(timeout: float = 120.0) -> OpenAI:
  """
  Get GLM-4.6V-Flash client (ALPHA vision endpoint via Tailscale)
  Use for: Image analysis, video frame analysis, content verification

  Note: This uses the Tailscale HTTPS endpoint (https://alpha.tail5f2bae.ts.net/v1)
  rather than direct IP, as vision models are served via Tailscale Serve.
  """
  return OpenAI(
    base_url=VISION_ALPHA.base_url,
    api_key="lm-studio",  # LM Studio ignores API key
    timeout=timeout,
    http_client=httpx.Client(timeout=timeout)
  )


def check_endpoint(endpoint: LMStudioEndpoint, timeout: float = 5.0) -> dict:
  """
  Check if LM Studio endpoint is available

  Returns:
    dict with 'available', 'models', and 'error' keys
  """
  try:
    client = _create_client(endpoint, timeout)
    models = client.models.list()
    model_ids = [m.id for m in models.data]
    return {
      "available": True,
      "models": model_ids,
      "error": None
    }
  except Exception as e:
    return {
      "available": False,
      "models": [],
      "error": str(e)
    }

def check_all_endpoints() -> dict:
  """Check availability of all LM Studio endpoints"""
  return {
    "alpha": {
      "name": ALPHA_LM.name,
      "role": ALPHA_LM.role,
      "url": ALPHA_LM.base_url,
      **check_endpoint(ALPHA_LM)
    },
    "beta": {
      "name": BETA_LM.name,
      "role": BETA_LM.role,
      "url": BETA_LM.base_url,
      **check_endpoint(BETA_LM)
    }
  }

def chat_completion(
  client: OpenAI,
  messages: list[dict],
  model: Optional[str] = None,
  temperature: float = 0.7,
  max_tokens: int = 4096,
  stream: bool = False
) -> str | Generator:
  """
  Simple chat completion wrapper

  Args:
    client: OpenAI client from get_strategist() or get_executor()
    messages: List of message dicts with 'role' and 'content'
    model: Model ID (optional, LM Studio uses loaded model)
    temperature: Sampling temperature
    max_tokens: Max response tokens
    stream: Whether to stream the response

  Returns:
    Response content as string, or generator if streaming
  """
  # LM Studio uses whatever model is loaded, but we need to pass something
  if model is None:
    model = "local-model"

  response = client.chat.completions.create(
    model=model,
    messages=messages,
    temperature=temperature,
    max_tokens=max_tokens,
    stream=stream
  )

  if stream:
    return _stream_response(response)
  else:
    return response.choices[0].message.content

def _stream_response(response) -> Generator[str, None, None]:
  """Stream response chunks"""
  for chunk in response:
    if chunk.choices[0].delta.content:
      yield chunk.choices[0].delta.content
