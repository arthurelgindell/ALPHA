/**
 * FFmpeg Subprocess Wrapper
 * Apple Silicon optimized with VideoToolbox hardware acceleration
 *
 * Uses native ARM64 ffmpeg from Homebrew
 */

import config from "../config";

export interface FFmpegResult {
  success: boolean;
  outputPath: string;
  error?: string;
  duration?: number;
}

export interface MuxOptions {
  videoPath: string;
  audioPath: string;
  outputPath: string;
  audioOffset?: number; // seconds
  audioBitrate?: string;
}

export interface TranscodeOptions {
  inputPath: string;
  outputPath: string;
  codec?: "h264" | "hevc";
  crf?: number;
  audioBitrate?: string;
  scale?: string;
}

export interface ProbeResult {
  success: boolean;
  duration?: number;
  width?: number;
  height?: number;
  fps?: number;
  codec?: string;
  error?: string;
}

/**
 * Mux video with audio track
 * Uses hardware-accelerated AAC encoding on Apple Silicon
 *
 * @example
 * ```typescript
 * const result = await muxAudio({
 *   videoPath: "video.mp4",
 *   audioPath: "narration.wav",
 *   outputPath: "final.mp4",
 *   audioOffset: 0.5 // delay audio by 0.5s
 * });
 * ```
 */
export async function muxAudio(options: MuxOptions): Promise<FFmpegResult> {
  const {
    videoPath,
    audioPath,
    outputPath,
    audioOffset = 0,
    audioBitrate = "192k",
  } = options;

  const args: string[] = [
    config.binaries.ffmpeg,
    "-y",
    "-i", videoPath,
    "-i", audioPath,
    "-c:v", "copy",
    ...config.ffmpeg.aacEncoder, // -c:a aac_at (Apple AudioToolbox)
    "-b:a", audioBitrate,
    "-map", "0:v",
    "-map", "1:a",
  ];

  // Add audio delay if specified
  if (audioOffset > 0) {
    const delayMs = Math.round(audioOffset * 1000);
    args.push("-af", `adelay=${delayMs}|${delayMs}`);
  }

  args.push(outputPath);

  try {
    console.log(`Muxing: ${videoPath} + ${audioPath} → ${outputPath}`);
    const startTime = Date.now();

    const proc = Bun.spawn(args, {
      stdout: "pipe",
      stderr: "pipe",
    });

    const exitCode = await proc.exited;
    const duration = (Date.now() - startTime) / 1000;

    if (exitCode !== 0) {
      const stderr = await new Response(proc.stderr).text();
      return {
        success: false,
        outputPath,
        error: stderr || `FFmpeg exited with code ${exitCode}`,
      };
    }

    console.log(`Mux complete: ${outputPath} (${duration.toFixed(1)}s)`);

    return {
      success: true,
      outputPath,
      duration,
    };
  } catch (error) {
    return {
      success: false,
      outputPath,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

/**
 * Transcode video with hardware acceleration
 * Uses VideoToolbox H.264/HEVC encoders on Apple Silicon
 *
 * @example
 * ```typescript
 * const result = await transcode({
 *   inputPath: "input.mp4",
 *   outputPath: "output.mp4",
 *   codec: "h264",
 *   scale: "1920:1080"
 * });
 * ```
 */
export async function transcode(options: TranscodeOptions): Promise<FFmpegResult> {
  const {
    inputPath,
    outputPath,
    codec = "h264",
    audioBitrate = "192k",
    scale,
  } = options;

  // Select hardware encoder
  const encoder = codec === "hevc"
    ? config.ffmpeg.hevcEncoder
    : config.ffmpeg.h264Encoder;

  const args: string[] = [
    config.binaries.ffmpeg,
    "-y",
    ...config.ffmpeg.videoToolbox, // -hwaccel videotoolbox
    "-i", inputPath,
    ...encoder,
    ...config.ffmpeg.aacEncoder,
    "-b:a", audioBitrate,
  ];

  // Add scaling if specified
  if (scale) {
    args.push("-vf", `scale=${scale}`);
  }

  args.push(outputPath);

  try {
    console.log(`Transcoding: ${inputPath} → ${outputPath}`);
    const startTime = Date.now();

    const proc = Bun.spawn(args, {
      stdout: "pipe",
      stderr: "pipe",
    });

    const exitCode = await proc.exited;
    const duration = (Date.now() - startTime) / 1000;

    if (exitCode !== 0) {
      const stderr = await new Response(proc.stderr).text();
      return {
        success: false,
        outputPath,
        error: stderr || `FFmpeg exited with code ${exitCode}`,
      };
    }

    console.log(`Transcode complete: ${outputPath} (${duration.toFixed(1)}s)`);

    return {
      success: true,
      outputPath,
      duration,
    };
  } catch (error) {
    return {
      success: false,
      outputPath,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

/**
 * Probe video file for metadata
 *
 * @example
 * ```typescript
 * const info = await probe("video.mp4");
 * console.log(`Duration: ${info.duration}s, Resolution: ${info.width}x${info.height}`);
 * ```
 */
export async function probe(inputPath: string): Promise<ProbeResult> {
  const args = [
    config.binaries.ffprobe,
    "-v", "quiet",
    "-print_format", "json",
    "-show_format",
    "-show_streams",
    inputPath,
  ];

  try {
    const proc = Bun.spawn(args, {
      stdout: "pipe",
      stderr: "pipe",
    });

    const exitCode = await proc.exited;

    if (exitCode !== 0) {
      return { success: false, error: "FFprobe failed" };
    }

    const stdout = await new Response(proc.stdout).text();
    const data = JSON.parse(stdout);

    // Find video stream
    const videoStream = data.streams?.find(
      (s: { codec_type: string }) => s.codec_type === "video"
    );

    // Parse frame rate (e.g., "30/1" or "30000/1001")
    let fps: number | undefined;
    if (videoStream?.r_frame_rate) {
      const [num, den] = videoStream.r_frame_rate.split("/").map(Number);
      fps = den ? num / den : num;
    }

    return {
      success: true,
      duration: data.format?.duration ? parseFloat(data.format.duration) : undefined,
      width: videoStream?.width,
      height: videoStream?.height,
      fps,
      codec: videoStream?.codec_name,
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

/**
 * Extract audio from video file
 *
 * @example
 * ```typescript
 * const result = await extractAudio("video.mp4", "audio.wav");
 * ```
 */
export async function extractAudio(
  inputPath: string,
  outputPath: string
): Promise<FFmpegResult> {
  const args = [
    config.binaries.ffmpeg,
    "-y",
    "-i", inputPath,
    "-vn", // No video
    "-acodec", "pcm_s16le", // WAV format
    "-ar", "44100", // Sample rate
    "-ac", "2", // Stereo
    outputPath,
  ];

  try {
    const proc = Bun.spawn(args, {
      stdout: "pipe",
      stderr: "pipe",
    });

    const exitCode = await proc.exited;

    if (exitCode !== 0) {
      const stderr = await new Response(proc.stderr).text();
      return {
        success: false,
        outputPath,
        error: stderr || "Audio extraction failed",
      };
    }

    return { success: true, outputPath };
  } catch (error) {
    return {
      success: false,
      outputPath,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

/**
 * Concatenate multiple video files
 *
 * @example
 * ```typescript
 * const result = await concat(
 *   ["clip1.mp4", "clip2.mp4", "clip3.mp4"],
 *   "final.mp4"
 * );
 * ```
 */
export async function concat(
  inputPaths: string[],
  outputPath: string
): Promise<FFmpegResult> {
  // Create concat file content
  const concatContent = inputPaths
    .map((p) => `file '${p}'`)
    .join("\n");

  // Write temporary concat file
  const concatFile = `/tmp/concat_${Date.now()}.txt`;
  await Bun.write(concatFile, concatContent);

  const args = [
    config.binaries.ffmpeg,
    "-y",
    "-f", "concat",
    "-safe", "0",
    "-i", concatFile,
    "-c", "copy",
    outputPath,
  ];

  try {
    const proc = Bun.spawn(args, {
      stdout: "pipe",
      stderr: "pipe",
    });

    const exitCode = await proc.exited;

    // Cleanup temp file
    await Bun.write(concatFile, ""); // Clear
    // Note: In real use, should delete the file

    if (exitCode !== 0) {
      const stderr = await new Response(proc.stderr).text();
      return {
        success: false,
        outputPath,
        error: stderr || "Concat failed",
      };
    }

    return { success: true, outputPath };
  } catch (error) {
    return {
      success: false,
      outputPath,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}
