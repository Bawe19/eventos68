from django.urls import path
from . import views

app_name = 'web'

urlpatterns = [
    path('', views.home, name='home'),
    path('solicitar/', views.solicitar_cotizacion, name='solicitar'),
    path('solicitud-enviada/<int:cotizacion_id>/', views.solicitud_enviada, name='solicitud_enviada'),
    path('cotizacion/<int:cotizacion_id>/', views.detalle_cotizacion, name='detalle_cotizacion'),
    path('cotizacion/<int:cotizacion_id>/pdf/', views.descargar_pdf, name='descargar_pdf'),
    path('cotizacion/<int:cotizacion_id>/enviar-correo/', views.enviar_correo_cotizacion, name='enviar_correo'),
]
