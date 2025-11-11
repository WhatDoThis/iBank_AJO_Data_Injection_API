from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('run/', views.run_batch, name='run_batch'),
    path('status/<str:batch_id>/', views.batch_status, name='batch_status'),
    path('list/', views.batch_list, name='batch_list'),
    path('test-payload/', views.test_payload, name='test_payload'),  # 추가
]
