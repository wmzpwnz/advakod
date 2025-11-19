дальшеimport React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Kanban,
    Plus,
    MoreHorizontal,
    Edit,
    Trash2,
    Eye,
    Clock,
    Users,
    Flag,
    AlertTriangle,
    CheckCircle,
    Circle,
    Target,
    Zap,
    MessageSquare,
    Paperclip,
    Settings,
    Filter,
    Search
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import ModuleCard from './ModuleCard';
import EnhancedButton from './EnhancedButton';
import LoadingSpinner from './LoadingSpinner';

const KanbanBoard = ({
    projectId,
    sprintId,
    onTaskClick,
    onTaskUpdate,
    className = ''
}) => {
    const { getModuleColor } = useTheme();
    const [columns, setColumns] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [draggedTask, setDraggedTask] = useState(null);
    const [dragOverColumn, setDragOverColumn] = useState(null);

    useEffect(() => {
        loadKanbanData();
    }, [projectId, sprintId]);

    const loadKanbanData = async () => {
        try {
            setLoading(true);
            const token = localStorage.getItem('token');

            const params = new URLSearchParams();
            if (projectId) params.append('project_id', projectId);
            if (sprintId) params.append('sprint_id', sprintId);

            const response = await fetch(`/api/v1/project/kanban?${params}`, {
                headers: { Authorization: `Bearer ${token}` }
            });

            if (response.ok) {
                const data = await response.json();
                setColumns(data.columns || []);
            } else {
                // Fallback to mock data if API not available
                setColumns([
                    {
                        id: 'backlog',
                        name: 'Бэклог',
                        status: 'backlog',
                        color: 'gray',
                        wipLimit: null,
                        tasks: []
                    },
                    {
                        id: 'todo',
                        name: 'К выполнению',
                        status: 'todo',
                        color: 'blue',
                        wipLimit: 5,
                        tasks: []
                    },
                    {
                        id: 'in_progress',
                        name: 'В работе',
                        status: 'in_progress',
                        color: 'yellow',
                        wipLimit: 3,
                        tasks: []
                    },
                    {
                        id: 'review',
                        name: 'На проверке',
                        status: 'review',
                        color: 'purple',
                        wipLimit: 2,
                        tasks: []
                    },
                    {
                        id: 'done',
                        name: 'Выполнено',
                        status: 'done',
                        color: 'green',
                        wipLimit: null,
                        tasks: []
                    }
                ]);
            }
        } catch (err) {
            console.error('Error loading kanban data:', err);
            setError('Ошибка загрузки канбан-доски');
        } finally {
            setLoading(false);
        }
    };

    const handleDragStart = (e, task) => {
        setDraggedTask(task);
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/html', e.target.outerHTML);
    };

    const handleDragOver = (e, columnId) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        setDragOverColumn(columnId);
    };

    const handleDragLeave = (e) => {
        // Only clear if we're leaving the column entirely
        if (!e.currentTarget.contains(e.relatedTarget)) {
            setDragOverColumn(null);
        }
    };

    const handleDrop = async (e, columnStatus) => {
        e.preventDefault();
        setDragOverColumn(null);

        if (!draggedTask || draggedTask.status === columnStatus) {
            setDraggedTask(null);
            return;
        }

        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`/api/v1/project/tasks/${draggedTask.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({ status: columnStatus })
            });

            if (response.ok) {
                // Update local state optimistically
                setColumns(prev => {
                    const newColumns = prev.map(col => ({
                        ...col,
                        tasks: col.tasks.filter(t => t.id !== draggedTask.id)
                    }));

                    const targetColumn = newColumns.find(col => col.status === columnStatus);
                    if (targetColumn) {
                        targetColumn.tasks.push({ ...draggedTask, status: columnStatus });
                    }

                    return newColumns;
                });

                // Notify parent component
                if (onTaskUpdate) {
                    onTaskUpdate({ ...draggedTask, status: columnStatus });
                }
            } else {
                setError('Ошибка обновления статуса задачи');
            }
        } catch (err) {
            setError('Ошибка обновления статуса задачи');
        }

        setDraggedTask(null);
    };

    const getPriorityColor = (priority) => {
        const colors = {
            critical: 'bg-red-500',
            high: 'bg-orange-500',
            medium: 'bg-yellow-500',
            low: 'bg-green-500'
        };
        return colors[priority] || 'bg-gray-500';
    };

    const getPriorityIcon = (priority) => {
        const icons = {
            critical: <AlertTriangle className="h-3 w-3" />,
            high: <Flag className="h-3 w-3" />,
            medium: <Circle className="h-3 w-3" />,
            low: <CheckCircle className="h-3 w-3" />
        };
        return icons[priority] || <Circle className="h-3 w-3" />;
    };

    const getTypeIcon = (type) => {
        const icons = {
            feature: <Zap className="h-3 w-3" />,
            bug: <AlertTriangle className="h-3 w-3" />,
            improvement: <Target className="h-3 w-3" />,
            maintenance: <Settings className="h-3 w-3" />,
            research: <Search className="h-3 w-3" />,
            documentation: <MessageSquare className="h-3 w-3" />
        };
        return icons[type] || <Circle className="h-3 w-3" />;
    };

    const formatDate = (date) => {
        if (!date) return null;
        return new Date(date).toLocaleDateString('ru-RU', {
            day: '2-digit',
            month: '2-digit'
        });
    };

    const isOverdue = (dueDate) => {
        if (!dueDate) return false;
        return new Date(dueDate) < new Date();
    };

    const getColumnColor = (color) => {
        const colors = {
            gray: 'border-gray-300 dark:border-gray-600',
            blue: 'border-blue-300 dark:border-blue-600',
            yellow: 'border-yellow-300 dark:border-yellow-600',
            purple: 'border-purple-300 dark:border-purple-600',
            green: 'border-green-300 dark:border-green-600',
            red: 'border-red-300 dark:border-red-600'
        };
        return colors[color] || colors.gray;
    };

    const renderTaskCard = (task) => (
        <motion.div
            key={task.id}
            className="bg-white dark:bg-gray-800 rounded-lg p-3 shadow-sm border border-gray-200 dark:border-gray-700 cursor-pointer hover:shadow-md transition-all duration-200"
            draggable
            onDragStart={(e) => handleDragStart(e, task)}
            onClick={() => onTaskClick && onTaskClick(task)}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            layout
        >
            {/* Task Header */}
            <div className="flex items-start justify-between mb-2">
                <div className="flex items-center space-x-1">
                    <div className={`p-0.5 rounded ${getPriorityColor(task.priority)} text-white`}>
                        {getPriorityIcon(task.priority)}
                    </div>
                    <div className="text-gray-500">
                        {getTypeIcon(task.type)}
                    </div>
                </div>

                <div className="flex items-center space-x-1">
                    {task.due_date && (
                        <span className={`text-xs px-1.5 py-0.5 rounded ${isOverdue(task.due_date)
                                ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
                                : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                            }`}>
                            {formatDate(task.due_date)}
                        </span>
                    )}

                    <button className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity">
                        <MoreHorizontal className="h-3 w-3" />
                    </button>
                </div>
            </div>

            {/* Task Title */}
            <h4 className="font-medium text-sm text-gray-900 dark:text-gray-100 mb-2 line-clamp-2 leading-tight">
                {task.title}
            </h4>

            {/* Task Labels */}
            {task.labels && task.labels.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-2">
                    {task.labels.slice(0, 2).map((label, index) => (
                        <span key={index} className="text-xs px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded">
                            {label}
                        </span>
                    ))}
                    {task.labels.length > 2 && (
                        <span className="text-xs text-gray-500">+{task.labels.length - 2}</span>
                    )}
                </div>
            )}

            {/* Task Footer */}
            <div className="flex items-center justify-between text-xs text-gray-500">
                <div className="flex items-center space-x-2">
                    {task.assignee_name && (
                        <div className="flex items-center space-x-1">
                            <div className="w-4 h-4 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-medium">
                                {task.assignee_name.charAt(0).toUpperCase()}
                            </div>
                        </div>
                    )}

                    {task.estimated_hours && (
                        <div className="flex items-center space-x-1">
                            <Clock className="h-3 w-3" />
                            <span>{task.estimated_hours}ч</span>
                        </div>
                    )}
                </div>

                <div className="flex items-center space-x-1">
                    {task.comments_count > 0 && (
                        <div className="flex items-center space-x-1">
                            <MessageSquare className="h-3 w-3" />
                            <span>{task.comments_count}</span>
                        </div>
                    )}

                    {task.attachments_count > 0 && (
                        <div className="flex items-center space-x-1">
                            <Paperclip className="h-3 w-3" />
                            <span>{task.attachments_count}</span>
                        </div>
                    )}
                </div>
            </div>
        </motion.div>
    );

    const renderColumn = (column, index) => {
        const isOverWipLimit = column.wipLimit && column.tasks.length > column.wipLimit;
        const isDragOver = dragOverColumn === column.id;

        return (
            <motion.div
                key={column.id}
                className="flex-shrink-0 w-72"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
            >
                <div className={`h-full border-t-4 ${getColumnColor(column.color)} ${isDragOver ? 'bg-blue-50 dark:bg-blue-900/20' : ''
                    } transition-colors`}>
                    <ModuleCard module="project" variant="module" className="h-full">
                        {/* Column Header */}
                        <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-200 dark:border-gray-700">
                            <div className="flex items-center space-x-2">
                                <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-sm">
                                    {column.name}
                                </h3>
                                <span className="bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 text-xs px-2 py-1 rounded-full">
                                    {column.tasks?.length || 0}
                                </span>
                                {column.wipLimit && (
                                    <span className={`text-xs px-2 py-1 rounded-full ${isOverWipLimit
                                            ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
                                            : 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
                                        }`}>
                                        WIP: {column.tasks?.length || 0}/{column.wipLimit}
                                    </span>
                                )}
                            </div>

                            <button
                                onClick={() => {
                                    // Handle add task to column
                                    if (onTaskClick) {
                                        onTaskClick({ status: column.status, isNew: true });
                                    }
                                }}
                                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                            >
                                <Plus className="h-4 w-4" />
                            </button>
                        </div>

                        {/* Column Tasks */}
                        <div
                            className={`space-y-3 min-h-[400px] ${isDragOver ? 'bg-blue-50 dark:bg-blue-900/10 rounded-lg' : ''} transition-colors`}
                            onDragOver={(e) => handleDragOver(e, column.id)}
                            onDragLeave={handleDragLeave}
                            onDrop={(e) => handleDrop(e, column.status)}
                        >
                            <AnimatePresence>
                                {column.tasks?.map(task => (
                                    <div key={task.id} className="group">
                                        {renderTaskCard(task)}
                                    </div>
                                ))}
                            </AnimatePresence>

                            {(!column.tasks || column.tasks.length === 0) && (
                                <div className="text-center py-8 text-gray-400 dark:text-gray-500">
                                    <Circle className="h-8 w-8 mx-auto mb-2 opacity-50" />
                                    <p className="text-sm">Нет задач</p>
                                </div>
                            )}

                            {/* Drop zone indicator */}
                            {isDragOver && draggedTask && (
                                <motion.div
                                    className="border-2 border-dashed border-blue-400 bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 text-center text-blue-600 dark:text-blue-400"
                                    initial={{ opacity: 0, scale: 0.9 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    exit={{ opacity: 0, scale: 0.9 }}
                                >
                                    <Target className="h-6 w-6 mx-auto mb-2" />
                                    <p className="text-sm">Перетащите сюда</p>
                                </motion.div>
                            )}
                        </div>
                    </ModuleCard>
                </div>
            </motion.div>
        );
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center py-12">
                <LoadingSpinner
                    size="md"
                    module="project"
                    variant="neon"
                    text="Загрузка канбан-доски..."
                />
            </div>
        );
    }

    if (error) {
        return (
            <div className="text-center py-12">
                <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
                <p className="text-red-600 dark:text-red-400">{error}</p>
                <EnhancedButton
                    variant="module-outline"
                    module="project"
                    onClick={loadKanbanData}
                    className="mt-4"
                >
                    Попробовать снова
                </EnhancedButton>
            </div>
        );
    }

    return (
        <div className={`${className}`}>
            <div className="flex space-x-6 overflow-x-auto pb-6">
                {columns.map((column, index) => renderColumn(column, index))}
            </div>

            {/* Drag overlay */}
            {draggedTask && (
                <div className="fixed inset-0 pointer-events-none z-50">
                    <div className="absolute top-4 left-4 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 px-3 py-1 rounded-lg text-sm font-medium">
                        Перемещение: {draggedTask.title}
                    </div>
                </div>
            )}
        </div>
    );
};

export default KanbanBoard;