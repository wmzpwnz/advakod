import React, { useState } from 'react';
import axios from 'axios';
import { ThumbsUp, ThumbsDown } from 'lucide-react';

const FeedbackButtons = ({ messageId, onFeedbackSubmitted }) => {
  const [feedback, setFeedback] = useState(null);
  const [showReasonModal, setShowReasonModal] = useState(false);
  const [selectedReason, setSelectedReason] = useState('');
  const [comment, setComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const reasons = [
    { value: 'not_answered', label: 'Не ответил на вопрос' },
    { value: 'inaccurate', label: 'Неточная информация' },
    { value: 'hard_to_understand', label: 'Сложно понять' },
    { value: 'other', label: 'Другое' }
  ];

  const handlePositiveFeedback = async () => {
    try {
      setIsSubmitting(true);
      const token = localStorage.getItem('token');
      
      await axios.post(
        `${process.env.REACT_APP_API_URL}/api/v1/feedback/rate`,
        {
          message_id: messageId,
          rating: 'positive'
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      setFeedback('positive');
      if (onFeedbackSubmitted) onFeedbackSubmitted('positive');
    } catch (error) {
      console.error('Error submitting positive feedback:', error);
      alert('Ошибка отправки оценки');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleNegativeFeedback = () => {
    setShowReasonModal(true);
  };

  const submitNegativeFeedback = async () => {
    if (!selectedReason) {
      alert('Пожалуйста, выберите причину');
      return;
    }

    try {
      setIsSubmitting(true);
      const token = localStorage.getItem('token');
      
      await axios.post(
        `${process.env.REACT_APP_API_URL}/api/v1/feedback/rate`,
        {
          message_id: messageId,
          rating: 'negative',
          reason: selectedReason,
          comment: comment || undefined
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      setFeedback('negative');
      setShowReasonModal(false);
      if (onFeedbackSubmitted) onFeedbackSubmitted('negative');
    } catch (error) {
      console.error('Error submitting negative feedback:', error);
      alert('Ошибка отправки оценки');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (feedback) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-500">
        {feedback === 'positive' ? (
          <>
            <ThumbsUp className="w-4 h-4 text-green-500 fill-current" />
            <span>Спасибо за оценку!</span>
          </>
        ) : (
          <>
            <ThumbsDown className="w-4 h-4 text-red-500 fill-current" />
            <span>Спасибо за обратную связь!</span>
          </>
        )}
      </div>
    );
  }

  return (
    <>
      <div className="flex items-center gap-2">
        <button
          onClick={handlePositiveFeedback}
          disabled={isSubmitting}
          className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors disabled:opacity-50"
          title="Полезно"
        >
          <ThumbsUp className="w-4 h-4" />
          <span>Полезно</span>
        </button>
        
        <button
          onClick={handleNegativeFeedback}
          disabled={isSubmitting}
          className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
          title="Не помогло"
        >
          <ThumbsDown className="w-4 h-4" />
          <span>Не помогло</span>
        </button>
      </div>

      {/* Modal для негативной оценки */}
      {showReasonModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Почему ответ не помог?</h3>
            
            <div className="space-y-2 mb-4">
              {reasons.map((reason) => (
                <label key={reason.value} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="reason"
                    value={reason.value}
                    checked={selectedReason === reason.value}
                    onChange={(e) => setSelectedReason(e.target.value)}
                    className="w-4 h-4 text-blue-600"
                  />
                  <span className="text-sm">{reason.label}</span>
                </label>
              ))}
            </div>

            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Дополнительный комментарий (опционально)"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows="3"
            />

            <div className="flex gap-2 mt-4">
              <button
                onClick={submitNegativeFeedback}
                disabled={isSubmitting || !selectedReason}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Отправка...' : 'Отправить'}
              </button>
              <button
                onClick={() => {
                  setShowReasonModal(false);
                  setSelectedReason('');
                  setComment('');
                }}
                disabled={isSubmitting}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
              >
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default FeedbackButtons;
