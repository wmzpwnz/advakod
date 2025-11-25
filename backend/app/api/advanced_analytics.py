"""
API для продвинутой аналитики и отчетности
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging

from ..core.database import get_db
from ..services.auth_service import auth_service
from ..services.analytics_service import analytics_service
from ..services.cohort_analysis_service import cohort_analysis_service
from ..services.metrics_service import metrics_service
from ..services.ml_service import ml_service
from ..models.user import User
from ..schemas.analytics import (
    Dashboard, DashboardCreate, DashboardUpdate,
    DashboardWidget, DashboardWidgetCreate, DashboardWidgetUpdate,
    CustomMetric, CustomMetricCreate, CustomMetricUpdate,
    MetricAlert, MetricAlertCreate, MetricAlertUpdate,
    CohortAnalysis, CohortAnalysisCreate,
    UserSegment, UserSegmentCreate, UserSegmentUpdate,
    MLPrediction, ReportTemplate, ReportExecution,
    DataSourceInfo, WidgetData, DashboardBuilderResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/advanced-analytics", tags=["Advanced Analytics"])


# Dashboard Builder Endpoints
@router.get("/dashboard-builder", response_model=DashboardBuilderResponse)
async def get_dashboard_builder_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Получение данных для конструктора дашбордов"""
    try:
        # Получаем дашборды пользователя
        dashboards = await analytics_service.get_dashboards(db, current_user.id)
        
        # Получаем источники данных
        data_sources = analytics_service.get_data_sources()
        
        # Получаем шаблоны виджетов
        widget_templates = analytics_service.get_widget_templates()
        
        return DashboardBuilderResponse(
            dashboards=dashboards,
            data_sources=data_sources,
            widget_templates=widget_templates,
            total=len(dashboards)
        )
        
    except Exception as e:
        logger.error(f"Error getting dashboard builder data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard builder data")


@router.get("/dashboards", response_model=List[Dashboard])
async def get_dashboards(
    include_public: bool = Query(True, description="Включать публичные дашборды"),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Получение списка дашбордов"""
    try:
        dashboards = await analytics_service.get_dashboards(db, current_user.id, include_public)
        return dashboards
        
    except Exception as e:
        logger.error(f"Error getting dashboards: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboards")


@router.post("/dashboards", response_model=Dashboard)
async def create_dashboard(
    dashboard_data: DashboardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Создание нового дашборда"""
    try:
        dashboard = await analytics_service.create_dashboard(db, dashboard_data, current_user.id)
        return dashboard
        
    except Exception as e:
        logger.error(f"Error creating dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to create dashboard")


@router.get("/dashboards/{dashboard_id}", response_model=Dashboard)
async def get_dashboard(
    dashboard_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Получение дашборда по ID"""
    try:
        dashboard = await analytics_service.get_dashboard(db, dashboard_id, current_user.id)
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        return dashboard
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dashboard {dashboard_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard")


@router.put("/dashboards/{dashboard_id}", response_model=Dashboard)
async def update_dashboard(
    dashboard_id: int,
    dashboard_data: DashboardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Обновление дашборда"""
    try:
        dashboard = await analytics_service.update_dashboard(db, dashboard_id, dashboard_data, current_user.id)
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        return dashboard
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating dashboard {dashboard_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update dashboard")


@router.delete("/dashboards/{dashboard_id}")
async def delete_dashboard(
    dashboard_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Удаление дашборда"""
    try:
        success = await analytics_service.delete_dashboard(db, dashboard_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        return {"message": "Dashboard deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting dashboard {dashboard_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete dashboard")


# Widget Endpoints
@router.post("/dashboards/{dashboard_id}/widgets", response_model=DashboardWidget)
async def create_widget(
    dashboard_id: int,
    widget_data: DashboardWidgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Создание виджета в дашборде"""
    try:
        widget = await analytics_service.create_widget(db, widget_data, dashboard_id, current_user.id)
        if not widget:
            raise HTTPException(status_code=404, detail="Dashboard not found or access denied")
        
        return widget
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating widget: {e}")
        raise HTTPException(status_code=500, detail="Failed to create widget")


@router.put("/widgets/{widget_id}", response_model=DashboardWidget)
async def update_widget(
    widget_id: int,
    widget_data: DashboardWidgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Обновление виджета"""
    try:
        widget = await analytics_service.update_widget(db, widget_id, widget_data, current_user.id)
        if not widget:
            raise HTTPException(status_code=404, detail="Widget not found")
        
        return widget
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating widget {widget_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update widget")


@router.delete("/widgets/{widget_id}")
async def delete_widget(
    widget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Удаление виджета"""
    try:
        success = await analytics_service.delete_widget(db, widget_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Widget not found")
        
        return {"message": "Widget deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting widget {widget_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete widget")


@router.get("/widgets/{widget_id}/data", response_model=WidgetData)
async def get_widget_data(
    widget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Получение данных для виджета"""
    try:
        # Получаем виджет
        from ..models.analytics import DashboardWidget, Dashboard
        widget = db.query(DashboardWidget).join(Dashboard).filter(
            DashboardWidget.id == widget_id,
            Dashboard.user_id == current_user.id
        ).first()
        
        if not widget:
            raise HTTPException(status_code=404, detail="Widget not found")
        
        # Получаем данные
        data = await analytics_service.get_widget_data(db, widget)
        return data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting widget data {widget_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get widget data")


# Data Sources Endpoints
@router.get("/data-sources", response_model=List[DataSourceInfo])
async def get_data_sources(
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Получение списка источников данных"""
    try:
        data_sources = analytics_service.get_data_sources()
        return data_sources
        
    except Exception as e:
        logger.error(f"Error getting data sources: {e}")
        raise HTTPException(status_code=500, detail="Failed to get data sources")


@router.get("/widget-templates")
async def get_widget_templates(
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Получение шаблонов виджетов"""
    try:
        templates = analytics_service.get_widget_templates()
        return templates
        
    except Exception as e:
        logger.error(f"Error getting widget templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to get widget templates")


# Preview endpoint for testing widgets
@router.post("/widgets/preview", response_model=WidgetData)
async def preview_widget(
    widget_config: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Предварительный просмотр виджета"""
    try:
        # Создаем временный виджет для предварительного просмотра
        from ..models.analytics import DashboardWidget
        temp_widget = DashboardWidget(
            widget_type=widget_config.get('widget_type', 'metric'),
            title=widget_config.get('title', 'Preview'),
            config=widget_config.get('config', {}),
            data_source=widget_config.get('data_source', 'users')
        )
        
        # Получаем данные
        data = await analytics_service.get_widget_data(db, temp_widget)
        return data
        
    except Exception as e:
        logger.error(f"Error previewing widget: {e}")
        raise HTTPException(status_code=500, detail="Failed to preview widget")


# Dashboard export/import
@router.get("/dashboards/{dashboard_id}/export")
async def export_dashboard(
    dashboard_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Экспорт дашборда"""
    try:
        dashboard = await analytics_service.get_dashboard(db, dashboard_id, current_user.id)
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        # Экспортируем конфигурацию дашборда
        export_data = {
            "name": dashboard.name,
            "description": dashboard.description,
            "layout": dashboard.layout,
            "widgets": [
                {
                    "widget_type": widget.widget_type,
                    "title": widget.title,
                    "config": widget.config,
                    "position": widget.position,
                    "data_source": widget.data_source,
                    "refresh_interval": widget.refresh_interval
                }
                for widget in dashboard.widgets
            ]
        }
        
        return export_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting dashboard {dashboard_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to export dashboard")


@router.post("/dashboards/import", response_model=Dashboard)
async def import_dashboard(
    import_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Импорт дашборда"""
    try:
        # Создаем дашборд
        dashboard_data = DashboardCreate(
            name=import_data.get('name', 'Imported Dashboard'),
            description=import_data.get('description'),
            layout=import_data.get('layout', {}),
            is_public=False,
            is_default=False
        )
        
        dashboard = await analytics_service.create_dashboard(db, dashboard_data, current_user.id)
        
        # Создаем виджеты
        for widget_data in import_data.get('widgets', []):
            widget_create = DashboardWidgetCreate(
                widget_type=widget_data.get('widget_type', 'metric'),
                title=widget_data.get('title', 'Imported Widget'),
                config=widget_data.get('config', {}),
                position=widget_data.get('position', {'x': 0, 'y': 0, 'w': 4, 'h': 3}),
                data_source=widget_data.get('data_source', 'users'),
                refresh_interval=widget_data.get('refresh_interval', 300)
            )
            
            await analytics_service.create_widget(db, widget_create, dashboard.id, current_user.id)
        
        # Обновляем дашборд с виджетами
        updated_dashboard = await analytics_service.get_dashboard(db, dashboard.id, current_user.id)
        return updated_dashboard
        
    except Exception as e:
        logger.error(f"Error importing dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to import dashboard")


# Cohort Analysis Endpoints
@router.get("/cohort-analysis", response_model=List[CohortAnalysis])
async def get_cohort_analyses(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Получение списка когортных анализов"""
    try:
        analyses = await cohort_analysis_service.get_cohort_analyses(db, current_user.id)
        return analyses
        
    except Exception as e:
        logger.error(f"Error getting cohort analyses: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cohort analyses")


@router.post("/cohort-analysis", response_model=CohortAnalysis)
async def create_cohort_analysis(
    cohort_data: CohortAnalysisCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Создание когортного анализа"""
    try:
        analysis = await cohort_analysis_service.create_cohort_analysis(db, cohort_data, current_user.id)
        return analysis
        
    except Exception as e:
        logger.error(f"Error creating cohort analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to create cohort analysis")


@router.get("/cohort-analysis/{analysis_id}", response_model=CohortAnalysis)
async def get_cohort_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Получение когортного анализа по ID"""
    try:
        analysis = await cohort_analysis_service.get_cohort_analysis(db, analysis_id, current_user.id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Cohort analysis not found")
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cohort analysis {analysis_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cohort analysis")


@router.put("/cohort-analysis/{analysis_id}", response_model=CohortAnalysis)
async def update_cohort_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Обновление когортного анализа"""
    try:
        analysis = await cohort_analysis_service.update_cohort_analysis(db, analysis_id, current_user.id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Cohort analysis not found")
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating cohort analysis {analysis_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update cohort analysis")


@router.delete("/cohort-analysis/{analysis_id}")
async def delete_cohort_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Удаление когортного анализа"""
    try:
        success = await cohort_analysis_service.delete_cohort_analysis(db, analysis_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Cohort analysis not found")
        
        return {"message": "Cohort analysis deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting cohort analysis {analysis_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete cohort analysis")


# User Segmentation Endpoints
@router.get("/user-segments", response_model=List[UserSegment])
async def get_user_segments(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Получение списка сегментов пользователей"""
    try:
        segments = await cohort_analysis_service.get_user_segments(db, current_user.id)
        return segments
        
    except Exception as e:
        logger.error(f"Error getting user segments: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user segments")


@router.post("/user-segments", response_model=UserSegment)
async def create_user_segment(
    segment_data: UserSegmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Создание сегмента пользователей"""
    try:
        segment = await cohort_analysis_service.create_user_segment(db, segment_data, current_user.id)
        return segment
        
    except Exception as e:
        logger.error(f"Error creating user segment: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user segment")


@router.put("/user-segments/{segment_id}", response_model=UserSegment)
async def update_user_segment(
    segment_id: int,
    segment_data: UserSegmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Обновление сегмента пользователей"""
    try:
        segment = await cohort_analysis_service.update_user_segment(db, segment_id, segment_data, current_user.id)
        if not segment:
            raise HTTPException(status_code=404, detail="User segment not found")
        
        return segment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user segment {segment_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user segment")


@router.delete("/user-segments/{segment_id}")
async def delete_user_segment(
    segment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Удаление сегмента пользователей"""
    try:
        success = await cohort_analysis_service.delete_user_segment(db, segment_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="User segment not found")
        
        return {"message": "User segment deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user segment {segment_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete user segment")


@router.get("/user-segments/{segment_id}/users")
async def get_segment_users(
    segment_id: int,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Получение пользователей сегмента"""
    try:
        result = await cohort_analysis_service.get_segment_users(db, segment_id, current_user.id, limit, offset)
        return result
        
    except Exception as e:
        logger.error(f"Error getting segment users: {e}")
        raise HTTPException(status_code=500, detail="Failed to get segment users")


# Cohort and Segment Configuration Endpoints
@router.get("/cohort-types")
async def get_cohort_types(
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Получение доступных типов когорт"""
    try:
        return cohort_analysis_service.get_available_cohort_types()
        
    except Exception as e:
        logger.error(f"Error getting cohort types: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cohort types")


@router.get("/period-types")
async def get_period_types(
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Получение доступных типов периодов"""
    try:
        return cohort_analysis_service.get_available_period_types()
        
    except Exception as e:
        logger.error(f"Error getting period types: {e}")
        raise HTTPException(status_code=500, detail="Failed to get period types")


# Custom Metrics Endpoints
@router.get("/custom-metrics", response_model=List[CustomMetric])
async def get_custom_metrics(
    include_public: bool = Query(True, description="Включать публичные метрики"),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Получение списка пользовательских метрик"""
    try:
        metrics = await metrics_service.get_custom_metrics(db, current_user.id, include_public)
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting custom metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get custom metrics")


@router.post("/custom-metrics", response_model=CustomMetric)
async def create_custom_metric(
    metric_data: CustomMetricCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Создание пользовательской метрики"""
    try:
        metric = await metrics_service.create_custom_metric(db, metric_data, current_user.id)
        return metric
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating custom metric: {e}")
        raise HTTPException(status_code=500, detail="Failed to create custom metric")


@router.get("/custom-metrics/{metric_id}", response_model=CustomMetric)
async def get_custom_metric(
    metric_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Получение пользовательской метрики по ID"""
    try:
        metric = await metrics_service.get_custom_metric(db, metric_id, current_user.id)
        if not metric:
            raise HTTPException(status_code=404, detail="Custom metric not found")
        
        return metric
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting custom metric {metric_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get custom metric")


@router.put("/custom-metrics/{metric_id}", response_model=CustomMetric)
async def update_custom_metric(
    metric_id: int,
    metric_data: CustomMetricUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Обновление пользовательской метрики"""
    try:
        metric = await metrics_service.update_custom_metric(db, metric_id, metric_data, current_user.id)
        if not metric:
            raise HTTPException(status_code=404, detail="Custom metric not found")
        
        return metric
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating custom metric {metric_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update custom metric")


@router.delete("/custom-metrics/{metric_id}")
async def delete_custom_metric(
    metric_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Удаление пользовательской метрики"""
    try:
        success = await metrics_service.delete_custom_metric(db, metric_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Custom metric not found")
        
        return {"message": "Custom metric deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting custom metric {metric_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete custom metric")


@router.get("/custom-metrics/{metric_id}/calculate")
async def calculate_metric_value(
    metric_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Вычисление значения пользовательской метрики"""
    try:
        metric = await metrics_service.get_custom_metric(db, metric_id, current_user.id)
        if not metric:
            raise HTTPException(status_code=404, detail="Custom metric not found")
        
        result = await metrics_service.calculate_metric_value(db, metric)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating metric value {metric_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate metric value")


# Metric Alerts Endpoints
@router.get("/metric-alerts", response_model=List[MetricAlert])
async def get_metric_alerts(
    metric_id: Optional[int] = Query(None, description="Фильтр по ID метрики"),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Получение списка алертов метрик"""
    try:
        alerts = await metrics_service.get_metric_alerts(db, current_user.id, metric_id)
        return alerts
        
    except Exception as e:
        logger.error(f"Error getting metric alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metric alerts")


@router.post("/metric-alerts", response_model=MetricAlert)
async def create_metric_alert(
    alert_data: MetricAlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Создание алерта метрики"""
    try:
        alert = await metrics_service.create_metric_alert(db, alert_data, current_user.id)
        return alert
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating metric alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to create metric alert")


@router.put("/metric-alerts/{alert_id}", response_model=MetricAlert)
async def update_metric_alert(
    alert_id: int,
    alert_data: MetricAlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Обновление алерта метрики"""
    try:
        alert = await metrics_service.update_metric_alert(db, alert_id, alert_data, current_user.id)
        if not alert:
            raise HTTPException(status_code=404, detail="Metric alert not found")
        
        return alert
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating metric alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update metric alert")


@router.delete("/metric-alerts/{alert_id}")
async def delete_metric_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Удаление алерта метрики"""
    try:
        success = await metrics_service.delete_metric_alert(db, alert_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Metric alert not found")
        
        return {"message": "Metric alert deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting metric alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete metric alert")


# KPI and Templates Endpoints
@router.get("/predefined-kpis")
async def get_predefined_kpis(
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Получение предустановленных KPI"""
    try:
        kpis = metrics_service.get_predefined_kpis()
        return kpis
        
    except Exception as e:
        logger.error(f"Error getting predefined KPIs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get predefined KPIs")


@router.post("/check-alerts")
async def check_metric_alerts(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Проверка алертов метрик (только для админов)"""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Запускаем проверку в фоне
        background_tasks.add_task(metrics_service.check_metric_alerts, db)
        
        return {"message": "Alert check started"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting alert check: {e}")
        raise HTTPException(status_code=500, detail="Failed to start alert check")


@router.post("/custom-metrics/from-template")
async def create_metric_from_template(
    template_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Создание метрики из шаблона KPI"""
    try:
        metric_data = CustomMetricCreate(
            name=template_data.get('name', ''),
            description=template_data.get('description', ''),
            formula=template_data.get('formula', ''),
            unit=template_data.get('unit', ''),
            format_type=template_data.get('format_type', 'number'),
            category=template_data.get('category', ''),
            tags=template_data.get('tags', []),
            is_public=False
        )
        
        metric = await metrics_service.create_custom_metric(db, metric_data, current_user.id)
        return metric
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating metric from template: {e}")
        raise HTTPException(status_code=500, detail="Failed to create metric from template")


# ML Predictions and Recommendations Endpoints
@router.get("/ml-predictions")
async def get_ml_predictions(
    prediction_type: Optional[str] = Query(None, description="Тип прогноза"),
    target_user_id: Optional[int] = Query(None, description="ID целевого пользователя"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Получение ML прогнозов"""
    try:
        predictions = await ml_service.get_predictions(db, prediction_type, target_user_id, limit)
        return predictions
        
    except Exception as e:
        logger.error(f"Error getting ML predictions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get ML predictions")


@router.post("/ml-predictions/{prediction_type}")
async def generate_ml_prediction(
    prediction_type: str,
    target_user_id: Optional[int] = Query(None, description="ID целевого пользователя"),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Генерация ML прогноза"""
    try:
        result = await ml_service.generate_prediction(db, prediction_type, target_user_id)
        
        return {
            "prediction_type": result.prediction_type,
            "value": result.value,
            "confidence": result.confidence,
            "explanation": result.explanation,
            "recommendations": result.recommendations,
            "features": result.features,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating ML prediction: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate ML prediction")


@router.post("/ml-recommendations/{recommendation_type}")
async def generate_ml_recommendations(
    recommendation_type: str,
    context: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Генерация ML рекомендаций"""
    try:
        recommendations = await ml_service.generate_recommendations(db, recommendation_type, context)
        
        return {
            "recommendation_type": recommendation_type,
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating ML recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate ML recommendations")


@router.get("/user-insights/{user_id}")
async def get_user_insights(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Получение инсайтов о пользователе"""
    try:
        insights = await ml_service.get_user_insights(db, user_id)
        return insights
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting user insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user insights")


@router.get("/business-insights")
async def get_business_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Получение бизнес-инсайтов"""
    try:
        insights = await ml_service.get_business_insights(db)
        return insights
        
    except Exception as e:
        logger.error(f"Error getting business insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to get business insights")


@router.get("/prediction-types")
async def get_prediction_types(
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Получение доступных типов прогнозов"""
    try:
        prediction_types = [
            {
                "type": "ltv",
                "name": "Lifetime Value",
                "description": "Прогноз пожизненной ценности пользователя"
            },
            {
                "type": "churn",
                "name": "Риск оттока",
                "description": "Вероятность того, что пользователь перестанет использовать продукт"
            },
            {
                "type": "conversion",
                "name": "Конверсия",
                "description": "Вероятность конверсии в платную подписку"
            },
            {
                "type": "engagement",
                "name": "Вовлеченность",
                "description": "Уровень вовлеченности пользователя"
            },
            {
                "type": "revenue",
                "name": "Доходы",
                "description": "Прогноз доходов на следующий период"
            }
        ]
        
        return prediction_types
        
    except Exception as e:
        logger.error(f"Error getting prediction types: {e}")
        raise HTTPException(status_code=500, detail="Failed to get prediction types")


@router.get("/recommendation-types")
async def get_recommendation_types(
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Получение доступных типов рекомендаций"""
    try:
        recommendation_types = [
            {
                "type": "user_optimization",
                "name": "Оптимизация пользователя",
                "description": "Рекомендации по работе с конкретным пользователем"
            },
            {
                "type": "metric_optimization",
                "name": "Оптимизация метрик",
                "description": "Рекомендации по улучшению ключевых метрик"
            },
            {
                "type": "feature_usage",
                "name": "Использование функций",
                "description": "Рекомендации по повышению использования функций"
            },
            {
                "type": "retention_improvement",
                "name": "Улучшение удержания",
                "description": "Рекомендации по повышению retention"
            }
        ]
        
        return recommendation_types
        
    except Exception as e:
        logger.error(f"Error getting recommendation types: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommendation types")