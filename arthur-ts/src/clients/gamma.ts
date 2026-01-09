/**
 * GAMMA HunyuanVideo Client
 * Translated from: arthur/generators/video.py (generate_gamma method)
 *
 * GAMMA (100.102.59.5:8421) runs HunyuanVideo-1.5 on NVIDIA GB10 GPU.
 * Provides high-quality video generation at $0 cost.
 */

import config from "../config";
import { retryFetch } from "../utils/retry";
import type { VideoResult, GammaQuality, GammaGenerateRequest } from "../types";
import { VideoBackend } from "../types";

export interface GammaHealthResponse {
  status: "healthy" | "error";
  gpu_available?: boolean;
  gpu_name?: string;
  model_loaded?: boolean;
  error?: string;
}

export interface GammaGenerateResponse {
  success: boolean;
  job_id?: string;
  video_path?: string;
  filename?: string;
  download_url?: string;
  generation_time_seconds?: number;
  file_size_mb?: number;
  error?: string;
}

export interface GammaVideoInfo {
  filename: string;
  path: string;
  created: string;
}

export interface GammaListResponse {
  count: number;
  videos: GammaVideoInfo[];
}

// Default frame counts by quality preset
const DEFAULT_FRAMES: Record<GammaQuality, number> = {
  test: 25,      // ~2s at 12fps
  medium: 61,    // ~5s
  high: 81,      // ~6.5s
  maximum: 97,   // ~8s
};

/**
 * GAMMA HunyuanVideo client for local video generation
 *
 * @example
 * ```typescript
 * const gamma = new GammaClient();
 *
 * // Check health
 * const health = await gamma.checkHealth();
 * console.log(`GPU: ${health.gpu_name}`);
 *
 * // Generate video
 * const result = await gamma.generate({
 *   prompt: "A cinematic shot of a robot in a futuristic city",
 *   quality: "medium",
 * });
 *
 * if (result.success) {
 *   console.log(`Video saved: ${result.path}`);
 * }
 * ```
 */
export class GammaClient {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl ?? config.urls.gamma;
  }

  /**
   * Check GAMMA endpoint health
   */
  async checkHealth(): Promise<GammaHealthResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        signal: AbortSignal.timeout(10000),
      });

      if (!response.ok) {
        return { status: "error", error: `HTTP ${response.status}` };
      }

      return await response.json();
    } catch (error) {
      return {
        status: "error",
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  /**
   * List videos stored on GAMMA server
   */
  async listVideos(): Promise<GammaVideoInfo[]> {
    try {
      const response = await fetch(`${this.baseUrl}/videos/list`, {
        signal: AbortSignal.timeout(10000),
      });

      if (!response.ok) {
        return [];
      }

      const data: GammaListResponse = await response.json();
      return data.videos ?? [];
    } catch {
      return [];
    }
  }

  /**
   * Generate video using GAMMA (HunyuanVideo-1.5)
   *
   * @param options - Generation options
   * @param options.prompt - Cinematic prompt (use Five-Part Formula)
   * @param options.quality - Quality preset (test, medium, high, maximum)
   * @param options.numFrames - Override frame count (auto-calculated if omitted)
   * @param options.seed - Random seed for reproducibility
   * @param options.downloadPath - Custom download path (optional)
   *
   * @returns VideoResult with path and metadata
   */
  async generate(options: {
    prompt: string;
    quality?: GammaQuality;
    numFrames?: number;
    seed?: number;
    downloadPath?: string;
  }): Promise<VideoResult> {
    const quality = options.quality ?? "medium";
    const numFrames = options.numFrames ?? DEFAULT_FRAMES[quality];
    const backend = `gamma-${quality}` as VideoBackend;

    const requestData: GammaGenerateRequest = {
      prompt: options.prompt,
      quality,
      num_frames: numFrames,
    };

    if (options.seed !== undefined) {
      requestData.seed = options.seed;
    }

    const startTime = Date.now();

    try {
      // Submit generation request
      // GAMMA can take up to 90 minutes for maximum quality
      const response = await retryFetch(
        `${this.baseUrl}/generate`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(requestData),
          // 2 hour timeout for high quality
          signal: AbortSignal.timeout(7200000),
        },
        { maxRetries: 2, initialDelay: 5000 }
      );

      if (!response.ok) {
        return {
          success: false,
          backend,
          prompt: options.prompt,
          error: `HTTP ${response.status}: ${await response.text()}`,
        };
      }

      const result: GammaGenerateResponse = await response.json();

      if (!result.success) {
        return {
          success: false,
          backend,
          prompt: options.prompt,
          error: result.error ?? "Unknown error",
        };
      }

      const generationTime = (Date.now() - startTime) / 1000;
      const filename = result.filename!;

      // Determine download path
      const downloadPath = options.downloadPath ?? `${config.paths.videosDir}/${filename}`;

      // Download video
      const downloadResponse = await retryFetch(
        `${this.baseUrl}/download/${filename}`,
        { signal: AbortSignal.timeout(120000) },
        { maxRetries: 3 }
      );

      if (!downloadResponse.ok) {
        return {
          success: false,
          backend,
          prompt: options.prompt,
          error: `Download failed: HTTP ${downloadResponse.status}`,
        };
      }

      // Write to disk using Bun's optimized file I/O
      const videoData = await downloadResponse.arrayBuffer();
      await Bun.write(downloadPath, videoData);

      return {
        success: true,
        path: downloadPath,
        backend,
        prompt: options.prompt,
        duration: numFrames / 12, // frames / fps
        generationTime,
        fileSize: videoData.byteLength,
      };
    } catch (error) {
      return {
        success: false,
        backend,
        prompt: options.prompt,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  /**
   * Download a specific video from GAMMA by filename
   */
  async downloadVideo(
    filename: string,
    outputPath: string
  ): Promise<{ success: boolean; error?: string }> {
    try {
      const response = await retryFetch(
        `${this.baseUrl}/download/${filename}`,
        { signal: AbortSignal.timeout(120000) },
        { maxRetries: 3 }
      );

      if (!response.ok) {
        return { success: false, error: `HTTP ${response.status}` };
      }

      const videoData = await response.arrayBuffer();
      await Bun.write(outputPath, videoData);

      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }
}

// Export singleton instance for convenience
export const gamma = new GammaClient();
