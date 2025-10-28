import React, { useState, useEffect, useCallback } from 'react';
import { Responsive, WidthProvider } from 'react-grid-layout';
import { 
  PlusIcon, 
  CogIcon, 
  TrashIcon, 
  EyeIcon,
  SaveIcon,
  ShareIcon,
  ArrowDownTrayIcon as DownloadIcon,
  ArrowUpTrayIcon as UploadIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import DashboardWidget from './DashboardWidget';
import WidgetConfigModal from './WidgetConfigModal';
import DashboardSettingsModal from './DashboardSettingsModal';
import WidgetLibrary from './WidgetLibrary';
import LoadingSpinner from './LoadingSpinner';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

const ResponsiveGridLayout = WidthProvider(Responsive);

const DashboardBuilder = () => {
  const [dashboards, setDashboards] = useState([]);
  const [currentDashboard, setCurrentDashboard] = useState(null);
  const [widgets, setWidgets] = useState([]);
  const [layouts, setLayouts] = useState({});
  const [dataSource, setDataSources] = useState([]);
  const [widgetTemplates, setWidgetTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  // Модальные окна
  const [showWidgetConfig, setShowWidgetConfig] = useState(false);
  const [showDashboardSettings, setShowDashboardSettings] = useState(false);
  const [showWidgetLibrary, setShowWidgetLibrary] = useState(false);
  const [editingWidget, setEditingWidget] = useState(null);
  
  // Настройки grid layout
  const [breakpoints, setBreakpoints] = useState({ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 });
  const [cols, setCols] = useState({ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 });

  // Загрузка данных при монтировании
  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/advanced-analytics/dashboard-builder', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load dashboard data');
      }

      const data = await response.json();
      setDashboards(data.dashboards);
      setDataSources(data.data_sources);
      setWidgetTemplates(data.widget_templates);

      // Устанавливаем первый дашборд как текущий
      if (data.dashboards.length > 0) {
        setCurrentDashboard(data.dashboards[0]);
        setWidgets(data.dashboards[0].widgets || []);
        setLayouts(data.dashboards[0].layout || {});
      }
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      toast.error('Ошибка загрузки данных дашборда');
    } finally {
      setLoading(false);
    }
  };

  const handleLayoutChange = useCallback((layout, layouts) => {
    setLayouts(layouts);
    
    // Автосохранение layout
    if (currentDashboard) {
      saveDashboardLayout(layouts);
    }
  }, [currentDashboard]);

  const saveDashboardLayout = async (newLayouts) => {
    if (!currentDashboard || saving) return;

    try {
      setSaving(true);
      const response = await fetch(`/api/v1/advanced-analytics/dashboards/${currentDashboard.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          layout: newLayouts
        })
      });

      if (!response.ok) {
        throw new Error('Failed to save layout');
      }

      // Обновляем локальное состояние
      setCurrentDashboard(prev => ({
        ...prev,
        layout: newLayouts
      }));
    } catch (error) {
      console.error('Error saving layout:', error);
      toast.error('Ошибка сохранения макета');
    } finally {
      setSaving(false);
    }
  };

  const handleAddWidget = (widgetTemplate) => {
    if (!currentDashboard) {
      toast.error('Выберите дашборд для добавления виджета');
      return;
    }

    const newWidget = {
      widget_type: widgetTemplate.type,
      title: widgetTemplate.name,
      config: {
        ...widgetTemplate.config,
        chart_type: widgetTemplate.chart_type
      },
      position: {
        x: 0,
        y: 0,
        w: 4,
        h: 3
      },
      data_source: widgetTemplate.config.data_source,
      refresh_interval: 300
    };

    setEditingWidget(newWidget);
    setShowWidgetConfig(true);
  };

  const handleSaveWidget = async (widgetData) => {
    try {
      const url = editingWidget?.id 
        ? `/api/v1/advanced-analytics/widgets/${editingWidget.id}`
        : `/api/v1/advanced-analytics/dashboards/${currentDashboard.id}/widgets`;
      
      const method = editingWidget?.id ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(widgetData)
      });

      if (!response.ok) {
        throw new Error('Failed to save widget');
      }

      const savedWidget = await response.json();

      if (editingWidget?.id) {
        // Обновление существующего виджета
        setWidgets(prev => prev.map(w => w.id === savedWidget.id ? savedWidget : w));
      } else {
        // Добавление нового виджета
        setWidgets(prev => [...prev, savedWidget]);
      }

      setShowWidgetConfig(false);
      setEditingWidget(null);
      toast.success('Виджет сохранен');
    } catch (error) {
      console.error('Error saving widget:', error);
      toast.error('Ошибка сохранения виджета');
    }
  };

  const handleEditWidget = (widget) => {
    setEditingWidget(widget);
    setShowWidgetConfig(true);
  };

  const handleDeleteWidget = async (widgetId) => {
    if (!window.confirm('Удалить виджет?')) return;

    try {
      const response = await fetch(`/api/v1/advanced-analytics/widgets/${widgetId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete widget');
      }

      setWidgets(prev => prev.filter(w => w.id !== widgetId));
      toast.success('Виджет удален');
    } catch (error) {
      console.error('Error deleting widget:', error);
      toast.error('Ошибка удаления виджета');
    }
  };

  const handleCreateDashboard = async (dashboardData) => {
    try {
      const response = await fetch('/api/v1/advanced-analytics/dashboards', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(dashboardData)
      });

      if (!response.ok) {
        throw new Error('Failed to create dashboard');
      }

      const newDashboard = await response.json();
      setDashboards(prev => [...prev, newDashboard]);
      setCurrentDashboard(newDashboard);
      setWidgets([]);
      setLayouts({});
      
      toast.success('Дашборд создан');
    } catch (error) {
      console.error('Error creating dashboard:', error);
      toast.error('Ошибка создания дашборда');
    }
  };

  const handleExportDashboard = async () => {
    if (!currentDashboard) return;

    try {
      const response = await fetch(`/api/v1/advanced-analytics/dashboards/${currentDashboard.id}/export`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to export dashboard');
      }

      const exportData = await response.json();
      
      // Скачиваем как JSON файл
      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `dashboard-${currentDashboard.name}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast.success('Дашборд экспортирован');
    } catch (error) {
      console.error('Error exporting dashboard:', error);
      toast.error('Ошибка экспорта дашборда');
    }
  };

  const handleImportDashboard = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    try {
      const text = await file.text();
      const importData = JSON.parse(text);

      const response = await fetch('/api/v1/advanced-analytics/dashboards/import', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(importData)
      });

      if (!response.ok) {
        throw new Error('Failed to import dashboard');
      }

      const importedDashboard = await response.json();
      setDashboards(prev => [...prev, importedDashboard]);
      setCurrentDashboard(importedDashboard);
      setWidgets(importedDashboard.widgets || []);
      setLayouts(importedDashboard.layout || {});

      toast.success('Дашборд импортирован');
    } catch (error) {
      console.error('Error importing dashboard:', error);
      toast.error('Ошибка импорта дашборда');
    }

    // Сбрасываем input
    event.target.value = '';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Toolbar */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {/* Dashboard Selector */}
            <select
              value={currentDashboard?.id || ''}
              onChange={(e) => {
                const dashboard = dashboards.find(d => d.id === parseInt(e.target.value));
                setCurrentDashboard(dashboard);
                setWidgets(dashboard?.widgets || []);
                setLayouts(dashboard?.layout || {});
              }}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="">Выберите дашборд</option>
              {dashboards.map(dashboard => (
                <option key={dashboard.id} value={dashboard.id}>
                  {dashboard.name}
                </option>
              ))}
            </select>

            {/* Dashboard Actions */}
            <button
              onClick={() => setShowDashboardSettings(true)}
              className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
              title="Настройки дашборда"
            >
              <CogIcon className="h-5 w-5" />
            </button>
          </div>

          <div className="flex items-center space-x-2">
            {/* Add Widget */}
            <button
              onClick={() => setShowWidgetLibrary(true)}
              className="flex items-center px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              <PlusIcon className="h-4 w-4 mr-2" />
              Добавить виджет
            </button>

            {/* Export/Import */}
            <button
              onClick={handleExportDashboard}
              disabled={!currentDashboard}
              className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white disabled:opacity-50"
              title="Экспорт дашборда"
            >
              <DownloadIcon className="h-5 w-5" />
            </button>

            <label className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white cursor-pointer" title="Импорт дашборда">
              <UploadIcon className="h-5 w-5" />
              <input
                type="file"
                accept=".json"
                onChange={handleImportDashboard}
                className="hidden"
              />
            </label>

            {/* Save Status */}
            {saving && (
              <div className="flex items-center text-sm text-gray-500">
                <LoadingSpinner size="sm" />
                <span className="ml-2">Сохранение...</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Dashboard Content */}
      <div className="flex-1 p-4 overflow-auto">
        {currentDashboard ? (
          <ResponsiveGridLayout
            className="layout"
            layouts={layouts}
            onLayoutChange={handleLayoutChange}
            breakpoints={breakpoints}
            cols={cols}
            rowHeight={60}
            isDraggable={true}
            isResizable={true}
            margin={[16, 16]}
            containerPadding={[0, 0]}
          >
            {widgets.map(widget => (
              <div key={widget.id} className="widget-container">
                <DashboardWidget
                  widget={widget}
                  onEdit={() => handleEditWidget(widget)}
                  onDelete={() => handleDeleteWidget(widget.id)}
                />
              </div>
            ))}
          </ResponsiveGridLayout>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                Нет выбранного дашборда
              </h3>
              <p className="text-gray-500 dark:text-gray-400 mb-4">
                Выберите существующий дашборд или создайте новый
              </p>
              <button
                onClick={() => setShowDashboardSettings(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Создать дашборд
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      {showWidgetConfig && (
        <WidgetConfigModal
          widget={editingWidget}
          dataSources={dataSource}
          onSave={handleSaveWidget}
          onClose={() => {
            setShowWidgetConfig(false);
            setEditingWidget(null);
          }}
        />
      )}

      {showDashboardSettings && (
        <DashboardSettingsModal
          dashboard={currentDashboard}
          onSave={currentDashboard ? undefined : handleCreateDashboard}
          onClose={() => setShowDashboardSettings(false)}
        />
      )}

      {showWidgetLibrary && (
        <WidgetLibrary
          templates={widgetTemplates}
          onSelectTemplate={handleAddWidget}
          onClose={() => setShowWidgetLibrary(false)}
        />
      )}
    </div>
  );
};

export default DashboardBuilder;