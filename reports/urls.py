from django.urls import path
from .views import DashboardAnalyticsView, SmartInsightsView, WeeklySummaryView, ReportExportView, AdminAnalyticsView

urlpatterns = [
    path('analytics/dashboard/', DashboardAnalyticsView.as_view(), name='dashboard_analytics'),
    path('analytics/smart-insights/', SmartInsightsView.as_view(), name='smart_insights'),
    path('analytics/weekly-summary/', WeeklySummaryView.as_view(), name='weekly_summary'),
    path('reports/export/', ReportExportView.as_view(), name='report_export'),
    path('admin/analytics/', AdminAnalyticsView.as_view(), name='admin_analytics'),
]
