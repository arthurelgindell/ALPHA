/**
 * Wan 2.6 Cloud API Client
 * Translated from: arthur/generators/wan26_api.py
 *
 * PiAPI integration for premium video generation features:
 * - Text-to-Video (T2V): Up to 15 seconds, 1080p, with audio
 * - Image-to-Video (I2V): Animate images with motion
 * - Reference-to-Video (R2V): Character/object preservation
 *
 * Pricing (as of 2025):
 * - 720p: $0.08/second
 * - 1080p: $0.12/second
 */

import config from "../config";
import { retryFetch } from "../utils/retry";
import type { VideoResult } from "../types";
import { VideoBackend } from "../types";

// ============================================================================
// Types
// ============================================================================

export type Wan26TaskType =
  | "wan26-txt2video"
  | "wan26-img2video"
  | "wan26-ref2video";

export type Wan26Resolution = "720P" | "1080P";
export type Wan26AspectRatio = "16:9" | "9:16" | "1:1" | "4:3" | "3:4";
export type Wan26Duration = 5 | 10 | 15;

export interface Wan26Result {
  success: boolean;
  taskId: string;
  videoUrl: string | null;
  status: string;
  prompt: string;
  resolution: Wan26Resolution;
  duration: number;
  costEstimate: number;
  error?: string;
  audioUrl?: string;
}

export interface Wan26TextToVideoOptions {
  prompt: string;
  duration?: Wan26Duration;
  resolution?: Wan26Resolution;
  aspectRatio?: Wan26AspectRatio;
  withAudio?: boolean;
  multiShot?: boolean;
  negativePrompt?: string;
  seed?: number;
  promptExtend?: boolean;
}

export interface Wan26ImageToVideoOptions {
  imageUrl: string;
  prompt: string;
  duration?: Wan26Duration;
  resolution?: Wan26Resolution;
  aspectRatio?: Wan26AspectRatio;
  withAudio?: boolean;
  seed?: number;
}

export interface Wan26ReferenceToVideoOptions {
  referenceUrl: string;
  prompt: string;
  duration?: 5 | 10; // R2V max is 10 seconds
  resolution?: Wan26Resolution;
  withAudio?: boolean;
}

interface Wan26TaskStatusResponse {
  status: string;
  videoUrl: string | null;
  audioUrl: string | null;
  error?: string;
}

// ============================================================================
// Pricing Constants
// ============================================================================

const PRICING: Record<Wan26Resolution, number> = {
  "720P": 0.08,
  "1080P": 0.12,
};

// ============================================================================
// Client Implementation
// ============================================================================

/**
 * Wan 2.6 cloud API client for premium video generation
 *
 * @example
 * ```typescript
 * const wan26 = new Wan26Client();
 *
 * // Text-to-video with audio
 * const result = await wan26.textToVideo({
 *   prompt: "A cinematic shot of a robot in a futuristic city",
 *   duration: 5,
 *   resolution: "720P",
 *   withAudio: true
 * });
 *
 * // Wait for completion
 * const videoUrl = await wan26.waitForCompletion(result.taskId);
 * if (videoUrl) {
 *   await wan26.downloadVideo(result.taskId, "output.mp4");
 * }
 * ```
 */
export class Wan26Client {
  private baseUrl = "https://api.piapi.ai";
  private apiKey: string;

  constructor(apiKey?: string) {
    this.apiKey = apiKey ?? process.env.WAN26_API_KEY ?? "";

    if (!this.apiKey) {
      throw new Error(
        "Wan 2.6 API key required. Set WAN26_API_KEY environment variable " +
        "or pass apiKey parameter. Get key from https://piapi.ai"
      );
    }
  }

  /**
   * Calculate estimated cost for generation
   */
  private calculateCost(duration: number, resolution: Wan26Resolution): number {
    const rate = PRICING[resolution] ?? 0.08;
    return duration * rate;
  }

  /**
   * Submit a generation task to the API
   */
  private async submitTask(
    taskType: Wan26TaskType,
    inputParams: Record<string, unknown>,
    webhookUrl?: string
  ): Promise<Wan26Result> {
    const requestBody: Record<string, unknown> = {
      model: "Wan",
      task_type: taskType,
      input: inputParams,
    };

    if (webhookUrl) {
      requestBody.config = {
        webhook_config: { endpoint: webhookUrl },
      };
    }

    try {
      const response = await retryFetch(
        `${this.baseUrl}/api/v1/task`,
        {
          method: "POST",
          headers: {
            "X-API-Key": this.apiKey,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(requestBody),
          signal: AbortSignal.timeout(120000),
        },
        { maxRetries: 3, initialDelay: 2000 }
      );

      const data = await response.json() as {
        code: number;
        message?: string;
        data?: {
          task_id?: string;
          status?: string;
        };
      };

      const prompt = String(inputParams.prompt ?? "");
      const resolution = (inputParams.resolution as Wan26Resolution) ?? "720P";
      const duration = Number(inputParams.duration ?? 5);

      if (data.code !== 200) {
        return {
          success: false,
          taskId: "",
          videoUrl: null,
          status: "failed",
          prompt,
          resolution,
          duration,
          costEstimate: 0,
          error: data.message ?? "Unknown error",
        };
      }

      const taskData = data.data ?? {};

      console.log(`Task submitted: ${taskData.task_id ?? "unknown"}`);

      return {
        success: true,
        taskId: taskData.task_id ?? "",
        videoUrl: null, // Available after completion
        status: taskData.status ?? "pending",
        prompt,
        resolution,
        duration,
        costEstimate: this.calculateCost(duration, resolution),
      };
    } catch (error) {
      const prompt = String(inputParams.prompt ?? "");
      const resolution = (inputParams.resolution as Wan26Resolution) ?? "720P";
      const duration = Number(inputParams.duration ?? 5);

      return {
        success: false,
        taskId: "",
        videoUrl: null,
        status: "error",
        prompt,
        resolution,
        duration,
        costEstimate: 0,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  /**
   * Generate video from text prompt
   */
  async textToVideo(options: Wan26TextToVideoOptions): Promise<Wan26Result> {
    const inputParams: Record<string, unknown> = {
      prompt: options.prompt,
      duration: options.duration ?? 5,
      resolution: options.resolution ?? "720P",
      aspect_ratio: options.aspectRatio ?? "16:9",
      audio: options.withAudio ?? true,
      shot_type: options.multiShot ? "multi" : "single",
      prompt_extend: options.promptExtend ?? true,
      watermark: false,
    };

    if (options.negativePrompt) {
      inputParams.negative_prompt = options.negativePrompt;
    }
    if (options.seed !== undefined) {
      inputParams.seed = options.seed;
    }

    return this.submitTask("wan26-txt2video", inputParams);
  }

  /**
   * Animate an image into video
   */
  async imageToVideo(options: Wan26ImageToVideoOptions): Promise<Wan26Result> {
    const inputParams: Record<string, unknown> = {
      image_url: options.imageUrl,
      prompt: options.prompt,
      duration: options.duration ?? 5,
      resolution: options.resolution ?? "720P",
      aspect_ratio: options.aspectRatio ?? "16:9",
      audio: options.withAudio ?? false,
      watermark: false,
    };

    if (options.seed !== undefined) {
      inputParams.seed = options.seed;
    }

    return this.submitTask("wan26-img2video", inputParams);
  }

  /**
   * Generate video preserving character/object from reference
   * Note: R2V supports up to 10 seconds max (vs 15 for T2V/I2V)
   */
  async referenceToVideo(options: Wan26ReferenceToVideoOptions): Promise<Wan26Result> {
    // R2V max duration is 10 seconds
    const duration = Math.min(options.duration ?? 5, 10) as 5 | 10;

    const inputParams: Record<string, unknown> = {
      video_url: options.referenceUrl,
      prompt: options.prompt,
      duration,
      resolution: options.resolution ?? "720P",
      audio: options.withAudio ?? false,
      watermark: false,
    };

    return this.submitTask("wan26-ref2video", inputParams);
  }

  /**
   * Check status of a generation task
   */
  async getTaskStatus(taskId: string): Promise<Wan26TaskStatusResponse> {
    try {
      const response = await retryFetch(
        `${this.baseUrl}/api/v1/task/${taskId}`,
        {
          method: "GET",
          headers: { "X-API-Key": this.apiKey },
          signal: AbortSignal.timeout(30000),
        },
        { maxRetries: 3, initialDelay: 1000 }
      );

      const data = await response.json() as {
        code: number;
        message?: string;
        data?: {
          status?: string;
          output?: {
            video_url?: string;
            audio_url?: string;
          };
          error?: {
            message?: string;
          };
        };
      };

      if (data.code !== 200) {
        console.warn(`Task ${taskId} status check failed: ${data.message}`);
        return { status: "error", videoUrl: null, audioUrl: null, error: data.message };
      }

      const taskData = data.data ?? {};
      const output = taskData.output ?? {};

      return {
        status: taskData.status ?? "unknown",
        videoUrl: output.video_url ?? null,
        audioUrl: output.audio_url ?? null,
        error: taskData.error?.message,
      };
    } catch (error) {
      console.error(`Error checking task ${taskId}:`, error);
      return {
        status: "error",
        videoUrl: null,
        audioUrl: null,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  /**
   * Wait for task completion and return video URL
   *
   * @param taskId - Task ID to monitor
   * @param timeout - Max wait time in ms (default: 5 minutes)
   * @param pollInterval - Ms between status checks (default: 5 seconds)
   * @returns Video URL if successful, null if failed/timeout
   */
  async waitForCompletion(
    taskId: string,
    timeout = 300000,
    pollInterval = 5000
  ): Promise<string | null> {
    const startTime = Date.now();
    console.log(`Waiting for task ${taskId} (timeout: ${timeout / 1000}s)`);

    while (Date.now() - startTime < timeout) {
      const status = await this.getTaskStatus(taskId);
      const elapsed = Math.round((Date.now() - startTime) / 1000);

      if (status.status.toLowerCase() === "completed") {
        console.log(`Task ${taskId} completed in ${elapsed}s`);
        return status.videoUrl;
      }

      if (status.status.toLowerCase() === "failed") {
        console.error(`Task ${taskId} failed: ${status.error ?? "unknown"}`);
        return null;
      }

      await Bun.sleep(pollInterval);
    }

    console.warn(`Task ${taskId} timed out after ${timeout / 1000}s`);
    return null;
  }

  /**
   * Download completed video to local path
   */
  async downloadVideo(
    taskId: string,
    outputPath: string,
    includeAudio = true
  ): Promise<boolean> {
    const status = await this.getTaskStatus(taskId);

    if (status.status.toLowerCase() !== "completed") {
      return false;
    }

    const videoUrl = status.videoUrl;
    if (!videoUrl) {
      return false;
    }

    try {
      // Download video
      console.log(`Downloading video from task ${taskId}`);
      const response = await fetch(videoUrl, {
        signal: AbortSignal.timeout(120000),
      });

      if (!response.ok) {
        console.error(`HTTP error downloading video: ${response.status}`);
        return false;
      }

      const videoData = await response.arrayBuffer();
      await Bun.write(outputPath, videoData);
      console.log(`Video saved to ${outputPath} (${(videoData.byteLength / 1e6).toFixed(1)}MB)`);

      // Download audio if available and requested
      if (includeAudio && status.audioUrl) {
        const audioPath = outputPath.replace(/\.\w+$/, ".audio.mp3");
        const audioResponse = await fetch(status.audioUrl, {
          signal: AbortSignal.timeout(60000),
        });

        if (audioResponse.ok) {
          const audioData = await audioResponse.arrayBuffer();
          await Bun.write(audioPath, audioData);
          console.log(`Audio saved to ${audioPath}`);
        }
      }

      return true;
    } catch (error) {
      console.error(`Error downloading video:`, error);
      return false;
    }
  }

  /**
   * High-level method: Generate, wait, and download in one call
   */
  async generateAndDownload(
    options: Wan26TextToVideoOptions,
    outputPath: string
  ): Promise<VideoResult> {
    // Determine backend based on options
    let backend: VideoBackend;
    if (options.multiShot) {
      backend = VideoBackend.WAN26_MULTISHOT;
    } else if (options.withAudio) {
      backend = VideoBackend.WAN26_AUDIO;
    } else if (options.resolution === "1080P") {
      backend = VideoBackend.WAN26_1080P;
    } else {
      backend = VideoBackend.WAN26_720P;
    }

    const startTime = Date.now();

    // Submit generation
    const result = await this.textToVideo(options);

    if (!result.success) {
      return {
        success: false,
        backend,
        prompt: options.prompt,
        error: result.error,
      };
    }

    // Wait for completion
    const videoUrl = await this.waitForCompletion(result.taskId, 600000);

    if (!videoUrl) {
      return {
        success: false,
        backend,
        prompt: options.prompt,
        error: "Generation timed out or failed",
      };
    }

    // Download video
    const downloadSuccess = await this.downloadVideo(result.taskId, outputPath);
    const generationTime = (Date.now() - startTime) / 1000;

    if (downloadSuccess) {
      return {
        success: true,
        path: outputPath,
        backend,
        prompt: options.prompt,
        duration: options.duration ?? 5,
        generationTime,
      };
    } else {
      return {
        success: false,
        backend,
        prompt: options.prompt,
        error: "Failed to download video",
      };
    }
  }
}
