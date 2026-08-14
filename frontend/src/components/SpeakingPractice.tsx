import { useEffect, useRef, useState } from 'react';


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

  const buttonClass = 'px-4 py-2 rounded text-sm font-semibold transition ' +
    (isRecording
      ? 'bg-red-700 text-white hover:bg-red-600'
      : 'bg-teal-800 text-teal-100 hover:bg-teal-700');

  if (!isExpanded) {
    return (
      <div className="bg-gray-800 rounded-lg p-5 border border-teal-900 flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-teal-300">Prática de fala privada</div>
          <div className="text-xs text-gray-400 mt-1">
            Abra depois de concluir o cloze; a frase completa revela a resposta.
          </div>
        </div>
        <button
          type="button"
          onClick={() => setIsExpanded(true)}
          className="px-4 py-2 rounded text-sm font-semibold transition bg-teal-900 text-teal-100 hover:bg-teal-800"
        >
          Revelar frase e praticar
        </button>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-5 border border-teal-900">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-teal-300">Prática de fala privada</div>
          <div className="text-xs text-gray-400 mt-1">
            Leia “{expectedText}”. O áudio fica somente neste navegador e não é enviado nem salvo.
          </div>
        </div>
        <button type="button" onClick={isRecording ? stopRecording : startRecording} className={buttonClass}>
          {isRecording ? 'Parar gravação' : 'Gravar leitura'}
        </button>
      </div>
      {recordingUrl && (
        <div className="mt-4">
          <audio controls src={recordingUrl} className="w-full" aria-label="Sua gravação de leitura" />
          <div className="text-xs text-gray-400 mt-2">
            Compare sua gravação com o áudio-modelo da frase e tente novamente.
          </div>
        </div>
      )}
      {error && <div className="mt-3 text-sm text-amber-300">{error}</div>}
    </div>
  );
};

export default SpeakingPractice;
