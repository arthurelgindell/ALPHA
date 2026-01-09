/**
 * Veo 3.1 REST API Client
 * Pure TypeScript implementation - NO Python SDK
 *
 * Veo is Google's video generation model accessed via REST API.
 * Pricing: $0.15/sec (fast) to $0.40/sec (standard)
 *
 * API Flow:
 * 1. POST to predictLongRunning → returns operation name
 * 2. Poll GET on operation name until done=true
 * 3. Download video from response URI
 */

import config from "../config";
import { retryFetch } from "../utils/retry";
import type { VideoResult } from "../types";
import { VideoBackend } from "../types";

// ============================================================================
// Types
// ============================================================================

export type VeoModel = "veo-3.1-generate-preview" | "veo-3.1-fast-generate-preview";
export type VeoAspectRatio = "16:9" | "9:16" | "1:1";

export interface VeoGenerateOptions {
  prompt: string;
  model?: VeoModel;
  aspectRatio?: VeoAspectRatio;
  negativePrompt?: string;
  durationSeconds?: number;
}

interface VeoOperation {
  name: string;
  done: boolean;
  error?: {
    code: number;
    message: string;
  };
  response?: {
    generateVideoResponse: {
      generatedSamples: Array<{
        video: {
          uri: string;
        };
      }>;
    };
  };
}

// ============================================================================
// Client Implementation
// ============================================================================

/**
 * Veo 3.1 REST API client for video generation
 *
 * @example
 * ```typescript
 * const veo = new VeoClient();
 *
 * // Generate video
 * const result = await veo.generate({
 *   prompt: "A cinematic shot of a robot in a futuristic city",
 *   model: "veo-3.1-fast-generate-preview",
 *   aspectRatio: "16:9"
 * });
 *
 * if (result.success) {
 *   console.log(`Video saved: ${result.path}`);
 * }
 * ```
 */
export class VeoClient {
  private baseUrl = "https://generativelanguage.googleapis.com/v1beta";
  private apiKey: string;

  constructor(apiKey?: string) {
    this.apiKey = apiKey ?? process.env.GEMINI_API_KEY ?? config.apiKeys?.google ?? "";

    if (!this.apiKey) {
      throw new Error(
        "Veo API key required. Set GEMINI_API_KEY environment variable " +
        "or pass apiKey parameter."
      );
    }
  }

  /**
   * Start video generation (returns operation for polling)
   */
  private async startGeneration(options: VeoGenerateOptions): Promise<string> {
    const model = options.model ?? "veo-3.1-fast-generate-preview";

    const requestBody: Record<string, unknown> = {
      instances: [{
        prompt: options.prompt,
      }],
      parameters: {
        aspectRatio: options.aspectRatio ?? "16:9",
      },
    };

    if (options.negativePrompt) {
      (requestBody.parameters as Record<string, unknown>).negativePrompt = options.negativePrompt;
    }

    const response = await retryFetch(
      `${this.baseUrl}/models/${model}:predictLongRunning`,
      {
        method: "POST",
        headers: {
          "x-goog-api-key": this.apiKey,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
        signal: AbortSignal.timeout(60000),
      },
      { maxRetries: 2, initialDelay: 2000 }
    );

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Veo API error: HTTP ${response.status} - ${errorText}`);
    }

    const data = await response.json() as { name: string };
    return data.name;
  }

  /**
   * Poll operation status until complete
   */
  private async pollOperation(
    operationName: string,
    timeout = 600000,
    pollInterval = 10000
  ): Promise<VeoOperation> {
    const startTime = Date.now();
    console.log(`Polling Veo operation: ${operationName}`);

    while (Date.now() - startTime < timeout) {
      const response = await fetch(
        `${this.baseUrl}/${operationName}`,
        {
          headers: { "x-goog-api-key": this.apiKey },
          signal: AbortSignal.timeout(30000),
        }
      );

      if (!response.ok) {
        throw new Error(`Poll error: HTTP ${response.status}`);
      }

      const operation: VeoOperation = await response.json();

      if (operation.done) {
        if (operation.error) {
          throw new Error(`Veo error: ${operation.error.message}`);
        }
        return operation;
      }

      const elapsed = Math.round((Date.now() - startTime) / 1000);
      console.log(`  Waiting... (${elapsed}s elapsed)`);
      await Bun.sleep(pollInterval);
    }

    throw new Error(`Veo operation timed out after ${timeout / 1000}s`);
  }

  /**
   * Download video from URI
   */
  private async downloadVideo(uri: string, outputPath: string): Promise<void> {
    console.log(`Downloading video from Veo...`);

    const response = await retryFetch(
      uri,
      {
        headers: { "x-goog-api-key": this.apiKey },
        signal: AbortSignal.timeout(120000),
      },
      { maxRetries: 3 }
    );

    if (!response.ok) {
      throw new Error(`Download failed: HTTP ${response.status}`);
    }

    const videoData = await response.arrayBuffer();
    await Bun.write(outputPath, videoData);
    console.log(`Video saved: ${outputPath} (${(videoData.byteLength / 1e6).toFixed(1)}MB)`);
  }

  /**
   * Generate video using Veo 3.1 API
   *
   * @param options - Generation options
   * @param outputPath - Path to save the video (optional)
   * @returns VideoResult with path and metadata
   */
  async generate(
    options: VeoGenerateOptions,
    outputPath?: string
  ): Promise<VideoResult> {
    const model = options.model ?? "veo-3.1-fast-generate-preview";
    const backend = model.includes("fast")
      ? VideoBackend.VEO_FAST
      : VideoBackend.VEO_STANDARD;

    const startTime = Date.now();

    try {
      // Step 1: Start generation
      console.log(`Starting Veo generation (${model})...`);
      const operationName = await this.startGeneration(options);

      // Step 2: Poll until complete
      const operation = await this.pollOperation(operationName);

      // Step 3: Extract video URI
      const videoUri = operation.response?.generateVideoResponse?.generatedSamples?.[0]?.video?.uri;

      if (!videoUri) {
        return {
          success: false,
          backend,
          prompt: options.prompt,
          error: "No video URI in response",
        };
      }

      // Step 4: Download video
      const finalPath = outputPath ?? `${config.paths.videosDir}/veo_${Date.now()}.mp4`;
      await this.downloadVideo(videoUri, finalPath);

      const generationTime = (Date.now() - startTime) / 1000;

      return {
        success: true,
        path: finalPath,
        backend,
        prompt: options.prompt,
        duration: options.durationSeconds,
        generationTime,
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
   * Generate video with the fast model (cheaper, faster)
   */
  async generateFast(
    prompt: string,
    options: Omit<VeoGenerateOptions, "prompt" | "model"> = {},
    outputPath?: string
  ): Promise<VideoResult> {
    return this.generate(
      { ...options, prompt, model: "veo-3.1-fast-generate-preview" },
      outputPath
    );
  }

  /**
   * Generate video with the standard model (higher quality)
   */
  async generateStandard(
    prompt: string,
    options: Omit<VeoGenerateOptions, "prompt" | "model"> = {},
    outputPath?: string
  ): Promise<VideoResult> {
    return this.generate(
      { ...options, prompt, model: "veo-3.1-generate-preview" },
      outputPath
    );
  }
}

// Lazy singleton - only initializes when accessed
let _veo: VeoClient | null = null;
export function getVeoClient(): VeoClient {
  if (!_veo) {
    _veo = new VeoClient();
  }
  return _veo;
}
