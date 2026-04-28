import type { ProxyOptions } from 'vite';

const DEFAULT_API_PROXY_TARGET = 'http://localhost:8000';
const DEFAULT_TTS_PROXY_TARGET = 'http://localhost:8001';

const getProxyTarget = (envName: string, fallback: string): string => {
  const value = process.env[envName]?.trim();
  return value || fallback;
};

export const createDevProxy = (): Record<string, string | ProxyOptions> => {
  const apiTarget = getProxyTarget('WORDBRIDGE_API_PROXY_TARGET', DEFAULT_API_PROXY_TARGET);
  const ttsTarget = getProxyTarget('WORDBRIDGE_TTS_PROXY_TARGET', DEFAULT_TTS_PROXY_TARGET);

  return {
    '/api/v1/chat/ws': {
      target: apiTarget,
      changeOrigin: true,
      ws: true,
    },
    '/api/tts': {
      target: ttsTarget,
      changeOrigin: true,
    },
    '/api': {
      target: apiTarget,
      changeOrigin: true,
    },
    '/health': {
      target: apiTarget,
      changeOrigin: true,
    },
  };
};
