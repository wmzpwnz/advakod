import React, { useState, useRef, useEffect } from 'react';
import { Play, Pause, Volume2, VolumeX, Download, Trash2 } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

const VoicePlayer = ({ 
  audioUrl, 
  duration, 
  onDelete, 
  showControls = true,
  autoPlay = false,
  className = ""
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const audioRef = useRef(null);
  const progressRef = useRef(null);
  const { isDark } = useTheme();

  // Форматирование времени
  const formatTime = (seconds) => {
    if (!seconds || isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Обработчики аудио
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleLoadStart = () => setIsLoading(true);
    const handleLoadedData = () => setIsLoading(false);
    const handleError = () => {
      setError('Ошибка загрузки аудио');
      setIsLoading(false);
    };
    const handleTimeUpdate = () => setCurrentTime(audio.currentTime);
    const handleEnded = () => setIsPlaying(false);
    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);

    audio.addEventListener('loadstart', handleLoadStart);
    audio.addEventListener('loadeddata', handleLoadedData);
    audio.addEventListener('error', handleError);
    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('play', handlePlay);
    audio.addEventListener('pause', handlePause);

    return () => {
      audio.removeEventListener('loadstart', handleLoadStart);
      audio.removeEventListener('loadeddata', handleLoadedData);
      audio.removeEventListener('error', handleError);
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('play', handlePlay);
      audio.removeEventListener('pause', handlePause);
    };
  }, [audioUrl]);

  // Автовоспроизведение
  useEffect(() => {
    if (autoPlay && audioRef.current && !isLoading) {
      audioRef.current.play();
    }
  }, [autoPlay, isLoading]);

  // Обновление громкости
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = isMuted ? 0 : volume;
    }
  }, [volume, isMuted]);

  // Воспроизведение/пауза
  const togglePlayback = () => {
    if (!audioRef.current) return;
    
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
  };

  // Перемотка по клику на прогресс-бар
  const handleProgressClick = (e) => {
    if (!audioRef.current || !progressRef.current) return;
    
    const rect = progressRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const width = rect.width;
    const percentage = clickX / width;
    const newTime = percentage * audioRef.current.duration;
    
    audioRef.current.currentTime = newTime;
    setCurrentTime(newTime);
  };

  // Скачивание аудио
  const downloadAudio = () => {
    if (!audioUrl) return;
    
    const link = document.createElement('a');
    link.href = audioUrl;
    link.download = `voice-message-${Date.now()}.webm`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Удаление аудио
  const handleDelete = () => {
    if (onDelete) {
      onDelete();
    }
  };

  if (error) {
    return (
      <div className={`p-3 bg-red-100 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg ${className}`}>
        <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
      </div>
    );
  }

  return (
    <div className={`flex items-center space-x-3 p-3 bg-gray-100 dark:bg-gray-700 rounded-lg ${className}`}>
      {/* Аудио элемент */}
      <audio
        ref={audioRef}
        src={audioUrl}
        preload="metadata"
      />

      {/* Кнопка воспроизведения */}
      <button
        onClick={togglePlayback}
        disabled={isLoading}
        className="flex-shrink-0 p-2 bg-primary-600 hover:bg-primary-500 disabled:bg-gray-400 text-white rounded-full transition-colors duration-200"
        title={isPlaying ? 'Пауза' : 'Воспроизвести'}
      >
        {isLoading ? (
          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
        ) : isPlaying ? (
          <Pause className="h-4 w-4" />
        ) : (
          <Play className="h-4 w-4" />
        )}
      </button>

      {/* Прогресс-бар */}
      <div className="flex-1 min-w-0">
        <div
          ref={progressRef}
          onClick={handleProgressClick}
          className="w-full bg-gray-300 dark:bg-gray-600 rounded-full h-2 cursor-pointer"
        >
          <div
            className="bg-primary-500 h-2 rounded-full transition-all duration-100"
            style={{
              width: audioRef.current?.duration 
                ? `${(currentTime / audioRef.current.duration) * 100}%` 
                : '0%'
            }}
          />
        </div>
        
        {/* Время */}
        <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
          <span>{formatTime(currentTime)}</span>
          <span>{formatTime(duration || audioRef.current?.duration)}</span>
        </div>
      </div>

      {/* Дополнительные элементы управления */}
      {showControls && (
        <div className="flex items-center space-x-2">
          {/* Громкость */}
          <button
            onClick={() => setIsMuted(!isMuted)}
            className="p-1.5 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
            title={isMuted ? 'Включить звук' : 'Выключить звук'}
          >
            {isMuted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
          </button>

          {/* Скачивание */}
          <button
            onClick={downloadAudio}
            className="p-1.5 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
            title="Скачать аудио"
          >
            <Download className="h-4 w-4" />
          </button>

          {/* Удаление */}
          {onDelete && (
            <button
              onClick={handleDelete}
              className="p-1.5 text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200 transition-colors"
              title="Удалить аудио"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          )}
        </div>
      )}

      {/* Индикатор голосового сообщения */}
      <div className="flex-shrink-0">
        <div className="flex items-center space-x-1">
          <div className="w-2 h-2 bg-primary-500 rounded-full"></div>
          <span className="text-xs text-gray-500 dark:text-gray-400">Голос</span>
        </div>
      </div>
    </div>
  );
};

export default VoicePlayer;
