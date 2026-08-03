from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("", views.ReportsView.as_view(), name="index"),
    path("export/employees/", views.EmployeeReportExportView.as_view(), name="export_employees"),
    path("export/worksites/", views.WorksiteReportExportView.as_view(), name="export_worksites"),
    path("export/financials/", views.FinancialReportExportView.as_view(), name="export_financials"),
    path("export/materials/", views.MaterialsReportExportView.as_view(), name="export_materials"),
    path("export/summary/", views.SummaryReportExportView.as_view(), name="export_summary"),
    path("export/attendance/", views.MonthlyAttendanceExportView.as_view(), name="export_attendance"),
]
