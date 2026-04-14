/** Audio service for TTS playback */

import { buildTtsUrl, resolveBrowserUrl } from './transportUrls';

export class AudioService {
  private audioCache = new Map<string, HTMLAudioElement>();
  private blobUrlCache = new Map<string, string>();
  private currentAudio: HTMLAudioElement | null = null;

  getAudioUrl(text: string, language: string, audioType: 'word' | 'sentence'): string {
    const slug = this.generateSlug(text);
    return buildTtsUrl(`/api/audio/${language}/${audioType}/${slug}.wav`);
  }

  async generateAudio(
    text: string,
    language: string,
    audioType: 'word' | 'sentence'
  ): Promise<string> {
    const cacheKey = `${language}-${audioType}-${text}`;
    if (this.audioCache.has(cacheKey)) {
      return cacheKey;
    }

    const endpoint = audioType === 'word' ? 'word' : 'sentence';
    const id = this.generateSlug(text);
    const url = buildTtsUrl(`/api/tts/${endpoint}/${id}?text=${encodeURIComponent(text)}&lang=${language}`);

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`TTS generation failed: ${response.status} ${response.statusText}`);
    }

    const blob = await response.blob();
    const audioUrl = URL.createObjectURL(blob);
    this.revokeBlobUrl(cacheKey);

    const audio = new Audio(audioUrl);
    this.attachLifecycleListeners(audio);
    this.audioCache.set(cacheKey, audio);
    this.blobUrlCache.set(cacheKey, audioUrl);

    return cacheKey;
  }

  async playAudio(cacheKey: string): Promise<void> {
    this.stopCurrentAudio();

    const audio = this.audioCache.get(cacheKey);
    if (!audio) {
      throw new Error(`Audio not found in cache: ${cacheKey}`);
    }

    this.currentAudio = audio;
    audio.currentTime = 0;
    this.attachLifecycleListeners(audio);
    await audio.play();
  }

  async playWordAudio(word: string, language = 'en'): Promise<void> {
    const cacheKey = await this.generateAudio(word, language, 'word');
    await this.playAudio(cacheKey);
  }

  async playSentenceAudio(sentence: string, language = 'en'): Promise<void> {
    const cacheKey = await this.generateAudio(sentence, language, 'sentence');
    await this.playAudio(cacheKey);
  }

  stopCurrentAudio(): void {
    if (!this.currentAudio) {
      return;
    }

    this.currentAudio.pause();
    this.currentAudio.currentTime = 0;
    this.currentAudio = null;
  }

  private generateSlug(text: string): string {
    let hash = 0;
    for (let i = 0; i < text.length; i++) {
      const char = text.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return Math.abs(hash).toString(16).substring(0, 12);
  }

  private attachLifecycleListeners(audio: HTMLAudioElement): void {
    audio.onended = () => {
      if (this.currentAudio === audio) {
        this.currentAudio = null;
      }
    };

    audio.onerror = (event) => {
      console.error('Audio playback error:', event);
      if (this.currentAudio === audio) {
        this.currentAudio = null;
      }
    };
  }

  private revokeBlobUrl(cacheKey: string): void {
    const existingBlobUrl = this.blobUrlCache.get(cacheKey);
    if (existingBlobUrl) {
      URL.revokeObjectURL(existingBlobUrl);
      this.blobUrlCache.delete(cacheKey);
    }
  }

  async preloadFromUrl(url: string): Promise<void> {
    try {
      if (this.audioCache.has(url)) {
        return;
      }

      const resolved = resolveBrowserUrl(url);
      const audio = new Audio(resolved);
      audio.preload = 'auto';
      this.attachLifecycleListeners(audio);
      this.audioCache.set(url, audio);
      audio.load();
      audio.addEventListener('canplaythrough', () => {
        console.log(`✅ Audio preloaded and ready: ${url.substring(0, 50)}...`);
      }, { once: true });
    } catch (error) {
      console.error('Error preloading audio:', error);
    }
  }

  async playFromUrl(url: string): Promise<void> {
    try {
      if (this.audioCache.has(url)) {
        const cachedAudio = this.audioCache.get(url)!;
        this.stopCurrentAudio();
        this.currentAudio = cachedAudio;
        cachedAudio.currentTime = 0;
        this.attachLifecycleListeners(cachedAudio);
        await cachedAudio.play();
        return;
      }

      this.stopCurrentAudio();

      const resolved = resolveBrowserUrl(url);
      const audio = new Audio(resolved);
      this.attachLifecycleListeners(audio);
      this.currentAudio = audio;

      audio.addEventListener('canplaythrough', () => {
        this.audioCache.set(url, audio);
      }, { once: true });

      await audio.play();
      this.audioCache.set(url, audio);
    } catch (error) {
      const errorName = (error as Error).name || 'UnknownError';
      const errorMessage = (error as Error).message || 'No message';
      console.error(`Error playing audio from URL [${errorName}]: ${errorMessage}`);
      this.currentAudio = null;
      throw error;
    }
  }

  clearCache(): void {
    this.stopCurrentAudio();
    for (const cacheKey of this.blobUrlCache.keys()) {
      this.revokeBlobUrl(cacheKey);
    }
    this.audioCache.clear();
  }

  async playFromUrlAndWaitEnded(url: string, timeoutMs: number = 60000): Promise<void> {
    return new Promise((resolve) => {
      let timeoutHandle: number | null = null;
      let hasResolved = false;

      const cleanup = () => {
        if (timeoutHandle) {
          clearTimeout(timeoutHandle);
          timeoutHandle = null;
        }
      };

      const resolveOnce = () => {
        if (!hasResolved) {
          hasResolved = true;
          cleanup();
          resolve();
        }
      };

      timeoutHandle = window.setTimeout(() => {
        console.log(`Audio timeout after ${timeoutMs}ms (failsafe), advancing anyway`);
        resolveOnce();
      }, timeoutMs);

      this.playFromUrl(url)
        .then(() => {
          if (this.currentAudio) {
            this.currentAudio.addEventListener('ended', () => {
              console.log('Audio ended naturally');
              resolveOnce();
            }, { once: true });

            this.currentAudio.addEventListener('error', (e) => {
              console.error('Audio playback error:', e);
              resolveOnce();
            }, { once: true });
          } else {
            resolveOnce();
          }
        })
        .catch((error) => {
          console.error('Failed to start audio:', error);
          resolveOnce();
        });
    });
  }
}

export const audioService = new AudioService();
