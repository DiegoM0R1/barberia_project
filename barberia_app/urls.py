from django.urls import path
from . import views

urlpatterns = [
    # Otras URLs...
    path('admin/crear-venta/<int:cita_id>/', views.crear_venta_desde_cita, name='crear_venta'),
    path('crear-venta/<int:cita_id>/', views.crear_venta_desde_cita, name='crear_venta'),

]