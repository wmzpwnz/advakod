import React, { useState } from 'react';
import { 
  CheckCircle, 
  AlertTriangle, 
  FileText, 
  ExternalLink, 
  ChevronDown, 
  ChevronUp,
  Shield,
  Lightbulb,
  Clock,
  Target
} from 'lucide-react';

const EnhancedResponse = ({ message, enhancements = {} }) => {
  const [showDetails, setShowDetails] = useState(false);
  const [showSources, setShowSources] = useState(false);
  const [showWarnings, setShowWarnings] = useState(false);

  // Извлекаем данные из enhancements
  const factChecking = enhancements.fact_checking || {};
  const explainability = enhancements.explainability || {};
  const overallQuality = enhancements.overall_quality || 0.5;

  // Определяем качество ответа
  const getQualityLevel = (quality) => {
    if (quality >= 0.8) return { level: 'high', color: 'text-green-600', bg: 'bg-green-100' };
    if (quality >= 0.6) return { level: 'medium', color: 'text-yellow-600', bg: 'bg-yellow-100' };
    return { level: 'low', color: 'text-red-600', bg: 'bg-red-100' };
  };

  const qualityInfo = getQualityLevel(overallQuality);

  // Форматируем метрики факт-чекинга
  const formatMetric = (value) => {
    if (typeof value === 'number') {
      return `${(value * 100).toFixed(1)}%`;
    }
    return value || 'N/A';
  };

  return (
    <div className="space-y-4">
      {/* Основной контент сообщения */}
      <div className="whitespace-pre-wrap">
        {message.content}
      </div>

      {/* Индикатор качества ответа */}
      {overallQuality > 0 && (
        <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${qualityInfo.bg} ${qualityInfo.color}`}>
          <Shield className="w-4 h-4 mr-2" />
          Качество: {qualityInfo.level === 'high' ? 'Высокое' : qualityInfo.level === 'medium' ? 'Среднее' : 'Низкое'}
        </div>
      )}

      {/* Кнопки для детальной информации */}
      <div className="flex flex-wrap gap-2">
        {Object.keys(factChecking).length > 0 && (
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="flex items-center px-3 py-1 bg-blue-100 text-blue-700 rounded-lg text-sm hover:bg-blue-200 transition-colors"
          >
            <Target className="w-4 h-4 mr-2" />
            Факт-чекинг
            {showDetails ? <ChevronUp className="w-4 h-4 ml-1" /> : <ChevronDown className="w-4 h-4 ml-1" />}
          </button>
        )}

        {explainability.sources && explainability.sources.length > 0 && (
          <button
            onClick={() => setShowSources(!showSources)}
            className="flex items-center px-3 py-1 bg-green-100 text-green-700 rounded-lg text-sm hover:bg-green-200 transition-colors"
          >
            <FileText className="w-4 h-4 mr-2" />
            Источники ({explainability.sources.length})
            {showSources ? <ChevronUp className="w-4 h-4 ml-1" /> : <ChevronDown className="w-4 h-4 ml-1" />}
          </button>
        )}

        {explainability.warnings && explainability.warnings.length > 0 && (
          <button
            onClick={() => setShowWarnings(!showWarnings)}
            className="flex items-center px-3 py-1 bg-yellow-100 text-yellow-700 rounded-lg text-sm hover:bg-yellow-200 transition-colors"
          >
            <AlertTriangle className="w-4 h-4 mr-2" />
            Предупреждения ({explainability.warnings.length})
            {showWarnings ? <ChevronUp className="w-4 h-4 ml-1" /> : <ChevronDown className="w-4 h-4 ml-1" />}
          </button>
        )}
      </div>

      {/* Детали факт-чекинга */}
      {showDetails && Object.keys(factChecking).length > 0 && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <h4 className="font-semibold text-blue-900 dark:text-blue-100 mb-3 flex items-center">
            <Target className="w-5 h-5 mr-2" />
            Анализ факт-чекинга
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Точность ссылок:</span>
                <span className={`font-medium ${factChecking.citation_recall >= 0.7 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatMetric(factChecking.citation_recall)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Покрытие контекстом:</span>
                <span className={`font-medium ${factChecking.support_coverage >= 0.5 ? 'text-green-600' : 'text-yellow-600'}`}>
                  {formatMetric(factChecking.support_coverage)}
                </span>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Риск галлюцинаций:</span>
                <span className={`font-medium ${factChecking.hallucination_score <= 0.3 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatMetric(factChecking.hallucination_score)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Правовая согласованность:</span>
                <span className={`font-medium ${factChecking.legal_consistency >= 0.8 ? 'text-green-600' : 'text-yellow-600'}`}>
                  {formatMetric(factChecking.legal_consistency)}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Источники */}
      {showSources && explainability.sources && explainability.sources.length > 0 && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
          <h4 className="font-semibold text-green-900 dark:text-green-100 mb-3 flex items-center">
            <FileText className="w-5 h-5 mr-2" />
            Источники информации
          </h4>
          <div className="space-y-3">
            {explainability.sources.map((source, index) => (
              <div key={index} className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-green-200 dark:border-green-700">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="font-medium text-gray-900 dark:text-gray-100">
                      {source.code} {source.article} {source.part} {source.item}
                    </div>
                    {source.edition && (
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        {source.edition}
                      </div>
                    )}
                    <div className="text-sm text-gray-700 dark:text-gray-300 mt-2">
                      {source.excerpt}
                    </div>
                    {source.url && (
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800 mt-2"
                      >
                        <ExternalLink className="w-4 h-4 mr-1" />
                        Открыть источник
                      </a>
                    )}
                  </div>
                  {source.relevance_score && (
                    <div className="text-xs text-gray-500 dark:text-gray-400 ml-2">
                      {Math.round(source.relevance_score * 100)}%
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Предупреждения */}
      {showWarnings && explainability.warnings && explainability.warnings.length > 0 && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
          <h4 className="font-semibold text-yellow-900 dark:text-yellow-100 mb-3 flex items-center">
            <AlertTriangle className="w-5 h-5 mr-2" />
            Важные предупреждения
          </h4>
          <div className="space-y-2">
            {explainability.warnings.map((warning, index) => (
              <div key={index} className="flex items-start space-x-2 text-sm text-yellow-800 dark:text-yellow-200">
                <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <span>{warning}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Рекомендации пользователю */}
      {explainability.user_actions && explainability.user_actions.length > 0 && (
        <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-4">
          <h4 className="font-semibold text-purple-900 dark:text-purple-100 mb-3 flex items-center">
            <Lightbulb className="w-5 h-5 mr-2" />
            Рекомендации
          </h4>
          <div className="space-y-2">
            {explainability.user_actions.map((action, index) => (
              <div key={index} className="flex items-start space-x-2 text-sm text-purple-800 dark:text-purple-200">
                <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <span>{action}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Аргументы (если есть) */}
      {explainability.arguments && explainability.arguments.length > 0 && (
        <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-3 flex items-center">
            <FileText className="w-5 h-5 mr-2" />
            Аргументация
          </h4>
          <div className="space-y-3">
            {explainability.arguments.map((argument, index) => (
              <div key={index} className="bg-white dark:bg-gray-700 rounded-lg p-3">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="text-sm text-gray-700 dark:text-gray-300">
                      {argument.text}
                    </div>
                    {argument.confidence && (
                      <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        Уверенность: {Math.round(argument.confidence * 100)}%
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Метаданные ответа */}
      {explainability.metadata && (
        <div className="text-xs text-gray-500 dark:text-gray-400 flex items-center space-x-4">
          <div className="flex items-center">
            <Clock className="w-3 h-3 mr-1" />
            {explainability.metadata.created_at && 
              new Date(explainability.metadata.created_at).toLocaleString('ru-RU')
            }
          </div>
          {explainability.metadata.sources_count && (
            <div>
              Источников: {explainability.metadata.sources_count}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default EnhancedResponse;
