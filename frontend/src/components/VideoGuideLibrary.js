import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Play,
    Clock,
    BookOpen,
    Search,
    Filter,
    Grid,
    List,
    Star,
    Download,
    Share2,
    Eye,
    Calendar,
    Tag,
    Users,
    FileText,
    Shield,
    MessageSquare,
    TrendingUp,
    Target,
    Bell,
    BarChart3,
    Database,
    Settings,
    X
} from 'lucide-react';
import VideoGuidePlayer from './VideoGuidePlayer';

const VideoGuideLibrary = ({ isOpen, onClose }) => {
    const [selectedVideo, setSelectedVideo] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('all');
    const [viewMode, setViewMode] = useState('grid');
    const [sortBy, setSortBy] = useState('newest');
    const [watchedVideos, setWatchedVideos] = useState([]);

    // Load watched videos from localStorage
    useEffect(() => {
        const watched = JSON.parse(localStorage.getItem('watchedVideoGuides') || '[]');
        setWatchedVideos(watched);
    }, []);

    // Video guide data
    const videoGuides = [
        {
            id: 'admin-overview',
            title: 'Обзор админ-панели АДВАКОД',
            description: 'Полное введение в интегрированную админ-панель, её возможности и основные функции.',
            category: 'overview',
            duration: 480, // 8 minutes
            thumbnail: '/api/video-guides/thumbnails/admin-overview.jpg',
            videoUrl: '/api/video-guides/admin-overview.mp4',
            downloadUrl: '/api/video-guides/downloads/admin-overview.mp4',
            views: 1250,
            rating: 4.8,
            createdAt: '2024-10-20',
            tags: ['введение', 'обзор', 'навигация'],
            chapters: [
                { title: 'Введение', startTime: 0 },
                { title: 'Навигация', startTime: 60 },
                { title: 'Дашборд', startTime: 180 },
                { title: 'Модули', startTime: 300 },
                { title: 'Настройки', startTime: 420 }
            ]
        },
        {
            id: 'user-management',
            title: 'Управление пользователями',
            description: 'Детальное руководство по работе с модулем управления пользователями.',
            category: 'users',
            duration: 600, // 10 minutes
            thumbnail: '/api/video-guides/thumbnails/user-management.jpg',
            videoUrl: '/api/video-guides/user-management.mp4',
            downloadUrl: '/api/video-guides/downloads/user-management.mp4',
            views: 890,
            rating: 4.7,
            createdAt: '2024-10-18',
            tags: ['пользователи', 'управление', 'фильтры'],
            chapters: [
                { title: 'Обзор модуля', startTime: 0 },
                { title: 'Поиск и фильтрация', startTime: 120 },
                { title: 'Редактирование профилей', startTime: 240 },
                { title: 'Массовые операции', startTime: 360 },
                { title: 'Экспорт данных', startTime: 480 }
            ]
        },
        {
            id: 'moderation-system',
            title: 'Система модерации',
            description: 'Как эффективно работать с системой модерации и геймификацией.',
            category: 'moderation',
            duration: 720, // 12 minutes
            thumbnail: '/api/video-guides/thumbnails/moderation-system.jpg',
            videoUrl: '/api/video-guides/moderation-system.mp4',
            downloadUrl: '/api/video-guides/downloads/moderation-system.mp4',
            views: 650,
            rating: 4.9,
            createdAt: '2024-10-15',
            tags: ['модерация', 'оценки', 'геймификация'],
            chapters: [
                { title: 'Очередь модерации', startTime: 0 },
                { title: 'Система оценок', startTime: 180 },
                { title: 'Геймификация', startTime: 360 },
                { title: 'Аналитика', startTime: 540 },
                { title: 'Лучшие практики', startTime: 640 }
            ]
        },
        {
            id: 'marketing-tools',
            title: 'Маркетинговые инструменты',
            description: 'Полное руководство по использованию маркетинговых инструментов.',
            category: 'marketing',
            duration: 900, // 15 minutes
            thumbnail: '/api/video-guides/thumbnails/marketing-tools.jpg',
            videoUrl: '/api/video-guides/marketing-tools.mp4',
            downloadUrl: '/api/video-guides/downloads/marketing-tools.mp4',
            views: 420,
            rating: 4.6,
            createdAt: '2024-10-12',
            tags: ['маркетинг', 'воронка', 'промокоды', 'аналитика'],
            chapters: [
                { title: 'Дашборд маркетинга', startTime: 0 },
                { title: 'Воронка продаж', startTime: 200 },
                { title: 'Промокоды', startTime: 400 },
                { title: 'Аналитика трафика', startTime: 600 },
                { title: 'A/B тестирование', startTime: 750 }
            ]
        },
        {
            id: 'project-management',
            title: 'Управление проектом',
            description: 'Как использовать инструменты управления проектом для координации команды.',
            category: 'project',
            duration: 780, // 13 minutes
            thumbnail: '/api/video-guides/thumbnails/project-management.jpg',
            videoUrl: '/api/video-guides/project-management.mp4',
            downloadUrl: '/api/video-guides/downloads/project-management.mp4',
            views: 320,
            rating: 4.8,
            createdAt: '2024-10-10',
            tags: ['проект', 'задачи', 'календарь', 'ресурсы'],
            chapters: [
                { title: 'Дашборд проекта', startTime: 0 },
                { title: 'Управление задачами', startTime: 180 },
                { title: 'Календарь', startTime: 360 },
                { title: 'Ресурсы команды', startTime: 540 },
                { title: 'Отчеты', startTime: 680 }
            ]
        },
        {
            id: 'advanced-analytics',
            title: 'Продвинутая аналитика',
            description: 'Создание дашбордов, когортный анализ и ML прогнозы.',
            category: 'analytics',
            duration: 1080, // 18 minutes
            thumbnail: '/api/video-guides/thumbnails/advanced-analytics.jpg',
            videoUrl: '/api/video-guides/advanced-analytics.mp4',
            downloadUrl: '/api/video-guides/downloads/advanced-analytics.mp4',
            views: 280,
            rating: 4.9,
            createdAt: '2024-10-08',
            tags: ['аналитика', 'дашборды', 'когорты', 'ML'],
            chapters: [
                { title: 'Конструктор дашбордов', startTime: 0 },
                { title: 'Виджеты и источники данных', startTime: 240 },
                { title: 'Когортный анализ', startTime: 480 },
                { title: 'Пользовательские метрики', startTime: 720 },
                { title: 'ML прогнозы', startTime: 900 }
            ]
        },
        {
            id: 'notification-system',
            title: 'Система уведомлений',
            description: 'Настройка и использование системы уведомлений и алертов.',
            category: 'notifications',
            duration: 420, // 7 minutes
            thumbnail: '/api/video-guides/thumbnails/notification-system.jpg',
            videoUrl: '/api/video-guides/notification-system.mp4',
            downloadUrl: '/api/video-guides/downloads/notification-system.mp4',
            views: 510,
            rating: 4.7,
            createdAt: '2024-10-05',
            tags: ['уведомления', 'алерты', 'настройки'],
            chapters: [
                { title: 'Центр уведомлений', startTime: 0 },
                { title: 'Push уведомления', startTime: 120 },
                { title: 'Интеграции', startTime: 240 },
                { title: 'Настройки фильтрации', startTime: 340 }
            ]
        },
        {
            id: 'backup-system',
            title: 'Система резервного копирования',
            description: 'Управление резервными копиями и восстановление данных.',
            category: 'backup',
            duration: 540, // 9 minutes
            thumbnail: '/api/video-guides/thumbnails/backup-system.jpg',
            videoUrl: '/api/video-guides/backup-system.mp4',
            downloadUrl: '/api/video-guides/downloads/backup-system.mp4',
            views: 180,
            rating: 4.8,
            createdAt: '2024-10-03',
            tags: ['бэкапы', 'восстановление', 'безопасность'],
            chapters: [
                { title: 'Создание бэкапов', startTime: 0 },
                { title: 'Автоматическое копирование', startTime: 150 },
                { title: 'Восстановление данных', startTime: 300 },
                { title: 'Мониторинг целостности', startTime: 450 }
            ]
        }
    ];

    const categories = [
        { id: 'all', name: 'Все видео', icon: BookOpen },
        { id: 'overview', name: 'Обзор', icon: BookOpen },
        { id: 'users', name: 'Пользователи', icon: Users },
        { id: 'documents', name: 'Документы', icon: FileText },
        { id: 'roles', name: 'Роли', icon: Shield },
        { id: 'moderation', name: 'Модерация', icon: MessageSquare },
        { id: 'marketing', name: 'Маркетинг', icon: TrendingUp },
        { id: 'project', name: 'Проект', icon: Target },
        { id: 'notifications', name: 'Уведомления', icon: Bell },
        { id: 'analytics', name: 'Аналитика', icon: BarChart3 },
        { id: 'backup', name: 'Бэкапы', icon: Database },
        { id: 'system', name: 'Система', icon: Settings }
    ];

    // Filter and sort videos
    const filteredVideos = videoGuides
        .filter(video => {
            const matchesSearch = video.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                video.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
                video.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
            const matchesCategory = selectedCategory === 'all' || video.category === selectedCategory;
            return matchesSearch && matchesCategory;
        })
        .sort((a, b) => {
            switch (sortBy) {
                case 'newest':
                    return new Date(b.createdAt) - new Date(a.createdAt);
                case 'oldest':
                    return new Date(a.createdAt) - new Date(b.createdAt);
                case 'popular':
                    return b.views - a.views;
                case 'rating':
                    return b.rating - a.rating;
                case 'duration':
                    return a.duration - b.duration;
                default:
                    return 0;
            }
        });

    const formatDuration = (seconds) => {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    };

    const markAsWatched = (videoId) => {
        const newWatched = [...watchedVideos, videoId];
        setWatchedVideos(newWatched);
        localStorage.setItem('watchedVideoGuides', JSON.stringify(newWatched));
    };

    const isWatched = (videoId) => {
        return watchedVideos.includes(videoId);
    };

    const playVideo = (video) => {
        setSelectedVideo(video);
        if (!isWatched(video.id)) {
            markAsWatched(video.id);
        }
    };

    if (!isOpen) return null;

    return (
        <>
            {/* Main Library Modal */}
            <div className="fixed inset-0 bg-black bg-opacity-50 z-40 flex items-center justify-center p-4">
                <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl w-full max-w-6xl h-[90vh] flex flex-col"
                >
                    {/* Header */}
                    <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
                        <div>
                            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                                Видео-гайды по админ-панели
                            </h2>
                            <p className="text-gray-600 dark:text-gray-400 mt-1">
                                Изучите все возможности системы с помощью подробных видео-инструкций
                            </p>
                        </div>
                        <button
                            onClick={onClose}
                            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                        >
                            <X className="h-6 w-6" />
                        </button>
                    </div>

                    {/* Filters and Search */}
                    <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
                            {/* Search */}
                            <div className="relative flex-1 max-w-md">
                                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                                <input
                                    type="text"
                                    placeholder="Поиск видео..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>

                            <div className="flex items-center space-x-4">
                                {/* Category Filter */}
                                <select
                                    value={selectedCategory}
                                    onChange={(e) => setSelectedCategory(e.target.value)}
                                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                >
                                    {categories.map(category => (
                                        <option key={category.id} value={category.id}>
                                            {category.name}
                                        </option>
                                    ))}
                                </select>

                                {/* Sort */}
                                <select
                                    value={sortBy}
                                    onChange={(e) => setSortBy(e.target.value)}
                                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                >
                                    <option value="newest">Новые</option>
                                    <option value="oldest">Старые</option>
                                    <option value="popular">Популярные</option>
                                    <option value="rating">По рейтингу</option>
                                    <option value="duration">По длительности</option>
                                </select>

                                {/* View Mode */}
                                <div className="flex border border-gray-300 dark:border-gray-600 rounded-lg">
                                    <button
                                        onClick={() => setViewMode('grid')}
                                        className={`p-2 ${viewMode === 'grid' ? 'bg-blue-500 text-white' : 'text-gray-600 dark:text-gray-400'}`}
                                    >
                                        <Grid className="h-4 w-4" />
                                    </button>
                                    <button
                                        onClick={() => setViewMode('list')}
                                        className={`p-2 ${viewMode === 'list' ? 'bg-blue-500 text-white' : 'text-gray-600 dark:text-gray-400'}`}
                                    >
                                        <List className="h-4 w-4" />
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Video Grid/List */}
                    <div className="flex-1 overflow-y-auto p-6">
                        {filteredVideos.length === 0 ? (
                            <div className="text-center py-12">
                                <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                                    Видео не найдены
                                </h3>
                                <p className="text-gray-600 dark:text-gray-400">
                                    Попробуйте изменить параметры поиска или фильтры
                                </p>
                            </div>
                        ) : (
                            <div className={viewMode === 'grid'
                                ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'
                                : 'space-y-4'
                            }>
                                {filteredVideos.map((video) => (
                                    <motion.div
                                        key={video.id}
                                        className={`bg-gray-50 dark:bg-gray-700 rounded-lg overflow-hidden hover:shadow-lg transition-shadow cursor-pointer ${viewMode === 'list' ? 'flex' : ''
                                            }`}
                                        onClick={() => playVideo(video)}
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.98 }}
                                    >
                                        {/* Thumbnail */}
                                        <div className={`relative ${viewMode === 'list' ? 'w-48 flex-shrink-0' : 'aspect-video'}`}>
                                            <img
                                                src={video.thumbnail}
                                                alt={video.title}
                                                className="w-full h-full object-cover"
                                                onError={(e) => {
                                                    e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIwIiBoZWlnaHQ9IjE4MCIgdmlld0JveD0iMCAwIDMyMCAxODAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIzMjAiIGhlaWdodD0iMTgwIiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik0xNDQgNzJMMTc2IDkwTDE0NCAxMDhWNzJaIiBmaWxsPSIjOUI5QkEwIi8+Cjwvc3ZnPgo=';
                                                }}
                                            />

                                            {/* Play Overlay */}
                                            <div className="absolute inset-0 bg-black bg-opacity-30 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity">
                                                <div className="p-3 bg-white bg-opacity-20 rounded-full">
                                                    <Play className="h-8 w-8 text-white ml-1" />
                                                </div>
                                            </div>

                                            {/* Duration */}
                                            <div className="absolute bottom-2 right-2 bg-black bg-opacity-70 text-white text-xs px-2 py-1 rounded">
                                                {formatDuration(video.duration)}
                                            </div>

                                            {/* Watched Indicator */}
                                            {isWatched(video.id) && (
                                                <div className="absolute top-2 left-2 bg-green-500 text-white text-xs px-2 py-1 rounded">
                                                    Просмотрено
                                                </div>
                                            )}
                                        </div>

                                        {/* Content */}
                                        <div className="p-4 flex-1">
                                            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2 line-clamp-2">
                                                {video.title}
                                            </h3>

                                            <p className="text-gray-600 dark:text-gray-400 text-sm mb-3 line-clamp-2">
                                                {video.description}
                                            </p>

                                            {/* Meta Info */}
                                            <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
                                                <div className="flex items-center space-x-4">
                                                    <div className="flex items-center space-x-1">
                                                        <Eye className="h-4 w-4" />
                                                        <span>{video.views}</span>
                                                    </div>

                                                    <div className="flex items-center space-x-1">
                                                        <Star className="h-4 w-4 text-yellow-400" />
                                                        <span>{video.rating}</span>
                                                    </div>

                                                    <div className="flex items-center space-x-1">
                                                        <Calendar className="h-4 w-4" />
                                                        <span>{new Date(video.createdAt).toLocaleDateString('ru-RU')}</span>
                                                    </div>
                                                </div>

                                                {/* Actions */}
                                                <div className="flex items-center space-x-2">
                                                    {video.downloadUrl && (
                                                        <button
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                const link = document.createElement('a');
                                                                link.href = video.downloadUrl;
                                                                link.download = `${video.title}.mp4`;
                                                                link.click();
                                                            }}
                                                            className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
                                                        >
                                                            <Download className="h-4 w-4" />
                                                        </button>
                                                    )}

                                                    <button
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            if (navigator.share) {
                                                                navigator.share({
                                                                    title: video.title,
                                                                    text: video.description,
                                                                    url: window.location.href
                                                                });
                                                            }
                                                        }}
                                                        className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
                                                    >
                                                        <Share2 className="h-4 w-4" />
                                                    </button>
                                                </div>
                                            </div>

                                            {/* Tags */}
                                            {video.tags && video.tags.length > 0 && (
                                                <div className="flex flex-wrap gap-1 mt-3">
                                                    {video.tags.slice(0, 3).map((tag, index) => (
                                                        <span
                                                            key={index}
                                                            className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs rounded-full"
                                                        >
                                                            {tag}
                                                        </span>
                                                    ))}
                                                    {video.tags.length > 3 && (
                                                        <span className="px-2 py-1 bg-gray-100 dark:bg-gray-600 text-gray-600 dark:text-gray-400 text-xs rounded-full">
                                                            +{video.tags.length - 3}
                                                        </span>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        )}
                    </div>
                </motion.div>
            </div>

            {/* Video Player */}
            {selectedVideo && (
                <VideoGuidePlayer
                    videoGuide={selectedVideo}
                    isOpen={true}
                    onClose={() => setSelectedVideo(null)}
                    autoPlay={true}
                />
            )}
        </>
    );
};

export default VideoGuideLibrary;