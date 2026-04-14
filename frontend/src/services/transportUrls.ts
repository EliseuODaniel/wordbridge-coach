const trimTrailingSlash = (value: string): string => value.replace(/\/$/, '');

const normalizeBaseUrl = (value: string | undefined): string => {
  const trimmed = (value ?? '').trim();
  if (!trimmed || trimmed === '/') {
    return '';
  }

  return trimTrailingSlash(trimmed);
};

const joinBaseUrl = (baseUrl: string, path: string): string => {
  if (!baseUrl) {
    return path;
  }

  return `${baseUrl}${path.startsWith('/') ? path : `/${path}`}`;
};

const hasAbsoluteScheme = (value: string): boolean => /^[a-z][a-z0-9+.-]*:/i.test(value);

export const getApiBaseUrl = (): string => normalizeBaseUrl(import.meta.env.VITE_API_URL);

export const getTtsBaseUrl = (): string => normalizeBaseUrl(import.meta.env.VITE_TTS_URL);

export const buildApiUrl = (path: string): string => joinBaseUrl(getApiBaseUrl(), path);

export const buildTtsUrl = (path: string): string => joinBaseUrl(getTtsBaseUrl(), path);

export const buildChatWebSocketUrl = (conversationId: string): string => {
  const explicitApiBase = getApiBaseUrl();
  const path = `/api/v1/chat/ws/${conversationId}`;

  if (explicitApiBase) {
    const wsBase = explicitApiBase
      .replace(/^http:\/\//i, 'ws://')
      .replace(/^https:\/\//i, 'wss://');
    return joinBaseUrl(wsBase, path);
  }

  const scheme = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${scheme}//${window.location.host}${path}`;
};

export const resolveBrowserUrl = (pathOrUrl: string): string => {
  if (hasAbsoluteScheme(pathOrUrl)) {
    return pathOrUrl;
  }

  return new URL(pathOrUrl, window.location.origin).toString();
};
