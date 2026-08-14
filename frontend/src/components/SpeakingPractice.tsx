import { useEffect, useRef, useState } from 'react';
import InfoTooltip from './InfoTooltip';


interface SpeakingPracticeProps {
  expectedText: string;
}


const SpeakingPractice = ({ expectedText }: SpeakingPracticeProps) => {
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const recordingUrlRef = useRef<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [recordingUrl, setRecordingUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const stopTracks = () => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  };

  const startRecording = async () => {
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      setError('Este navegador não oferece gravação de áudio compatível.');
      return;
    }
    setError(null);
    if (recordingUrlRef.current) URL.revokeObjectURL(recordingUrlRef.current);
    recordingUrlRef.current = null;
    setRecordingUrl(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      streamRef.current = stream;
      recorderRef.current = recorder;
      chunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        stopTracks();
        recorderRef.current = null;
        setIsRecording(false);
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || 'audio/webm' });
        if (!blob.size) {
          setError('Nenhum áudio foi capturado.');
          return;
        }
        const url = URL.createObjectURL(blob);
        recordingUrlRef.current = url;
        setRecordingUrl(url);
      };
      recorder.start();
      setIsRecording(true);
    } catch (permissionError) {
      console.error('Microphone permission failed:', permissionError);
      stopTracks();
      setError('Não foi possível acessar o microfone.');
    }
  };

  const stopRecording = () => {
    const recorder = recorderRef.current;
    if (recorder && recorder.state !== 'inactive') recorder.stop();
  };

  useEffect(() => () => {
    const recorder = recorderRef.current;
    if (recorder && recorder.state !== 'inactive') {
      recorder.ondataavailable = null;
      recorder.onstop = null;
      recorder.stop();
    }
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (recordingUrlRef.current) URL.revokeObjectURL(recordingUrlRef.current);
  }, []);

  const buttonClass = 'btn min-h-10 px-3 text-xs ' +
    (isRecording
      ? 'bg-red-600 text-white hover:bg-red-500'
      : 'border border-teal-400/20 bg-teal-400/10 text-teal-100 hover:bg-teal-400/20');

  if (!isExpanded) {
    return (
      <div className="surface-soft flex flex-wrap items-center gap-3 p-3">
        <div className="min-w-0 flex-1 text-sm font-semibold text-teal-200">Prática de fala privada</div>
        <InfoTooltip label="Sobre a prática de fala">Abra depois de concluir o cloze. A frase completa revela a resposta; o áudio permanece somente neste navegador.</InfoTooltip>
        <button
          type="button"
          onClick={() => setIsExpanded(true)}
          className="btn btn-secondary min-h-10 px-3 text-xs"
        >
          Praticar fala
        </button>
      </div>
    );
  }

  return (
    <div className="surface-soft p-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-teal-200">Leia em voz alta</div>
          <div className="mt-1 line-clamp-2 text-xs text-gray-400">“{expectedText}”</div>
        </div>
        <button type="button" onClick={isRecording ? stopRecording : startRecording} className={buttonClass}>
          {isRecording ? 'Parar gravação' : 'Gravar leitura'}
        </button>
      </div>
      {recordingUrl && (
        <div className="mt-4">
          <audio controls src={recordingUrl} className="w-full" aria-label="Sua gravação de leitura" />
          <div className="mt-2 text-xs text-gray-500">Compare com o áudio-modelo e tente novamente.</div>
        </div>
      )}
      {error && <div className="mt-3 text-sm text-amber-300">{error}</div>}
    </div>
  );
};

export default SpeakingPractice;
