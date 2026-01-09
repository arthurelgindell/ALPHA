/**
 * VoiceGenerator - TTS via BETA's F5-TTS-MLX
 * Translated from: arthur/generators/voice.py
 *
 * Executes voice synthesis on BETA via SSH and retrieves the audio file.
 * Designed for voiceover narration in video production.
 */

import { sshExec, sshCat, sshCheck, sshRm } from "../utils/ssh";
import config from "../config";
import type { VoiceResult } from "../types";

export interface VoiceGenerateOptions {
  text: string;
  outputPath: string;
  timeout?: number;
}

export interface NarrationSegment {
  text: string;
  outputPath: string;
}

/**
 * TTS generation via BETA's F5-TTS-MLX
 *
 * @example
 * ```typescript
 * const gen = new VoiceGenerator();
 *
 * // Check if BETA is reachable
 * const connected = await gen.checkConnection();
 *
 * // Generate single narration
 * const result = await gen.generate({
 *   text: "Welcome to the AI-Powered Professional Stack.",
 *   outputPath: "videos/intro_narration.wav"
 * });
 *
 * // Generate multiple segments
 * const results = await gen.generateNarration([
 *   "First, we have the Mac Studio M3 Ultra.",
 *   "Next, the NVIDIA DGX Spark.",
 *   "Finally, Claude Code for AI-assisted development."
 * ], "videos/narration/");
 * ```
 */
export class VoiceGenerator {
  private betaHost: string;
  private pythonEnv: string;
  private ttsScript: string;
  private remoteOutputDir: string;

  constructor(options?: {
    betaHost?: string;
    pythonEnv?: string;
    ttsScript?: string;
    remoteOutputDir?: string;
  }) {
    this.betaHost = options?.betaHost ?? config.voice.betaHost;
    this.pythonEnv = options?.pythonEnv ?? config.voice.pythonEnv;
    this.ttsScript = options?.ttsScript ?? config.voice.ttsScript;
    this.remoteOutputDir = options?.remoteOutputDir ?? config.voice.outputDir;
  }

  /**
   * Check if BETA is reachable via SSH
   */
  async checkConnection(): Promise<boolean> {
    return sshCheck(this.betaHost);
  }

  /**
   * Generate speech from text using F5-TTS on BETA
   */
  async generate(options: VoiceGenerateOptions): Promise<VoiceResult> {
    const { text, outputPath, timeout = 90000 } = options;
    const startTime = Date.now();

    // Validate input
    if (!text || text.trim().length < 3) {
      return {
        success: false,
        text,
        error: "Text too short (min 3 characters)",
      };
    }

    // Generate unique filename on BETA
    const timestamp = new Date().toISOString().replace(/[-:T.Z]/g, "").slice(0, 17);
    const remoteFilename = `voice_${timestamp}.wav`;
    const remotePath = `${this.remoteOutputDir}/${remoteFilename}`;

    console.log(`Generating voice on BETA: "${text.slice(0, 50)}..."`);

    // Escape single quotes in text
    const escapedText = text.replace(/'/g, "'\"'\"'");
    const remoteCmd = `${this.pythonEnv} ${this.ttsScript} --no-play --output ${remotePath} '${escapedText}'`;

    // Execute F5-TTS on BETA
    const result = await sshExec(remoteCmd, {
      host: this.betaHost,
      timeout,
    });

    if (!result.success) {
      const generationTime = (Date.now() - startTime) / 1000;
      console.error(`F5-TTS failed: ${result.stderr || result.error}`);
      return {
        success: false,
        text,
        generationTime,
        error: result.stderr || result.error || "Generation failed",
      };
    }

    // Transfer file back to ALPHA
    const transfer = await sshCat(remotePath, outputPath, {
      host: this.betaHost,
      timeout: 60000,
    });

    if (!transfer.success) {
      const generationTime = (Date.now() - startTime) / 1000;
      console.error(`File transfer failed: ${transfer.error}`);
      return {
        success: false,
        text,
        generationTime,
        error: `File transfer failed: ${transfer.error}`,
      };
    }

    // Cleanup remote file
    await sshRm(remotePath, { host: this.betaHost });

    const generationTime = (Date.now() - startTime) / 1000;

    // Get file size
    const file = Bun.file(outputPath);
    const fileSize = await file.exists() ? file.size : 0;

    console.log(`Voice generated: ${outputPath} (${fileSize} bytes, ${generationTime.toFixed(1)}s)`);

    return {
      success: true,
      path: outputPath,
      text,
      generationTime,
      fileSize,
    };
  }

  /**
   * Generate multiple narration segments
   */
  async generateNarration(
    segments: string[],
    outputDir: string,
    prefix = "narration"
  ): Promise<VoiceResult[]> {
    const results: VoiceResult[] = [];

    for (let i = 0; i < segments.length; i++) {
      const text = segments[i];
      const outputPath = `${outputDir}/${prefix}_${String(i + 1).padStart(3, "0")}.wav`;

      console.log(`Generating segment ${i + 1}/${segments.length}`);

      const result = await this.generate({ text, outputPath });
      results.push(result);

      if (!result.success) {
        console.warn(`Segment ${i + 1} failed: ${result.error}`);
      }
    }

    const successful = results.filter((r) => r.success).length;
    console.log(`Narration complete: ${successful}/${segments.length} segments`);

    return results;
  }

  /**
   * Generate narration from structured segments
   */
  async generateFromSegments(
    segments: NarrationSegment[]
  ): Promise<VoiceResult[]> {
    const results: VoiceResult[] = [];

    for (let i = 0; i < segments.length; i++) {
      const { text, outputPath } = segments[i];
      console.log(`Generating segment ${i + 1}/${segments.length}`);

      const result = await this.generate({ text, outputPath });
      results.push(result);
    }

    return results;
  }
}

// Export singleton for convenience
export const voiceGenerator = new VoiceGenerator();
