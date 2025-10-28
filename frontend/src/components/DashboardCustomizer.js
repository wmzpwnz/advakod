import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Grid, 
  Plus, 
  X, 
  Move, 
  Settings, 
  Eye, 
  EyeOff,
  Save,
  RotateCcw,
  Maximize2,
  Minimize2,
  Edit3
} from 'lucide-react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import ModernButton from './ModernButton';
import GlassCard from './GlassCard';

const DashboardCustomizer = ({ isOpen, onClose, onSave, initialLayout }) => {
  const [layout, setLayout] = useState(initialLayout || []);
  const [availableWidgets, setAvailableWidgets] = useState([]);
  const [previewMode, setPreviewMode] = useState(false);
  const [selectedWidget, setSelectedWidget] = useState(null);

  // Доступные виджеты для добавления
  const widgetTypes = [
    {
      id: 'user-stats',
      name: 'Статистика пользователей',
      description: 'Общее количество пользователей и активность',
      icon: '👥',
      category: 'analytics',
      defaultSize: { w: 2, h: 1 }
    },
    {
      id: 'revenue-chart',
      name: 'График доходов',
      description: 'Динамика доходов по времени',
      icon: '💰',
      category: 'analytics',
      defaultSize: { w: 3, h: 2 }
    },
    {
      id: 'system-health',
      name: 'Состояние системы',
      description: 'Мониторинг серверов и сервисов',
      icon: '⚡',
      category: 'system',
      defaultSize: { w: 2, h: 1 }
    },
    {
      id: 'recent-activity',
      name: 'Последняя активность',
      description: 'Недавние действия пользователей',
      icon: '📊',
      category: 'activity',
      defaultSize: { w: 2, h: 2 }
    },
    {
      id: 'moderation-queue',
      name: 'Очередь модерации',
      description: 'Количество сообщений на модерации',
      icon: '🛡️',
      category: 'moderation',
      defaultSize: { w: 2, h: 1 }
    },
    {
      id: 'ai-performance',
      name: 'Производительность ИИ',
      description: 'Метрики работы AI моделей',
      icon: '🤖',
      category: 'ai',
      defaultSize: { w: 3, h: 2 }
    },
    {
      id: 'storage-usage',
      name: 'Использование хранилища',
      description: 'Занятое место и лимиты',
      icon: '💾',
      category: 'system',
      defaultSize: { w: 2, h: 1 }
    },
    {
      id: 'top-documents',
      name: 'Популярные документы',
      description: 'Наиболее используемые документы',
      icon: '📄',
      category: 'content',
      defaultSize: { w: 2, h: 2 }
    },
    {
      id: 'error-rate',
      name: 'Частота ошибок',
      description: 'Мониторинг ошибок системы',
      icon: '⚠️',
      category: 'system',
      defaultSize: { w: 2, h: 1 }
    },
    {
      id: 'conversion-funnel',
      name: 'Воронка конверсии',
      description: 'Анализ пути пользователей',
      icon: '🎯',
      category: 'marketing',
      defaultSize: { w: 3, h: 2 }
    }
  ];

  useEffect(() => {
    // Инициализация доступных виджетов (те, которые не добавлены в layout)
    const usedWidgetIds = layout.map(widget => widget.type);
    const available = widgetTypes.filter(widget => !usedWidgetIds.includes(widget.id));
    setAvailableWidgets(available);
  }, [layout]);

  const handleDragEnd = useCallback((result) => {
    const { destination, source, draggableId } = result;

    if (!destination) return;

    // Перемещение внутри layout
    if (source.droppableId === 'dashboard' && destination.droppableId === 'dashboard') {
      const newLayout = Array.from(layout);
      const [reorderedItem] = newLayout.splice(source.index, 1);
      newLayout.splice(destination.index, 0, reorderedItem);
      setLayout(newLayout);
    }

    // Добавление виджета из библиотеки
    if (source.droppableId === 'widget-library' && destination.droppableId === 'dashboard') {
      const widgetType = widgetTypes.find(w => w.id === draggableId);
      if (widgetType) {
        const newWidget = {
          id: `${widgetType.id}-${Date.now()}`,
          type: widgetType.id,
          name: widgetType.name,
          size: widgetType.defaultSize,
          position: { x: 0, y: 0 },
          visible: true,
          config: {}
        };

        const newLayout = Array.from(layout);
        newLayout.splice(destination.index, 0, newWidget);
        setLayout(newLayout);
      }
    }

    // Удаление виджета (перетаскивание в библиотеку)
    if (source.droppableId === 'dashboard' && destination.droppableId === 'widget-library') {
      const newLayout = Array.from(layout);
      newLayout.splice(source.index, 1);
      setLayout(newLayout);
    }
  }, [layout]);

  const addWidget = (widgetType) => {
    const newWidget = {
      id: `${widgetType.id}-${Date.now()}`,
      type: widgetType.id,
      name: widgetType.name,
      size: widgetType.defaultSize,
      position: { x: 0, y: 0 },
      visible: true,
      config: {}
    };

    setLayout(prev => [...prev, newWidget]);
  };

  const removeWidget = (widgetId) => {
    setLayout(prev => prev.filter(widget => widget.id !== widgetId));
  };

  const toggleWidgetVisibility = (widgetId) => {
    setLayout(prev => prev.map(widget => 
      widget.id === widgetId 
        ? { ...widget, visible: !widget.visible }
        : widget
    ));
  };

  const updateWidgetSize = (widgetId, newSize) => {
    setLayout(prev => prev.map(widget => 
      widget.id === widgetId 
        ? { ...widget, size: newSize }
        : widget
    ));
  };

  const resetLayout = () => {
    setLayout([]);
    setSelectedWidget(null);
  };

  const saveLayout = () => {
    if (onSave) {
      onSave(layout);
    }
    onClose();
  };

  const getWidgetIcon = (widgetType) => {
    const widget = widgetTypes.find(w => w.id === widgetType);
    return widget?.icon || '📊';
  };

  const getCategoryColor = (category) => {
    const colors = {
      analytics: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
      system: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
      activity: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
      moderation: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
      ai: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-400',
      content: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
      marketing: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400'
    };
    return colors[category] || 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400';
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
            onClick={onClose}
          />

          {/* Customizer Panel */}
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed inset-4 bg-white dark:bg-gray-900 rounded-2xl shadow-2xl z-50 overflow-hidden"
          >
            <div className="flex h-full">
              {/* Sidebar - Widget Library */}
              <div className="w-80 border-r border-gray-200 dark:border-gray-700 flex flex-col">
                {/* Sidebar Header */}
                <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                      <Grid className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div>
                      <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                        Конструктор дашборда
                      </h2>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        Перетащите виджеты на дашборд
                      </p>
                    </div>
                  </div>
                </div>

                {/* Widget Library */}
                <div className="flex-1 overflow-y-auto p-4">
                  <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-4">
                    Доступные виджеты
                  </h3>
                  
                  <Droppable droppableId="widget-library">
                    {(provided, snapshot) => (
                      <div
                        ref={provided.innerRef}
                        {...provided.droppableProps}
                        className={`space-y-2 min-h-[200px] p-2 rounded-lg border-2 border-dashed transition-colors ${
                          snapshot.isDraggingOver
                            ? 'border-red-300 bg-red-50 dark:border-red-700 dark:bg-red-900/20'
                            : 'border-gray-300 dark:border-gray-600'
                        }`}
                      >
                        {availableWidgets.map((widget, index) => (
                          <Draggable key={widget.id} draggableId={widget.id} index={index}>
                            {(provided, snapshot) => (
                              <div
                                ref={provided.innerRef}
                                {...provided.draggableProps}
                                {...provided.dragHandleProps}
                                className={`p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 cursor-move transition-all ${
                                  snapshot.isDragging
                                    ? 'shadow-lg scale-105 rotate-2'
                                    : 'hover:shadow-md'
                                }`}
                              >
                                <div className="flex items-start space-x-3">
                                  <div className="text-2xl">{widget.icon}</div>
                                  <div className="flex-1 min-w-0">
                                    <h4 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                                      {widget.name}
                                    </h4>
                                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                      {widget.description}
                                    </p>
                                    <span className={`inline-block px-2 py-1 rounded text-xs mt-2 ${getCategoryColor(widget.category)}`}>
                                      {widget.category}
                                    </span>
                                  </div>
                                  <button
                                    onClick={() => addWidget(widget)}
                                    className="p-1 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                                    title="Добавить виджет"
                                  >
                                    <Plus className="h-4 w-4" />
                                  </button>
                                </div>
                              </div>
                            )}
                          </Draggable>
                        ))}
                        {provided.placeholder}
                        
                        {availableWidgets.length === 0 && (
                          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                            <Grid className="h-8 w-8 mx-auto mb-2 opacity-50" />
                            <p className="text-sm">Все виджеты добавлены</p>
                          </div>
                        )}
                      </div>
                    )}
                  </Droppable>
                </div>
              </div>

              {/* Main Content - Dashboard Preview */}
              <div className="flex-1 flex flex-col">
                {/* Header */}
                <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        Предварительный просмотр дашборда
                      </h3>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {layout.length} виджетов • Перетащите для изменения порядка
                      </p>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => setPreviewMode(!previewMode)}
                        className={`p-2 rounded-lg transition-colors ${
                          previewMode 
                            ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                            : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'
                        }`}
                        title="Режим предварительного просмотра"
                      >
                        {previewMode ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Dashboard Grid */}
                <div className="flex-1 overflow-y-auto p-6">
                  <DragDropContext onDragEnd={handleDragEnd}>
                    <Droppable droppableId="dashboard">
                      {(provided, snapshot) => (
                        <div
                          ref={provided.innerRef}
                          {...provided.droppableProps}
                          className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 min-h-[400px] p-4 rounded-lg border-2 border-dashed transition-colors ${
                            snapshot.isDraggingOver
                              ? 'border-blue-300 bg-blue-50 dark:border-blue-700 dark:bg-blue-900/20'
                              : 'border-gray-300 dark:border-gray-600'
                          }`}
                        >
                          {layout.map((widget, index) => (
                            <Draggable key={widget.id} draggableId={widget.id} index={index}>
                              {(provided, snapshot) => (
                                <div
                                  ref={provided.innerRef}
                                  {...provided.draggableProps}
                                  className={`relative group ${
                                    widget.size.w === 2 ? 'md:col-span-2' : ''
                                  } ${
                                    widget.size.w === 3 ? 'lg:col-span-3' : ''
                                  } ${
                                    widget.size.h === 2 ? 'row-span-2' : ''
                                  } ${
                                    snapshot.isDragging
                                      ? 'scale-105 rotate-1 z-10'
                                      : ''
                                  } ${
                                    !widget.visible ? 'opacity-50' : ''
                                  }`}
                                >
                                  <GlassCard className="h-full p-4 transition-all duration-200">
                                    {/* Widget Header */}
                                    <div className="flex items-center justify-between mb-3">
                                      <div className="flex items-center space-x-2">
                                        <span className="text-lg">{getWidgetIcon(widget.type)}</span>
                                        <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                                          {widget.name}
                                        </h4>
                                      </div>
                                      
                                      {!previewMode && (
                                        <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                          <button
                                            {...provided.dragHandleProps}
                                            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 cursor-move"
                                            title="Переместить"
                                          >
                                            <Move className="h-4 w-4" />
                                          </button>
                                          
                                          <button
                                            onClick={() => toggleWidgetVisibility(widget.id)}
                                            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                                            title={widget.visible ? "Скрыть" : "Показать"}
                                          >
                                            {widget.visible ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
                                          </button>
                                          
                                          <button
                                            onClick={() => setSelectedWidget(widget)}
                                            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                                            title="Настроить"
                                          >
                                            <Settings className="h-4 w-4" />
                                          </button>
                                          
                                          <button
                                            onClick={() => removeWidget(widget.id)}
                                            className="p-1 text-gray-400 hover:text-red-500 dark:hover:text-red-400"
                                            title="Удалить"
                                          >
                                            <X className="h-4 w-4" />
                                          </button>
                                        </div>
                                      )}
                                    </div>

                                    {/* Widget Content Preview */}
                                    <div className="flex-1 flex items-center justify-center bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                                      <div className="text-center">
                                        <div className="text-3xl mb-2">{getWidgetIcon(widget.type)}</div>
                                        <p className="text-xs text-gray-500 dark:text-gray-400">
                                          Предварительный просмотр
                                        </p>
                                      </div>
                                    </div>
                                  </GlassCard>
                                </div>
                              )}
                            </Draggable>
                          ))}
                          {provided.placeholder}
                          
                          {layout.length === 0 && (
                            <div className="col-span-full text-center py-12 text-gray-500 dark:text-gray-400">
                              <Grid className="h-12 w-12 mx-auto mb-4 opacity-50" />
                              <h3 className="text-lg font-medium mb-2">Пустой дашборд</h3>
                              <p className="text-sm">
                                Перетащите виджеты из библиотеки слева для создания дашборда
                              </p>
                            </div>
                          )}
                        </div>
                      )}
                    </Droppable>
                  </DragDropContext>
                </div>

                {/* Footer */}
                <div className="border-t border-gray-200 dark:border-gray-700 p-6">
                  <div className="flex items-center justify-between">
                    <ModernButton
                      variant="glass-ghost"
                      size="sm"
                      onClick={resetLayout}
                      className="flex items-center space-x-2"
                    >
                      <RotateCcw className="h-4 w-4" />
                      <span>Очистить</span>
                    </ModernButton>

                    <div className="flex items-center space-x-3">
                      <ModernButton
                        variant="glass-ghost"
                        size="sm"
                        onClick={onClose}
                      >
                        Отмена
                      </ModernButton>
                      
                      <ModernButton
                        variant="glass-primary"
                        size="sm"
                        onClick={saveLayout}
                        className="flex items-center space-x-2"
                      >
                        <Save className="h-4 w-4" />
                        <span>Сохранить макет</span>
                      </ModernButton>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default DashboardCustomizer;