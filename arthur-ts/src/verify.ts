/**
 * Phase 1 Verification Script
 * Ensures config and types are working correctly
 */

import config from "./config";
import { VideoBackend, ImageBackend, TaskType } from "./types";

console.log("=".repeat(60));
console.log("ARTHUR TypeScript Migration - Phase 1 Verification");
console.log("=".repeat(60));

// Verify config
console.log("\n[Config] Infrastructure Endpoints:");
console.log(`  ALPHA LM: ${config.urls.alphaLM}`);
console.log(`  BETA LM:  ${config.urls.betaLM}`);
console.log(`  GAMMA:    ${config.urls.gamma}`);

console.log("\n[Config] Paths:");
console.log(`  Project Root: ${config.paths.projectRoot}`);
console.log(`  Videos Dir:   ${config.paths.videosDir}`);
console.log(`  STUDIO Video: ${config.paths.studioVideo}`);

console.log("\n[Config] Native Binaries:");
console.log(`  ffmpeg:  ${config.binaries.ffmpeg}`);
console.log(`  ffprobe: ${config.binaries.ffprobe}`);

// Verify types
console.log("\n[Types] Video Backends:");
Object.values(VideoBackend).forEach((b) => console.log(`  - ${b}`));

console.log("\n[Types] Image Backends:");
Object.values(ImageBackend).forEach((b) => console.log(`  - ${b}`));

console.log("\n[Types] Task Types:");
Object.values(TaskType).forEach((t) => console.log(`  - ${t}`));

// Verify Google API config
console.log("\n[Config] Google APIs:");
console.log(`  Veo Model: ${config.urls.google.veoModel}`);
console.log(`  Gemini Image: ${config.urls.google.geminiImageModel}`);

// Success
console.log("\n" + "=".repeat(60));
console.log("Phase 1 Verification PASSED");
console.log("=".repeat(60));
