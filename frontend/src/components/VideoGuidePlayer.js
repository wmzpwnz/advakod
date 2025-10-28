import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Play, 
  Pause, 
  Volume2, 
  VolumeX, 
  Maximize, 
  Minimize,
  SkipBack,
  SkipForward,
  RotateCcw,
  Settings,
  Download,
  Share2,
  BookOpen,
  X,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';

const VideoGuidePlayer = ({ 
  videoGuide, 
  isOpen, 
  onClose,
  autoPlay = false 
}) => {
  const videoRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showControls, setShowControls] = useState(true);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [showSettings, setShowSettings] = useState(false);
  const [currentChapter, setCurrentChapter] = useState(0);

  // Auto-hide controls
  useEffect(() => {
    let timeout;
    if (showControls && isPlaying) {
      timeout = setTimeout(() => setShowControls(false), 3000);
    }
    return () => clearTimeout(timeout);
  }, [showControls, isPlaying]);

  // Video event handlers
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleTimeUpdate = () => setCurrentTime(video.currentTime);
    const handleDurationChange = () => setDuration(video.duration);
    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);
    const handleEnded = () => {
      setIsPlaying(false);
      setCurrentTime(0);
    };

    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('durationchange', handleDurationChange);
    video.addEventListener('play', handlePlay);
    video.addEventListener('pause', handlePause);
    video.addEventListener('ended', handleEnded);

    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('durationchange', handleDurationChange);
      video.removeEventListener('play', handlePlay);
      video.removeEventListener('pause', handlePause);
      video.removeEventListener('ended', handleEnded);
    };
  }, []);

  // Auto-play
  useEffect(() => {
    if (autoPlay && videoRef.current) {
      videoRef.current.play();
    }
  }, [autoPlay]);

  // Chapter navigation
  useEffect(() => {
    if (videoGuide?.chapters && videoRef.current) {
      const chapter = videoGuide.chapters[currentChapter];
      if (chapter && Math.abs(currentTime - chapter.startTime) > 1) {
        videoRef.current.currentTime = chapter.startTime;
      }
    }
  }, [currentChapter, videoGuide?.chapters]);

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
    }
  };

  const handleSeek = (time) => {
    if (videoRef.current) {
      videoRef.current.currentTime = time;
      setCurrentTime(time);
    }
  };

  const handleVolumeChange = (newVolume) => {
    if (videoRef.current) {
      videoRef.current.volume = newVolume;
      setVolume(newVolume);
      setIsMuted(newVolume === 0);
    }
  };

  const toggleMute = () => {
    if (videoRef.current) {
      const newMuted = !isMuted;
      videoRef.current.muted = newMuted;
      setIsMuted(newMuted);
    }
  };

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      videoRef.current?.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  const changePlaybackRate = (rate) => {
    if (videoRef.current) {
      videoRef.current.playbackRate = rate;
      setPlaybackRate(rate);
      setShowSettings(false);
    }
  };

  const skipTime = (seconds) => {
    if (videoRef.current) {
      const newTime = Math.max(0, Math.min(duration, currentTime + seconds));
      handleSeek(newTime);
    }
  };

  const goToChapter = (chapterIndex) => {
    if (videoGuide?.chapters && videoRef.current) {
      const chapter = videoGuide.chapters[chapterIndex];
      if (chapter) {
        setCurrentChapter(chapterIndex);
        handleSeek(chapter.startTime);
      }
    }
  };

  const formatTime = (time) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const downloadVideo = () => {
    if (videoGuide?.downloadUrl) {
      const link = document.createElement('a');
      link.href = videoGuide.downloadUrl;
      link.download = `${videoGuide.title}.mp4`;
      link.click();
    }
  };

  const shareVideo = async () => {
    if (navigator.share && videoGuide) {
      try {
        await navigator.share({
          title: videoGuide.title,
          text: videoGuide.description,
          url: window.location.href
        });
      } catch (err) {
        console.log('Error sharing:', err);
      }
    }
  };

  if (!isOpen || !videoGuide) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-90 z-50 flex items-center justify-center">
      <div className="w-full h-full max-w-6xl max-h-[90vh] relative">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-10 p-2 bg-black bg-opacity-50 text-white rounded-full hover:bg-opacity-70 transition-colors"
        >
          <X className="h-6 w-6" />
        </button>

        {/* Video Container */}
        <div 
          className="relative w-full h-full bg-black rounded-lg overflow-hidden"
          onMouseMove={() => setShowControls(true)}
          onMouseLeave={() => isPlaying && setShowControls(false)}
        >
          {/* Video Element */}
          <video
            ref={videoRef}
            className="w-full h-full object-contain"
            src={videoGuide.videoUrl}
            poster={videoGuide.thumbnail}
            onClick={togglePlay}
          />

          {/* Loading Overlay */}
          {!duration && (
            <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white"></div>
            </div>
          )}

          {/* Play Button Overlay */}
          {!isPlaying && duration > 0 && (
            <motion.button
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              onClick={togglePlay}
              className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-30 hover:bg-opacity-40 transition-colors"
            >
              <div className="p-4 bg-white bg-opacity-20 rounded-full">
                <Play className="h-12 w-12 text-white ml-1" />
              </div>
            </motion.button>
          )}

          {/* Controls */}
          <AnimatePresence>
            {showControls && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent p-4"
              >
                {/* Progress Bar */}
                <div className="mb-4">
                  <div className="relative">
                    <div className="w-full h-1 bg-white bg-opacity-30 rounded-full">
                      <div
                        className="h-1 bg-blue-500 rounded-full transition-all duration-100"
                        style={{ width: `${(currentTime / duration) * 100}%` }}
                      />
                    </div>
                    <input
                      type="range"
                      min="0"
                      max={duration || 0}
                      value={currentTime}
                      onChange={(e) => handleSeek(parseFloat(e.target.value))}
                      className="absolute inset-0 w-full h-1 opacity-0 cursor-pointer"
                    />
                  </div>
                  
                  {/* Chapter Markers */}
                  {videoGuide.chapters && (
                    <div className="relative mt-1">
                      {videoGuide.chapters.map((chapter, index) => (
                        <button
                          key={index}
                          onClick={() => goToChapter(index)}
                          className="absolute w-2 h-2 bg-yellow-400 rounded-full transform -translate-x-1/2 hover:scale-125 transition-transform"
                          style={{ left: `${(chapter.startTime / duration) * 100}%` }}
                          title={chapter.title}
                        />
                      ))}
                    </div>
                  )}
                </div>

                {/* Control Buttons */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {/* Play/Pause */}
                    <button
                      onClick={togglePlay}
                      className="p-2 text-white hover:bg-white hover:bg-opacity-20 rounded-full transition-colors"
                    >
                      {isPlaying ? (
                        <Pause className="h-6 w-6" />
                      ) : (
                        <Play className="h-6 w-6" />
                      )}
                    </button>

                    {/* Skip Buttons */}
                    <button
                      onClick={() => skipTime(-10)}
                      className="p-2 text-white hover:bg-white hover:bg-opacity-20 rounded-full transition-colors"
                    >
                      <SkipBack className="h-5 w-5" />
                    </button>
                    <button
                      onClick={() => skipTime(10)}
                      className="p-2 text-white hover:bg-white hover:bg-opacity-20 rounded-full transition-colors"
                    >
                      <SkipForward className="h-5 w-5" />
                    </button>

                    {/* Volume */}
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={toggleMute}
                        className="p-2 text-white hover:bg-white hover:bg-opacity-20 rounded-full transition-colors"
                      >
                        {isMuted ? (
                          <VolumeX className="h-5 w-5" />
                        ) : (
                          <Volume2 className="h-5 w-5" />
                        )}
                      </button>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={isMuted ? 0 : volume}
                        onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
                        className="w-20 h-1 bg-white bg-opacity-30 rounded-full appearance-none slider"
                      />
                    </div>

                    {/* Time */}
                    <span className="text-white text-sm">
                      {formatTime(currentTime)} / {formatTime(duration)}
                    </span>
                  </div>

                  <div className="flex items-center space-x-2">
                    {/* Chapter Navigation */}
                    {videoGuide.chapters && videoGuide.chapters.length > 1 && (
                      <div className="flex items-center space-x-1">
                        <button
                          onClick={() => goToChapter(Math.max(0, currentChapter - 1))}
                          disabled={currentChapter === 0}
                          className="p-2 text-white hover:bg-white hover:bg-opacity-20 rounded-full transition-colors disabled:opacity-50"
                        >
                          <ChevronLeft className="h-5 w-5" />
                        </button>
                        <span className="text-white text-sm px-2">
                          {currentChapter + 1}/{videoGuide.chapters.length}
                        </span>
                        <button
                          onClick={() => goToChapter(Math.min(videoGuide.chapters.length - 1, currentChapter + 1))}
                          disabled={currentChapter === videoGuide.chapters.length - 1}
                          className="p-2 text-white hover:bg-white hover:bg-opacity-20 rounded-full transition-colors disabled:opacity-50"
                        >
                          <ChevronRight className="h-5 w-5" />
                        </button>
                      </div>
                    )}

                    {/* Settings */}
                    <div className="relative">
                      <button
                        onClick={() => setShowSettings(!showSettings)}
                        className="p-2 text-white hover:bg-white hover:bg-opacity-20 rounded-full transition-colors"
                      >
                        <Settings className="h-5 w-5" />
                      </button>
                      
                      {showSettings && (
                        <div className="absolute bottom-full right-0 mb-2 bg-black bg-opacity-80 rounded-lg p-2 min-w-[120px]">
                          <div className="text-white text-sm mb-2">Скорость:</div>
                          {[0.5, 0.75, 1, 1.25, 1.5, 2].map((rate) => (
                            <button
                              key={rate}
                              onClick={() => changePlaybackRate(rate)}
                              className={`block w-full text-left px-2 py-1 text-sm rounded hover:bg-white hover:bg-opacity-20 transition-colors ${
                                playbackRate === rate ? 'text-blue-400' : 'text-white'
                              }`}
                            >
                              {rate}x
                            </button>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Download */}
                    {videoGuide.downloadUrl && (
                      <button
                        onClick={downloadVideo}
                        className="p-2 text-white hover:bg-white hover:bg-opacity-20 rounded-full transition-colors"
                      >
                        <Download className="h-5 w-5" />
                      </button>
                    )}

                    {/* Share */}
                    <button
                      onClick={shareVideo}
                      className="p-2 text-white hover:bg-white hover:bg-opacity-20 rounded-full transition-colors"
                    >
                      <Share2 className="h-5 w-5" />
                    </button>

                    {/* Fullscreen */}
                    <button
                      onClick={toggleFullscreen}
                      className="p-2 text-white hover:bg-white hover:bg-opacity-20 rounded-full transition-colors"
                    >
                      {isFullscreen ? (
                        <Minimize className="h-5 w-5" />
                      ) : (
                        <Maximize className="h-5 w-5" />
                      )}
                    </button>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Video Info Panel */}
        <div className="absolute top-4 left-4 bg-black bg-opacity-50 text-white p-4 rounded-lg max-w-md">
          <h3 className="text-lg font-semibold mb-2">{videoGuide.title}</h3>
          <p className="text-sm text-gray-300 mb-2">{videoGuide.description}</p>
          
          {videoGuide.chapters && (
            <div className="text-sm">
              <div className="font-medium mb-1">Текущая глава:</div>
              <div className="text-gray-300">
                {videoGuide.chapters[currentChapter]?.title}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Custom Styles */}
      <style jsx>{`
        .slider::-webkit-slider-thumb {
          appearance: none;
          width: 12px;
          height: 12px;
          border-radius: 50%;
          background: #3b82f6;
          cursor: pointer;
        }
        
        .slider::-moz-range-thumb {
          width: 12px;
          height: 12px;
          border-radius: 50%;
          background: #3b82f6;
          cursor: pointer;
          border: none;
        }
      `}</style>
    </div>
  );
};

export default VideoGuidePlayer;