/** 动漫短视频：每 5 镜头 = 15s 一段，每剧本最多 4 段（60s） */

export const SHOTS_PER_SEGMENT = 5;
export const SEGMENT_DURATION_SEC = 15;
export const MAX_SEGMENTS_PER_SCRIPT = 4;
export const MAX_SHOTS_PER_SCRIPT = SHOTS_PER_SEGMENT * MAX_SEGMENTS_PER_SCRIPT;

export type AssetStatus = 'pending' | 'ok' | 'failed' | 'generating';

export interface AnimeCharacter {
  name: string;
  description: string;
  image_prompt?: string;
  image_path?: string;
  /** Seedance 输入用公网 URL（生图 API 返回） */
  image_url?: string;
  image_status?: AssetStatus;
  image_error?: string;
}

export interface AnimeShot {
  index: number;
  text: string;
  video_prompt?: string;
}

export interface AnimeSegment {
  segment_index: number;
  shots: AnimeShot[];
  status: AssetStatus;
  video_path?: string;
  video_url?: string;
  task_id?: string;
  error?: string;
}

export interface AnimeScript {
  index: number;
  title: string;
  synopsis: string;
  shots: AnimeShot[];
  segments: AnimeSegment[];
  completed?: boolean;
}

export interface AnimeData {
  synopsis: string;
  characters: AnimeCharacter[];
  scripts: AnimeScript[];
  has_videos: boolean;
  video_size?: string;
  /** 用户选择的短视频段数（每段 15 秒） */
  num_segments?: number;
}

export interface AnimeStoryboardResult {
  synopsis: string;
  character_description: string;
  characters: Omit<AnimeCharacter, 'image_status' | 'image_path' | 'image_url'>[];
  scripts: {
    title: string;
    synopsis: string;
    shots: { text: string; video_prompt?: string }[];
  }[];
  num_segments?: number;
}
