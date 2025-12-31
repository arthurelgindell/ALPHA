#!/usr/bin/env python3
"""
ComfyUI Python Client for Video Generation
Provides programmatic control over ComfyUI via REST API + WebSocket
"""

import json
import uuid
import requests
import websocket
import time
from pathlib import Path
from typing import Dict, Optional, List, Callable
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VideoFormat:
    """Video format specifications"""
    width: int
    height: int
    fps: int
    name: str

    # Standard formats
    LINKEDIN_SQUARE = None  # Will be initialized below
    LINKEDIN_WIDE = None
    YOUTUBE_SHORTS = None


# Initialize standard formats
VideoFormat.LINKEDIN_SQUARE = VideoFormat(1080, 1080, 24, "LinkedIn Square")
VideoFormat.LINKEDIN_WIDE = VideoFormat(1920, 1080, 24, "LinkedIn Wide")
VideoFormat.YOUTUBE_SHORTS = VideoFormat(1080, 1920, 30, "YouTube Shorts")


@dataclass
class QualityProfile:
    """Quality profile based on message density"""
    name: str
    resolution: str
    model_steps: int
    text_encoder: str
    use_case: str
    cost_multiplier: float

    # Standard profiles
    HIGH_DENSITY = None
    MEDIUM_DENSITY = None
    LOW_DENSITY = None


# Initialize quality profiles
QualityProfile.HIGH_DENSITY = QualityProfile(
    name="HIGH_DENSITY",
    resolution="720p",
    model_steps=30,
    text_encoder="t5_xxl",
    use_case="Complex narratives, data visualization, infographics",
    cost_multiplier=1.0
)

QualityProfile.MEDIUM_DENSITY = QualityProfile(
    name="MEDIUM_DENSITY",
    resolution="480p",
    model_steps=20,
    text_encoder="clip_g14",
    use_case="Simple messages, motion-focused, ambient scenes",
    cost_multiplier=0.5
)

QualityProfile.LOW_DENSITY = QualityProfile(
    name="LOW_DENSITY",
    resolution="480p",
    model_steps=15,
    text_encoder="clip_g14",
    use_case="Ambient content, background loops, establishing shots",
    cost_multiplier=0.3
)


class ComfyUIClient:
    """
    Python client for ComfyUI REST API + WebSocket

    Provides programmatic control over video generation workflows
    """

    def __init__(self,
                 server_address: str = "127.0.0.1:8188",
                 output_dir: str = "/Users/arthurdell/ARTHUR/videos/raw"):
        """
        Initialize ComfyUI client

        Args:
            server_address: ComfyUI server address (host:port)
            output_dir: Directory for generated videos
        """
        self.server_address = server_address
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.client_id = str(uuid.uuid4())
        self.ws = None

        logger.info(f"ComfyUI Client initialized (ID: {self.client_id})")

    def connect_websocket(self):
        """Connect to ComfyUI WebSocket for real-time monitoring"""
        ws_url = f"ws://{self.server_address}/ws?clientId={self.client_id}"
        self.ws = websocket.create_connection(ws_url)
        logger.info(f"Connected to WebSocket: {ws_url}")

    def queue_prompt(self, workflow: Dict) -> str:
        """
        Submit workflow to ComfyUI queue

        Args:
            workflow: ComfyUI workflow JSON

        Returns:
            prompt_id: Unique ID for tracking this generation
        """
        url = f"http://{self.server_address}/prompt"

        payload = {
            "prompt": workflow,
            "client_id": self.client_id
        }

        response = requests.post(url, json=payload)
        response.raise_for_status()

        result = response.json()
        prompt_id = result["prompt_id"]

        logger.info(f"Queued prompt: {prompt_id}")
        return prompt_id

    def get_history(self, prompt_id: str) -> Dict:
        """Get generation history for a prompt ID"""
        url = f"http://{self.server_address}/history/{prompt_id}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def get_image(self, filename: str, subfolder: str = "", folder_type: str = "output") -> bytes:
        """Download generated image/video from ComfyUI"""
        url = f"http://{self.server_address}/view"
        params = {
            "filename": filename,
            "subfolder": subfolder,
            "type": folder_type
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.content

    def wait_for_completion(self,
                           prompt_id: str,
                           timeout: int = 1800,
                           progress_callback: Optional[Callable] = None) -> Dict:
        """
        Wait for generation to complete with real-time monitoring

        Args:
            prompt_id: Prompt ID to monitor
            timeout: Maximum wait time in seconds (default 30 minutes)
            progress_callback: Optional callback for progress updates

        Returns:
            Final history data
        """
        if not self.ws:
            self.connect_websocket()

        start_time = time.time()
        last_status = None

        while True:
            # Check timeout
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Generation timed out after {timeout}s")

            # Get WebSocket message
            try:
                message = self.ws.recv()
                data = json.loads(message)

                # Handle different message types
                if data.get("type") == "progress":
                    progress = data.get("data", {})
                    current = progress.get("value", 0)
                    total = progress.get("max", 100)

                    if progress_callback:
                        progress_callback(current, total)

                    # Log progress
                    if current != last_status:
                        logger.info(f"Progress: {current}/{total}")
                        last_status = current

                elif data.get("type") == "executing":
                    node_id = data.get("data", {}).get("node")
                    if node_id is None:
                        # Execution finished
                        logger.info("Execution completed")
                        break

            except Exception as e:
                # Non-fatal WebSocket errors - continue polling
                logger.warning(f"WebSocket error: {e}")
                time.sleep(1)

            time.sleep(0.5)

        # Get final history
        history = self.get_history(prompt_id)
        return history

    def generate_video(self,
                      workflow: Dict,
                      output_filename: Optional[str] = None,
                      timeout: int = 1800) -> Path:
        """
        Complete video generation workflow

        Args:
            workflow: ComfyUI workflow JSON
            output_filename: Optional output filename
            timeout: Generation timeout in seconds

        Returns:
            Path to generated video
        """
        logger.info("Starting video generation...")

        # Queue prompt
        prompt_id = self.queue_prompt(workflow)

        # Wait for completion with progress tracking
        def log_progress(current, total):
            percent = (current / total * 100) if total > 0 else 0
            logger.info(f"⏳ Generating: {percent:.1f}%")

        history = self.wait_for_completion(
            prompt_id,
            timeout=timeout,
            progress_callback=log_progress
        )

        # Extract output filename from history
        if prompt_id not in history:
            raise ValueError(f"Prompt ID {prompt_id} not found in history")

        outputs = history[prompt_id].get("outputs", {})

        # Find video output node
        video_data = None
        for node_id, node_output in outputs.items():
            if "videos" in node_output:
                video_data = node_output["videos"][0]
                break
            elif "images" in node_output:
                # Fallback to images if video not found
                video_data = node_output["images"][0]
                break

        if not video_data:
            raise ValueError("No video output found in generation results")

        # Download video
        video_bytes = self.get_image(
            filename=video_data["filename"],
            subfolder=video_data.get("subfolder", ""),
            folder_type=video_data.get("type", "output")
        )

        # Save to output directory
        if output_filename is None:
            output_filename = f"video_{prompt_id}.mp4"

        output_path = self.output_dir / output_filename
        output_path.write_bytes(video_bytes)

        logger.info(f"✅ Video saved: {output_path}")
        return output_path

    def close(self):
        """Close WebSocket connection"""
        if self.ws:
            self.ws.close()
            logger.info("WebSocket closed")


def determine_quality_profile(prompt: str, has_text_overlay: bool = False) -> QualityProfile:
    """
    Analyze prompt to determine optimal quality profile

    High density indicators:
    - Text in video (statistics, quotes, data)
    - Multiple elements
    - Complex composition

    Low density indicators:
    - Single subject
    - Motion/action focus
    - Ambient/background

    Args:
        prompt: Video generation prompt
        has_text_overlay: Whether video will have text overlays

    Returns:
        Optimal quality profile
    """
    # High density keywords
    high_density_keywords = [
        "statistic", "chart", "data", "infographic", "visualization",
        "complex", "detailed", "text", "information", "diagram"
    ]

    # Low density keywords
    low_density_keywords = [
        "ambient", "background", "simple", "motion", "flowing",
        "abstract", "atmosphere", "establishing"
    ]

    prompt_lower = prompt.lower()

    # Check for text overlay requirement
    if has_text_overlay:
        return QualityProfile.HIGH_DENSITY

    # Check for high density keywords
    if any(keyword in prompt_lower for keyword in high_density_keywords):
        return QualityProfile.HIGH_DENSITY

    # Check for low density keywords
    if any(keyword in prompt_lower for keyword in low_density_keywords):
        return QualityProfile.LOW_DENSITY

    # Default to medium density
    return QualityProfile.MEDIUM_DENSITY


if __name__ == "__main__":
    # Test client initialization
    client = ComfyUIClient()
    logger.info("ComfyUI client ready for automation")

    # Example quality profile determination
    test_prompts = [
        ("A cinematic shot of a cyberpunk city at night", False),
        ("Data visualization showing AI adoption statistics", True),
        ("Ambient background of a futuristic office", False)
    ]

    for prompt, has_text in test_prompts:
        profile = determine_quality_profile(prompt, has_text)
        logger.info(f"Prompt: {prompt[:50]}...")
        logger.info(f"Quality: {profile.name} ({profile.use_case})")
        logger.info("")
