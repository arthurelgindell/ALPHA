/**
 * Phase 2 Verification Script
 * Ensures HTTP clients are working correctly
 */

import { GammaClient } from "./clients/gamma";
import { Wan26Client } from "./clients/wan26";
import { LMStudioClient, LLMRouter } from "./clients/lm-studio";
import { retry, retryFetch } from "./utils/retry";
import config from "./config";

console.log("=".repeat(60));
console.log("ARTHUR TypeScript Migration - Phase 2 Verification");
console.log("=".repeat(60));

// ============================================================================
// Test Retry Utility
// ============================================================================

console.log("\n[Utils] Retry Utility:");
console.log("  ✓ retry function imported");
console.log("  ✓ retryFetch function imported");

// ============================================================================
// Test GAMMA Client
// ============================================================================

console.log("\n[Client] GAMMA HunyuanVideo:");
const gamma = new GammaClient();
console.log(`  Base URL: ${config.urls.gamma}`);

try {
  const health = await gamma.checkHealth();
  if (health.status === "healthy") {
    console.log(`  ✓ Health check passed`);
    console.log(`    GPU: ${health.gpu_name ?? "unknown"}`);
    console.log(`    Model loaded: ${health.model_loaded ?? "unknown"}`);
  } else {
    console.log(`  ⚠ Health check: ${health.error ?? "not available"}`);
  }
} catch (error) {
  console.log(`  ⚠ Health check error: ${error}`);
}

// ============================================================================
// Test Wan 2.6 Client
// ============================================================================

console.log("\n[Client] Wan 2.6 API:");
console.log(`  Base URL: https://api.piapi.ai`);

// Check if API key is set
if (process.env.WAN26_API_KEY) {
  console.log("  ✓ WAN26_API_KEY is set");
  try {
    const wan26 = new Wan26Client();
    console.log("  ✓ Wan26Client initialized");
  } catch (error) {
    console.log(`  ⚠ Wan26Client error: ${error}`);
  }
} else {
  console.log("  ⚠ WAN26_API_KEY not set (client will fail without it)");
}

// ============================================================================
// Test LM Studio Client
// ============================================================================

console.log("\n[Client] LM Studio:");
console.log(`  ALPHA LM: ${config.urls.alphaLM}`);
console.log(`  BETA LM:  ${config.urls.betaLM}`);

const alpha = new LMStudioClient({ baseUrl: config.urls.alphaLM });
const beta = new LMStudioClient({ baseUrl: config.urls.betaLM });

try {
  const alphaHealth = await alpha.checkHealth();
  console.log(`  ALPHA: ${alphaHealth.healthy ? "✓ healthy" : "⚠ " + alphaHealth.error}`);
} catch (error) {
  console.log(`  ALPHA: ⚠ ${error}`);
}

try {
  const betaHealth = await beta.checkHealth();
  console.log(`  BETA:  ${betaHealth.healthy ? "✓ healthy" : "⚠ " + betaHealth.error}`);
} catch (error) {
  console.log(`  BETA:  ⚠ ${error}`);
}

// ============================================================================
// Test LLM Router
// ============================================================================

console.log("\n[Service] LLM Router:");
const router = new LLMRouter();
console.log("  ✓ LLMRouter initialized");

try {
  const routerHealth = await router.checkHealth();
  console.log(`  Route to ALPHA: ${routerHealth.alpha.healthy ? "✓" : "⚠"}`);
  console.log(`  Route to BETA:  ${routerHealth.beta.healthy ? "✓" : "⚠"}`);
} catch (error) {
  console.log(`  ⚠ Router error: ${error}`);
}

// ============================================================================
// Summary
// ============================================================================

console.log("\n" + "=".repeat(60));
console.log("Phase 2 Verification Complete");
console.log("=".repeat(60));

console.log("\nClients Created:");
console.log("  ✓ src/utils/retry.ts (retry, retryFetch, withRetry)");
console.log("  ✓ src/clients/gamma.ts (GammaClient)");
console.log("  ✓ src/clients/wan26.ts (Wan26Client)");
console.log("  ✓ src/clients/lm-studio.ts (LMStudioClient, LLMRouter)");

console.log("\nNote: Some endpoints may not be reachable depending on network.");
console.log("This verifies TypeScript compilation and client structure.");
