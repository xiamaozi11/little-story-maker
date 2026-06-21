export interface Scene {
  index: number;
  scene_number: number;
  text: string;
  text_en?: string;
  image_prompt?: string;
  image_path?: string;
  image_status?: 'ok' | 'failed' | 'pending';
  image_error?: string;
}

export type ContentType = 'book' | 'anime';

export interface Book {
  id: string;
  idea: string;
  character: string;
  num_scenes: number;
  character_description: string;
  story_generated: boolean;
  has_images: boolean;
  content_type?: ContentType;
  image_style?: string;
  image_service?: 'doubao' | 'tongyi';
  image_size?: string;
  scenes: Scene[];
  anime?: import('./anime').AnimeData;
  pdf_path?: string;
  title?: string;
  author?: string;
  created_at: string;
  updated_at: string;
}

export interface BookSummary {
  id: string;
  character: string;
  idea: string;
  num_scenes: number;
  has_images: boolean;
  content_type?: ContentType;
  created_at: string;
  title?: string;
}
