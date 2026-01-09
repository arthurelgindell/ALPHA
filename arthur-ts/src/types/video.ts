/**
 * Video Generation Types
 * Translated from: arthur/generators/video.py
 */

// ============================================================================
// Video Backend Enum
// ============================================================================

export enum VideoBackend {
  // Local GAMMA (HunyuanVideo-1.5) - $0
  GAMMA_TEST = "gamma-test",
  GAMMA_MEDIUM = "gamma-medium",
  GAMMA_HIGH = "gamma-high",
  GAMMA_MAXIMUM = "gamma-maximum",

  // Cloud Veo 3.1 (Google) - $0.15-0.40/sec
  VEO_FAST = "veo-fast",
  VEO_STANDARD = "veo-standard",

  // Cloud Wan 2.6 API (PiAPI) - $0.08-0.12/sec
  WAN26_720P = "wan26-720p",
  WAN26_1080P = "wan26-1080p",
  WAN26_AUDIO = "wan26-audio",
  WAN26_MULTISHOT = "wan26-multishot",
}

// ============================================================================
// Quality Presets
// ============================================================================

export type GammaQuality = "test" | "medium" | "high" | "maximum";

export const GAMMA_QUALITY_CONFIG: Record<GammaQuality, { steps: number; numFrames: number }> = {
  test: { steps: 10, numFrames: 25 },
  medium: { steps: 30, numFrames: 61 },
  high: { steps: 40, numFrames: 81 },
  maximum: { steps: 50, numFrames: 97 },
};

// ============================================================================
// Request Types
// ============================================================================

export interface GammaRequest {
  prompt: string;
  quality?: GammaQuality;
  numFrames?: number;
  seed?: number;
}

// Used by GammaClient internally (snake_case for API)
export interface GammaGenerateRequest {
  prompt: string;
  quality: GammaQuality;
  num_frames: number;
  seed?: number;
}

export interface VeoRequest {
  prompt: string;
  durationSeconds?: number;
  aspectRatio?: "16:9" | "9:16" | "1:1";
  fast?: boolean;
}

export interface Wan26Request {
  prompt: string;
  resolution?: "720p" | "1080p";
  duration?: number;
  aspectRatio?: "16:9" | "9:16" | "1:1";
  withAudio?: boolean;
}

// ============================================================================
// Result Types
// ============================================================================

export interface VideoResult {
  success: boolean;
  path?: string;
  backend: VideoBackend;
  prompt: string;
  duration?: number;
  generationTime?: number;
  resolution?: string;
  fileSize?: number;
  error?: string;
  errorCode?: string;
}

export interface GammaGenerateResponse {
  success: boolean;
  job_id: string;
  video_path: string;
  filename: string;
  download_url: string;
  generation_time_seconds: number;
  file_size_mb: number;
  error: string | null;
}

export interface GammaHealthResponse {
  status: "healthy" | "unhealthy";
  gpu_available: boolean;
  gpu_name: string;
  model_loaded: boolean;
}

export interface GammaVideoListResponse {
  count: number;
  videos: Array<{
    filename: string;
    path: string;
    created: string;
  }>;
}

// ============================================================================
// Veo API Types (Google REST)
// ============================================================================

export interface VeoOperation {
  name: string;
  done: boolean;
  error?: {
    code: number;
    message: string;
  };
  response?: VeoResponse;
}

export interface VeoResponse {
  generatedVideos: Array<{
    video: {
      uri: string;
    };
  }>;
}

// ============================================================================
// Wan 2.6 API Types
// ============================================================================

export type Wan26TaskType = "text_to_video" | "image_to_video" | "reference_to_video";

export type Wan26TaskStatus =
  | "pending"
  | "processing"
  | "completed"
  | "failed"
  | "cancelled";

export interface Wan26TaskResponse {
  task_id: string;
  status: Wan26TaskStatus;
  video_url?: string;
  audio_url?: string;
  progress?: number;
  error?: string;
}

export interface Wan26Result {
  success: boolean;
  taskId?: string;
  videoUrl?: string;
  audioUrl?: string;
  status: Wan26TaskStatus;
  prompt: string;
  resolution?: string;
  duration?: number;
  costEstimate?: number;
  error?: string;
}

// ============================================================================
// Backend Selection
// ============================================================================

export interface BackendSelection {
  backend: VideoBackend;
  reason: string;
  estimatedTime: string;
  estimatedCost: number;
}

export function selectBackend(
  duration: number,
  priority: "speed" | "quality" | "cost"
): BackendSelection {
  switch (priority) {
    case "speed":
      return {
        backend: VideoBackend.VEO_FAST,
        reason: "Fastest turnaround (~1 min)",
        estimatedTime: "~1 minute",
        estimatedCost: duration * 0.15,
      };
    case "quality":
      return {
        backend: VideoBackend.GAMMA_MAXIMUM,
        reason: "Highest quality (50 steps)",
        estimatedTime: "~85 minutes",
        estimatedCost: 0,
      };
    case "cost":
    default:
      return {
        backend: VideoBackend.GAMMA_MEDIUM,
        reason: "Free local generation",
        estimatedTime: "~25 minutes",
        estimatedCost: 0,
      };
  }
}
