#!/usr/bin/env bun
/**
 * ARTHUR CLI
 * Translated from: arthur/cli.py
 *
 * Main entry point for ARTHUR media production system
 * Usage: bun run cli.ts <command> [options]
 */

import { program } from "commander";
import chalk from "chalk";
import config from "./config";
import { VideoGenerator } from "./generators/video";
import { ImageGenerator } from "./generators/image";
import { VoiceGenerator } from "./generators/voice";
import { ShortVideoWorkflow } from "./workflows/short-video";
import { CarouselWorkflow } from "./workflows/carousel";
import { VideoBackend, ImageBackend } from "./types";

// ============================================================================
// CLI Setup
// ============================================================================

program
  .name("arthur")
  .version("2.0.0")
  .description("ARTHUR Media Production CLI - TypeScript/Bun Edition");

// ============================================================================
// Video Commands
// ============================================================================

program
  .command("video <prompt>")
  .description("Generate video from text prompt")
  .option("-b, --backend <backend>", "Video backend", "gamma-medium")
  .option("-o, --output <path>", "Output path")
  .option("-q, --quality <quality>", "Quality preset (test/medium/high/maximum)", "medium")
  .action(async (prompt: string, options) => {
    console.log(chalk.blue("🎬 ARTHUR Video Generation"));
    console.log(chalk.gray(`Backend: ${options.backend}`));
    console.log(chalk.gray(`Prompt: ${prompt.slice(0, 50)}...`));
    console.log();

    const generator = new VideoGenerator();

    const result = await generator.generate({
      prompt,
      backend: options.backend as VideoBackend,
      outputPath: options.output,
    });

    if (result.success) {
      console.log(chalk.green(`✓ Video saved: ${result.path}`));
      console.log(chalk.gray(`  Duration: ${result.duration}s`));
      console.log(chalk.gray(`  Generation time: ${result.generationTime?.toFixed(1)}s`));
    } else {
      console.log(chalk.red(`✗ Failed: ${result.error}`));
      process.exit(1);
    }
  });

// ============================================================================
// Image Commands
// ============================================================================

program
  .command("image <prompt>")
  .description("Generate image from text prompt")
  .option("-o, --output <path>", "Output path")
  .option("-a, --aspect <ratio>", "Aspect ratio (1:1, 16:9, 9:16)", "1:1")
  .option("-p, --preset <preset>", "Resolution preset (linkedin-carousel, linkedin-post)")
  .action(async (prompt: string, options) => {
    console.log(chalk.blue("🖼️  ARTHUR Image Generation"));
    console.log(chalk.gray(`Prompt: ${prompt.slice(0, 50)}...`));
    console.log();

    const generator = new ImageGenerator();

    if (!generator.isAvailable()) {
      console.log(chalk.red("✗ Image generation not available (GEMINI_API_KEY not set)"));
      process.exit(1);
    }

    const result = await generator.generate({
      prompt,
      preset: options.preset,
      aspectRatio: options.aspect,
      outputPath: options.output,
    });

    if (result.success) {
      console.log(chalk.green(`✓ Image saved: ${result.path}`));
      console.log(chalk.gray(`  Resolution: ${result.resolution}`));
      console.log(chalk.gray(`  Generation time: ${result.generationTime?.toFixed(1)}s`));
    } else {
      console.log(chalk.red(`✗ Failed: ${result.error}`));
      process.exit(1);
    }
  });

// ============================================================================
// Voice Commands
// ============================================================================

program
  .command("voice <text>")
  .description("Generate voiceover from text")
  .option("-o, --output <path>", "Output path", "voice.wav")
  .action(async (text: string, options) => {
    console.log(chalk.blue("🎙️  ARTHUR Voice Generation"));
    console.log(chalk.gray(`Text: ${text.slice(0, 50)}...`));
    console.log();

    const generator = new VoiceGenerator();

    const connected = await generator.checkConnection();
    if (!connected) {
      console.log(chalk.red("✗ BETA not reachable (required for voice generation)"));
      process.exit(1);
    }

    const result = await generator.generate({
      text,
      outputPath: options.output,
    });

    if (result.success) {
      console.log(chalk.green(`✓ Voice saved: ${result.path}`));
      console.log(chalk.gray(`  Duration: ${result.duration}s`));
      console.log(chalk.gray(`  File size: ${result.fileSize} bytes`));
    } else {
      console.log(chalk.red(`✗ Failed: ${result.error}`));
      process.exit(1);
    }
  });

// ============================================================================
// Workflow Commands
// ============================================================================

program
  .command("workflow:video <brief>")
  .description("Execute short video production workflow")
  .option("-d, --duration <seconds>", "Target duration", "30")
  .option("-b, --backend <backend>", "Video backend", "gamma-medium")
  .option("-o, --output <dir>", "Output directory")
  .option("--no-voiceover", "Disable voiceover")
  .action(async (brief: string, options) => {
    console.log(chalk.blue("🎬 ARTHUR Short Video Workflow"));
    console.log(chalk.gray(`Brief: ${brief}`));
    console.log(chalk.gray(`Duration: ${options.duration}s`));
    console.log();

    const workflow = new ShortVideoWorkflow({
      brief,
      duration: parseInt(options.duration),
      backend: options.backend as VideoBackend,
      voiceover: options.voiceover !== false,
      outputDir: options.output,
    });

    const result = await workflow.execute();

    if (result.success) {
      console.log(chalk.green(`✓ Workflow complete!`));
      console.log(chalk.gray(`  Outputs: ${result.outputs.join(", ")}`));
      console.log(chalk.gray(`  Duration: ${(result.duration / 1000).toFixed(1)}s`));
    } else {
      console.log(chalk.red(`✗ Workflow failed`));
      result.errors.forEach((e) => console.log(chalk.red(`  ${e}`)));
      process.exit(1);
    }
  });

program
  .command("workflow:carousel <brief>")
  .description("Execute carousel production workflow")
  .option("-s, --slides <count>", "Number of slides", "7")
  .option("-o, --output <dir>", "Output directory")
  .option("--style <style>", "Visual style", "minimal")
  .action(async (brief: string, options) => {
    console.log(chalk.blue("🎠 ARTHUR Carousel Workflow"));
    console.log(chalk.gray(`Brief: ${brief}`));
    console.log(chalk.gray(`Slides: ${options.slides}`));
    console.log();

    const workflow = new CarouselWorkflow({
      brief,
      slides: parseInt(options.slides),
      style: options.style,
      outputDir: options.output,
    });

    const result = await workflow.execute();

    if (result.success) {
      console.log(chalk.green(`✓ Workflow complete!`));
      console.log(chalk.gray(`  Outputs: ${result.outputs.length} files`));
      console.log(chalk.gray(`  Duration: ${(result.duration / 1000).toFixed(1)}s`));
    } else {
      console.log(chalk.red(`✗ Workflow failed`));
      result.errors.forEach((e) => console.log(chalk.red(`  ${e}`)));
      process.exit(1);
    }
  });

// ============================================================================
// Status Command
// ============================================================================

program
  .command("status")
  .description("Check infrastructure status")
  .action(async () => {
    console.log(chalk.blue("🔍 ARTHUR Infrastructure Status"));
    console.log();

    // Check video backends
    console.log(chalk.yellow("Video Backends:"));
    const videoGen = new VideoGenerator();
    const gammaHealth = await videoGen.checkGamma();
    console.log(`  GAMMA (HunyuanVideo): ${gammaHealth.healthy ? chalk.green("✓") : chalk.red("✗")} ${gammaHealth.error ?? ""}`);
    console.log(`  Veo 3.1: ${process.env.GEMINI_API_KEY ? chalk.green("✓ configured") : chalk.yellow("⚠ GEMINI_API_KEY not set")}`);
    console.log(`  Wan 2.6: ${process.env.WAN26_API_KEY ? chalk.green("✓ configured") : chalk.yellow("⚠ WAN26_API_KEY not set")}`);

    // Check image backends
    console.log();
    console.log(chalk.yellow("Image Backends:"));
    const imageGen = new ImageGenerator();
    console.log(`  Gemini Pro: ${imageGen.isAvailable() ? chalk.green("✓") : chalk.yellow("⚠ GEMINI_API_KEY not set")}`);

    // Check voice
    console.log();
    console.log(chalk.yellow("Voice Generation:"));
    const voiceGen = new VoiceGenerator();
    const voiceConnected = await voiceGen.checkConnection();
    console.log(`  BETA (F5-TTS): ${voiceConnected ? chalk.green("✓ connected") : chalk.red("✗ not reachable")}`);

    // Available backends
    console.log();
    console.log(chalk.yellow("Available Backends:"));
    const backends = videoGen.getAvailableBackends();
    backends.forEach((b) => console.log(`  - ${b}`));
  });

// ============================================================================
// Config Command
// ============================================================================

program
  .command("config")
  .description("Show configuration")
  .action(() => {
    console.log(chalk.blue("⚙️  ARTHUR Configuration"));
    console.log();

    console.log(chalk.yellow("Endpoints:"));
    console.log(`  ALPHA LM: ${config.urls.alphaLM}`);
    console.log(`  BETA LM:  ${config.urls.betaLM}`);
    console.log(`  GAMMA:    ${config.urls.gamma}`);

    console.log();
    console.log(chalk.yellow("Paths:"));
    console.log(`  Project:   ${config.paths.projectRoot}`);
    console.log(`  Videos:    ${config.paths.videosDir}`);
    console.log(`  Images:    ${config.paths.imagesDir}`);
    console.log(`  Carousels: ${config.paths.carouselsDir}`);

    console.log();
    console.log(chalk.yellow("Binaries (ARM64):"));
    console.log(`  ffmpeg:  ${config.binaries.ffmpeg}`);
    console.log(`  ffprobe: ${config.binaries.ffprobe}`);
    console.log(`  ssh:     ${config.binaries.ssh}`);
  });

// ============================================================================
// Parse & Execute
// ============================================================================

program.parse();
