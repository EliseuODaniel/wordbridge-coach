import axios from 'axios';

export type JsonObject = Record<string, unknown>;

export interface ApiErrorDetailObject {
  error?: string;
  message?: string;
  [key: string]: unknown;
}

export interface ApiErrorResponse {
  detail?: string | ApiErrorDetailObject;
  message?: string;
  error?: string;
}

const getApiErrorDetailMessage = (detail: string | ApiErrorDetailObject | undefined): string | null => {
  if (typeof detail === 'string' && detail.trim()) {
    return detail;
  }

  if (detail && typeof detail === 'object') {
    if (typeof detail.message === 'string' && detail.message.trim()) {
      return detail.message;
    }

    if (typeof detail.error === 'string' && detail.error.trim()) {
      return detail.error;
    }

    return JSON.stringify(detail);
  }

  return null;
};

export const getApiErrorStatus = (error: unknown): number | undefined => {
  if (!axios.isAxiosError<ApiErrorResponse>(error)) {
    return undefined;
  }

  return error.response?.status;
};

export const getApiErrorCode = (error: unknown): string | undefined => {
  if (!axios.isAxiosError(error)) {
    return undefined;
  }

  return error.code;
};

export const getApiErrorMessage = (
  error: unknown,
  fallback: string = 'Request failed'
): string => {
  if (axios.isAxiosError<ApiErrorResponse>(error)) {
    const detailMessage = getApiErrorDetailMessage(error.response?.data?.detail);
    if (detailMessage) {
      return detailMessage;
    }

    if (typeof error.response?.data?.message === 'string' && error.response.data.message.trim()) {
      return error.response.data.message;
    }

    if (typeof error.response?.data?.error === 'string' && error.response.data.error.trim()) {
      return error.response.data.error;
    }

    if (error.message) {
      return error.message;
    }
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  return fallback;
};

export const isRetryableApiError = (error: unknown): boolean => {
  const code = getApiErrorCode(error);
  const status = getApiErrorStatus(error);

  return code === 'NETWORK_ERROR' || code === 'ECONNABORTED' || (typeof status === 'number' && status >= 500);
};
