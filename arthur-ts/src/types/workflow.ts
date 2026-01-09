/**
 * Workflow Types
 * Translated from: arthur/workflows/base.py
 */

// ============================================================================
// Workflow Status
// ============================================================================

export enum WorkflowStatus {
  PENDING = "pending",
  PLANNING = "planning",
  GENERATING = "generating",
  ASSEMBLING = "assembling",
  RENDERING = "rendering",
  COMPLETED = "completed",
  FAILED = "failed",
  CANCELLED = "cancelled",
}

// ============================================================================
// Workflow Result
// ============================================================================

export interface WorkflowResult {
  success: boolean;
  status: WorkflowStatus;
  outputs: string[];
  errors: string[];
  metadata: Record<string, unknown>;
  duration: number; // milliseconds
  startedAt: Date;
  completedAt?: Date;
}

// ============================================================================
// Workflow Options
// ============================================================================

export interface ShortVideoWorkflowOptions {
  brief: string;
  duration?: number;
  backend?: string;
  outputDir?: string;
  voiceover?: boolean;
}

export interface CarouselWorkflowOptions {
  topic: string;
  slides?: number;
  style?: "minimal" | "bold" | "professional";
  outputFormat?: "pdf" | "png";
  outputDir?: string;
}

// ============================================================================
// Workflow Progress
// ============================================================================

export interface WorkflowProgress {
  stage: string;
  stageIndex: number;
  totalStages: number;
  progress: number; // 0-100
  currentTask?: string;
  eta?: number; // seconds
}

export type ProgressCallback = (progress: WorkflowProgress) => void;

// ============================================================================
// Workflow Configuration
// ============================================================================

export interface WorkflowConfig {
  name: string;
  version: string;
  stages: string[];
  timeout?: number; // milliseconds
  retries?: number;
}

export const SHORT_VIDEO_WORKFLOW_CONFIG: WorkflowConfig = {
  name: "short-video",
  version: "2.0.0",
  stages: ["planning", "video-generation", "assembly", "voiceover", "rendering"],
  timeout: 30 * 60 * 1000, // 30 minutes
  retries: 2,
};

export const CAROUSEL_WORKFLOW_CONFIG: WorkflowConfig = {
  name: "carousel",
  version: "2.0.0",
  stages: ["planning", "image-generation", "layout", "rendering"],
  timeout: 15 * 60 * 1000, // 15 minutes
  retries: 2,
};
