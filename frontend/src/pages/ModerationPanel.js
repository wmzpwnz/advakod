import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { 
  Star, CheckCircle, Clock, Award, Zap 
} from 'lucide-react';

const ModerationPanel = () => {
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    priority: '',
    status: '',
    assigned_to_me: false
  });
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [stats, setStats] = useState(null);
  const [categories, setCategories] = useState([]);
  const [selectedMessage, setSelectedMessage] = useState(null);

  const loadQueueData = useCallback(async () => {
    await loadQueue();
  }, [page, filters]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    loadQueueData();
    loadStats();
    loadCategories();
  }, [loadQueueData]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadQueue = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const params = new URLSearchParams({
        page,
        page_size: 20,
        ...filters
      });

      const response = await axios.get(
        `${process.env.REACT_APP_API_URL}/api/v1/moderation/queue?${params}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setQueue(response.data.items);
      setTotalPages(response.data.total_pages);
    } catch (error) {
      console.error('Error loading queue:', error);
      if (error.response?.status === 403) {
        alert('У вас нет прав модератора');
      }
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${process.env.REACT_APP_API_URL}/api/v1/moderation/my-stats`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setStats(response.data);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const loadCategories = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${process.env.REACT_APP_API_URL}/api/v1/moderation/categories`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setCategories(response.data);
    } catch (error) {
      console.error('Error loading categories:', error);
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'text-red-600 dark:text-red-400 bg-red-500/10 border-red-400/30';
      case 'medium': return 'text-yellow-600 dark:text-yellow-400 bg-yellow-500/10 border-yellow-400/30';
      case 'low': return 'text-green-600 dark:text-green-400 bg-green-500/10 border-green-400/30';
      default: return 'text-gray-600 dark:text-gray-400 bg-gray-500/10 border-gray-400/30';
    }
  };

  const getRankIcon = (rank) => {
    switch (rank) {
      case 'legend': return '👑';
      case 'master': return '⭐';
      case 'expert': return '🎯';
      default: return '🌱';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-purple-50/30 dark:from-gray-900 dark:via-gray-800 dark:to-purple-900/20">
      {/* Header */}
      <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl border-b border-purple-200/30 dark:border-purple-500/20 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-600 via-blue-600 to-cyan-600 bg-clip-text text-transparent">
                Панель модерации
              </h1>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Оценка качества ответов ИИ
              </p>
            </div>

            {/* Stats Cards */}
            {stats && (
              <div className="flex gap-4">
                <div className="bg-white/50 dark:bg-gray-800/50 backdrop-blur-md rounded-xl px-4 py-2 border border-purple-200/30 dark:border-purple-500/20">
                  <div className="flex items-center gap-2">
                    <Award className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                    <div>
                      <div className="text-xs text-gray-600 dark:text-gray-400">Ранг</div>
                      <div className="text-lg font-bold text-purple-600 dark:text-purple-400">
                        {getRankIcon(stats.rank)} {stats.rank}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-white/50 dark:bg-gray-800/50 backdrop-blur-md rounded-xl px-4 py-2 border border-blue-200/30 dark:border-blue-500/20">
                  <div className="flex items-center gap-2">
                    <Zap className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                    <div>
                      <div className="text-xs text-gray-600 dark:text-gray-400">Баллы</div>
                      <div className="text-lg font-bold text-blue-600 dark:text-blue-400">
                        {stats.points}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-white/50 dark:bg-gray-800/50 backdrop-blur-md rounded-xl px-4 py-2 border border-cyan-200/30 dark:border-cyan-500/20">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-5 h-5 text-cyan-600 dark:text-cyan-400" />
                    <div>
                      <div className="text-xs text-gray-600 dark:text-gray-400">Оценок</div>
                      <div className="text-lg font-bold text-cyan-600 dark:text-cyan-400">
                        {stats.total_reviews}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Filters */}
          <div className="flex gap-3 mt-4">
            <select
              value={filters.priority}
              onChange={(e) => setFilters({ ...filters, priority: e.target.value })}
              className="px-4 py-2 bg-white/70 dark:bg-gray-800/70 backdrop-blur-md rounded-lg border border-purple-200/30 dark:border-purple-500/20 focus:border-purple-400/60 focus:ring-2 focus:ring-purple-500/20 transition-all"
            >
              <option value="">Все приоритеты</option>
              <option value="high">🔴 Высокий</option>
              <option value="medium">🟡 Средний</option>
              <option value="low">🟢 Низкий</option>
            </select>

            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="px-4 py-2 bg-white/70 dark:bg-gray-800/70 backdrop-blur-md rounded-lg border border-purple-200/30 dark:border-purple-500/20 focus:border-purple-400/60 focus:ring-2 focus:ring-purple-500/20 transition-all"
            >
              <option value="">Все статусы</option>
              <option value="pending">⏳ Ожидает</option>
              <option value="in_review">👀 На проверке</option>
              <option value="completed">✅ Завершено</option>
            </select>

            <label className="flex items-center gap-2 px-4 py-2 bg-white/70 dark:bg-gray-800/70 backdrop-blur-md rounded-lg border border-purple-200/30 dark:border-purple-500/20 cursor-pointer hover:bg-purple-500/10 transition-all">
              <input
                type="checkbox"
                checked={filters.assigned_to_me}
                onChange={(e) => setFilters({ ...filters, assigned_to_me: e.target.checked })}
                className="w-4 h-4 text-purple-600 rounded"
              />
              <span className="text-sm text-gray-700 dark:text-gray-300">Только мои</span>
            </label>
          </div>
        </div>
      </div>

      {/* Queue List */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-purple-500/20 border-t-purple-600"></div>
          </div>
        ) : queue.length === 0 ? (
          <div className="text-center py-12">
            <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Очередь пуста!
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Все ответы проверены. Отличная работа! 🎉
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {queue.map((item) => (
              <div
                key={item.queue_item.id}
                className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-xl border border-purple-200/30 dark:border-purple-500/20 p-6 hover:shadow-xl hover:shadow-purple-500/10 transition-all cursor-pointer"
                onClick={() => setSelectedMessage(item)}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <span className={`px-3 py-1 rounded-lg text-xs font-semibold border ${getPriorityColor(item.queue_item.priority)}`}>
                      {item.queue_item.priority === 'high' && '🔴 '}
                      {item.queue_item.priority === 'medium' && '🟡 '}
                      {item.queue_item.priority === 'low' && '🟢 '}
                      {item.queue_item.priority.toUpperCase()}
                    </span>
                    {item.queue_item.reason && (
                      <span className="text-xs text-gray-600 dark:text-gray-400">
                        {item.queue_item.reason === 'user_complaint' && '👤 Жалоба пользователя'}
                        {item.queue_item.reason === 'low_confidence' && '⚠️ Низкая уверенность'}
                        {item.queue_item.reason === 'random_sample' && '🎲 Случайная выборка'}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                    <Clock className="w-4 h-4" />
                    {new Date(item.queue_item.created_at).toLocaleString('ru-RU')}
                  </div>
                </div>

                <div className="space-y-3">
                  <div>
                    <div className="text-xs font-semibold text-purple-600 dark:text-purple-400 mb-1">
                      Вопрос пользователя:
                    </div>
                    <div className="text-sm text-gray-700 dark:text-gray-300 bg-purple-500/5 rounded-lg p-3">
                      {item.message.user_question}
                    </div>
                  </div>

                  <div>
                    <div className="text-xs font-semibold text-blue-600 dark:text-blue-400 mb-1">
                      Ответ ИИ:
                    </div>
                    <div className="text-sm text-gray-700 dark:text-gray-300 bg-blue-500/5 rounded-lg p-3 line-clamp-3">
                      {item.message.ai_response}
                    </div>
                  </div>

                  {item.message.user_feedback && (
                    <div className="flex items-center gap-2 text-xs">
                      {item.message.user_feedback.rating === 'negative' ? (
                        <span className="text-red-600 dark:text-red-400">👎 Пользователь: не помогло</span>
                      ) : (
                        <span className="text-green-600 dark:text-green-400">👍 Пользователь: полезно</span>
                      )}
                    </div>
                  )}
                </div>

                <div className="mt-4 flex justify-end">
                  <button className="px-4 py-2 bg-gradient-to-r from-purple-500/20 via-blue-500/20 to-cyan-500/20 backdrop-blur-lg rounded-lg border border-purple-400/40 text-purple-600 dark:text-purple-400 font-semibold hover:shadow-lg hover:shadow-purple-500/30 transition-all">
                    Оценить →
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center gap-2 mt-6">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-4 py-2 bg-white/70 dark:bg-gray-800/70 backdrop-blur-md rounded-lg border border-purple-200/30 dark:border-purple-500/20 disabled:opacity-50 hover:bg-purple-500/10 transition-all"
            >
              ← Назад
            </button>
            <span className="px-4 py-2 bg-white/70 dark:bg-gray-800/70 backdrop-blur-md rounded-lg border border-purple-200/30 dark:border-purple-500/20">
              {page} / {totalPages}
            </span>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-4 py-2 bg-white/70 dark:bg-gray-800/70 backdrop-blur-md rounded-lg border border-purple-200/30 dark:border-purple-500/20 disabled:opacity-50 hover:bg-purple-500/10 transition-all"
            >
              Вперед →
            </button>
          </div>
        )}
      </div>

      {/* Review Modal */}
      {selectedMessage && (
        <ReviewModal
          message={selectedMessage}
          categories={categories}
          onClose={() => setSelectedMessage(null)}
          onSubmit={() => {
            setSelectedMessage(null);
            loadQueue();
            loadStats();
          }}
        />
      )}
    </div>
  );
};

// Review Modal Component
const ReviewModal = ({ message, categories, onClose, onSubmit }) => {
  const [rating, setRating] = useState(0);
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [comment, setComment] = useState('');
  const [suggestedFix, setSuggestedFix] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (rating === 0) {
      alert('Пожалуйста, поставьте оценку');
      return;
    }

    if (!comment || comment.length < 10) {
      alert('Пожалуйста, напишите комментарий (минимум 10 символов)');
      return;
    }

    if (rating < 5 && comment.length < 20) {
      alert('Для оценки ниже 5 требуется детальный комментарий (минимум 20 символов)');
      return;
    }

    try {
      setIsSubmitting(true);
      const token = localStorage.getItem('token');

      await axios.post(
        `${process.env.REACT_APP_API_URL}/api/v1/moderation/review`,
        {
          message_id: message.message.message_id,
          star_rating: rating,
          problem_categories: selectedCategories,
          comment,
          suggested_fix: suggestedFix || undefined
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      alert('Оценка успешно отправлена! +' + (10 + (suggestedFix ? 30 : 0)) + ' баллов');
      onSubmit();
    } catch (error) {
      console.error('Error submitting review:', error);
      alert('Ошибка отправки оценки: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsSubmitting(false);
    }
  };

  const toggleCategory = (categoryName) => {
    setSelectedCategories(prev =>
      prev.includes(categoryName)
        ? prev.filter(c => c !== categoryName)
        : [...prev, categoryName]
    );
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white/90 dark:bg-gray-800/90 backdrop-blur-xl rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto border border-purple-200/30 dark:border-purple-500/20 shadow-2xl">
        <div className="sticky top-0 bg-white/90 dark:bg-gray-800/90 backdrop-blur-xl border-b border-purple-200/30 dark:border-purple-500/20 p-6">
          <h2 className="text-2xl font-bold bg-gradient-to-r from-purple-600 via-blue-600 to-cyan-600 bg-clip-text text-transparent">
            Оценка ответа ИИ
          </h2>
        </div>

        <div className="p-6 space-y-6">
          {/* Question & Answer */}
          <div className="space-y-4">
            <div>
              <div className="text-sm font-semibold text-purple-600 dark:text-purple-400 mb-2">
                Вопрос пользователя:
              </div>
              <div className="text-sm text-gray-700 dark:text-gray-300 bg-purple-500/10 rounded-lg p-4">
                {message.message.user_question}
              </div>
            </div>

            <div>
              <div className="text-sm font-semibold text-blue-600 dark:text-blue-400 mb-2">
                Ответ ИИ:
              </div>
              <div className="text-sm text-gray-700 dark:text-gray-300 bg-blue-500/10 rounded-lg p-4 max-h-60 overflow-y-auto">
                {message.message.ai_response}
              </div>
            </div>
          </div>

          {/* Star Rating */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
              Оценка (1-10 звезд):
            </label>
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((star) => (
                <button
                  key={star}
                  onClick={() => setRating(star)}
                  className={`w-10 h-10 rounded-lg border-2 transition-all ${
                    star <= rating
                      ? 'bg-gradient-to-r from-purple-500 to-blue-500 border-purple-400 text-white shadow-lg shadow-purple-500/30'
                      : 'bg-white/50 dark:bg-gray-700/50 border-gray-300 dark:border-gray-600 text-gray-400 hover:border-purple-400'
                  }`}
                >
                  <Star className={`w-5 h-5 mx-auto ${star <= rating ? 'fill-current' : ''}`} />
                </button>
              ))}
              <span className="ml-2 text-2xl font-bold text-purple-600 dark:text-purple-400">
                {rating}/10
              </span>
            </div>
          </div>

          {/* Problem Categories */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
              Категории проблем:
            </label>
            <div className="grid grid-cols-2 gap-2">
              {categories.map((category) => (
                <button
                  key={category.id}
                  onClick={() => toggleCategory(category.name)}
                  className={`px-4 py-2 rounded-lg border-2 text-sm font-medium transition-all ${
                    selectedCategories.includes(category.name)
                      ? 'bg-purple-500/20 border-purple-400 text-purple-600 dark:text-purple-400'
                      : 'bg-white/50 dark:bg-gray-700/50 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-purple-400'
                  }`}
                >
                  {category.icon} {category.display_name}
                </button>
              ))}
            </div>
          </div>

          {/* Comment */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Комментарий (обязательно, мин. 10 символов):
            </label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Опишите проблемы в ответе..."
              className="w-full px-4 py-3 bg-white/70 dark:bg-gray-800/70 backdrop-blur-md rounded-lg border border-purple-200/30 dark:border-purple-500/20 focus:border-purple-400/60 focus:ring-2 focus:ring-purple-500/20 resize-none transition-all"
              rows="4"
            />
            <div className="text-xs text-gray-500 mt-1">
              {comment.length} символов {rating < 5 && '(требуется минимум 20 для оценки ниже 5)'}
            </div>
          </div>

          {/* Suggested Fix */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Предложенное исправление (опционально, +30 баллов):
            </label>
            <textarea
              value={suggestedFix}
              onChange={(e) => setSuggestedFix(e.target.value)}
              placeholder="Напишите правильный ответ для обучения модели..."
              className="w-full px-4 py-3 bg-white/70 dark:bg-gray-800/70 backdrop-blur-md rounded-lg border border-blue-200/30 dark:border-blue-500/20 focus:border-blue-400/60 focus:ring-2 focus:ring-blue-500/20 resize-none transition-all"
              rows="6"
            />
          </div>
        </div>

        {/* Actions */}
        <div className="sticky bottom-0 bg-white/90 dark:bg-gray-800/90 backdrop-blur-xl border-t border-purple-200/30 dark:border-purple-500/20 p-6 flex gap-3">
          <button
            onClick={handleSubmit}
            disabled={isSubmitting || rating === 0 || comment.length < 10}
            className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-500 via-blue-500 to-cyan-500 text-white rounded-lg font-semibold hover:shadow-xl hover:shadow-purple-500/30 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {isSubmitting ? 'Отправка...' : `Отправить оценку (+${10 + (suggestedFix ? 30 : 0)} баллов)`}
          </button>
          <button
            onClick={onClose}
            disabled={isSubmitting}
            className="px-6 py-3 bg-white/70 dark:bg-gray-700/70 backdrop-blur-md rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-600 transition-all"
          >
            Отмена
          </button>
        </div>
      </div>
    </div>
  );
};

export default ModerationPanel;
