/**
 * Image Generation Types
 * Translated from: arthur/generators/image.py
 */

// ============================================================================
// Image Backend Enum
// ============================================================================

export enum ImageBackend {
  // Cloud Gemini (Google) - Active
  GEMINI_PRO = "gemini-pro",

  // Deprecated - DO NOT USE
  // FLUX_SCHNELL = "flux-schnell",
  // FLUX_DEV = "flux-dev",
}

// ============================================================================
// Resolution Presets
// ============================================================================

export type AspectRatio = "1:1" | "16:9" | "9:16" | "4:3" | "3:4";

export interface Resolution {
  width: number;
  height: number;
  aspectRatio: AspectRatio;
  name: string;
}

export const PRESETS: Record<string, Resolution> = {
  // Square
  "square": { width: 1024, height: 1024, aspectRatio: "1:1", name: "Square" },
  "square-large": { width: 1536, height: 1536, aspectRatio: "1:1", name: "Square Large" },

  // Landscape 16:9
  "16:9": { width: 1344, height: 768, aspectRatio: "16:9", name: "HD Landscape" },
  "16:9-large": { width: 1920, height: 1088, aspectRatio: "16:9", name: "Full HD Landscape" },

  // Portrait 9:16
  "9:16": { width: 768, height: 1344, aspectRatio: "9:16", name: "HD Portrait" },
  "9:16-large": { width: 1088, height: 1920, aspectRatio: "9:16", name: "Full HD Portrait" },

  // LinkedIn optimized
  "linkedin-post": { width: 1200, height: 627, aspectRatio: "16:9", name: "LinkedIn Post" },
  "linkedin-carousel": { width: 1080, height: 1080, aspectRatio: "1:1", name: "LinkedIn Carousel" },
};

// ============================================================================
// Request Types
// ============================================================================

export interface GeminiImageRequest {
  prompt: string;
  aspectRatio?: AspectRatio;
  numberOfImages?: number;
}

export interface ImageGenerateOptions {
  prompt: string;
  preset?: keyof typeof PRESETS;
  width?: number;
  height?: number;
  backend?: ImageBackend;
  outputPath?: string;
}

// ============================================================================
// Result Types
// ============================================================================

export interface ImageResult {
  success: boolean;
  path?: string;
  backend: ImageBackend;
  prompt: string;
  resolution?: string;
  generationTime?: number;
  fileSize?: number;
  error?: string;
  errorCode?: string;
}

// ============================================================================
// Gemini API Types
// ============================================================================

export interface GeminiGenerateResponse {
  candidates: Array<{
    content: {
      parts: Array<{
        inline_data?: {
          mime_type: string;
          data: string; // base64
        };
        text?: string;
      }>;
    };
    finishReason: string;
  }>;
}

// ============================================================================
// Backend Selection
// ============================================================================

export function selectImageBackend(): ImageBackend {
  // Only Gemini is active (FLUX deprecated)
  return ImageBackend.GEMINI_PRO;
}
