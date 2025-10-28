import React, { useState, useEffect, useRef } from 'react';
import { 
  CogIcon, 
  TrashIcon, 
  ArrowPathIcon,
  EyeIcon,
  ChartBarIcon,
  TableCellsIcon,
  PresentationChartLineIcon
} from '@heroicons/react/24/outline';
import { Line, Bar, Pie, Scatter } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import LoadingSpinner from './LoadingSpinner';

// Регистрируем компоненты Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const DashboardWidget = ({ widget, onEdit, onDelete }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastRefresh, setLastRefresh] = useState(null);
  const refreshIntervalRef = useRef(null);

  useEffect(() => {
    loadWidgetData();
    
    // Устанавливаем интервал обновления
    if (widget.refresh_interval && widget.refresh_interval > 0) {
      refreshIntervalRef.current = setInterval(() => {
        loadWidgetData();
      }, widget.refresh_interval * 1000);
    }

    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, [widget.id, widget.refresh_interval]);

  const loadWidgetData = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/v1/advanced-analytics/widgets/${widget.id}/data`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load widget data');
      }

      const widgetData = await response.json();
      setData(widgetData);
      setLastRefresh(new Date());
    } catch (err) {
      console.error('Error loading widget data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    loadWidgetData();
  };

  const getWidgetIcon = () => {
    switch (widget.widget_type) {
      case 'chart':
        return <ChartBarIcon className="h-4 w-4" />;
      case 'table':
        return <TableCellsIcon className="h-4 w-4" />;
      case 'metric':
        return <PresentationChartLineIcon className="h-4 w-4" />;
      default:
        return <ChartBarIcon className="h-4 w-4" />;
    }
  };

  const renderMetricWidget = () => {
    if (!data || !data.datasets || data.datasets.length === 0) {
      return (
        <div className="flex items-center justify-center h-full text-gray-500">
          Нет данных
        </div>
      );
    }

    const value = data.datasets[0].data[0] || 0;
    const label = data.datasets[0].label || 'Метрика';

    return (
      <div className="flex flex-col items-center justify-center h-full">
        <div className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          {typeof value === 'number' ? value.toLocaleString() : value}
        </div>
        <div className="text-sm text-gray-500 dark:text-gray-400">
          {label}
        </div>
      </div>
    );
  };

  const renderChartWidget = () => {
    if (!data || !data.datasets) {
      return (
        <div className="flex items-center justify-center h-full text-gray-500">
          Нет данных
        </div>
      );
    }

    const chartConfig = widget.config || {};
    const chartType = chartConfig.chart_type || 'line';

    const chartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: chartConfig.show_legend !== false,
          position: 'top',
        },
        title: {
          display: false,
        },
      },
      scales: chartType !== 'pie' ? {
        y: {
          beginAtZero: true,
          grid: {
            display: chartConfig.show_grid !== false,
          },
        },
        x: {
          grid: {
            display: chartConfig.show_grid !== false,
          },
        },
      } : undefined,
    };

    const chartData = {
      labels: data.labels || [],
      datasets: data.datasets.map(dataset => ({
        ...dataset,
        borderWidth: 2,
        tension: 0.4,
      })),
    };

    switch (chartType) {
      case 'bar':
        return <Bar data={chartData} options={chartOptions} />;
      case 'pie':
        return <Pie data={chartData} options={chartOptions} />;
      case 'area':
        return <Line data={chartData} options={chartOptions} />;
      case 'scatter':
        return <Scatter data={chartData} options={chartOptions} />;
      case 'line':
      default:
        return <Line data={chartData} options={chartOptions} />;
    }
  };

  const renderTableWidget = () => {
    if (!data || !data.datasets || data.datasets.length === 0) {
      return (
        <div className="flex items-center justify-center h-full text-gray-500">
          Нет данных
        </div>
      );
    }

    const tableData = data.datasets[0].data || [];
    const labels = data.labels || [];

    return (
      <div className="overflow-auto h-full">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Название
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Значение
              </th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
            {labels.map((label, index) => (
              <tr key={index}>
                <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                  {label}
                </td>
                <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                  {tableData[index] || 0}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderWidgetContent = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-full">
          <LoadingSpinner />
        </div>
      );
    }

    if (error) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-red-500">
          <div className="text-sm mb-2">Ошибка загрузки</div>
          <button
            onClick={handleRefresh}
            className="text-xs text-blue-600 hover:text-blue-800"
          >
            Повторить
          </button>
        </div>
      );
    }

    switch (widget.widget_type) {
      case 'metric':
        return renderMetricWidget();
      case 'chart':
        return renderChartWidget();
      case 'table':
        return renderTableWidget();
      default:
        return renderMetricWidget();
    }
  };

  return (
    <div className="h-full bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 flex flex-col">
      {/* Widget Header */}
      <div className="flex items-center justify-between p-3 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center space-x-2 min-w-0 flex-1">
          {getWidgetIcon()}
          <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate">
            {widget.title}
          </h3>
        </div>
        
        <div className="flex items-center space-x-1 ml-2">
          <button
            onClick={handleRefresh}
            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            title="Обновить"
          >
            <ArrowPathIcon className="h-4 w-4" />
          </button>
          
          <button
            onClick={onEdit}
            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            title="Настроить"
          >
            <CogIcon className="h-4 w-4" />
          </button>
          
          <button
            onClick={onDelete}
            className="p-1 text-gray-400 hover:text-red-600 transition-colors"
            title="Удалить"
          >
            <TrashIcon className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Widget Content */}
      <div className="flex-1 p-3 min-h-0">
        {renderWidgetContent()}
      </div>

      {/* Widget Footer */}
      {lastRefresh && (
        <div className="px-3 py-1 border-t border-gray-200 dark:border-gray-700">
          <div className="text-xs text-gray-500 dark:text-gray-400">
            Обновлено: {lastRefresh.toLocaleTimeString()}
          </div>
        </div>
      )}
    </div>
  );
};

export default DashboardWidget;