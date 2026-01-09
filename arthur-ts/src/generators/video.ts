/**
 * VideoGenerator - Unified Video Generation Interface
 * Translated from: arthur/generators/video.py
 *
 * Orchestrates multiple video generation backends:
 * - GAMMA HunyuanVideo (local, free)
 * - Veo 3.1 (Google API, fast)
 * - Wan 2.6 (PiAPI, premium features)
 */

import { GammaClient } from "../clients/gamma";
import { Wan26Client } from "../clients/wan26";
import { VeoClient } from "../clients/veo";
import { muxAudio } from "../utils/ffmpeg";
import config from "../config";
import type { VideoResult, GammaQuality } from "../types";
import { VideoBackend } from "../types";

// Re-export muxAudio for convenience
export { muxAudio } from "../utils/ffmpeg";

export interface GenerateOptions {
  prompt: string;
  backend?: VideoBackend;
  outputPath?: string;
}

export interface GammaOptions {
  prompt: string;
  quality?: GammaQuality;
  numFrames?: number;
  seed?: number;
  outputPath?: string;
}

export interface VeoOptions {
  prompt: string;
  fast?: boolean;
  aspectRatio?: "16:9" | "9:16" | "1:1";
  negativePrompt?: string;
  outputPath?: string;
}

export interface Wan26Options {
  prompt: string;
  duration?: 5 | 10 | 15;
  resolution?: "720P" | "1080P";
  aspectRatio?: "16:9" | "9:16" | "1:1";
  withAudio?: boolean;
  multiShot?: boolean;
  outputPath?: string;
}

export type BackendPriority = "speed" | "quality" | "cost";

export interface BackendRequirements {
  needsAudio?: boolean;
  needs1080p?: boolean;
  needsMultiShot?: boolean;
  isHeroShot?: boolean;
}

/**
 * Unified video generation interface
 *
 * @example
 * ```typescript
 * const gen = new VideoGenerator();
 *
 * // Generate with GAMMA (local, high quality)
 * const result = await gen.generateGamma({
 *   prompt: "Cinematic shot of a robot walking",
 *   quality: "medium"
 * });
 *
 * // Generate with Veo (fast turnaround)
 * const result = await gen.generateVeo({
 *   prompt: "Product placement shot",
 *   fast: true
 * });
 *
 * // Auto-select backend based on priority
 * const backend = gen.selectBackend("quality", { isHeroShot: true });
 * ```
 */
export class VideoGenerator {
  private gamma: GammaClient;
  private veo: VeoClient | null = null;
  private wan26: Wan26Client | null = null;

  constructor() {
    this.gamma = new GammaClient();

    // Lazy init clients that require API keys
    if (process.env.GEMINI_API_KEY) {
      try {
        this.veo = new VeoClient();
      } catch {
        console.warn("VeoClient not available (missing API key)");
      }
    }

    if (process.env.WAN26_API_KEY) {
      try {
        this.wan26 = new Wan26Client();
      } catch {
        console.warn("Wan26Client not available (missing API key)");
      }
    }
  }

  /**
   * Check GAMMA endpoint health
   */
  async checkGamma(): Promise<{ healthy: boolean; error?: string }> {
    const health = await this.gamma.checkHealth();
    return {
      healthy: health.status === "healthy",
      error: health.error,
    };
  }

  /**
   * Generate video using GAMMA (HunyuanVideo-1.5)
   * Local, free, highest quality
   */
  async generateGamma(options: GammaOptions): Promise<VideoResult> {
    return this.gamma.generate({
      prompt: options.prompt,
      quality: options.quality ?? "medium",
      numFrames: options.numFrames,
      seed: options.seed,
      downloadPath: options.outputPath,
    });
  }

  /**
   * Generate video using Veo 3.1 (Google API)
   * Fast turnaround, $0.15-0.40/sec
   */
  async generateVeo(options: VeoOptions): Promise<VideoResult> {
    if (!this.veo) {
      return {
        success: false,
        backend: options.fast ? VideoBackend.VEO_FAST : VideoBackend.VEO_STANDARD,
        prompt: options.prompt,
        error: "Veo client not available (GEMINI_API_KEY not set)",
      };
    }

    const model = options.fast
      ? "veo-3.1-fast-generate-preview"
      : "veo-3.1-generate-preview";

    return this.veo.generate(
      {
        prompt: options.prompt,
        model,
        aspectRatio: options.aspectRatio ?? "16:9",
        negativePrompt: options.negativePrompt,
      },
      options.outputPath
    );
  }

  /**
   * Generate video using Wan 2.6 API
   * Premium features: audio, 1080p, multi-shot
   */
  async generateWan26(options: Wan26Options): Promise<VideoResult> {
    if (!this.wan26) {
      return {
        success: false,
        backend: VideoBackend.WAN26_720P,
        prompt: options.prompt,
        error: "Wan26 client not available (WAN26_API_KEY not set)",
      };
    }

    const outputPath = options.outputPath ??
      `${config.paths.videosDir}/wan26_${Date.now()}.mp4`;

    return this.wan26.generateAndDownload(
      {
        prompt: options.prompt,
        duration: options.duration ?? 5,
        resolution: options.resolution ?? "720P",
        aspectRatio: options.aspectRatio ?? "16:9",
        withAudio: options.withAudio ?? false,
        multiShot: options.multiShot ?? false,
      },
      outputPath
    );
  }

  /**
   * Generate video with automatic backend selection
   */
  async generate(options: GenerateOptions): Promise<VideoResult> {
    const backend = options.backend ?? VideoBackend.GAMMA_MEDIUM;

    // Route to appropriate generator
    if (backend.startsWith("gamma")) {
      const quality = backend.replace("gamma-", "") as GammaQuality;
      return this.generateGamma({
        prompt: options.prompt,
        quality,
        outputPath: options.outputPath,
      });
    }

    if (backend.startsWith("veo")) {
      const fast = backend === "veo-fast";
      return this.generateVeo({
        prompt: options.prompt,
        fast,
        outputPath: options.outputPath,
      });
    }

    if (backend.startsWith("wan26")) {
      const resolution = backend.includes("1080") ? "1080P" : "720P";
      const withAudio = backend.includes("audio");
      const multiShot = backend.includes("multishot");

      return this.generateWan26({
        prompt: options.prompt,
        resolution,
        withAudio,
        multiShot,
        outputPath: options.outputPath,
      });
    }

    return {
      success: false,
      backend,
      prompt: options.prompt,
      error: `Unknown backend: ${backend}`,
    };
  }

  /**
   * Smart backend selection based on requirements and priority
   */
  selectBackend(
    priority: BackendPriority,
    requirements: BackendRequirements = {}
  ): VideoBackend {
    // Premium features require Wan 2.6 API
    if (requirements.needsMultiShot) {
      return VideoBackend.WAN26_MULTISHOT;
    }
    if (requirements.needsAudio) {
      return VideoBackend.WAN26_AUDIO;
    }
    if (requirements.needs1080p) {
      return VideoBackend.WAN26_1080P;
    }

    // Speed priority → Veo (fastest turnaround ~1 min)
    if (priority === "speed") {
      return this.veo ? VideoBackend.VEO_FAST : VideoBackend.WAN26_720P;
    }

    // Quality priority or hero shot → GAMMA (highest quality)
    if (priority === "quality" || requirements.isHeroShot) {
      return VideoBackend.GAMMA_HIGH;
    }

    // Cost priority → GAMMA (free)
    return VideoBackend.GAMMA_MEDIUM;
  }

  /**
   * List videos on GAMMA server
   */
  async listGammaVideos() {
    return this.gamma.listVideos();
  }

  /**
   * Get available backends based on configured API keys
   */
  getAvailableBackends(): VideoBackend[] {
    const backends: VideoBackend[] = [
      VideoBackend.GAMMA_TEST,
      VideoBackend.GAMMA_MEDIUM,
      VideoBackend.GAMMA_HIGH,
      VideoBackend.GAMMA_MAXIMUM,
    ];

    if (this.veo) {
      backends.push(VideoBackend.VEO_FAST, VideoBackend.VEO_STANDARD);
    }

    if (this.wan26) {
      backends.push(
        VideoBackend.WAN26_720P,
        VideoBackend.WAN26_1080P,
        VideoBackend.WAN26_AUDIO,
        VideoBackend.WAN26_MULTISHOT
      );
    }

    return backends;
  }
}

// Export singleton for convenience
export const videoGenerator = new VideoGenerator();
