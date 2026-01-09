/**
 * ImageGenerator - Unified Image Generation Interface
 * Translated from: arthur/generators/image.py
 *
 * Currently uses Gemini Image API (FLUX deprecated 2026-01-06)
 */

import { GeminiImageClient } from "../clients/gemini-image";
import config from "../config";
import type { ImageResult, AspectRatio } from "../types";
import { ImageBackend, PRESETS } from "../types";

export interface GenerateOptions {
  prompt: string;
  preset?: keyof typeof PRESETS;
  aspectRatio?: AspectRatio;
  outputPath?: string;
}

/**
 * Unified image generation interface
 *
 * @example
 * ```typescript
 * const gen = new ImageGenerator();
 *
 * // Generate with default settings (square)
 * const result = await gen.generate({
 *   prompt: "A minimalist coffee shop logo"
 * });
 *
 * // Generate with preset
 * const result = await gen.generate({
 *   prompt: "Abstract background",
 *   preset: "linkedin-carousel"
 * });
 *
 * // LinkedIn-specific methods
 * const post = await gen.generateLinkedInPost("Professional headshot background");
 * const carousel = await gen.generateLinkedInCarousel("Tech infographic");
 * ```
 */
export class ImageGenerator {
  private gemini: GeminiImageClient | null = null;

  constructor() {
    if (process.env.GEMINI_API_KEY) {
      try {
        this.gemini = new GeminiImageClient();
      } catch {
        console.warn("GeminiImageClient not available (missing API key)");
      }
    }
  }

  /**
   * Generate image with options
   */
  async generate(options: GenerateOptions): Promise<ImageResult> {
    if (!this.gemini) {
      return {
        success: false,
        backend: ImageBackend.GEMINI_PRO,
        prompt: options.prompt,
        error: "Gemini client not available (GEMINI_API_KEY not set)",
      };
    }

    // Determine aspect ratio from preset or explicit option
    let aspectRatio: AspectRatio = options.aspectRatio ?? "1:1";

    if (options.preset && PRESETS[options.preset]) {
      aspectRatio = PRESETS[options.preset].aspectRatio;
    }

    // Determine output path
    const outputPath = options.outputPath ??
      `${config.paths.imagesDir}/gemini_${Date.now()}.png`;

    return this.gemini.generate(
      {
        prompt: options.prompt,
        aspectRatio,
      },
      outputPath
    );
  }

  /**
   * Generate square image (1:1)
   */
  async generateSquare(
    prompt: string,
    outputPath?: string
  ): Promise<ImageResult> {
    return this.generate({ prompt, aspectRatio: "1:1", outputPath });
  }

  /**
   * Generate landscape image (16:9)
   */
  async generateLandscape(
    prompt: string,
    outputPath?: string
  ): Promise<ImageResult> {
    return this.generate({ prompt, aspectRatio: "16:9", outputPath });
  }

  /**
   * Generate portrait image (9:16)
   */
  async generatePortrait(
    prompt: string,
    outputPath?: string
  ): Promise<ImageResult> {
    return this.generate({ prompt, aspectRatio: "9:16", outputPath });
  }

  /**
   * Generate LinkedIn post image (16:9 for feed)
   */
  async generateLinkedInPost(
    prompt: string,
    outputPath?: string
  ): Promise<ImageResult> {
    return this.generate({
      prompt,
      preset: "linkedin-post",
      outputPath,
    });
  }

  /**
   * Generate LinkedIn carousel slide (1:1)
   */
  async generateLinkedInCarousel(
    prompt: string,
    outputPath?: string
  ): Promise<ImageResult> {
    return this.generate({
      prompt,
      preset: "linkedin-carousel",
      outputPath,
    });
  }

  /**
   * Generate multiple images for a carousel
   */
  async generateCarouselSlides(
    prompts: string[],
    outputDir: string,
    prefix = "slide"
  ): Promise<ImageResult[]> {
    const results: ImageResult[] = [];

    for (let i = 0; i < prompts.length; i++) {
      const outputPath = `${outputDir}/${prefix}_${String(i + 1).padStart(2, "0")}.png`;

      console.log(`Generating slide ${i + 1}/${prompts.length}`);
      const result = await this.generateLinkedInCarousel(prompts[i], outputPath);
      results.push(result);

      if (!result.success) {
        console.warn(`Slide ${i + 1} failed: ${result.error}`);
      }
    }

    const successful = results.filter((r) => r.success).length;
    console.log(`Carousel complete: ${successful}/${prompts.length} slides`);

    return results;
  }

  /**
   * Check if image generation is available
   */
  isAvailable(): boolean {
    return this.gemini !== null;
  }

  /**
   * Get current backend
   */
  getBackend(): ImageBackend {
    return ImageBackend.GEMINI_PRO;
  }
}

// Export singleton for convenience
export const imageGenerator = new ImageGenerator();
