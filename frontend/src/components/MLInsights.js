import React, { useState, useEffect } from 'react';
import {
  SparklesIcon,
  LightBulbIcon,
  ChartBarIcon,
  UserIcon,
  CurrencyDollarIcon,
  ExclamationTriangleIcon,
  ArrowTrendingUpIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import LoadingSpinner from './LoadingSpinner';

const MLInsights = () => {
  const [insights, setInsights] = useState([]);
  const [loading, setLoading] = useState(false);
  const [recommendations, setRecommendations] = useState([]);

  const generateInsights = async (context = {}) => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/ml/insights', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(context)
      });

      if (!response.ok) {
        throw new Error('Failed to generate insights');
      }

      const data = await response.json();
      setInsights(data.insights || []);
      toast.success('Insights generated successfully');
    } catch (error) {
      console.error('Error generating insights:', error);
      toast.error('Failed to generate insights');
    } finally {
      setLoading(false);
    }
  };

  const generateRecommendations = async (context = {}) => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/ml/recommendations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(context || {})
      });

      if (!response.ok) {
        throw new Error('Failed to generate recommendations');
      }

      const data = await response.json();
      setRecommendations(data.recommendations || []);
      toast.success('Recommendations generated successfully');
    } catch (error) {
      console.error('Error generating recommendations:', error);
      toast.error('Failed to generate recommendations');
    } finally {
      setLoading(false);
    }
  };

  const getInsightIcon = (type) => {
    const icons = {
      'performance': ChartBarIcon,
      'user_behavior': UserIcon,
      'ltv': CurrencyDollarIcon,
      'churn': ExclamationTriangleIcon,
      'conversion': ArrowTrendingUpIcon,
      'engagement': UserIcon,
      'revenue': ChartBarIcon
    };

    const IconComponent = icons[type] || SparklesIcon;
    return <IconComponent className="h-6 w-6" />;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          ML Insights
        </h2>
        <div className="flex space-x-3">
          <button
            onClick={() => generateInsights()}
            disabled={loading}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {loading ? (
              <ArrowPathIcon className="animate-spin -ml-1 mr-3 h-5 w-5" />
            ) : (
              <SparklesIcon className="-ml-1 mr-3 h-5 w-5" />
            )}
            Generate Insights
          </button>
          <button
            onClick={() => generateRecommendations()}
            disabled={loading}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
          >
            {loading ? (
              <ArrowPathIcon className="animate-spin -ml-1 mr-3 h-5 w-5" />
            ) : (
              <LightBulbIcon className="-ml-1 mr-3 h-5 w-5" />
            )}
            Get Recommendations
          </button>
        </div>
      </div>

      {loading && (
        <div className="flex justify-center py-8">
          <LoadingSpinner />
        </div>
      )}

      {insights.length > 0 && (
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Generated Insights
          </h3>
          <div className="space-y-4">
            {insights.map((insight, index) => (
              <div key={index} className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  {getInsightIcon(insight.type)}
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                    {insight.title}
                  </h4>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {insight.description}
                  </p>
                  {insight.confidence && (
                    <div className="mt-2">
                      <div className="flex items-center">
                        <span className="text-xs text-gray-500 dark:text-gray-400 mr-2">
                          Confidence:
                        </span>
                        <div className="w-20 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${insight.confidence * 100}%` }}
                          ></div>
                        </div>
                        <span className="text-xs text-gray-500 dark:text-gray-400 ml-2">
                          {Math.round(insight.confidence * 100)}%
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {recommendations.length > 0 && (
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Recommendations
          </h3>
          <div className="space-y-4">
            {recommendations.map((rec, index) => (
              <div key={index} className="border-l-4 border-green-400 pl-4">
                <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                  {rec.title}
                </h4>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {rec.description}
                </p>
                {rec.impact && (
                  <div className="mt-2">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      Expected Impact: {rec.impact}
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default MLInsights;