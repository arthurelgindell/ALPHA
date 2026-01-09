/**
 * ShortVideoWorkflow
 * Produces short-form video content (< 60s)
 *
 * Pipeline:
 * 1. Plan: LLM creates scene breakdown
 * 2. Generate: Create video clips per scene
 * 3. Assemble: Concat clips, add voiceover
 */

import { Workflow, type WorkflowOptions } from "./base";
import { VideoBackend, TaskType, ContentPlanSchema } from "../types";
import type { ContentPlan, Scene } from "../types";
import { muxAudio, concat } from "../utils/ffmpeg";
import config from "../config";

export interface ShortVideoOptions extends WorkflowOptions {
  duration?: number;
  backend?: VideoBackend;
  voiceover?: boolean;
}

/**
 * Short video production workflow
 *
 * @example
 * ```typescript
 * const workflow = new ShortVideoWorkflow({
 *   brief: "Create a 30-second AI demo video",
 *   duration: 30,
 *   backend: VideoBackend.GAMMA_MEDIUM,
 *   voiceover: true
 * });
 *
 * const result = await workflow.execute();
 * console.log(`Video: ${result.outputs[0]}`);
 * ```
 */
export class ShortVideoWorkflow extends Workflow {
  private duration: number;
  private backend: VideoBackend;
  private voiceover: boolean;

  constructor(options: ShortVideoOptions) {
    super(options);
    this.duration = options.duration ?? 30;
    this.backend = options.backend ?? VideoBackend.GAMMA_MEDIUM;
    this.voiceover = options.voiceover ?? true;
  }

  getStages(): string[] {
    return ["planning", "video-generation", "voiceover", "assembly", "rendering"];
  }

  /**
   * Plan video content using LLM
   */
  async plan(): Promise<ContentPlan> {
    const systemPrompt = `You are a video content strategist. Create a detailed scene breakdown for a ${this.duration}-second video.

Style: ${this.style}
Target: LinkedIn professional audience

For each scene, provide:
- id: Unique scene identifier
- prompt: Detailed visual prompt for video generation (use Five-Part Formula)
- duration: Scene duration in seconds
- notes: Production notes

Total duration must equal ${this.duration} seconds.`;

    const userPrompt = `Create a scene breakdown for: ${this.brief}`;

    const result = await this.router.routeWithSchema(
      TaskType.STRUCTURED,
      [
        { role: "system", content: systemPrompt },
        { role: "user", content: userPrompt },
      ],
      ContentPlanSchema,
      "create_content_plan"
    );

    if (!result.success || !result.data) {
      throw new Error(`Planning failed: ${result.error}`);
    }

    console.log(`Plan created: ${result.data.title} (${result.data.scenes.length} scenes)`);
    return result.data;
  }

  /**
   * Generate video clips for each scene
   */
  async generate(plan: ContentPlan): Promise<string[]> {
    const assets: string[] = [];
    const scenes = plan.scenes;

    for (let i = 0; i < scenes.length; i++) {
      const scene = scenes[i];
      this.reportProgress(
        "generating",
        30 + (i / scenes.length) * 40,
        `Scene ${i + 1}/${scenes.length}: ${scene.id}`
      );

      const outputPath = `${this.outputDir}/scene_${String(i + 1).padStart(2, "0")}.mp4`;

      const result = await this.videoGen.generate({
        prompt: scene.prompt,
        backend: this.backend,
        outputPath,
      });

      if (result.success && result.path) {
        assets.push(result.path);
        console.log(`  ✓ Scene ${i + 1}: ${result.path}`);
      } else {
        console.warn(`  ⚠ Scene ${i + 1} failed: ${result.error}`);
        // Continue with other scenes
      }
    }

    return assets;
  }

  /**
   * Assemble final video from clips
   */
  async assemble(assets: string[], plan: ContentPlan): Promise<string[]> {
    if (assets.length === 0) {
      throw new Error("No assets to assemble");
    }

    const timestamp = new Date().toISOString().replace(/[-:T.Z]/g, "").slice(0, 14);
    const finalPath = `${this.outputDir}/video_${timestamp}.mp4`;

    // Step 1: Concatenate video clips
    this.reportProgress("assembling", 75, "Concatenating clips...");
    const concatResult = await concat(assets, `${this.outputDir}/concat_temp.mp4`);

    if (!concatResult.success) {
      throw new Error(`Concat failed: ${concatResult.error}`);
    }

    let videoPath = concatResult.outputPath;

    // Step 2: Generate and add voiceover (if enabled)
    if (this.voiceover) {
      this.reportProgress("assembling", 85, "Generating voiceover...");

      // Create narration text from scene notes
      const narrationText = plan.scenes
        .map((s) => s.notes || s.prompt.split(".")[0])
        .join(". ");

      const voiceResult = await this.voiceGen.generate({
        text: narrationText,
        outputPath: `${this.outputDir}/narration.wav`,
      });

      if (voiceResult.success && voiceResult.path) {
        this.reportProgress("assembling", 90, "Muxing audio...");
        const muxResult = await muxAudio({
          videoPath,
          audioPath: voiceResult.path,
          outputPath: finalPath,
        });

        if (muxResult.success) {
          videoPath = muxResult.outputPath;
        } else {
          console.warn(`Mux failed, using video without audio: ${muxResult.error}`);
          // Copy concat result as final
          await Bun.write(finalPath, Bun.file(videoPath));
          videoPath = finalPath;
        }
      } else {
        console.warn(`Voiceover failed: ${voiceResult.error}`);
        await Bun.write(finalPath, Bun.file(videoPath));
        videoPath = finalPath;
      }
    } else {
      // No voiceover, just rename concat result
      await Bun.write(finalPath, Bun.file(videoPath));
      videoPath = finalPath;
    }

    console.log(`✓ Final video: ${videoPath}`);
    return [videoPath];
  }
}
