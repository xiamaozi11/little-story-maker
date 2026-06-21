/**
 * Seedance 2.0 客户端（与根目录 seedance20_client.py 对齐）
 */
import {
  DEFAULT_SEEDANCE_MODEL,
  DEFAULT_SEEDANCE_RESULT_URL,
  DEFAULT_SEEDANCE_URL,
  SEGMENT_DURATION_SEC,
} from '../config/constants';
import { AppSettings } from './settings';

const POLL_INTERVAL_MS = 5000;
const POLL_TIMEOUT_MS = 1200000;
const SEEDANCE20_MAX_AUDIOS = 3;

const VIDEO_URL_JSON_PATHS = [
  'video_url',
  'output_url',
  'url',
  'data.video_url',
  'data.output_url',
  'data.url',
  'result.video_url',
  'result.url',
  'content.video_url',
  'content.url',
];

const TASK_ID_JSON_PATHS = [
  'task_id',
  'taskId',
  'data.task_id',
  'data.taskId',
  'data.id',
  'result.task_id',
  'content.task_id',
];

export type TaskState = 'pending' | 'succeeded' | 'failed' | 'unknown';

function digJson(obj: unknown, dotted: string): unknown {
  let cur: unknown = obj;
  for (const part of dotted.split('.')) {
    if (!part || typeof cur !== 'object' || cur === null || !(part in cur)) {
      return undefined;
    }
    cur = (cur as Record<string, unknown>)[part];
  }
  return cur;
}

export function extractVideoUrl(data: unknown): string | undefined {
  if (typeof data === 'string' && /^https?:\/\//i.test(data.trim())) {
    return data.trim().split(/\s/)[0];
  }
  if (Array.isArray(data)) {
    for (const item of data) {
      const u = extractVideoUrl(item);
      if (u) return u;
    }
    return undefined;
  }
  if (typeof data !== 'object' || data === null) return undefined;

  const nested = (data as Record<string, unknown>).data;
  if (Array.isArray(nested)) {
    for (const item of nested) {
      if (item && typeof item === 'object' && 'url' in item) {
        const u = String((item as { url: string }).url);
        if (/^https?:\/\//i.test(u)) return u.trim();
      }
    }
  }

  for (const p of VIDEO_URL_JSON_PATHS) {
    const v = digJson(data, p);
    if (typeof v === 'string' && /^https?:\/\//i.test(v)) return v.trim();
  }
  return undefined;
}

export function extractTaskId(data: unknown): string | undefined {
  if (typeof data === 'string' && data.trim()) return data.trim();
  if (typeof data !== 'object' || data === null) return undefined;
  const d = data as Record<string, unknown>;
  for (const k of ['task_id', 'taskId', 'taskID', 'id']) {
    const v = d[k];
    if (typeof v === 'string' && v.trim()) return v.trim();
  }
  for (const p of TASK_ID_JSON_PATHS) {
    const v = digJson(data, p);
    if (typeof v === 'string' && v.trim()) return v.trim();
  }
  return undefined;
}

function normalizeTaskStatus(raw: unknown): TaskState {
  const s = String(raw ?? '').trim().toLowerCase();
  if (['success', 'succeeded', 'completed', 'complete', 'done', 'finish', 'finished'].includes(s)) {
    return 'succeeded';
  }
  if (['fail', 'failed', 'failure', 'error', 'cancelled', 'canceled', 'timeout'].includes(s)) {
    return 'failed';
  }
  if (
    [
      'pending',
      'processing',
      'process',
      'running',
      'run',
      'queued',
      'queue',
      'waiting',
      'in_progress',
      'in progress',
      'submitted',
    ].includes(s)
  ) {
    return 'pending';
  }
  return 'unknown';
}

export function classifySeedanceTaskState(
  data: unknown
): { state: TaskState; message?: string } {
  const videoUrl = extractVideoUrl(data);
  if (videoUrl) return { state: 'succeeded' };

  if (typeof data !== 'object' || data === null) return { state: 'unknown' };

  for (const path of ['error', 'message', 'msg', 'data.error', 'data.message']) {
    const err = digJson(data, path);
    if (typeof err === 'string' && err.trim()) {
      const st = normalizeTaskStatus(err);
      if (st === 'failed') return { state: 'failed', message: err.trim() };
    }
  }

  for (const path of [
    'status',
    'state',
    'task_status',
    'data.status',
    'data.state',
    'result.status',
  ]) {
    const raw = digJson(data, path);
    if (raw != null) {
      const st = normalizeTaskStatus(raw);
      if (st !== 'unknown') {
        let msg: string | undefined;
        if (st === 'failed') {
          const m = digJson(data, 'message') ?? digJson(data, 'data.message');
          msg = typeof m === 'string' && m.trim() ? m.trim() : undefined;
        }
        return { state: st, message: msg };
      }
    }
  }

  const code = (data as Record<string, unknown>).code;
  if (code !== undefined && code !== null && code !== 0 && code !== '0') {
    const em = (data as Record<string, unknown>).message ?? (data as Record<string, unknown>).msg;
    return {
      state: 'failed',
      message: typeof em === 'string' && em.trim() ? em.trim() : `code=${code}`,
    };
  }

  return { state: 'unknown' };
}

function extractErrorMessage(data: unknown, fallback?: string): string {
  const { state, message } = classifySeedanceTaskState(data);
  if (state === 'failed' && message) return message;
  if (typeof data !== 'object' || data === null) return fallback ?? '任务失败';
  for (const p of ['message', 'msg', 'error', 'data.message', 'data.error']) {
    const v = digJson(data, p);
    if (typeof v === 'string' && v.trim()) return v.trim();
  }
  return fallback ?? '任务失败';
}

/** Zeelin 网关密钥（与 seedance20_client._resolve_seedance_api_key 显式传参一致） */
function resolveApiKey(settings: AppSettings): string {
  return settings.seedanceApiKey.trim();
}

function buildHeaders(apiKey: string): Record<string, string> {
  return {
    Authorization: apiKey,
    'Content-Type': 'application/json',
    Connection: 'keep-alive',
  };
}

export interface SeedanceByPass {
  ratio?: string;
  resolution?: string;
  videos?: string[];
  audios?: string[];
}

export function validateSeedanceAudiosLimit(
  audios?: string[] | null,
  maxAudios = SEEDANCE20_MAX_AUDIOS
): { ok: boolean; error?: string } {
  const urls = (audios ?? []).filter((u) => u.trim());
  if (urls.length > maxAudios) {
    return {
      ok: false,
      error: `Seedance 2.0 最多上传 ${maxAudios} 条音频，当前 ${urls.length} 条`,
    };
  }
  return { ok: true };
}

/** 与 build_seedance20_payload 一致 */
export function buildSeedance20Payload(
  prompt: string,
  opts?: {
    duration?: number;
    size?: string;
    generateAudio?: boolean;
    generateMode?: number;
    byPass?: SeedanceByPass;
    images?: string[];
    model?: string;
  }
): Record<string, unknown> {
  const body: Record<string, unknown> = {
    model: opts?.model?.trim() || DEFAULT_SEEDANCE_MODEL,
    prompt,
    duration: opts?.duration ?? SEGMENT_DURATION_SEC,
    size: opts?.size ?? '960x1696',
    generate_audio: opts?.generateAudio ?? true,
    generate_mode: opts?.generateMode ?? 1,
  };
  if (opts?.byPass) body.byPass = { ...opts.byPass };
  if (opts?.images) body.images = [...opts.images];
  return body;
}

/** 与 build_seedance20_prompt_with_refs 一致：参考段在前，剧本 base 在后 */
export function buildSeedancePromptWithRefs(
  base: string,
  opts?: {
    imageLabels?: string[];
    audioLabels?: string[];
    videoLabels?: string[];
  }
): string {
  const parts: string[] = [];
  const b = base.trim();

  const appendRefs = (kindCn: string, atPrefix: string, labels?: string[]) => {
    if (!labels?.length) return;
    labels.forEach((lab, i) => {
      let line = `参考${kindCn}${i + 1}\n@${atPrefix}${i + 1}`;
      if (lab.trim()) line += `  ${lab.trim()}`;
      parts.push(line);
    });
  };

  appendRefs('图片', '图片', opts?.imageLabels);
  appendRefs('音频', '音频', opts?.audioLabels);
  appendRefs('视频', '视频', opts?.videoLabels);
  if (b) parts.push(b);
  return parts.join('\n').trim();
}

export interface PostSeedanceOptions {
  settings: AppSettings;
  prompt: string;
  duration?: number;
  size?: string;
  generateAudio?: boolean;
  generateMode?: number;
  images?: string[];
  byPass?: SeedanceByPass;
  poll?: boolean;
  onPoll?: (attempt: number, state: TaskState) => void;
}

export interface SeedanceResult {
  ok: boolean;
  taskId?: string;
  videoUrl?: string;
  error?: string;
}

async function queryResult(
  settings: AppSettings,
  taskId: string
): Promise<{ state: TaskState; videoUrl?: string; error?: string }> {
  const apiKey = resolveApiKey(settings);
  const url = settings.seedanceResultUrl || DEFAULT_SEEDANCE_RESULT_URL;
  const res = await fetch(url, {
    method: 'POST',
    headers: buildHeaders(apiKey),
    body: JSON.stringify({
      model: DEFAULT_SEEDANCE_MODEL,
      task_id: taskId,
    }),
  });
  const text = await res.text();
  let json: unknown = null;
  try {
    json = text ? JSON.parse(text) : null;
  } catch {
    json = null;
  }
  if (!res.ok) {
    return { state: 'failed', error: `HTTP ${res.status}: ${text.slice(0, 200)}` };
  }
  const { state, message } = classifySeedanceTaskState(json);
  return {
    state,
    videoUrl: extractVideoUrl(json),
    error: state === 'failed' ? message ?? extractErrorMessage(json) : undefined,
  };
}

/** 与 post_seedance20 一致：提交任务 */
export async function postSeedance20(options: PostSeedanceOptions): Promise<SeedanceResult> {
  const {
    settings,
    prompt,
    duration = SEGMENT_DURATION_SEC,
    size = '960x1696',
    generateAudio = true,
    generateMode = 1,
    images,
    byPass,
  } = options;

  const apiKey = resolveApiKey(settings);
  if (!apiKey) {
    return {
      ok: false,
      error:
        '未配置 Seedance API Key（请在设置中填写 Zeelin 网关密钥，百炼 Key 不能用于视频生成）',
    };
  }

  const audioCheck = validateSeedanceAudiosLimit(byPass?.audios);
  if (!audioCheck.ok) {
    return { ok: false, error: audioCheck.error };
  }

  const submitUrl = settings.seedanceUrl || DEFAULT_SEEDANCE_URL;
  const payload = buildSeedance20Payload(prompt, {
    duration,
    size,
    generateAudio,
    generateMode,
    byPass,
    images,
  });

  const submitRes = await fetch(submitUrl, {
    method: 'POST',
    headers: buildHeaders(apiKey),
    body: JSON.stringify(payload),
  });
  const submitText = await submitRes.text();
  let submitJson: unknown = null;
  try {
    submitJson = submitText ? JSON.parse(submitText) : null;
  } catch {
    submitJson = null;
  }

  if (!submitRes.ok) {
    const errFromJson =
      submitJson && typeof submitJson === 'object' && 'error' in submitJson
        ? String((submitJson as { error: unknown }).error)
        : '';
    return {
      ok: false,
      error: errFromJson
        ? `提交失败 HTTP ${submitRes.status}: ${errFromJson}`
        : `提交失败 HTTP ${submitRes.status}: ${submitText.slice(0, 300)}`,
    };
  }

  const syncUrl = extractVideoUrl(submitJson);
  const taskId = extractTaskId(submitJson);
  if (syncUrl) {
    return { ok: true, videoUrl: syncUrl, taskId };
  }
  if (!taskId) {
    return { ok: false, error: '提交成功但未返回 task_id，且响应中无 video_url' };
  }
  return { ok: true, taskId };
}

/** 与 post_seedance20_and_wait 一致：提交并轮询 */
export async function postSeedanceAndWait(
  options: PostSeedanceOptions
): Promise<SeedanceResult> {
  const { settings, poll = true, onPoll } = options;

  const submit = await postSeedance20(options);
  if (!submit.ok) return submit;

  if (submit.videoUrl) {
    return submit;
  }

  const taskId = submit.taskId;
  if (!taskId) {
    return { ok: false, error: '提交成功但未返回 task_id' };
  }

  if (!poll) {
    return { ok: true, taskId };
  }

  const deadline = Date.now() + POLL_TIMEOUT_MS;
  let attempt = 0;
  while (Date.now() < deadline) {
    attempt += 1;
    const q = await queryResult(settings, taskId);
    onPoll?.(attempt, q.state);
    if (q.state === 'succeeded' && q.videoUrl) {
      return { ok: true, taskId, videoUrl: q.videoUrl };
    }
    if (q.state === 'failed') {
      return { ok: false, taskId, error: q.error ?? '视频生成失败' };
    }
    await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
  }

  return { ok: false, taskId, error: `轮询超时（>${POLL_TIMEOUT_MS / 1000}s）` };
}
