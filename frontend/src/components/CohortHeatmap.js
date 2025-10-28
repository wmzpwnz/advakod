import React from 'react';

const CohortHeatmap = ({ cohortData }) => {
  if (!cohortData || !cohortData.retention_matrix || !cohortData.cohorts) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        Нет данных для отображения
      </div>
    );
  }

  const { cohorts, periods, retention_matrix, cohort_sizes, summary } = cohortData;

  const getHeatmapColor = (value) => {
    if (value === 0 || value === null || value === undefined) {
      return 'bg-gray-100 dark:bg-gray-800';
    }
    
    const intensity = Math.min(value / 100, 1);
    
    if (intensity >= 0.8) {
      return 'bg-green-500 text-white';
    } else if (intensity >= 0.6) {
      return 'bg-green-400 text-white';
    } else if (intensity >= 0.4) {
      return 'bg-yellow-400 text-gray-900';
    } else if (intensity >= 0.2) {
      return 'bg-orange-400 text-white';
    } else {
      return 'bg-red-400 text-white';
    }
  };

  const formatValue = (value) => {
    if (value === 0 || value === null || value === undefined) {
      return '-';
    }
    return `${value}%`;
  };

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
            <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {summary.total_users?.toLocaleString() || 0}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Всего пользователей
            </div>
          </div>
          
          <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
            <div className="text-2xl font-bold text-green-600 dark:text-green-400">
              {summary.total_cohorts || 0}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Количество когорт
            </div>
          </div>
          
          <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg">
            <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
              {summary.avg_retention || 0}%
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Средний retention
            </div>
          </div>
        </div>
      )}

      {/* Heatmap */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            Матрица удержания пользователей
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Процент пользователей, остающихся активными в каждом периоде
          </p>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="bg-gray-50 dark:bg-gray-900">
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Когорта
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Размер
                </th>
                {periods.map((period, index) => (
                  <th
                    key={index}
                    className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
                  >
                    {period}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {cohorts.map((cohort, cohortIndex) => (
                <tr key={cohort} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">
                    {cohort}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                    {cohort_sizes?.[cohortIndex]?.toLocaleString() || '-'}
                  </td>
                  {retention_matrix[cohortIndex]?.map((value, periodIndex) => (
                    <td key={periodIndex} className="px-2 py-2">
                      <div
                        className={`
                          w-16 h-8 flex items-center justify-center rounded text-xs font-medium
                          ${getHeatmapColor(value)}
                        `}
                      >
                        {formatValue(value)}
                      </div>
                    </td>
                  )) || periods.map((_, periodIndex) => (
                    <td key={periodIndex} className="px-2 py-2">
                      <div className="w-16 h-8 flex items-center justify-center rounded text-xs bg-gray-100 dark:bg-gray-800">
                        -
                      </div>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Legend */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
          Легенда
        </h4>
        <div className="flex items-center space-x-6 text-xs">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-green-500 rounded"></div>
            <span className="text-gray-600 dark:text-gray-400">80%+ (Отлично)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-green-400 rounded"></div>
            <span className="text-gray-600 dark:text-gray-400">60-80% (Хорошо)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-yellow-400 rounded"></div>
            <span className="text-gray-600 dark:text-gray-400">40-60% (Средне)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-orange-400 rounded"></div>
            <span className="text-gray-600 dark:text-gray-400">20-40% (Низко)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-red-400 rounded"></div>
            <span className="text-gray-600 dark:text-gray-400">0-20% (Критично)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded"></div>
            <span className="text-gray-600 dark:text-gray-400">Нет данных</span>
          </div>
        </div>
      </div>

      {/* Insights */}
      <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
        <h4 className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-2">
          Ключевые инсайты
        </h4>
        <div className="text-sm text-blue-800 dark:text-blue-200 space-y-1">
          {summary?.avg_retention && (
            <div>
              • Средний retention составляет {summary.avg_retention}%
              {summary.avg_retention > 70 && ' - это отличный показатель'}
              {summary.avg_retention >= 50 && summary.avg_retention <= 70 && ' - это хороший показатель'}
              {summary.avg_retention < 50 && ' - требует внимания'}
            </div>
          )}
          {cohorts.length > 0 && (
            <div>
              • Анализируется {cohorts.length} когорт за выбранный период
            </div>
          )}
          {retention_matrix.length > 0 && retention_matrix[0].length > 1 && (
            <div>
              • Отслеживается retention до {retention_matrix[0].length - 1} периодов
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CohortHeatmap;