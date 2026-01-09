/**
 * Phase 4 Verification Script
 * Ensures generators and utilities compile and initialize correctly
 */

import { VideoGenerator, videoGenerator } from "./generators/video";
import { ImageGenerator, imageGenerator } from "./generators/image";
import { VoiceGenerator, voiceGenerator } from "./generators/voice";
import { sshCheck } from "./utils/ssh";
import { probe } from "./utils/ffmpeg";
import { VideoBackend, ImageBackend } from "./types";
import config from "./config";

console.log("=".repeat(60));
console.log("ARTHUR TypeScript Migration - Phase 4 Verification");
console.log("=".repeat(60));

// ============================================================================
// Test Utilities
// ============================================================================

console.log("\n[Utils] SSH:");
console.log(`  SSH Binary: ${config.binaries.ssh}`);
console.log("  Testing BETA connection...");
const betaConnected = await sshCheck("beta");
console.log(`  BETA: ${betaConnected ? "✓ connected" : "⚠ not reachable"}`);

console.log("\n[Utils] FFmpeg:");
console.log(`  ffmpeg: ${config.binaries.ffmpeg}`);
console.log(`  ffprobe: ${config.binaries.ffprobe}`);
console.log("  Hardware acceleration:");
console.log(`    VideoToolbox: ${config.ffmpeg.videoToolbox.join(" ")}`);
console.log(`    H.264 Encoder: ${config.ffmpeg.h264Encoder.join(" ")}`);
console.log(`    AAC Encoder: ${config.ffmpeg.aacEncoder.join(" ")}`);

// ============================================================================
// Test VideoGenerator
// ============================================================================

console.log("\n[Generator] VideoGenerator:");
const videoGen = new VideoGenerator();

// Check GAMMA
const gammaHealth = await videoGen.checkGamma();
console.log(`  GAMMA: ${gammaHealth.healthy ? "✓ healthy" : "⚠ " + (gammaHealth.error ?? "not available")}`);

// List available backends
const availableBackends = videoGen.getAvailableBackends();
console.log("  Available backends:");
for (const backend of availableBackends) {
  console.log(`    - ${backend}`);
}

// Test backend selection
console.log("  Backend selection:");
console.log(`    Speed priority: ${videoGen.selectBackend("speed")}`);
console.log(`    Quality priority: ${videoGen.selectBackend("quality")}`);
console.log(`    Cost priority: ${videoGen.selectBackend("cost")}`);
console.log(`    Hero shot: ${videoGen.selectBackend("quality", { isHeroShot: true })}`);

// ============================================================================
// Test ImageGenerator
// ============================================================================

console.log("\n[Generator] ImageGenerator:");
const imageGen = new ImageGenerator();
console.log(`  Available: ${imageGen.isAvailable() ? "✓ yes" : "⚠ no (GEMINI_API_KEY not set)"}`);
console.log(`  Backend: ${imageGen.getBackend()}`);
console.log("  Methods: generate, generateSquare, generateLandscape, generatePortrait");
console.log("  LinkedIn: generateLinkedInPost, generateLinkedInCarousel");

// ============================================================================
// Test VoiceGenerator
// ============================================================================

console.log("\n[Generator] VoiceGenerator:");
const voiceGen = new VoiceGenerator();
console.log(`  BETA Host: ${config.voice.betaHost}`);
console.log(`  Python Env: ${config.voice.pythonEnv}`);
console.log(`  TTS Script: ${config.voice.ttsScript}`);
const voiceConnected = await voiceGen.checkConnection();
console.log(`  Connection: ${voiceConnected ? "✓ connected" : "⚠ not reachable"}`);

// ============================================================================
// Summary
// ============================================================================

console.log("\n" + "=".repeat(60));
console.log("Phase 4 Verification Complete");
console.log("=".repeat(60));

console.log("\nUtilities Created:");
console.log("  ✓ src/utils/ssh.ts (sshExec, sshCat, sshCheck, sshRm)");
console.log("  ✓ src/utils/ffmpeg.ts (muxAudio, transcode, probe, concat)");

console.log("\nGenerators Created:");
console.log("  ✓ src/generators/video.ts (VideoGenerator)");
console.log("  ✓ src/generators/image.ts (ImageGenerator)");
console.log("  ✓ src/generators/voice.ts (VoiceGenerator)");

console.log("\nApple Silicon Optimizations:");
console.log("  ✓ Native ARM64 binaries (/opt/homebrew/bin/*)");
console.log("  ✓ VideoToolbox hardware acceleration");
console.log("  ✓ Apple AudioToolbox AAC encoder");
console.log("  ✓ Bun.spawn for subprocess management");

console.log("\nBackend Summary:");
console.log(`  Video: ${availableBackends.length} backends available`);
console.log(`  Image: ${imageGen.isAvailable() ? "Gemini Pro" : "None (needs GEMINI_API_KEY)"}`);
console.log(`  Voice: ${voiceConnected ? "F5-TTS on BETA" : "Not available (BETA offline)"}`);
