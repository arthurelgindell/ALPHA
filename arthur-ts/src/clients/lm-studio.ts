/**
 * LM Studio OpenAI-Compatible Client
 * Translated from: arthur/llm/clients.py
 *
 * Provides OpenAI-compatible interface to local LM Studio instances:
 * - ALPHA LM (100.65.29.44:1234): DeepSeek V3.1 for strategic reasoning
 * - BETA LM (100.84.202.68:1234): Nemotron for structured output
 */

import config from "../config";
import { retryFetch } from "../utils/retry";
import type {
  ChatMessage,
  ChatCompletionRequest,
  ChatCompletionResponse,
  FunctionDefinition,
  LLMResult,
} from "../types";
import { TaskType, getTargetEndpoint } from "../types";
import { z } from "zod";
import { zodToJsonSchema } from "zod-to-json-schema";

export interface LMStudioClientOptions {
  baseUrl?: string;
  model?: string;
  timeout?: number;
}

/**
 * OpenAI-compatible client for LM Studio
 *
 * @example
 * ```typescript
 * // Basic chat completion
 * const client = new LMStudioClient({ baseUrl: config.urls.alphaLM });
 * const result = await client.chat([
 *   { role: "user", content: "Explain quantum computing" }
 * ]);
 *
 * // With function calling
 * const ContentPlanSchema = z.object({
 *   title: z.string(),
 *   scenes: z.array(z.object({
 *     id: z.string(),
 *     prompt: z.string(),
 *     duration: z.number()
 *   }))
 * });
 *
 * const plan = await client.chatWithSchema(
 *   [{ role: "user", content: "Plan a 30s video about AI" }],
 *   ContentPlanSchema,
 *   "create_plan"
 * );
 * ```
 */
export class LMStudioClient {
  private baseUrl: string;
  private model: string;
  private timeout: number;

  constructor(options: LMStudioClientOptions = {}) {
    this.baseUrl = options.baseUrl ?? config.urls.alphaLM;
    this.model = options.model ?? "default";
    this.timeout = options.timeout ?? 120000;
  }

  /**
   * Check if the LM Studio server is healthy
   */
  async checkHealth(): Promise<{ healthy: boolean; error?: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/models`, {
        signal: AbortSignal.timeout(5000),
      });

      if (!response.ok) {
        return { healthy: false, error: `HTTP ${response.status}` };
      }

      return { healthy: true };
    } catch (error) {
      return {
        healthy: false,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  /**
   * Send a chat completion request
   */
  async chat(
    messages: ChatMessage[],
    options: {
      temperature?: number;
      maxTokens?: number;
      functions?: FunctionDefinition[];
      functionCall?: "auto" | "none" | { name: string };
    } = {}
  ): Promise<LLMResult<string>> {
    const request: ChatCompletionRequest = {
      model: this.model,
      messages,
      temperature: options.temperature ?? 0.7,
      max_tokens: options.maxTokens ?? 4096,
    };

    if (options.functions) {
      request.functions = options.functions;
      request.function_call = options.functionCall ?? "auto";
    }

    try {
      const response = await retryFetch(
        `${this.baseUrl}/chat/completions`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(request),
          signal: AbortSignal.timeout(this.timeout),
        },
        { maxRetries: 2, initialDelay: 2000 }
      );

      if (!response.ok) {
        return {
          success: false,
          error: `HTTP ${response.status}: ${await response.text()}`,
        };
      }

      const data: ChatCompletionResponse = await response.json();
      const choice = data.choices[0];

      if (!choice) {
        return { success: false, error: "No response from model" };
      }

      // Handle function call response
      if (choice.message.function_call) {
        return {
          success: true,
          data: choice.message.function_call.arguments,
          rawResponse: JSON.stringify(data),
          usage: {
            promptTokens: data.usage.prompt_tokens,
            completionTokens: data.usage.completion_tokens,
            totalTokens: data.usage.total_tokens,
          },
        };
      }

      return {
        success: true,
        data: choice.message.content ?? "",
        rawResponse: JSON.stringify(data),
        usage: {
          promptTokens: data.usage.prompt_tokens,
          completionTokens: data.usage.completion_tokens,
          totalTokens: data.usage.total_tokens,
        },
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  /**
   * Chat with structured output using Zod schema
   *
   * This is the TypeScript replacement for Python's instructor library.
   * Uses OpenAI function calling to extract structured data.
   *
   * @param messages - Chat messages
   * @param schema - Zod schema for the expected output
   * @param functionName - Name for the function call
   * @returns Validated output matching the schema
   */
  async chatWithSchema<T extends z.ZodType>(
    messages: ChatMessage[],
    schema: T,
    functionName: string,
    options: {
      temperature?: number;
      maxTokens?: number;
    } = {}
  ): Promise<LLMResult<z.infer<T>>> {
    // Convert Zod schema to JSON Schema for function calling
    const jsonSchema = zodToJsonSchema(schema, functionName);

    const functionDef: FunctionDefinition = {
      name: functionName,
      description: `Generate structured output matching the ${functionName} schema`,
      parameters: jsonSchema.definitions?.[functionName] ?? jsonSchema,
    };

    const result = await this.chat(messages, {
      ...options,
      functions: [functionDef],
      functionCall: { name: functionName },
    });

    if (!result.success || !result.data) {
      return {
        success: false,
        error: result.error ?? "No data returned",
        rawResponse: result.rawResponse,
        usage: result.usage,
      };
    }

    // Parse and validate with Zod
    try {
      const parsed = JSON.parse(result.data);
      const validated = schema.parse(parsed);

      return {
        success: true,
        data: validated,
        rawResponse: result.rawResponse,
        usage: result.usage,
      };
    } catch (error) {
      if (error instanceof z.ZodError) {
        return {
          success: false,
          error: `Validation error: ${error.errors.map(e => e.message).join(", ")}`,
          rawResponse: result.data,
          usage: result.usage,
        };
      }

      return {
        success: false,
        error: error instanceof Error ? error.message : String(error),
        rawResponse: result.data,
        usage: result.usage,
      };
    }
  }

  /**
   * Simple text completion (no chat format)
   */
  async complete(
    prompt: string,
    options: {
      temperature?: number;
      maxTokens?: number;
    } = {}
  ): Promise<LLMResult<string>> {
    return this.chat([{ role: "user", content: prompt }], options);
  }
}

/**
 * LLM Router - Routes tasks to appropriate backend
 *
 * - Strategic tasks → ALPHA (DeepSeek V3.1)
 * - Execution/Structured tasks → BETA (Nemotron)
 *
 * @example
 * ```typescript
 * const router = new LLMRouter();
 *
 * // Strategic reasoning (uses ALPHA)
 * const strategy = await router.route(TaskType.STRATEGIC, [
 *   { role: "user", content: "Design a video content strategy" }
 * ]);
 *
 * // Structured output (uses BETA)
 * const plan = await router.routeWithSchema(
 *   TaskType.STRUCTURED,
 *   [{ role: "user", content: "Plan a 30s video" }],
 *   ContentPlanSchema,
 *   "create_plan"
 * );
 * ```
 */
export class LLMRouter {
  private alphaClient: LMStudioClient;
  private betaClient: LMStudioClient;

  constructor() {
    this.alphaClient = new LMStudioClient({ baseUrl: config.urls.alphaLM });
    this.betaClient = new LMStudioClient({ baseUrl: config.urls.betaLM });
  }

  /**
   * Get the appropriate client for a task type
   */
  private getClient(taskType: TaskType): LMStudioClient {
    const endpoint = getTargetEndpoint(taskType);
    return endpoint === "alpha" ? this.alphaClient : this.betaClient;
  }

  /**
   * Route a chat request to the appropriate backend
   */
  async route(
    taskType: TaskType,
    messages: ChatMessage[],
    options: {
      temperature?: number;
      maxTokens?: number;
    } = {}
  ): Promise<LLMResult<string>> {
    const client = this.getClient(taskType);
    return client.chat(messages, options);
  }

  /**
   * Route a structured request to the appropriate backend
   */
  async routeWithSchema<T extends z.ZodType>(
    taskType: TaskType,
    messages: ChatMessage[],
    schema: T,
    functionName: string,
    options: {
      temperature?: number;
      maxTokens?: number;
    } = {}
  ): Promise<LLMResult<z.infer<T>>> {
    const client = this.getClient(taskType);
    return client.chatWithSchema(messages, schema, functionName, options);
  }

  /**
   * Check health of both backends
   */
  async checkHealth(): Promise<{
    alpha: { healthy: boolean; error?: string };
    beta: { healthy: boolean; error?: string };
  }> {
    const [alpha, beta] = await Promise.all([
      this.alphaClient.checkHealth(),
      this.betaClient.checkHealth(),
    ]);

    return { alpha, beta };
  }
}

// Export singleton instances for convenience
export const alphaLM = new LMStudioClient({ baseUrl: config.urls.alphaLM });
export const betaLM = new LMStudioClient({ baseUrl: config.urls.betaLM });
export const llmRouter = new LLMRouter();
