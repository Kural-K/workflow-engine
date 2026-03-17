from django.urls import path
from . import views

urlpatterns = [
    path('workflows', views.WorkflowListCreateView.as_view()),
    path('workflows/<str:pk>', views.WorkflowDetailView.as_view()),
    path('workflows/<str:workflow_id>/steps', views.StepListCreateView.as_view()),
    path('workflows/<str:workflow_id>/execute', views.ExecuteWorkflowView.as_view()),
    path('steps/<str:pk>', views.StepDetailView.as_view()),
    path('steps/<str:step_id>/rules', views.RuleListCreateView.as_view()),
    path('rules/<str:pk>', views.RuleDetailView.as_view()),
    path('executions', views.ExecutionListView.as_view()),
    path('executions/<str:pk>', views.ExecutionDetailView.as_view()),
    path('executions/<str:pk>/cancel', views.CancelExecutionView.as_view()),
    path('executions/<str:pk>/retry', views.RetryExecutionView.as_view()),
    path('executions/<str:pk>/approve', views.ApproveStepView.as_view()),
]
