"""
Voice Generation via BETA's F5-TTS-MLX
Generates voiceover narration for video production.

Uses SSH to execute F5-TTS on BETA and SCP to retrieve audio files.
"""

import subprocess
import time
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class VoiceResult:
  """Result of voice generation"""
  success: bool
  path: Optional[Path]
  text: str
  generation_time: Optional[float] = None
  file_size: Optional[int] = None
  error: Optional[str] = None


class VoiceGenerator:
  """
  TTS generation via BETA's F5-TTS-MLX.

  Executes voice synthesis on BETA via SSH and retrieves the audio file.
  Designed for voiceover narration in video production.

  Usage:
    gen = VoiceGenerator()

    # Generate single narration
    result = gen.generate(
      text="Welcome to the AI-Powered Professional Stack.",
      output_path=Path("videos/intro_narration.wav")
    )

    # Generate multiple segments
    results = gen.generate_narration(
      segments=[
        "First, we have the Mac Studio M3 Ultra.",
        "Next, the NVIDIA DGX Spark.",
        "Finally, Claude Code for AI-assisted development."
      ],
      output_dir=Path("videos/narration/")
    )
  """

  def __init__(
    self,
    beta_host: str = "beta",
    python_env: str = "/Volumes/MODELS/mlx-env/bin/python3",
    tts_script: str = "/Volumes/CLAUDE/SPHERE/scripts/voice-pro.py",
    remote_output_dir: str = "/Volumes/MODELS/tts/output"
  ):
    self.beta_host = beta_host
    self.python_env = python_env
    self.tts_script = tts_script
    self.remote_output_dir = remote_output_dir

  def check_connection(self) -> bool:
    """Check if BETA is reachable via SSH."""
    try:
      result = subprocess.run(
        ["ssh", self.beta_host, "echo", "ok"],
        capture_output=True,
        text=True,
        timeout=10
      )
      return result.returncode == 0
    except (subprocess.TimeoutExpired, Exception) as e:
      logger.error(f"BETA connection check failed: {e}")
      return False

  def generate(
    self,
    text: str,
    output_path: Path,
    timeout: int = 90
  ) -> VoiceResult:
    """
    Generate speech from text using F5-TTS on BETA.

    Args:
      text: Text to convert to speech
      output_path: Local path to save the WAV file
      timeout: Timeout in seconds for generation

    Returns:
      VoiceResult with success status and file path
    """
    start_time = time.time()

    # Validate input
    if not text or len(text.strip()) < 3:
      return VoiceResult(
        success=False,
        path=None,
        text=text,
        error="Text too short (min 3 characters)"
      )

    # Generate unique filename on BETA
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    remote_filename = f"voice_{timestamp}.wav"
    remote_path = f"{self.remote_output_dir}/{remote_filename}"

    logger.info(f"Generating voice on BETA: \"{text[:50]}...\"")

    # Execute F5-TTS on BETA
    # Escape single quotes in text and wrap in single quotes for shell
    escaped_text = text.replace("'", "'\"'\"'")
    remote_cmd = f"{self.python_env} {self.tts_script} --no-play --output {remote_path} '{escaped_text}'"

    ssh_cmd = ["ssh", self.beta_host, remote_cmd]

    try:
      result = subprocess.run(
        ssh_cmd,
        capture_output=True,
        text=True,
        timeout=timeout
      )

      if result.returncode != 0:
        logger.error(f"F5-TTS failed: {result.stderr}")
        return VoiceResult(
          success=False,
          path=None,
          text=text,
          generation_time=time.time() - start_time,
          error=result.stderr or "Generation failed"
        )

      # Transfer file back to ALPHA using cat over SSH (more reliable than scp)
      output_path.parent.mkdir(parents=True, exist_ok=True)

      try:
        cat_cmd = ["ssh", self.beta_host, "cat", remote_path]
        with open(output_path, "wb") as f:
          cat_result = subprocess.run(
            cat_cmd,
            stdout=f,
            stderr=subprocess.PIPE,
            timeout=60
          )

        if cat_result.returncode != 0:
          logger.error(f"File transfer failed: {cat_result.stderr.decode()}")
          return VoiceResult(
            success=False,
            path=None,
            text=text,
            generation_time=time.time() - start_time,
            error=f"File transfer failed: {cat_result.stderr.decode()}"
          )
      except Exception as e:
        logger.error(f"File transfer error: {e}")
        return VoiceResult(
          success=False,
          path=None,
          text=text,
          generation_time=time.time() - start_time,
          error=f"File transfer error: {e}"
        )

      # Cleanup remote file
      subprocess.run(
        ["ssh", self.beta_host, "rm", "-f", remote_path],
        capture_output=True,
        timeout=10
      )

      generation_time = time.time() - start_time
      file_size = output_path.stat().st_size if output_path.exists() else 0

      logger.info(f"Voice generated: {output_path} ({file_size} bytes, {generation_time:.1f}s)")

      return VoiceResult(
        success=True,
        path=output_path,
        text=text,
        generation_time=generation_time,
        file_size=file_size
      )

    except subprocess.TimeoutExpired:
      logger.error(f"Voice generation timed out after {timeout}s")
      return VoiceResult(
        success=False,
        path=None,
        text=text,
        generation_time=time.time() - start_time,
        error=f"Timeout after {timeout}s"
      )
    except Exception as e:
      logger.error(f"Voice generation error: {e}")
      return VoiceResult(
        success=False,
        path=None,
        text=text,
        generation_time=time.time() - start_time,
        error=str(e)
      )

  def generate_narration(
    self,
    segments: list[str],
    output_dir: Path,
    prefix: str = "narration"
  ) -> list[VoiceResult]:
    """
    Generate multiple narration segments.

    Args:
      segments: List of text segments to convert to speech
      output_dir: Directory to save WAV files
      prefix: Filename prefix for segments

    Returns:
      List of VoiceResult for each segment
    """
    results = []
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, text in enumerate(segments, 1):
      output_path = output_dir / f"{prefix}_{i:03d}.wav"
      logger.info(f"Generating segment {i}/{len(segments)}")

      result = self.generate(text, output_path)
      results.append(result)

      if not result.success:
        logger.warning(f"Segment {i} failed: {result.error}")

    successful = sum(1 for r in results if r.success)
    logger.info(f"Narration complete: {successful}/{len(segments)} segments")

    return results


def mux_audio(
  video_path: Path,
  audio_path: Path,
  output_path: Path,
  audio_offset: float = 0.0
) -> Path:
  """
  Combine video with voiceover narration using ffmpeg.

  Args:
    video_path: Path to input video file
    audio_path: Path to audio file (WAV)
    output_path: Path for output video with audio
    audio_offset: Delay audio start in seconds (default 0)

  Returns:
    Path to output file

  Raises:
    subprocess.CalledProcessError: If ffmpeg fails
  """
  output_path.parent.mkdir(parents=True, exist_ok=True)

  cmd = [
    "ffmpeg", "-y",
    "-i", str(video_path),
    "-i", str(audio_path),
    "-c:v", "copy",
    "-c:a", "aac",
    "-b:a", "192k",
    "-map", "0:v",
    "-map", "1:a",
  ]

  # Add audio delay if specified
  if audio_offset > 0:
    cmd.extend(["-af", f"adelay={int(audio_offset * 1000)}|{int(audio_offset * 1000)}"])

  cmd.append(str(output_path))

  logger.info(f"Muxing video + audio: {output_path}")
  subprocess.run(cmd, check=True, capture_output=True)

  return output_path
