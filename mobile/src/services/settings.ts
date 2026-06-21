import AsyncStorage from '@react-native-async-storage/async-storage';
import { BUNDLED_DEFAULTS } from '../config/bundledDefaults';
import {
  DEFAULT_API_ENDPOINT,
  DEFAULT_ARK_BASE_URL,
  DEFAULT_DOUBAO_IMAGE_MODEL,
  DEFAULT_IMAGE_MODEL,
  DEFAULT_SEEDANCE_RESULT_URL,
  DEFAULT_SEEDANCE_URL,
  DEFAULT_TEXT_MODEL,
} from '../config/constants';

const KEYS = {
  API_KEY: '@storycraft/api_key',
  API_ENDPOINT: '@storycraft/api_endpoint',
  TEXT_MODEL: '@storycraft/text_model',
  IMAGE_MODEL: '@storycraft/image_model',
  ARK_API_KEY: '@storycraft/ark_api_key',
  ARK_BASE_URL: '@storycraft/ark_base_url',
  DOUBAO_MODEL: '@storycraft/doubao_model',
  SEEDANCE_API_KEY: '@storycraft/seedance_api_key',
  SEEDANCE_URL: '@storycraft/seedance_url',
  SEEDANCE_RESULT_URL: '@storycraft/seedance_result_url',
};

export interface AppSettings {
  apiKey: string;
  apiEndpoint: string;
  textModel: string;
  imageModel: string;
  arkApiKey: string;
  arkBaseUrl: string;
  doubaoModel: string;
  seedanceApiKey: string;
  seedanceUrl: string;
  seedanceResultUrl: string;
}

export async function loadSettings(): Promise<AppSettings> {
  const [
    apiKey,
    apiEndpoint,
    textModel,
    imageModel,
    arkApiKey,
    arkBaseUrl,
    doubaoModel,
    seedanceApiKey,
    seedanceUrl,
    seedanceResultUrl,
  ] = await Promise.all([
    AsyncStorage.getItem(KEYS.API_KEY),
    AsyncStorage.getItem(KEYS.API_ENDPOINT),
    AsyncStorage.getItem(KEYS.TEXT_MODEL),
    AsyncStorage.getItem(KEYS.IMAGE_MODEL),
    AsyncStorage.getItem(KEYS.ARK_API_KEY),
    AsyncStorage.getItem(KEYS.ARK_BASE_URL),
    AsyncStorage.getItem(KEYS.DOUBAO_MODEL),
    AsyncStorage.getItem(KEYS.SEEDANCE_API_KEY),
    AsyncStorage.getItem(KEYS.SEEDANCE_URL),
    AsyncStorage.getItem(KEYS.SEEDANCE_RESULT_URL),
  ]);

  return {
    apiKey: apiKey ?? BUNDLED_DEFAULTS.apiKey,
    apiEndpoint: apiEndpoint ?? BUNDLED_DEFAULTS.apiEndpoint ?? DEFAULT_API_ENDPOINT,
    textModel: textModel ?? BUNDLED_DEFAULTS.textModel ?? DEFAULT_TEXT_MODEL,
    imageModel: imageModel ?? BUNDLED_DEFAULTS.imageModel ?? DEFAULT_IMAGE_MODEL,
    arkApiKey: arkApiKey ?? BUNDLED_DEFAULTS.arkApiKey,
    arkBaseUrl: arkBaseUrl ?? BUNDLED_DEFAULTS.arkBaseUrl ?? DEFAULT_ARK_BASE_URL,
    doubaoModel: doubaoModel ?? BUNDLED_DEFAULTS.doubaoModel ?? DEFAULT_DOUBAO_IMAGE_MODEL,
    seedanceApiKey: seedanceApiKey ?? BUNDLED_DEFAULTS.seedanceApiKey,
    seedanceUrl: seedanceUrl ?? BUNDLED_DEFAULTS.seedanceUrl ?? DEFAULT_SEEDANCE_URL,
    seedanceResultUrl:
      seedanceResultUrl ?? BUNDLED_DEFAULTS.seedanceResultUrl ?? DEFAULT_SEEDANCE_RESULT_URL,
  };
}

export async function saveSettings(settings: Partial<AppSettings>): Promise<void> {
  const pairs: [string, string][] = [];
  if (settings.apiKey !== undefined) pairs.push([KEYS.API_KEY, settings.apiKey]);
  if (settings.apiEndpoint !== undefined)
    pairs.push([KEYS.API_ENDPOINT, settings.apiEndpoint]);
  if (settings.textModel !== undefined)
    pairs.push([KEYS.TEXT_MODEL, settings.textModel]);
  if (settings.imageModel !== undefined)
    pairs.push([KEYS.IMAGE_MODEL, settings.imageModel]);
  if (settings.arkApiKey !== undefined)
    pairs.push([KEYS.ARK_API_KEY, settings.arkApiKey]);
  if (settings.arkBaseUrl !== undefined)
    pairs.push([KEYS.ARK_BASE_URL, settings.arkBaseUrl]);
  if (settings.doubaoModel !== undefined)
    pairs.push([KEYS.DOUBAO_MODEL, settings.doubaoModel]);
  if (settings.seedanceApiKey !== undefined)
    pairs.push([KEYS.SEEDANCE_API_KEY, settings.seedanceApiKey]);
  if (settings.seedanceUrl !== undefined)
    pairs.push([KEYS.SEEDANCE_URL, settings.seedanceUrl]);
  if (settings.seedanceResultUrl !== undefined)
    pairs.push([KEYS.SEEDANCE_RESULT_URL, settings.seedanceResultUrl]);
  await AsyncStorage.multiSet(pairs);
}

export async function isConfiguredForText(): Promise<boolean> {
  const s = await loadSettings();
  return Boolean(s.apiKey.trim());
}

export async function isConfiguredForImages(
  service: 'doubao' | 'tongyi'
): Promise<boolean> {
  const s = await loadSettings();
  if (service === 'tongyi') return Boolean(s.apiKey.trim());
  return Boolean(s.arkApiKey.trim());
}

export async function isConfiguredForSeedance(): Promise<boolean> {
  const s = await loadSettings();
  return Boolean(s.seedanceApiKey.trim());
}
