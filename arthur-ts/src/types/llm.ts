/**
 * LLM Types and Zod Schemas
 * Replaces: arthur/llm/router.py (instructor + Pydantic)
 */

import { z } from "zod";

// ============================================================================
// Task Types (matches Python LLM Router)
// ============================================================================

export enum TaskType {
  STRATEGIC = "strategic",
  EXECUTION = "execution",
  STRUCTURED = "structured",
}

export function getTargetEndpoint(taskType: TaskType): "alpha" | "beta" {
  switch (taskType) {
    case TaskType.STRATEGIC:
      return "alpha"; // DeepSeek V3.1 - complex reasoning
    case TaskType.EXECUTION:
    case TaskType.STRUCTURED:
      return "beta"; // Nemotron - structured output
  }
}

// ============================================================================
// Zod Schemas (replaces Pydantic models)
// ============================================================================

// Scene for video content
export const SceneSchema = z.object({
  id: z.string(),
  prompt: z.string().describe("Detailed prompt for video generation"),
  duration: z.number().min(1).max(60).describe("Duration in seconds"),
  notes: z.string().optional().describe("Production notes"),
});

export type Scene = z.infer<typeof SceneSchema>;

// Content plan for video production
export const ContentPlanSchema = z.object({
  title: z.string().describe("Video title"),
  description: z.string().describe("Brief description of the video"),
  scenes: z.array(SceneSchema).min(1).max(20),
  totalDuration: z.number().describe("Total video duration in seconds"),
  style: z.string().optional().describe("Visual style guidance"),
  targetAudience: z.string().optional().describe("Target audience"),
});

export type ContentPlan = z.infer<typeof ContentPlanSchema>;

// Carousel slide
export const CarouselSlideSchema = z.object({
  slideNumber: z.number(),
  type: z.enum(["cover", "content", "cta"]),
  headline: z.string(),
  body: z.string().optional(),
  imagePrompt: z.string().describe("Prompt for image generation"),
  imageBackend: z.enum(["gemini-pro"]).default("gemini-pro"),
});

export type CarouselSlide = z.infer<typeof CarouselSlideSchema>;

// Carousel plan
export const CarouselPlanSchema = z.object({
  title: z.string(),
  topic: z.string(),
  slides: z.array(CarouselSlideSchema).min(3).max(10),
  colorScheme: z.object({
    primary: z.string(),
    secondary: z.string(),
    accent: z.string(),
  }).optional(),
});

export type CarouselPlan = z.infer<typeof CarouselPlanSchema>;

// Prompt refinement
export const RefinedPromptSchema = z.object({
  original: z.string(),
  refined: z.string().describe("Improved prompt with more detail"),
  additions: z.array(z.string()).describe("What was added to improve the prompt"),
  style: z.string().optional(),
});

export type RefinedPrompt = z.infer<typeof RefinedPromptSchema>;

// ============================================================================
// OpenAI Function Calling Types
// ============================================================================

export interface FunctionDefinition {
  name: string;
  description: string;
  parameters: Record<string, unknown>; // JSON Schema from Zod
}

export interface ChatMessage {
  role: "system" | "user" | "assistant" | "function";
  content: string;
  name?: string;
  function_call?: {
    name: string;
    arguments: string;
  };
}

export interface ChatCompletionRequest {
  model: string;
  messages: ChatMessage[];
  functions?: FunctionDefinition[];
  function_call?: "auto" | "none" | { name: string };
  temperature?: number;
  max_tokens?: number;
}

export interface ChatCompletionResponse {
  id: string;
  object: "chat.completion";
  created: number;
  model: string;
  choices: Array<{
    index: number;
    message: {
      role: "assistant";
      content: string | null;
      function_call?: {
        name: string;
        arguments: string;
      };
    };
    finish_reason: "stop" | "function_call" | "length";
  }>;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

// ============================================================================
// LLM Client Types
// ============================================================================

export interface LLMClientConfig {
  baseUrl: string;
  model?: string;
  timeout?: number;
}

export interface LLMResult<T> {
  success: boolean;
  data?: T;
  rawResponse?: string;
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
  error?: string;
}
