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
    
    # Portal de Gestión (Admin amigable para el equipo)
    path('gestor/login/', views.gestor_login, name='gestor_login'),
    path('gestor/logout/', views.gestor_logout, name='gestor_logout'),
    path('gestor/', views.gestor_dashboard, name='gestor_dashboard'),
    path('gestor/cotizacion/<int:cotizacion_id>/', views.gestor_detalle_cotizacion, name='gestor_detalle'),
    path('gestor/cotizacion/<int:cotizacion_id>/estado/', views.gestor_cambiar_estado, name='gestor_cambiar_estado'),
    path('gestor/cotizacion/<int:cotizacion_id>/convertir/', views.gestor_convertir_evento, name='gestor_convertir_evento'),
    path('gestor/evento/<int:evento_id>/abono/', views.gestor_registrar_abono, name='gestor_registrar_abono'),
]
