import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Calendar,
  ChevronLeft,
  ChevronRight,
  Plus,
  Clock,
  Target,
  Users,
  AlertTriangle,
  CheckCircle,
  Filter,
  Eye,
  Edit,
  Trash2,
  MoreHorizontal
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import ModuleCard from './ModuleCard';
import EnhancedButton from './EnhancedButton';
import LoadingSpinner from './LoadingSpinner';

const ProjectCalendar = () => {
  const { getModuleColor } = useTheme();
  const [currentDate, setCurrentDate] = useState(new Date());
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [viewMode, setViewMode] = useState('month'); // month, week, day
  const [filters, setFilters] = useState({
    projects: [],
    types: ['milestone', 'deadline', 'sprint', 'meeting'],
    priorities: ['high', 'medium', 'low']
  });

  useEffect(() => {
    loadCalendarEvents();
  }, [currentDate, viewMode, filters]);

  const loadCalendarEvents = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const params = new URLSearchParams({
        date: currentDate.toISOString(),
        view: viewMode,
        types: filters.types.join(','),
        priorities: filters.priorities.join(',')
      });

      if (filters.projects.length > 0) {
        params.append('projects', filters.projects.join(','));
      }
      
      const response = await fetch(`/api/v1/project/calendar/events?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setEvents(data);
      }
    } catch (err) {
      console.error('Error loading calendar events:', err);
    } finally {
      setLoading(false);
    }
  };

  const navigateDate = (direction) => {
    const newDate = new Date(currentDate);
    
    switch (viewMode) {
      case 'month':
        newDate.setMonth(newDate.getMonth() + direction);
        break;
      case 'week':
        newDate.setDate(newDate.getDate() + (direction * 7));
        break;
      case 'day':
        newDate.setDate(newDate.getDate() + direction);
        break;
    }
    
    setCurrentDate(newDate);
  };

  const getEventTypeColor = (type) => {
    const colors = {
      milestone: 'bg-purple-500',
      deadline: 'bg-red-500',
      sprint: 'bg-blue-500',
      meeting: 'bg-green-500',
      task: 'bg-yellow-500'
    };
    return colors[type] || 'bg-gray-500';
  };

  const getEventTypeIcon = (type) => {
    const icons = {
      milestone: <Target className="h-4 w-4" />,
      deadline: <Clock className="h-4 w-4" />,
      sprint: <Users className="h-4 w-4" />,
      meeting: <Calendar className="h-4 w-4" />,
      task: <CheckCircle className="h-4 w-4" />
    };
    return icons[type] || <Calendar className="h-4 w-4" />;
  };

  const getPriorityColor = (priority) => {
    const colors = {
      high: 'border-red-500',
      medium: 'border-yellow-500',
      low: 'border-green-500'
    };
    return colors[priority] || 'border-gray-500';
  };

  const formatDateHeader = () => {
    const options = {
      month: 'long',
      year: 'numeric'
    };
    
    if (viewMode === 'week') {
      const weekStart = new Date(currentDate);
      weekStart.setDate(currentDate.getDate() - currentDate.getDay());
      const weekEnd = new Date(weekStart);
      weekEnd.setDate(weekStart.getDate() + 6);
      
      return `${weekStart.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })} - ${weekEnd.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' })}`;
    } else if (viewMode === 'day') {
      return currentDate.toLocaleDateString('ru-RU', { 
        weekday: 'long', 
        day: 'numeric', 
        month: 'long', 
        year: 'numeric' 
      });
    }
    
    return currentDate.toLocaleDateString('ru-RU', options);
  };

  const renderMonthView = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startDate = new Date(firstDay);
    startDate.setDate(startDate.getDate() - firstDay.getDay());
    
    const days = [];
    const currentDay = new Date(startDate);
    
    for (let i = 0; i < 42; i++) {
      const dayEvents = events.filter(event => {
        const eventDate = new Date(event.date);
        return eventDate.toDateString() === currentDay.toDateString();
      });
      
      days.push({
        date: new Date(currentDay),
        isCurrentMonth: currentDay.getMonth() === month,
        isToday: currentDay.toDateString() === new Date().toDateString(),
        events: dayEvents
      });
      
      currentDay.setDate(currentDay.getDate() + 1);
    }

    return (
      <div className="grid grid-cols-7 gap-1">
        {/* Week headers */}
        {['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'].map(day => (
          <div key={day} className="p-2 text-center text-sm font-medium text-gray-500 dark:text-gray-400">
            {day}
          </div>
        ))}
        
        {/* Calendar days */}
        {days.map((day, index) => (
          <motion.div
            key={index}
            className={`min-h-[100px] p-2 border border-gray-200 dark:border-gray-700 ${
              day.isCurrentMonth 
                ? 'bg-white dark:bg-gray-800' 
                : 'bg-gray-50 dark:bg-gray-900'
            } ${
              day.isToday 
                ? 'ring-2 ring-blue-500' 
                : ''
            } hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors cursor-pointer`}
            whileHover={{ scale: 1.02 }}
            onClick={() => {
              setCurrentDate(day.date);
              setViewMode('day');
            }}
          >
            <div className={`text-sm font-medium mb-1 ${
              day.isCurrentMonth 
                ? day.isToday 
                  ? 'text-blue-600' 
                  : 'text-gray-900 dark:text-gray-100'
                : 'text-gray-400'
            }`}>
              {day.date.getDate()}
            </div>
            
            <div className="space-y-1">
              {day.events.slice(0, 3).map((event, eventIndex) => (
                <div
                  key={eventIndex}
                  className={`text-xs p-1 rounded truncate ${getEventTypeColor(event.type)} text-white cursor-pointer`}
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedEvent(event);
                  }}
                  title={event.title}
                >
                  {event.title}
                </div>
              ))}
              {day.events.length > 3 && (
                <div className="text-xs text-gray-500 text-center">
                  +{day.events.length - 3} еще
                </div>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    );
  };

  const renderWeekView = () => {
    const weekStart = new Date(currentDate);
    weekStart.setDate(currentDate.getDate() - currentDate.getDay());
    
    const weekDays = [];
    for (let i = 0; i < 7; i++) {
      const day = new Date(weekStart);
      day.setDate(weekStart.getDate() + i);
      
      const dayEvents = events.filter(event => {
        const eventDate = new Date(event.date);
        return eventDate.toDateString() === day.toDateString();
      });
      
      weekDays.push({
        date: day,
        events: dayEvents,
        isToday: day.toDateString() === new Date().toDateString()
      });
    }

    return (
      <div className="grid grid-cols-7 gap-4">
        {weekDays.map((day, index) => (
          <div key={index} className="space-y-2">
            <div className={`text-center p-2 rounded-lg ${
              day.isToday 
                ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600' 
                : 'bg-gray-100 dark:bg-gray-800'
            }`}>
              <div className="text-sm font-medium">
                {day.date.toLocaleDateString('ru-RU', { weekday: 'short' })}
              </div>
              <div className="text-lg font-bold">
                {day.date.getDate()}
              </div>
            </div>
            
            <div className="space-y-2 min-h-[300px]">
              {day.events.map((event, eventIndex) => (
                <motion.div
                  key={eventIndex}
                  className={`p-2 rounded-lg border-l-4 ${getPriorityColor(event.priority)} bg-white dark:bg-gray-800 shadow-sm cursor-pointer`}
                  whileHover={{ scale: 1.02 }}
                  onClick={() => setSelectedEvent(event)}
                >
                  <div className="flex items-center space-x-2 mb-1">
                    <div className={`p-1 rounded ${getEventTypeColor(event.type)} text-white`}>
                      {getEventTypeIcon(event.type)}
                    </div>
                    <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {event.title}
                    </span>
                  </div>
                  
                  {event.time && (
                    <div className="text-xs text-gray-500 flex items-center">
                      <Clock className="h-3 w-3 mr-1" />
                      {event.time}
                    </div>
                  )}
                  
                  {event.project && (
                    <div className="text-xs text-blue-600 mt-1">
                      {event.project}
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderDayView = () => {
    const dayEvents = events.filter(event => {
      const eventDate = new Date(event.date);
      return eventDate.toDateString() === currentDate.toDateString();
    });

    const hours = Array.from({ length: 24 }, (_, i) => i);

    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 gap-4">
          {dayEvents.length === 0 ? (
            <div className="text-center py-12">
              <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">Нет событий на этот день</p>
            </div>
          ) : (
            dayEvents.map((event, index) => (
              <motion.div
                key={index}
                className={`p-4 rounded-lg border-l-4 ${getPriorityColor(event.priority)} bg-white dark:bg-gray-800 shadow-sm`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <div className={`p-2 rounded ${getEventTypeColor(event.type)} text-white`}>
                        {getEventTypeIcon(event.type)}
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                          {event.title}
                        </h3>
                        {event.project && (
                          <p className="text-sm text-blue-600">{event.project}</p>
                        )}
                      </div>
                    </div>
                    
                    {event.description && (
                      <p className="text-gray-600 dark:text-gray-400 mb-3">
                        {event.description}
                      </p>
                    )}
                    
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      {event.time && (
                        <div className="flex items-center">
                          <Clock className="h-4 w-4 mr-1" />
                          {event.time}
                        </div>
                      )}
                      
                      {event.assignees && event.assignees.length > 0 && (
                        <div className="flex items-center">
                          <Users className="h-4 w-4 mr-1" />
                          {event.assignees.length} участников
                        </div>
                      )}
                      
                      {event.priority && (
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          event.priority === 'high' 
                            ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                            : event.priority === 'medium'
                              ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300'
                              : 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                        }`}>
                          {event.priority === 'high' ? 'Высокий' : event.priority === 'medium' ? 'Средний' : 'Низкий'}
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setSelectedEvent(event)}
                      className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    >
                      <Eye className="h-4 w-4" />
                    </button>
                    <button className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                      <Edit className="h-4 w-4" />
                    </button>
                    <button className="p-2 text-gray-400 hover:text-red-600">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </motion.div>
            ))
          )}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <LoadingSpinner 
          size="lg" 
          module="project" 
          variant="neon"
          text="Загрузка календаря..."
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <motion.div 
          className="mb-8"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 flex items-center">
                <Calendar className="h-8 w-8 text-blue-500 mr-3" />
                Календарь проекта
              </h1>
              <p className="mt-2 text-gray-600 dark:text-gray-400">
                События, дедлайны и планирование проекта
              </p>
            </div>
            
            <div className="mt-6 lg:mt-0 flex flex-wrap gap-3">
              <EnhancedButton
                variant="module-outline"
                module="project"
                icon={<Filter className="h-4 w-4" />}
              >
                Фильтры
              </EnhancedButton>
              
              <EnhancedButton
                variant="module"
                module="project"
                icon={<Plus className="h-4 w-4" />}
              >
                Добавить событие
              </EnhancedButton>
            </div>
          </div>
        </motion.div>

        {/* Calendar Controls */}
        <motion.div
          className="mb-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <ModuleCard module="project" variant="module">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => navigateDate(-1)}
                  className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  <ChevronLeft className="h-5 w-5" />
                </button>
                
                <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                  {formatDateHeader()}
                </h2>
                
                <button
                  onClick={() => navigateDate(1)}
                  className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  <ChevronRight className="h-5 w-5" />
                </button>
                
                <EnhancedButton
                  variant="module-outline"
                  module="project"
                  size="sm"
                  onClick={() => setCurrentDate(new Date())}
                >
                  Сегодня
                </EnhancedButton>
              </div>
              
              <div className="flex items-center space-x-2">
                {['month', 'week', 'day'].map((mode) => (
                  <button
                    key={mode}
                    onClick={() => setViewMode(mode)}
                    className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                      viewMode === mode
                        ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600'
                        : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
                    }`}
                  >
                    {mode === 'month' ? 'Месяц' : mode === 'week' ? 'Неделя' : 'День'}
                  </button>
                ))}
              </div>
            </div>
          </ModuleCard>
        </motion.div>

        {/* Calendar Content */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <ModuleCard module="project" variant="module">
            {viewMode === 'month' && renderMonthView()}
            {viewMode === 'week' && renderWeekView()}
            {viewMode === 'day' && renderDayView()}
          </ModuleCard>
        </motion.div>

        {/* Event Details Modal */}
        <AnimatePresence>
          {selectedEvent && (
            <motion.div
              className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <motion.div
                className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto"
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
              >
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded ${getEventTypeColor(selectedEvent.type)} text-white`}>
                      {getEventTypeIcon(selectedEvent.type)}
                    </div>
                    <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                      {selectedEvent.title}
                    </h2>
                  </div>
                  <button
                    onClick={() => setSelectedEvent(null)}
                    className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                  >
                    ×
                  </button>
                </div>

                <div className="space-y-4">
                  {selectedEvent.description && (
                    <div>
                      <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Описание</h3>
                      <p className="text-gray-600 dark:text-gray-400">{selectedEvent.description}</p>
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Дата</h3>
                      <p className="text-gray-600 dark:text-gray-400">
                        {new Date(selectedEvent.date).toLocaleDateString('ru-RU')}
                      </p>
                    </div>

                    {selectedEvent.time && (
                      <div>
                        <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Время</h3>
                        <p className="text-gray-600 dark:text-gray-400">{selectedEvent.time}</p>
                      </div>
                    )}

                    {selectedEvent.project && (
                      <div>
                        <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Проект</h3>
                        <p className="text-blue-600">{selectedEvent.project}</p>
                      </div>
                    )}

                    <div>
                      <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Приоритет</h3>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        selectedEvent.priority === 'high' 
                          ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                          : selectedEvent.priority === 'medium'
                            ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300'
                            : 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                      }`}>
                        {selectedEvent.priority === 'high' ? 'Высокий' : selectedEvent.priority === 'medium' ? 'Средний' : 'Низкий'}
                      </span>
                    </div>
                  </div>

                  {selectedEvent.assignees && selectedEvent.assignees.length > 0 && (
                    <div>
                      <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Участники</h3>
                      <div className="flex flex-wrap gap-2">
                        {selectedEvent.assignees.map((assignee, index) => (
                          <span key={index} className="px-3 py-1 bg-gray-100 dark:bg-gray-700 rounded-full text-sm">
                            {assignee.name}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex justify-end space-x-4 mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
                  <EnhancedButton
                    variant="outline"
                    onClick={() => setSelectedEvent(null)}
                  >
                    Закрыть
                  </EnhancedButton>
                  <EnhancedButton
                    variant="module"
                    module="project"
                    icon={<Edit className="h-4 w-4" />}
                  >
                    Редактировать
                  </EnhancedButton>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default ProjectCalendar;