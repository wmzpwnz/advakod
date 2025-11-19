import React, { useState, useRef, useEffect } from 'react';
import { Mic, MicOff, Play, Pause, Square, Trash2, Send, Volume2, VolumeX } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

const VoiceRecorder = ({ onSendVoiceMessage, onCancel, maxDuration = 300 }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioBlob, setAudioBlob] = useState(null);
  const [audioUrl, setAudioUrl] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [error, setError] = useState(null);
  
  const mediaRecorderRef = useRef(null);
  const audioRef = useRef(null);
  const streamRef = useRef(null);
  const timerRef = useRef(null);
  const chunksRef = useRef([]);
  
  const { isDark } = useTheme();

  // Очистка ресурсов при размонтировании
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);

  // Проверка поддержки браузера
  const checkBrowserSupport = () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setError('Ваш браузер не поддерживает запись аудио');
      return false;
    }
    return true;
  };

  // Начало записи
  const startRecording = async () => {
    if (!checkBrowserSupport()) return;

    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        } 
      });
      
      streamRef.current = stream;
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setAudioBlob(blob);
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);
        
        // Останавливаем все треки
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorder.start(100); // Записываем каждые 100мс
      setIsRecording(true);
      setRecordingTime(0);
      
      // Запускаем таймер
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => {
          if (prev >= maxDuration) {
            stopRecording();
            return maxDuration;
          }
          return prev + 1;
        });
      }, 1000);
      
    } catch (err) {
      console.error('Error starting recording:', err);
      setError('Не удалось начать запись. Проверьте разрешения микрофона.');
    }
  };

  // Пауза/возобновление записи
  const togglePause = () => {
    if (!mediaRecorderRef.current) return;
    
    if (isPaused) {
      mediaRecorderRef.current.resume();
      setIsPaused(false);
      // Возобновляем таймер
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => {
          if (prev >= maxDuration) {
            stopRecording();
            return maxDuration;
          }
          return prev + 1;
        });
      }, 1000);
    } else {
      mediaRecorderRef.current.pause();
      setIsPaused(true);
      clearInterval(timerRef.current);
    }
  };

  // Остановка записи
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsPaused(false);
      clearInterval(timerRef.current);
    }
  };

  // Воспроизведение записи
  const togglePlayback = () => {
    if (!audioRef.current || !audioUrl) return;
    
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  // Обработчики аудио
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleEnded = () => setIsPlaying(false);
    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);

    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('play', handlePlay);
    audio.addEventListener('pause', handlePause);

    return () => {
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('play', handlePlay);
      audio.removeEventListener('pause', handlePause);
    };
  }, [audioUrl]);

  // Отправка голосового сообщения
  const sendVoiceMessage = () => {
    if (audioBlob && onSendVoiceMessage) {
      onSendVoiceMessage(audioBlob, recordingTime);
      // Очищаем состояние
      setAudioBlob(null);
      setAudioUrl(null);
      setRecordingTime(0);
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    }
  };

  // Отмена записи
  const cancelRecording = () => {
    stopRecording();
    setAudioBlob(null);
    setAudioUrl(null);
    setRecordingTime(0);
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
    }
    if (onCancel) {
      onCancel();
    }
  };

  // Форматирование времени
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className={`p-4 ${isDark ? 'bg-gray-800' : 'bg-white'} rounded-lg border border-gray-200 dark:border-gray-700 shadow-lg`}>
      {error && (
        <div className="mb-4 p-3 bg-red-100 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
        </div>
      )}

      {/* Аудио элемент для воспроизведения */}
      {audioUrl && (
        <audio
          ref={audioRef}
          src={audioUrl}
          volume={isMuted ? 0 : volume}
          onVolumeChange={(e) => setVolume(e.target.volume)}
        />
      )}

      {/* Индикатор записи */}
      {isRecording && (
        <div className="mb-4 flex items-center justify-center space-x-2">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {isPaused ? 'Пауза' : 'Запись'}
            </span>
          </div>
          <div className="text-lg font-mono text-gray-900 dark:text-gray-100">
            {formatTime(recordingTime)}
          </div>
        </div>
      )}

      {/* Визуализация аудио */}
      {isRecording && (
        <div className="mb-4 flex items-center justify-center space-x-1">
          {[...Array(20)].map((_, i) => (
            <div
              key={i}
              className={`w-1 bg-primary-500 rounded-full animate-pulse`}
              style={{
                height: `${Math.random() * 20 + 10}px`,
                animationDelay: `${i * 0.1}s`
              }}
            />
          ))}
        </div>
      )}

      {/* Элементы управления */}
      <div className="flex items-center justify-center space-x-4">
        {!isRecording && !audioBlob && (
          <button
            onClick={startRecording}
            className="p-3 bg-red-500 hover:bg-red-600 text-white rounded-full transition-colors duration-200 shadow-lg"
            title="Начать запись"
          >
            <Mic className="h-6 w-6" />
          </button>
        )}

        {isRecording && (
          <>
            <button
              onClick={togglePause}
              className="p-3 bg-yellow-500 hover:bg-yellow-600 text-white rounded-full transition-colors duration-200"
              title={isPaused ? 'Возобновить запись' : 'Пауза'}
            >
              {isPaused ? <Play className="h-6 w-6" /> : <Pause className="h-6 w-6" />}
            </button>
            
            <button
              onClick={stopRecording}
              className="p-3 bg-gray-500 hover:bg-gray-600 text-white rounded-full transition-colors duration-200"
              title="Остановить запись"
            >
              <Square className="h-6 w-6" />
            </button>
          </>
        )}

        {audioBlob && (
          <>
            <button
              onClick={togglePlayback}
              className="p-3 bg-blue-500 hover:bg-blue-600 text-white rounded-full transition-colors duration-200"
              title={isPlaying ? 'Пауза' : 'Воспроизвести'}
            >
              {isPlaying ? <Pause className="h-6 w-6" /> : <Play className="h-6 w-6" />}
            </button>
            
            <button
              onClick={() => setIsMuted(!isMuted)}
              className="p-3 bg-gray-500 hover:bg-gray-600 text-white rounded-full transition-colors duration-200"
              title={isMuted ? 'Включить звук' : 'Выключить звук'}
            >
              {isMuted ? <VolumeX className="h-6 w-6" /> : <Volume2 className="h-6 w-6" />}
            </button>
            
            <button
              onClick={sendVoiceMessage}
              className="p-3 bg-green-500 hover:bg-green-600 text-white rounded-full transition-colors duration-200"
              title="Отправить голосовое сообщение"
            >
              <Send className="h-6 w-6" />
            </button>
            
            <button
              onClick={cancelRecording}
              className="p-3 bg-red-500 hover:bg-red-600 text-white rounded-full transition-colors duration-200"
              title="Удалить запись"
            >
              <Trash2 className="h-6 w-6" />
            </button>
          </>
        )}
      </div>

      {/* Информация о записи */}
      {audioBlob && (
        <div className="mt-4 text-center">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Длительность: {formatTime(recordingTime)} | 
            Размер: {(audioBlob.size / 1024).toFixed(1)} KB
          </p>
        </div>
      )}

      {/* Прогресс-бар для максимальной длительности */}
      {isRecording && (
        <div className="mt-4">
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className="bg-primary-500 h-2 rounded-full transition-all duration-1000"
              style={{ width: `${(recordingTime / maxDuration) * 100}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 text-center">
            Максимум: {formatTime(maxDuration)}
          </p>
        </div>
      )}
    </div>
  );
};

export default VoiceRecorder;
