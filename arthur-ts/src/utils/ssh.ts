/**
 * SSH Command Execution Utility
 * For remote operations on BETA and other hosts
 *
 * Uses Bun.spawn for efficient subprocess management
 */

import config from "../config";

export interface SSHResult {
  success: boolean;
  stdout: string;
  stderr: string;
  exitCode: number;
  error?: string;
}

export interface SSHOptions {
  host?: string;
  timeout?: number;
  cwd?: string;
}

/**
 * Execute a command on a remote host via SSH
 *
 * @param command - Command to execute on remote host
 * @param options - SSH options (host, timeout)
 * @returns SSHResult with stdout, stderr, and exit code
 *
 * @example
 * ```typescript
 * // Check if BETA is reachable
 * const result = await sshExec("echo ok", { host: "beta" });
 * if (result.success) {
 *   console.log("BETA is online");
 * }
 *
 * // Execute TTS on BETA
 * const result = await sshExec(
 *   "/path/to/python /path/to/tts.py --output /tmp/voice.wav 'Hello world'",
 *   { host: "beta", timeout: 90000 }
 * );
 * ```
 */
export async function sshExec(
  command: string,
  options: SSHOptions = {}
): Promise<SSHResult> {
  const host = options.host ?? "beta";
  const timeout = options.timeout ?? 60000;

  try {
    const proc = Bun.spawn([config.binaries.ssh, host, command], {
      stdout: "pipe",
      stderr: "pipe",
    });

    // Set up timeout
    const timeoutId = setTimeout(() => {
      proc.kill();
    }, timeout);

    // Wait for completion
    const exitCode = await proc.exited;
    clearTimeout(timeoutId);

    // Read output
    const stdout = await new Response(proc.stdout).text();
    const stderr = await new Response(proc.stderr).text();

    return {
      success: exitCode === 0,
      stdout: stdout.trim(),
      stderr: stderr.trim(),
      exitCode,
    };
  } catch (error) {
    return {
      success: false,
      stdout: "",
      stderr: "",
      exitCode: -1,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

/**
 * Transfer a file from remote host to local using SSH cat
 * More reliable than scp for single files
 *
 * @param remotePath - Path on remote host
 * @param localPath - Local destination path
 * @param options - SSH options
 * @returns Success status
 *
 * @example
 * ```typescript
 * const success = await sshCat(
 *   "/tmp/voice.wav",
 *   "/Users/local/voice.wav",
 *   { host: "beta" }
 * );
 * ```
 */
export async function sshCat(
  remotePath: string,
  localPath: string,
  options: SSHOptions = {}
): Promise<{ success: boolean; error?: string }> {
  const host = options.host ?? "beta";
  const timeout = options.timeout ?? 60000;

  try {
    const proc = Bun.spawn([config.binaries.ssh, host, "cat", remotePath], {
      stdout: "pipe",
      stderr: "pipe",
    });

    const timeoutId = setTimeout(() => {
      proc.kill();
    }, timeout);

    const exitCode = await proc.exited;
    clearTimeout(timeoutId);

    if (exitCode !== 0) {
      const stderr = await new Response(proc.stderr).text();
      return { success: false, error: stderr || "Transfer failed" };
    }

    // Write to local file
    const data = await new Response(proc.stdout).arrayBuffer();
    await Bun.write(localPath, data);

    return { success: true };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

/**
 * Check if a remote host is reachable via SSH
 *
 * @param host - Hostname to check
 * @returns True if reachable
 */
export async function sshCheck(host = "beta"): Promise<boolean> {
  const result = await sshExec("echo ok", { host, timeout: 10000 });
  return result.success && result.stdout === "ok";
}

/**
 * Delete a file on remote host
 *
 * @param remotePath - Path to delete
 * @param options - SSH options
 */
export async function sshRm(
  remotePath: string,
  options: SSHOptions = {}
): Promise<void> {
  await sshExec(`rm -f ${remotePath}`, options);
}
