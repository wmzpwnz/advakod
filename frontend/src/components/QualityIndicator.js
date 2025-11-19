import React from 'react';
import { Shield, CheckCircle, AlertTriangle, Info } from 'lucide-react';

const QualityIndicator = ({ quality, factCheck, compact = false }) => {
  const getQualityInfo = (score) => {
    if (score >= 0.8) {
      return {
        level: 'high',
        label: 'Высокое',
        color: 'text-green-600',
        bg: 'bg-green-100 dark:bg-green-900/20',
        icon: CheckCircle
      };
    } else if (score >= 0.6) {
      return {
        level: 'medium',
        label: 'Среднее',
        color: 'text-yellow-600',
        bg: 'bg-yellow-100 dark:bg-yellow-900/20',
        icon: AlertTriangle
      };
    } else {
      return {
        level: 'low',
        label: 'Низкое',
        color: 'text-red-600',
        bg: 'bg-red-100 dark:bg-red-900/20',
        icon: AlertTriangle
      };
    }
  };

  const qualityInfo = getQualityInfo(quality || 0.5);
  const Icon = qualityInfo.icon;

  if (compact) {
    return (
      <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${qualityInfo.bg} ${qualityInfo.color}`}>
        <Icon className="w-3 h-3 mr-1" />
        {qualityInfo.label}
      </div>
    );
  }

  return (
    <div className={`p-3 rounded-lg border ${qualityInfo.bg} border-current ${qualityInfo.color}`}>
      <div className="flex items-center space-x-2 mb-2">
        <Icon className="w-5 h-5" />
        <span className="font-semibold">Качество ответа: {qualityInfo.label}</span>
      </div>
      
      {factCheck && (
        <div className="space-y-1 text-sm">
          <div className="flex justify-between">
            <span>Точность ссылок:</span>
            <span className={factCheck.citation_recall >= 0.7 ? 'text-green-600' : 'text-red-600'}>
              {Math.round((factCheck.citation_recall || 0) * 100)}%
            </span>
          </div>
          <div className="flex justify-between">
            <span>Покрытие контекстом:</span>
            <span className={factCheck.support_coverage >= 0.5 ? 'text-green-600' : 'text-yellow-600'}>
              {Math.round((factCheck.support_coverage || 0) * 100)}%
            </span>
          </div>
          <div className="flex justify-between">
            <span>Риск галлюцинаций:</span>
            <span className={factCheck.hallucination_score <= 0.3 ? 'text-green-600' : 'text-red-600'}>
              {Math.round((factCheck.hallucination_score || 0) * 100)}%
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default QualityIndicator;
