/**
 * Base Workflow Classes
 * Translated from: arthur/workflows/base.py
 *
 * Foundation for all production workflows
 */

import { LLMRouter } from "../clients/lm-studio";
import { VideoGenerator } from "../generators/video";
import { ImageGenerator } from "../generators/image";
import { VoiceGenerator } from "../generators/voice";
import config from "../config";
import type {
  WorkflowStatus,
  WorkflowResult,
  WorkflowProgress,
  ProgressCallback,
} from "../types";

export interface WorkflowOptions {
  brief: string;
  style?: string;
  outputDir?: string;
}

/**
 * Base class for all production workflows
 *
 * Subclasses implement specific workflows like:
 * - CarouselWorkflow
 * - ShortVideoWorkflow
 *
 * @example
 * ```typescript
 * class MyWorkflow extends Workflow {
 *   async plan(): Promise<Record<string, unknown>> {
 *     // Planning logic
 *   }
 *
 *   async generate(plan: Record<string, unknown>): Promise<string[]> {
 *     // Generation logic
 *   }
 *
 *   async assemble(assets: string[], plan: Record<string, unknown>): Promise<string[]> {
 *     // Assembly logic
 *   }
 * }
 *
 * const workflow = new MyWorkflow({ brief: "..." });
 * const result = await workflow.execute();
 * ```
 */
export abstract class Workflow {
  protected brief: string;
  protected style: string;
  protected outputDir: string;

  // Components
  protected router: LLMRouter;
  protected videoGen: VideoGenerator;
  protected imageGen: ImageGenerator;
  protected voiceGen: VoiceGenerator;

  // State
  protected status: WorkflowStatus = "pending";
  protected result: WorkflowResult;
  protected progressCallbacks: ProgressCallback[] = [];

  constructor(options: WorkflowOptions) {
    this.brief = options.brief;
    this.style = options.style ?? "professional";
    this.outputDir = options.outputDir ?? config.paths.projectRoot;

    // Initialize components
    this.router = new LLMRouter();
    this.videoGen = new VideoGenerator();
    this.imageGen = new ImageGenerator();
    this.voiceGen = new VoiceGenerator();

    // Initialize result
    this.result = {
      success: false,
      status: "pending",
      outputs: [],
      errors: [],
      metadata: {},
      duration: 0,
      startedAt: new Date(),
    };
  }

  /**
   * Register progress callback
   */
  onProgress(callback: ProgressCallback): void {
    this.progressCallbacks.push(callback);
  }

  /**
   * Report progress to callbacks
   */
  protected reportProgress(stage: string, progress: number, currentTask?: string): void {
    const progressData: WorkflowProgress = {
      stage,
      stageIndex: this.getStageIndex(stage),
      totalStages: this.getStages().length,
      progress,
      currentTask,
    };

    for (const callback of this.progressCallbacks) {
      try {
        callback(progressData);
      } catch {
        // Ignore callback errors
      }
    }

    console.log(`[${Math.round(progress)}%] ${stage}${currentTask ? `: ${currentTask}` : ""}`);
  }

  /**
   * Update workflow status
   */
  protected updateStatus(status: WorkflowStatus): void {
    this.status = status;
    this.result.status = status;
  }

  /**
   * Get workflow stages
   */
  abstract getStages(): string[];

  /**
   * Get stage index
   */
  protected getStageIndex(stage: string): number {
    return this.getStages().indexOf(stage);
  }

  /**
   * Planning phase - create content plan using LLM
   */
  abstract plan(): Promise<Record<string, unknown>>;

  /**
   * Generation phase - create media assets
   */
  abstract generate(plan: Record<string, unknown>): Promise<string[]>;

  /**
   * Assembly phase - combine assets into final outputs
   */
  abstract assemble(assets: string[], plan: Record<string, unknown>): Promise<string[]>;

  /**
   * Execute complete workflow
   */
  async execute(): Promise<WorkflowResult> {
    const startTime = Date.now();
    this.result.startedAt = new Date();

    try {
      // Phase 1: Planning
      this.updateStatus("planning");
      this.reportProgress("planning", 10, "Creating content strategy...");
      const plan = await this.plan();
      this.result.metadata.plan = plan;

      // Phase 2: Generation
      this.updateStatus("generating");
      this.reportProgress("generating", 30, "Creating media assets...");
      const assets = await this.generate(plan);
      this.result.metadata.assets = assets;

      // Phase 3: Assembly
      this.updateStatus("assembling");
      this.reportProgress("assembling", 70, "Combining assets...");
      const outputs = await this.assemble(assets, plan);
      this.result.outputs = outputs;

      // Complete
      this.updateStatus("completed");
      this.reportProgress("completed", 100, "Done!");
      this.result.success = true;

    } catch (error) {
      this.updateStatus("failed");
      const errorMessage = error instanceof Error ? error.message : String(error);
      this.result.errors.push(errorMessage);
      console.error(`Workflow failed: ${errorMessage}`);
    }

    this.result.completedAt = new Date();
    this.result.duration = Date.now() - startTime;

    return this.result;
  }

  /**
   * Validate required infrastructure is available
   */
  async validateInfrastructure(): Promise<{
    llm: { alpha: boolean; beta: boolean };
    gamma: boolean;
    voice: boolean;
  }> {
    const [llmHealth, gammaHealth, voiceConnected] = await Promise.all([
      this.router.checkHealth(),
      this.videoGen.checkGamma(),
      this.voiceGen.checkConnection(),
    ]);

    return {
      llm: {
        alpha: llmHealth.alpha.healthy,
        beta: llmHealth.beta.healthy,
      },
      gamma: gammaHealth.healthy,
      voice: voiceConnected,
    };
  }

  /**
   * Get current status
   */
  getStatus(): WorkflowStatus {
    return this.status;
  }

  /**
   * Get current result
   */
  getResult(): WorkflowResult {
    return this.result;
  }
}
