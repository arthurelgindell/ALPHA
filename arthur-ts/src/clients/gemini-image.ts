/**
 * Gemini Image Generation REST API Client
 * Pure TypeScript implementation - NO Python SDK
 *
 * Uses Google's Gemini models for image generation via REST API.
 * Model: gemini-3-pro-image-preview (primary)
 *
 * API Flow:
 * 1. POST to generateContent with text prompt
 * 2. Response contains base64-encoded image data
 * 3. Decode and save to disk
 */

import config from "../config";
import { retryFetch } from "../utils/retry";
import type { ImageResult, AspectRatio } from "../types";
import { ImageBackend } from "../types";

// ============================================================================
// Types
// ============================================================================

export type GeminiImageModel =
  | "gemini-3-pro-image-preview"
  | "gemini-2.5-flash-image";

export interface GeminiImageOptions {
  prompt: string;
  model?: GeminiImageModel;
  aspectRatio?: AspectRatio;
  numberOfImages?: number;
}

interface GeminiImageResponse {
  candidates?: Array<{
    content: {
      parts: Array<{
        inlineData?: {
          mimeType: string;
          data: string; // base64
        };
        text?: string;
      }>;
    };
    finishReason: string;
  }>;
  error?: {
    code: number;
    message: string;
  };
}

// ============================================================================
// Client Implementation
// ============================================================================

/**
 * Gemini Image REST API client for image generation
 *
 * @example
 * ```typescript
 * const gemini = new GeminiImageClient();
 *
 * // Generate image
 * const result = await gemini.generate({
 *   prompt: "A minimalist logo for a coffee shop",
 *   aspectRatio: "1:1"
 * });
 *
 * if (result.success) {
 *   console.log(`Image saved: ${result.path}`);
 * }
 * ```
 */
export class GeminiImageClient {
  private baseUrl = "https://generativelanguage.googleapis.com/v1beta";
  private apiKey: string;

  constructor(apiKey?: string) {
    this.apiKey = apiKey ?? process.env.GEMINI_API_KEY ?? config.apiKeys?.google ?? "";

    if (!this.apiKey) {
      throw new Error(
        "Gemini API key required. Set GEMINI_API_KEY environment variable " +
        "or pass apiKey parameter."
      );
    }
  }

  /**
   * Generate image from text prompt
   *
   * @param options - Generation options
   * @param outputPath - Path to save the image (optional)
   * @returns ImageResult with path and metadata
   */
  async generate(
    options: GeminiImageOptions,
    outputPath?: string
  ): Promise<ImageResult> {
    const model = options.model ?? "gemini-3-pro-image-preview";
    const startTime = Date.now();

    const requestBody: Record<string, unknown> = {
      contents: [{
        parts: [{ text: options.prompt }],
      }],
      generationConfig: {
        responseModalities: ["IMAGE"],
        imageConfig: {
          aspectRatio: options.aspectRatio ?? "1:1",
        },
      },
    };

    try {
      console.log(`Generating image with ${model}...`);

      const response = await retryFetch(
        `${this.baseUrl}/models/${model}:generateContent`,
        {
          method: "POST",
          headers: {
            "x-goog-api-key": this.apiKey,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(requestBody),
          signal: AbortSignal.timeout(120000),
        },
        { maxRetries: 2, initialDelay: 2000 }
      );

      if (!response.ok) {
        const errorText = await response.text();
        return {
          success: false,
          backend: ImageBackend.GEMINI_PRO,
          prompt: options.prompt,
          error: `Gemini API error: HTTP ${response.status} - ${errorText}`,
        };
      }

      const data: GeminiImageResponse = await response.json();

      if (data.error) {
        return {
          success: false,
          backend: ImageBackend.GEMINI_PRO,
          prompt: options.prompt,
          error: `Gemini error: ${data.error.message}`,
        };
      }

      // Extract base64 image data from response
      const candidates = data.candidates ?? [];
      let imageData: string | null = null;
      let mimeType = "image/png";

      for (const candidate of candidates) {
        for (const part of candidate.content.parts) {
          if (part.inlineData?.data) {
            imageData = part.inlineData.data;
            mimeType = part.inlineData.mimeType;
            break;
          }
        }
        if (imageData) break;
      }

      if (!imageData) {
        return {
          success: false,
          backend: ImageBackend.GEMINI_PRO,
          prompt: options.prompt,
          error: "No image data in response",
        };
      }

      // Decode base64 and save to disk
      const extension = mimeType.includes("jpeg") ? "jpg" : "png";
      const finalPath = outputPath ?? `${config.paths.imagesDir}/gemini_${Date.now()}.${extension}`;

      // Decode base64 to binary
      const binaryData = Buffer.from(imageData, "base64");
      await Bun.write(finalPath, binaryData);

      const generationTime = (Date.now() - startTime) / 1000;

      console.log(`Image saved: ${finalPath} (${(binaryData.byteLength / 1024).toFixed(1)}KB)`);

      return {
        success: true,
        path: finalPath,
        backend: ImageBackend.GEMINI_PRO,
        prompt: options.prompt,
        resolution: options.aspectRatio ?? "1:1",
        generationTime,
        fileSize: binaryData.byteLength,
      };
    } catch (error) {
      return {
        success: false,
        backend: ImageBackend.GEMINI_PRO,
        prompt: options.prompt,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  /**
   * Generate square image (1:1 aspect ratio)
   */
  async generateSquare(
    prompt: string,
    outputPath?: string
  ): Promise<ImageResult> {
    return this.generate({ prompt, aspectRatio: "1:1" }, outputPath);
  }

  /**
   * Generate landscape image (16:9 aspect ratio)
   */
  async generateLandscape(
    prompt: string,
    outputPath?: string
  ): Promise<ImageResult> {
    return this.generate({ prompt, aspectRatio: "16:9" }, outputPath);
  }

  /**
   * Generate portrait image (9:16 aspect ratio)
   */
  async generatePortrait(
    prompt: string,
    outputPath?: string
  ): Promise<ImageResult> {
    return this.generate({ prompt, aspectRatio: "9:16" }, outputPath);
  }

  /**
   * Generate LinkedIn-optimized carousel image (1080x1080)
   */
  async generateLinkedInCarousel(
    prompt: string,
    outputPath?: string
  ): Promise<ImageResult> {
    return this.generate({ prompt, aspectRatio: "1:1" }, outputPath);
  }

  /**
   * Generate LinkedIn-optimized post image (1200x627 ~ 16:9)
   */
  async generateLinkedInPost(
    prompt: string,
    outputPath?: string
  ): Promise<ImageResult> {
    return this.generate({ prompt, aspectRatio: "16:9" }, outputPath);
  }
}

// Lazy singleton - only initializes when accessed
let _geminiImage: GeminiImageClient | null = null;
export function getGeminiImageClient(): GeminiImageClient {
  if (!_geminiImage) {
    _geminiImage = new GeminiImageClient();
  }
  return _geminiImage;
}
