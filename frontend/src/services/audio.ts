/** Audio service for TTS playback */

export class AudioService {
  private audioCache = new Map<string, HTMLAudioElement>();
  private currentAudio: HTMLAudioElement | null = null;

  // Get audio URL for cached file
  getAudioUrl(text: string, language: string, audioType: 'word' | 'sentence'): string {
    // Generate slug from text for cache URL
    const slug = this.generateSlug(text);
    return `${import.meta.env.VITE_TTS_URL}/api/audio/${language}/${audioType}/${slug}.wav`;
  }

  // Generate TTS audio via API
  async generateAudio(
    text: string,
    language: string,
    audioType: 'word' | 'sentence'
  ): Promise<string> {
    try {
      const cacheKey = `${language}-${audioType}-${text}`;

      // Check if already cached
      if (this.audioCache.has(cacheKey)) {
        return cacheKey;
      }

      // Generate audio via TTS service using correct endpoints
      const endpoint = audioType === 'word' ? 'word' : 'sentence';
      const id = this.generateSlug(text); // Use slug as ID
      const url = `${import.meta.env.VITE_TTS_URL}/api/tts/${endpoint}/${id}?text=${encodeURIComponent(text)}&lang=${language}`;

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`TTS generation failed: ${response.status} ${response.statusText}`);
      }

      // Get audio blob
      const blob = await response.blob();
      const audioUrl = URL.createObjectURL(blob);

      // Create audio element and cache it
      const audio = new Audio(audioUrl);
      this.audioCache.set(cacheKey, audio);

      return cacheKey;

    } catch (error) {
      console.error('Error generating TTS audio:', error);
      throw error;
    }
  }

  // Play audio file
  async playAudio(cacheKey: string): Promise<void> {
    try {
      // Stop any currently playing audio
      this.stopCurrentAudio();

      // Get cached audio element
      const audio = this.audioCache.get(cacheKey);
      if (!audio) {
        throw new Error(`Audio not found in cache: ${cacheKey}`);
      }

      this.currentAudio = audio;

      // Set up event listeners
      audio.addEventListener('ended', () => {
        this.currentAudio = null;
      });

      audio.addEventListener('error', (e) => {
        console.error('Audio playback error:', e);
        this.currentAudio = null;
      });

      // Play the audio
      await audio.play();

    } catch (error) {
      console.error('Error playing audio:', error);
      this.currentAudio = null;
      throw error;
    }
  }

  // Play word audio
  async playWordAudio(word: string, language = 'en'): Promise<void> {
    try {
      const cacheKey = await this.generateAudio(word, language, 'word');
      await this.playAudio(cacheKey);
    } catch (error) {
      console.error('Error playing word audio:', error);
      throw error;
    }
  }

  // Play sentence audio
  async playSentenceAudio(sentence: string, language = 'en'): Promise<void> {
    try {
      const cacheKey = await this.generateAudio(sentence, language, 'sentence');
      await this.playAudio(cacheKey);
    } catch (error) {
      console.error('Error playing sentence audio:', error);
      throw error;
    }
  }

  // Stop currently playing audio
  stopCurrentAudio(): void {
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio.currentTime = 0;
      this.currentAudio = null;
    }
  }

  // Generate slug from text (simplified)
  private generateSlug(text: string): string {
    // Simple hash for demo - in production, use proper crypto hash
    let hash = 0;
    for (let i = 0; i < text.length; i++) {
      const char = text.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash).toString(16).substring(0, 12);
  }

  // Preload audio from URL (non-blocking, for future playback)
  async preloadFromUrl(url: string): Promise<void> {
    try {
      // Check if already cached
      if (this.audioCache.has(url)) {
        return;
      }

      // Resolve absolute URL
      const resolved = new URL(url, window.location.origin).toString();

      // Create audio element
      const audio = new Audio(resolved);
      audio.preload = 'auto';

      // Cache immediately (will load in background)
      this.audioCache.set(url, audio);

      // Start loading (non-blocking)
      audio.load();

      // Log when ready
      audio.addEventListener('canplaythrough', () => {
        console.log(`✅ Audio preloaded and ready: ${url.substring(0, 50)}...`);
      }, { once: true });

    } catch (error) {
      console.error('Error preloading audio:', error);
      // Don't throw - preload failures are non-critical
    }
  }

  // Play audio directly from URL (preserves user gesture)
  async playFromUrl(url: string): Promise<void> {
    try {
      // Check if already cached by URL
      if (this.audioCache.has(url)) {
        const audio = this.audioCache.get(url)!;
        this.stopCurrentAudio();
        this.currentAudio = audio;

        // Rewind to beginning before replaying
        audio.currentTime = 0;

        await audio.play();
        return;
      }

      // Stop any currently playing audio
      this.stopCurrentAudio();

      // Resolve absolute URL to avoid relative path issues
      const resolved = new URL(url, window.location.origin).toString();

      // Create audio element directly from URL (preserves user gesture better than fetch)
      const audio = new Audio(resolved);
      this.currentAudio = audio;

      // Set up event listeners
      audio.addEventListener('ended', () => {
        this.currentAudio = null;
      });

      audio.addEventListener('error', (e: Event) => {
        const err = e.target as HTMLAudioElement;
        const mediaError = err.error;
        const errorName = mediaError ? 'MediaError' : 'UnknownError';
        const errorMessage = mediaError?.message || 'No message';
        console.error(`Audio playback error [${errorName}]: ${errorMessage}`);
        this.currentAudio = null;
      });

      audio.addEventListener('canplaythrough', () => {
        // Cache the audio element once it's loaded
        this.audioCache.set(url, audio);
      }, { once: true });

      // Play the audio directly (no fetch before play - better for user gesture)
      await audio.play();

      // Cache immediately for future use
      this.audioCache.set(url, audio);

    } catch (error) {
      const errorName = (error as Error).name || 'UnknownError';
      const errorMessage = (error as Error).message || 'No message';
      console.error(`Error playing audio from URL [${errorName}]: ${errorMessage}`);
      this.currentAudio = null;
      throw error;
    }
  }

  // Clear audio cache
  clearCache(): void {
    // Stop current audio
    this.stopCurrentAudio();

    // Clear cache
    this.audioCache.clear();
  }

  // Play audio from URL and wait for it to finish (or timeout)
  async playFromUrlAndWaitEnded(url: string, timeoutMs: number = 60000): Promise<void> {
    return new Promise((resolve) => {
      let timeoutHandle: number | null = null;
      let hasResolved = false;

      const cleanup = () => {
        if (timeoutHandle) {
          clearTimeout(timeoutHandle);
          timeoutHandle = null;
        }
        // Don't stop audio - let it finish naturally
      };

      const resolveOnce = () => {
        if (!hasResolved) {
          hasResolved = true;
          cleanup();
          resolve();
        }
      };

      // Set timeout fallback (only as failsafe for very long audio or stuck playback)
      timeoutHandle = window.setTimeout(() => {
        console.log(`Audio timeout after ${timeoutMs}ms (failsafe), advancing anyway`);
        resolveOnce();
      }, timeoutMs);

      // Play audio
      this.playFromUrl(url)
        .then(() => {
          // Audio started successfully, wait for it to end
          if (this.currentAudio) {
            this.currentAudio.addEventListener('ended', () => {
              console.log('Audio ended naturally');
              resolveOnce();
            }, { once: true });

            this.currentAudio.addEventListener('error', (e) => {
              console.error('Audio playback error:', e);
              // Still resolve - don't block the flow on audio error
              resolveOnce();
            }, { once: true });
          } else {
            // No audio element, resolve immediately
            resolveOnce();
          }
        })
        .catch((error) => {
          console.error('Failed to start audio:', error);
          // Still resolve - don't block the flow on audio failure
          resolveOnce();
        });
    });
  }
}

// Export singleton instance
export const audioService = new AudioService();
