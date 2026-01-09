/**
 * CarouselWorkflow
 * Produces LinkedIn carousel content
 *
 * Pipeline:
 * 1. Plan: LLM creates slide breakdown
 * 2. Generate: Create images per slide
 * 3. Assemble: Package as carousel (images + metadata)
 */

import { Workflow, type WorkflowOptions } from "./base";
import { TaskType, CarouselPlanSchema } from "../types";
import type { CarouselPlan, CarouselSlide } from "../types";
import config from "../config";

export interface CarouselOptions extends WorkflowOptions {
  slides?: number;
  format?: "png" | "pdf";
}

/**
 * LinkedIn carousel production workflow
 *
 * @example
 * ```typescript
 * const workflow = new CarouselWorkflow({
 *   brief: "10 AI Skills Every Professional Needs",
 *   slides: 10,
 *   style: "minimal"
 * });
 *
 * const result = await workflow.execute();
 * console.log(`Carousel: ${result.outputs}`);
 * ```
 */
export class CarouselWorkflow extends Workflow {
  private slideCount: number;
  private format: "png" | "pdf";

  constructor(options: CarouselOptions) {
    super(options);
    this.slideCount = options.slides ?? 7;
    this.format = options.format ?? "png";
  }

  getStages(): string[] {
    return ["planning", "image-generation", "layout", "rendering"];
  }

  /**
   * Plan carousel content using LLM
   */
  async plan(): Promise<CarouselPlan> {
    const systemPrompt = `You are a LinkedIn content strategist specializing in carousel posts.

Create a ${this.slideCount}-slide carousel breakdown:
- Slide 1: Cover with hook
- Slides 2-${this.slideCount - 1}: Content slides
- Slide ${this.slideCount}: CTA

Style: ${this.style}

For each slide provide:
- slideNumber: 1-${this.slideCount}
- type: "cover", "content", or "cta"
- headline: Main text (max 10 words)
- body: Supporting text (optional, max 25 words)
- imagePrompt: Detailed prompt for background image generation`;

    const userPrompt = `Create a carousel for: ${this.brief}`;

    const result = await this.router.routeWithSchema(
      TaskType.STRUCTURED,
      [
        { role: "system", content: systemPrompt },
        { role: "user", content: userPrompt },
      ],
      CarouselPlanSchema,
      "create_carousel_plan"
    );

    if (!result.success || !result.data) {
      throw new Error(`Planning failed: ${result.error}`);
    }

    console.log(`Plan created: ${result.data.title} (${result.data.slides.length} slides)`);
    return result.data;
  }

  /**
   * Generate images for each slide
   */
  async generate(plan: CarouselPlan): Promise<string[]> {
    const assets: string[] = [];
    const slides = plan.slides;

    for (let i = 0; i < slides.length; i++) {
      const slide = slides[i];
      this.reportProgress(
        "generating",
        30 + (i / slides.length) * 40,
        `Slide ${i + 1}/${slides.length}: ${slide.type}`
      );

      const outputPath = `${this.outputDir}/slide_${String(i + 1).padStart(2, "0")}.png`;

      const result = await this.imageGen.generateLinkedInCarousel(
        slide.imagePrompt,
        outputPath
      );

      if (result.success && result.path) {
        assets.push(result.path);
        console.log(`  ✓ Slide ${i + 1}: ${result.path}`);
      } else {
        console.warn(`  ⚠ Slide ${i + 1} failed: ${result.error}`);
        // Continue with other slides
      }
    }

    return assets;
  }

  /**
   * Assemble carousel package
   */
  async assemble(assets: string[], plan: CarouselPlan): Promise<string[]> {
    if (assets.length === 0) {
      throw new Error("No assets to assemble");
    }

    const timestamp = new Date().toISOString().replace(/[-:T.Z]/g, "").slice(0, 14);
    const outputDir = `${this.outputDir}/carousel_${timestamp}`;

    // Create output directory
    await Bun.write(`${outputDir}/.keep`, "");

    // Copy assets to output directory
    const outputs: string[] = [];
    for (let i = 0; i < assets.length; i++) {
      const destPath = `${outputDir}/slide_${String(i + 1).padStart(2, "0")}.png`;
      const sourceFile = Bun.file(assets[i]);
      await Bun.write(destPath, sourceFile);
      outputs.push(destPath);
    }

    // Create metadata file
    const metadata = {
      title: plan.title,
      topic: plan.topic,
      slideCount: plan.slides.length,
      slides: plan.slides.map((s, i) => ({
        ...s,
        imagePath: outputs[i] ?? null,
      })),
      createdAt: new Date().toISOString(),
      colorScheme: plan.colorScheme,
    };

    const metadataPath = `${outputDir}/metadata.json`;
    await Bun.write(metadataPath, JSON.stringify(metadata, null, 2));
    outputs.push(metadataPath);

    console.log(`✓ Carousel package: ${outputDir}`);
    console.log(`  ${outputs.length - 1} slides + metadata.json`);

    return outputs;
  }
}
