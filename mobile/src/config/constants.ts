export const MIN_SCENES = 1;
export const MAX_SCENES = 30;
export const DEFAULT_SCENES = 10;

export const DEFAULT_API_ENDPOINT =
  'https://dashscope.aliyuncs.com/compatible-mode/v1';
export const DEFAULT_TEXT_MODEL = 'qwen-plus';
export const DEFAULT_ARK_BASE_URL =
  'https://ark.cn-beijing.volces.com/api/v3';
export const DEFAULT_DOUBAO_IMAGE_MODEL = 'doubao-seedream-4-5-251128';
export const DEFAULT_IMAGE_MODEL = 'wan2.6-t2i';
/** @deprecated 使用 DEFAULT_IMAGE_MODEL */
export const TONGYI_IMAGE_MODEL = DEFAULT_IMAGE_MODEL;
export const DEFAULT_IMAGE_SIZE = '1104x1472';
export const DEFAULT_IMAGE_STYLE = '卡通';

export const DEFAULT_SEEDANCE_URL =
  'https://getways-jumu.zeelin.cn/v1/video/generations';
export const DEFAULT_SEEDANCE_RESULT_URL =
  'https://getways-jumu.zeelin.cn/v1/video/result';
export const DEFAULT_SEEDANCE_MODEL = 'Doubao-Seedance-2.0';
export const DEFAULT_ANIME_VIDEO_SIZE = '960x1696';
export const DEFAULT_ANIME_IMAGE_STYLE = '动漫';

export const SHOTS_PER_SEGMENT = 5;
export const SEGMENT_DURATION_SEC = 15;
export const MIN_ANIME_SEGMENTS = 1;
export const MAX_ANIME_SEGMENTS = 4;
export const DEFAULT_ANIME_SEGMENTS = 2;
export const MAX_SEGMENTS_PER_SCRIPT = MAX_ANIME_SEGMENTS;
export const MAX_SHOTS_PER_SCRIPT = SHOTS_PER_SEGMENT * MAX_SEGMENTS_PER_SCRIPT;

export const IMAGE_STYLES: Record<string, string> = {
  漫画风:
    'manga style, black and white, ink drawing, outlines, monochrome, suitable for kindle e-reader',
  动漫: 'anime style, colorful, vibrant, cel shading, Japanese animation style',
  中国风:
    'Chinese style painting, traditional Chinese art, ink wash, elegant, oriental aesthetics',
  水墨画:
    'ink wash painting, watercolor style, soft brush strokes, minimalist, artistic',
  古典:
    'classical painting style, renaissance art, oil painting texture, museum quality',
  油画:
    'oil painting, thick brush strokes, textured canvas, rich colors, classical art',
  水彩画:
    'watercolor painting, soft colors, gentle brush strokes, light and airy',
  卡通: 'cartoon style, cute, colorful, simple shapes, child-friendly illustration',
};

export const DOUBAO_SIZES: Record<string, string> = {
  '1920x2560 (3:4 竖版，推荐)': '1920x2560',
  '2048x2730 (3:4 竖版，高清)': '2048x2730',
  '2048x2048 (1:1 正方形)': '2048x2048',
  '2560x1920 (4:3 横版)': '2560x1920',
  '2048x1536 (4:3 横版小)': '2048x1536',
};

export const TONGYI_SIZES: Record<string, string> = {
  '1104x1472 (3:4 竖版，推荐)': '1104x1472',
  '1280x1280 (1:1 正方形)': '1280x1280',
  '960x1280 (3:4 竖版)': '960x1280',
  '1472x1104 (4:3 横版)': '1472x1104',
  '960x1696 (9:16 竖版长)': '960x1696',
};

export const APP_CONFIG = {
  min_scenes: MIN_SCENES,
  max_scenes: MAX_SCENES,
  default_scenes: DEFAULT_SCENES,
  image_styles: Object.keys(IMAGE_STYLES),
  default_image_style: DEFAULT_IMAGE_STYLE,
  image_services: [
    { id: 'tongyi', label: '百炼万象' },
    { id: 'doubao', label: '豆包（可选）' },
  ],
  doubao_sizes: DOUBAO_SIZES,
  tongyi_sizes: TONGYI_SIZES,
  anime_video_size: DEFAULT_ANIME_VIDEO_SIZE,
  anime_image_style: DEFAULT_ANIME_IMAGE_STYLE,
  min_anime_segments: MIN_ANIME_SEGMENTS,
  max_anime_segments: MAX_ANIME_SEGMENTS,
  default_anime_segments: DEFAULT_ANIME_SEGMENTS,
};
