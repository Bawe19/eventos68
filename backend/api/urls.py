from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClienteViewSet, TipoEventoViewSet, ServicioViewSet,
    CotizacionViewSet, EventoViewSet, GastoViewSet, PagoViewSet,
    DashboardStatsView
)

router = DefaultRouter()
router.register(r'clientes', ClienteViewSet)
router.register(r'tipos-evento', TipoEventoViewSet)
router.register(r'servicios', ServicioViewSet)
router.register(r'cotizaciones', CotizacionViewSet)
router.register(r'eventos', EventoViewSet)
router.register(r'gastos', GastoViewSet)
router.register(r'pagos', PagoViewSet)

urlpatterns = [
    path('dashboard-stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('', include(router.urls)),
]
