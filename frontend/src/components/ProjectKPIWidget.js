import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
    TrendingUp,
    TrendingDown,
    Target,
    Clock,
    Users,
    DollarSign,
    Activity,
    Award,
    AlertTriangle,
    CheckCircle,
    BarChart3,
    Zap,
    Calendar,
    ArrowUp,
    ArrowDown,
    Minus,
    Info
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import ModuleCard from './ModuleCard';

const ProjectKPIWidget = ({ kpiData, period = '30d', className = '' }) => {
    const { getModuleColor } = useTheme();
    const [selectedKPI, setSelectedKPI] = useState(null);

    const formatValue = (value, type) => {
        if (value === null || value === undefined) return 'N/A';

        switch (type) {
            case 'percentage':
                return `${value.toFixed(1)}%`;
            case 'currency':
                return new Intl.NumberFormat('ru-RU', {
                    style: 'currency',
                    currency: 'RUB'
                }).format(value);
            case 'hours':
                return `${value}ч`;
            case 'days':
                return `${value} дн.`;
            case 'number':
                return value.toLocaleString('ru-RU');
            default:
                return value;
        }
    };

    const getTrendIcon = (trend) => {
        if (trend > 0) return <ArrowUp className="h-4 w-4 text-green-500" />;
        if (trend < 0) return <ArrowDown className="h-4 w-4 text-red-500" />;
        return <Minus className="h-4 w-4 text-gray-500" />;
    };

    const getTrendColor = (trend) => {
        if (trend > 0) return 'text-green-600';
        if (trend < 0) return 'text-red-600';
        return 'text-gray-600';
    };

    const getHealthStatus = (value, target, type = 'higher_better') => {
        if (!target) return 'neutral';

        const ratio = value / target;

        if (type === 'higher_better') {
            if (ratio >= 1) return 'good';
            if (ratio >= 0.8) return 'warning';
            return 'critical';
        } else {
            if (ratio <= 1) return 'good';
            if (ratio <= 1.2) return 'warning';
            return 'critical';
        }
    };

    const getHealthIcon = (status) => {
        switch (status) {
            case 'good':
                return <CheckCircle className="h-5 w-5 text-green-500" />;
            case 'warning':
                return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
            case 'critical':
                return <AlertTriangle className="h-5 w-5 text-red-500" />;
            default:
                return <Info className="h-5 w-5 text-gray-500" />;
        }
    };

    const kpiMetrics = [
        {
            id: 'project_velocity',
            title: 'Скорость команды',
            value: kpiData?.velocity?.current || 0,
            target: kpiData?.velocity?.target || 0,
            trend: kpiData?.velocity?.trend || 0,
            type: 'number',
            icon: <Zap className="h-6 w-6" />,
            color: 'blue',
            description: 'Story points за спринт',
            healthType: 'higher_better'
        },
        {
            id: 'budget_utilization',
            title: 'Использование бюджета',
            value: kpiData?.budget?.utilization || 0,
            target: 100,
            trend: kpiData?.budget?.trend || 0,
            type: 'percentage',
            icon: <DollarSign className="h-6 w-6" />,
            color: 'green',
            description: 'Процент использованного бюджета',
            healthType: 'lower_better'
        },
        {
            id: 'team_utilization',
            title: 'Загрузка команды',
            value: kpiData?.team?.utilization || 0,
            target: 85,
            trend: kpiData?.team?.trend || 0,
            type: 'percentage',
            icon: <Users className="h-6 w-6" />,
            color: 'purple',
            description: 'Средняя загрузка участников команды',
            healthType: 'optimal'
        },
        {
            id: 'delivery_performance',
            title: 'Качество поставок',
            value: kpiData?.delivery?.onTime || 0,
            target: 90,
            trend: kpiData?.delivery?.trend || 0,
            type: 'percentage',
            icon: <Target className="h-6 w-6" />,
            color: 'orange',
            description: 'Процент задач, выполненных в срок',
            healthType: 'higher_better'
        },
        {
            id: 'code_quality',
            title: 'Качество кода',
            value: kpiData?.quality?.score || 0,
            target: 8.5,
            trend: kpiData?.quality?.trend || 0,
            type: 'number',
            icon: <Award className="h-6 w-6" />,
            color: 'indigo',
            description: 'Средний балл качества кода (1-10)',
            healthType: 'higher_better'
        },
        {
            id: 'cycle_time',
            title: 'Время цикла',
            value: kpiData?.cycleTime?.average || 0,
            target: kpiData?.cycleTime?.target || 0,
            trend: kpiData?.cycleTime?.trend || 0,
            type: 'days',
            icon: <Clock className="h-6 w-6" />,
            color: 'red',
            description: 'Среднее время от начала до завершения задачи',
            healthType: 'lower_better'
        }
    ];

    const getColorClasses = (color) => {
        const colors = {
            blue: {
                bg: 'bg-blue-100 dark:bg-blue-900/30',
                text: 'text-blue-600',
                icon: 'text-blue-600'
            },
            green: {
                bg: 'bg-green-100 dark:bg-green-900/30',
                text: 'text-green-600',
                icon: 'text-green-600'
            },
            purple: {
                bg: 'bg-purple-100 dark:bg-purple-900/30',
                text: 'text-purple-600',
                icon: 'text-purple-600'
            },
            orange: {
                bg: 'bg-orange-100 dark:bg-orange-900/30',
                text: 'text-orange-600',
                icon: 'text-orange-600'
            },
            indigo: {
                bg: 'bg-indigo-100 dark:bg-indigo-900/30',
                text: 'text-indigo-600',
                icon: 'text-indigo-600'
            },
            red: {
                bg: 'bg-red-100 dark:bg-red-900/30',
                text: 'text-red-600',
                icon: 'text-red-600'
            }
        };
        return colors[color] || colors.blue;
    };

    return (
        <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 ${className}`}>
            {kpiMetrics.map((metric, index) => {
                const colorClasses = getColorClasses(metric.color);
                const healthStatus = getHealthStatus(metric.value, metric.target, metric.healthType);

                return (
                    <motion.div
                        key={metric.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, delay: index * 0.1 }}
                    >
                        <ModuleCard
                            module="project"
                            variant="module"
                            className="cursor-pointer hover:shadow-lg transition-shadow"
                            onClick={() => setSelectedKPI(metric)}
                        >
                            <div className="flex items-start justify-between">
                                <div className="flex-1">
                                    <div className="flex items-center justify-between mb-3">
                                        <div className={`p-2 rounded-lg ${colorClasses.bg}`}>
                                            <div className={colorClasses.icon}>
                                                {metric.icon}
                                            </div>
                                        </div>
                                        <div className="flex items-center space-x-1">
                                            {getHealthIcon(healthStatus)}
                                            {getTrendIcon(metric.trend)}
                                        </div>
                                    </div>

                                    <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
                                        {metric.title}
                                    </h3>

                                    <div className="flex items-baseline space-x-2">
                                        <span className={`text-2xl font-bold ${colorClasses.text}`}>
                                            {formatValue(metric.value, metric.type)}
                                        </span>
                                        {metric.target && (
                                            <span className="text-sm text-gray-500">
                                                / {formatValue(metric.target, metric.type)}
                                            </span>
                                        )}
                                    </div>

                                    {metric.trend !== 0 && (
                                        <div className={`flex items-center mt-2 text-sm ${getTrendColor(metric.trend)}`}>
                                            {getTrendIcon(metric.trend)}
                                            <span className="ml-1">
                                                {Math.abs(metric.trend).toFixed(1)}% за {period === '7d' ? 'неделю' : period === '30d' ? 'месяц' : 'период'}
                                            </span>
                                        </div>
                                    )}

                                    <p className="text-xs text-gray-500 mt-2">
                                        {metric.description}
                                    </p>
                                </div>
                            </div>

                            {/* Progress bar for metrics with targets */}
                            {metric.target && (
                                <div className="mt-4">
                                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                                        <div
                                            className={`h-2 rounded-full transition-all duration-300 ${healthStatus === 'good'
                                                ? 'bg-green-500'
                                                : healthStatus === 'warning'
                                                    ? 'bg-yellow-500'
                                                    : 'bg-red-500'
                                                }`}
                                            style={{
                                                width: `${Math.min((metric.value / metric.target) * 100, 100)}%`
                                            }}
                                        />
                                    </div>
                                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                                        <span>0</span>
                                        <span>{formatValue(metric.target, metric.type)}</span>
                                    </div>
                                </div>
                            )}
                        </ModuleCard>
                    </motion.div>
                );
            })}

            {/* Detailed KPI Modal */}
            {selectedKPI && (
                <motion.div
                    className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    onClick={() => setSelectedKPI(null)}
                >
                    <motion.div
                        className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-2xl"
                        initial={{ scale: 0.9, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0.9, opacity: 0 }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="flex items-center justify-between mb-6">
                            <div className="flex items-center space-x-3">
                                <div className={`p-3 rounded-lg ${getColorClasses(selectedKPI.color).bg}`}>
                                    <div className={getColorClasses(selectedKPI.color).icon}>
                                        {selectedKPI.icon}
                                    </div>
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                                        {selectedKPI.title}
                                    </h2>
                                    <p className="text-gray-600 dark:text-gray-400">
                                        {selectedKPI.description}
                                    </p>
                                </div>
                            </div>
                            <button
                                onClick={() => setSelectedKPI(null)}
                                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                            >
                                ×
                            </button>
                        </div>

                        <div className="grid grid-cols-2 gap-6 mb-6">
                            <div className="space-y-4">
                                <div>
                                    <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                                        Текущее значение
                                    </h3>
                                    <p className={`text-3xl font-bold ${getColorClasses(selectedKPI.color).text}`}>
                                        {formatValue(selectedKPI.value, selectedKPI.type)}
                                    </p>
                                </div>

                                {selectedKPI.target && (
                                    <div>
                                        <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                                            Целевое значение
                                        </h3>
                                        <p className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                                            {formatValue(selectedKPI.target, selectedKPI.type)}
                                        </p>
                                    </div>
                                )}
                            </div>

                            <div className="space-y-4">
                                <div>
                                    <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                                        Тренд
                                    </h3>
                                    <div className={`flex items-center text-lg font-semibold ${getTrendColor(selectedKPI.trend)}`}>
                                        {getTrendIcon(selectedKPI.trend)}
                                        <span className="ml-2">
                                            {selectedKPI.trend > 0 ? '+' : ''}{selectedKPI.trend.toFixed(1)}%
                                        </span>
                                    </div>
                                </div>

                                <div>
                                    <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                                        Статус
                                    </h3>
                                    <div className="flex items-center">
                                        {getHealthIcon(getHealthStatus(selectedKPI.value, selectedKPI.target, selectedKPI.healthType))}
                                        <span className="ml-2 font-medium">
                                            {getHealthStatus(selectedKPI.value, selectedKPI.target, selectedKPI.healthType) === 'good'
                                                ? 'Отлично'
                                                : getHealthStatus(selectedKPI.value, selectedKPI.target, selectedKPI.healthType) === 'warning'
                                                    ? 'Требует внимания'
                                                    : 'Критично'
                                            }
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {selectedKPI.target && (
                            <div className="mb-6">
                                <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">
                                    Прогресс к цели
                                </h3>
                                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
                                    <div
                                        className={`h-4 rounded-full transition-all duration-500 ${getHealthStatus(selectedKPI.value, selectedKPI.target, selectedKPI.healthType) === 'good'
                                            ? 'bg-green-500'
                                            : getHealthStatus(selectedKPI.value, selectedKPI.target, selectedKPI.healthType) === 'warning'
                                                ? 'bg-yellow-500'
                                                : 'bg-red-500'
                                            }`}
                                        style={{
                                            width: `${Math.min((selectedKPI.value / selectedKPI.target) * 100, 100)}%`
                                        }}
                                    />
                                </div>
                                <div className="flex justify-between text-sm text-gray-500 mt-2">
                                    <span>0</span>
                                    <span className="font-medium">
                                        {((selectedKPI.value / selectedKPI.target) * 100).toFixed(1)}% достигнуто
                                    </span>
                                    <span>{formatValue(selectedKPI.target, selectedKPI.type)}</span>
                                </div>
                            </div>
                        )}

                        <div className="flex justify-end space-x-4">
                            <button
                                onClick={() => setSelectedKPI(null)}
                                className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100"
                            >
                                Закрыть
                            </button>
                            <button className={`px-4 py-2 rounded-lg font-medium ${getColorClasses(selectedKPI.color).bg} ${getColorClasses(selectedKPI.color).text}`}>
                                Подробный отчет
                            </button>
                        </div>
                    </motion.div>
                </motion.div>
            )}
        </div>
    );
};

export default ProjectKPIWidget;