/**
 * ARTHUR Type Definitions
 * Central export for all types
 */

// Video types
export * from "./video";

// Image types
export * from "./image";

// LLM types and Zod schemas
export * from "./llm";

// Workflow types
export * from "./workflow";

// Common types
export interface Result<T> {
  success: boolean;
  data?: T;
  error?: string;
  errorCode?: string;
}

export interface PaginatedResult<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

// Voice types
export interface VoiceResult {
  success: boolean;
  path?: string;
  text: string;
  duration?: number;
  generationTime?: number;
  fileSize?: number;
  error?: string;
}

export interface VoiceGenerateOptions {
  text: string;
  outputPath?: string;
  referenceVoice?: string;
}

// Vision types
export interface VisionResult {
  success: boolean;
  analysis: string;
  model: string;
  prompt: string;
  imagePath?: string;
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
  error?: string;
}

export interface MediaAnalysis {
  success: boolean;
  mediaPath: string;
  mediaType: "image" | "video";
  analysisType: "product" | "quality" | "accuracy" | "scene" | "custom";
  summary: string;
  details: Record<string, unknown>;
  keyframes?: string[];
  error?: string;
}
