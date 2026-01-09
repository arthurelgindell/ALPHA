/**
 * ARTHUR Configuration
 * Central configuration for all infrastructure endpoints and settings
 *
 * Translated from: arthur/config.py
 * Platform: Apple Silicon (ARM64 native)
 */

import { join } from "path";

// ============================================================================
// Infrastructure Endpoints
// ============================================================================

export interface LMStudioEndpoint {
  name: string;
  host: string;
  port: number;
  role: "strategist" | "executor";
  description: string;
}

export interface VisionEndpoint {
  name: string;
  baseUrl: string;
  modelId: string;
  description: string;
}

export interface GenerationEndpoint {
  name: string;
  endpointType: "local" | "api" | "remote";
  host?: string;
  port?: number;
  apiKey?: string;
}

// ============================================================================
// Default Infrastructure Configuration
// ============================================================================

// LM Studio Endpoints
export const ALPHA_LM: LMStudioEndpoint = {
  name: "DeepSeek V3.1",
  host: "100.65.29.44",
  port: 1234,
  role: "strategist",
  description: "Strategic planning, complex reasoning, storyboarding",
};

export const BETA_LM: LMStudioEndpoint = {
  name: "Nemotron",
  host: "100.84.202.68",
  port: 1234,
  role: "executor",
  description: "Structured output, prompt engineering, task execution",
};

// Vision Model Endpoint (GLM-4.6V-Flash)
export const VISION_ALPHA: VisionEndpoint = {
  name: "GLM-4.6V-Flash",
  baseUrl: "http://127.0.0.1:1234/v1", // Local LM Studio
  modelId: "glm-4.6v-flash",
  description: "Vision-language model for image/video analysis",
};

// ============================================================================
// Media Generation Endpoints (Production-Grade Only)
// ============================================================================
// NOTE: FLUX.1 and Wan 2.2 REMOVED 2026-01-06 - quality unacceptable

// Video Generation - GAMMA HunyuanVideo (Local, free)
export const GAMMA_VIDEO: GenerationEndpoint = {
  name: "HunyuanVideo-1.5",
  endpointType: "remote",
  host: "100.102.59.5",
  port: 8421,
};

// Video Generation - Veo 3.1 (API, premium quality)
export const VEO_VIDEO: GenerationEndpoint = {
  name: "Veo 3.1",
  endpointType: "api",
  apiKey: process.env.GEMINI_API_KEY,
};

// Video Generation - Wan 2.6 API (production-grade)
export const WAN26_API: GenerationEndpoint = {
  name: "Wan 2.6 API",
  endpointType: "api",
  apiKey: process.env.WAN26_API_KEY,
};

// Image Generation - Gemini Pro (API)
export const GEMINI_IMAGE: GenerationEndpoint = {
  name: "Gemini Pro Image",
  endpointType: "api",
  apiKey: process.env.GEMINI_API_KEY,
};

// ============================================================================
// Voice Generation (F5-TTS on BETA)
// ============================================================================

export interface VoiceConfig {
  betaHost: string;
  pythonEnv: string;
  ttsScript: string;
  outputDir: string;
  referenceVoice: string;
}

export const VOICE: VoiceConfig = {
  betaHost: "beta",
  pythonEnv: "/Volumes/MODELS/mlx-env/bin/python3",
  ttsScript: "/Volumes/CLAUDE/SPHERE/scripts/voice-pro.py",
  outputDir: "/Volumes/MODELS/tts/output",
  referenceVoice: "/Volumes/MODELS/tts/reference/default_voice.wav",
};

// ============================================================================
// Postmark Email Configuration
// ============================================================================

export interface PostmarkConfig {
  serverToken: string | undefined;
  defaultSender: string;
  defaultRecipient: string;
}

export const POSTMARK: PostmarkConfig = {
  serverToken: process.env.POSTMARK_SERVER_TOKEN,
  defaultSender: "alerts@dellight.ai",
  defaultRecipient: "arthur.dell@dellight.ai",
};

// ============================================================================
// Paths Configuration
// ============================================================================

export interface PathConfig {
  projectRoot: string;
  scriptsDir: string;
  imagesDir: string;
  videosDir: string;
  carouselsDir: string;
  studioMount: string;
  studioVideo: string;
  studioImages: string;
  studioCarousels: string;
}

const PROJECT_ROOT = "/Users/arthurdell/ARTHUR";
const STUDIO_MOUNT = "/Volumes/STUDIO";

export const PATHS: PathConfig = {
  projectRoot: PROJECT_ROOT,
  scriptsDir: join(PROJECT_ROOT, "scripts"),
  imagesDir: join(PROJECT_ROOT, "images"),
  videosDir: join(PROJECT_ROOT, "videos"),
  carouselsDir: join(PROJECT_ROOT, "carousels"),
  studioMount: STUDIO_MOUNT,
  studioVideo: join(STUDIO_MOUNT, "VIDEO"),
  studioImages: join(STUDIO_MOUNT, "IMAGES"),
  studioCarousels: join(STUDIO_MOUNT, "CAROUSELS"),
};

// ============================================================================
// Design System
// ============================================================================

export interface DesignSystem {
  backgroundDark: string;
  backgroundLight: string;
  accentAmber: string;
  textPrimary: string;
  textSecondary: string;
  fontHeader: string;
  fontBody: string;
}

export const DESIGN: DesignSystem = {
  backgroundDark: "#1a1a1a",
  backgroundLight: "#2d2d2d",
  accentAmber: "#f59e0b",
  textPrimary: "#ffffff",
  textSecondary: "#a0a0a0",
  fontHeader: "Inter",
  fontBody: "system-ui, sans-serif",
};

// ============================================================================
// Apple Silicon Optimizations
// ============================================================================

export const NATIVE_BINARIES = {
  ffmpeg: "/opt/homebrew/bin/ffmpeg",
  ffprobe: "/opt/homebrew/bin/ffprobe",
  ssh: "/usr/bin/ssh",
  scp: "/usr/bin/scp",
} as const;

export const FFMPEG_HWACCEL = {
  videoToolbox: ["-hwaccel", "videotoolbox"],
  h264Encoder: ["-c:v", "h264_videotoolbox"],
  hevcEncoder: ["-c:v", "hevc_videotoolbox"],
  aacEncoder: ["-c:a", "aac_at"],
} as const;

// ============================================================================
// API Endpoints (Computed)
// ============================================================================

export function getLMStudioUrl(endpoint: LMStudioEndpoint): string {
  return `http://${endpoint.host}:${endpoint.port}/v1`;
}

export function getGammaUrl(): string {
  return `http://${GAMMA_VIDEO.host}:${GAMMA_VIDEO.port}`;
}

// Google API base URLs
export const GOOGLE_API = {
  generativeLanguage: "https://generativelanguage.googleapis.com/v1beta",
  veoModel: "models/veo-3.1-fast-generate-preview",
  veoModelStandard: "models/veo-3.1-generate-preview",
  geminiImageModel: "models/gemini-3-pro-image-preview",
} as const;

// Wan 2.6 API
export const WAN26_API_URL = "https://api.piapi.ai";

// ============================================================================
// Export all for convenience
// ============================================================================

export const config = {
  lm: { alpha: ALPHA_LM, beta: BETA_LM },
  vision: VISION_ALPHA,
  generation: { gamma: GAMMA_VIDEO, veo: VEO_VIDEO, wan26: WAN26_API, gemini: GEMINI_IMAGE },
  voice: VOICE,
  postmark: POSTMARK,
  paths: PATHS,
  design: DESIGN,
  binaries: NATIVE_BINARIES,
  ffmpeg: FFMPEG_HWACCEL,
  urls: {
    alphaLM: getLMStudioUrl(ALPHA_LM),
    betaLM: getLMStudioUrl(BETA_LM),
    gamma: getGammaUrl(),
    google: GOOGLE_API,
    wan26: WAN26_API_URL,
  },
  apiKeys: {
    google: process.env.GEMINI_API_KEY,
    wan26: process.env.WAN26_API_KEY,
    postmark: process.env.POSTMARK_SERVER_TOKEN,
  },
};

export default config;
