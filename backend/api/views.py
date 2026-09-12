from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Count
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from core.models import (
    Cliente, TipoEvento, Servicio, DetalleServicio,
    Cotizacion, Evento, Gasto, Pago
)
from core.services import CotizacionService, EventoService
from .serializers import (
    ClienteSerializer, TipoEventoSerializer, ServicioSerializer,
    DetalleServicioSerializer, CotizacionListSerializer, CotizacionDetailSerializer,
    EventoListSerializer, EventoDetailSerializer, GastoSerializer,
    PagoSerializer, SolicitudPublicaInputSerializer
)


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    search_fields = ['nombre', 'identificacion', 'telefono']


class TipoEventoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TipoEvento.objects.filter(activo=True)
    serializer_class = TipoEventoSerializer
    pagination_class = None


class ServicioViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Servicio.objects.filter(activo=True).prefetch_related('detalles')
    serializer_class = ServicioSerializer
    pagination_class = None


class CotizacionViewSet(viewsets.ModelViewSet):
    queryset = Cotizacion.objects.select_related('cliente', 'tipo_evento').prefetch_related('detalles', 'gastos').all()

    def get_serializer_class(self):
        if self.action in ['list']:
            return CotizacionListSerializer
        return CotizacionDetailSerializer

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def crear_solicitud(self, request):
        """Endpoint público para que Flutter o Web envíen una solicitud de cotización."""
        serializer = SolicitudPublicaInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        d = serializer.validated_data
        try:
            cotizacion = CotizacionService.crear_solicitud(
                datos_cliente={
                    'identificacion': d['identificacion'],
                    'nombre': d['nombre'],
                    'telefono': d['telefono'],
                    'correo': d['correo'],
                    'direccion': d.get('direccion_cliente', ''),
                },
                id_tipo_evento=d['id_tipo_evento'],
                fecha_evento=d['fecha_evento'],
                cantidad_personas=d['cantidad_personas'],
                direccion_evento=d['direccion_evento'],
                items_seleccionados=d.get('items', []),
                modalidad_servicio=d.get('modalidad_servicio', 'Bufete'),
                detalle_otros_alimentacion=d.get('detalle_otros_alimentacion', ''),
                incluir_mobiliario=d.get('incluir_mobiliario', True),
                tipo_mobiliario=d.get('tipo_mobiliario', 'Redondas'),
                incluir_vajilla=d.get('incluir_vajilla', True),
                kilometros_transporte=d.get('kilometros_transporte', 1),
            )
            return Response(CotizacionDetailSerializer(cotizacion).data, status=status.HTTP_201_CREATED)
        except Exception as ex:
            return Response({'error': str(ex)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def contratar(self, request, pk=None):
        """Convierte una cotización en un Evento oficial contratado."""
        cotizacion = self.get_object()
        comprobante = request.FILES.get('comprobante_pago')
        notas = request.data.get('notas_operativas', '')

        try:
            evento = EventoService.contratar_evento(
                cotizacion_id=cotizacion.id,
                comprobante_pago=comprobante,
                notas_operativas=notas
            )
            return Response(EventoDetailSerializer(evento).data, status=status.HTTP_201_CREATED)
        except Exception as ex:
            return Response({'error': str(ex)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def recalcular(self, request, pk=None):
        """Fuerza el recálculo financiero de una cotización."""
        cotizacion = self.get_object()
        cotizacion.recalcular_totales(save=True)
        return Response(CotizacionDetailSerializer(cotizacion).data)


class EventoViewSet(viewsets.ModelViewSet):
    queryset = Evento.objects.select_related('cotizacion__cliente', 'cotizacion__tipo_evento').prefetch_related('pagos', 'gastos').all()

    def get_serializer_class(self):
        if self.action == 'list':
            return EventoListSerializer
        return EventoDetailSerializer

    @action(detail=True, methods=['post'])
    def abonar(self, request, pk=None):
        """Registra un nuevo abono para este evento."""
        evento = self.get_object()
        try:
            monto = Decimal(str(request.data.get('monto', 0)))
            descripcion = request.data.get('descripcion', 'Abono a evento')
            comprobante = request.FILES.get('comprobante_pago')

            pago = EventoService.registrar_abono(
                evento_id=evento.id,
                monto=monto,
                descripcion=descripcion,
                comprobante=comprobante
            )
            return Response(PagoSerializer(pago).data, status=status.HTTP_201_CREATED)
        except Exception as ex:
            return Response({'error': str(ex)}, status=status.HTTP_400_BAD_REQUEST)


class GastoViewSet(viewsets.ModelViewSet):
    queryset = Gasto.objects.all()
    serializer_class = GastoSerializer


class PagoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Pago.objects.select_related('evento').all()
    serializer_class = PagoSerializer


class DashboardStatsView(APIView):
    """
    Retorna métricas clave para el panel administrativo en Flutter o Web:
    - Eventos activos
    - Solicitudes pendientes
    - Ingresos totales abonados
    - Próximos eventos
    """
    def get(self, request):
        hoy = timezone.now().date()
        
        solicitudes_pendientes = Cotizacion.objects.filter(estado='Solicitud').count()
        cotizaciones_activas = Cotizacion.objects.filter(estado='Cotizacion').count()
        eventos_contratados = Evento.objects.filter(estado='Contratado', fecha_evento__gte=hoy).count()
        
        total_ingresos = Pago.objects.aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        total_gastos = Gasto.objects.aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        
        proximos = Evento.objects.filter(fecha_evento__gte=hoy).order_by('fecha_evento')[:5]
        
        return Response({
            'solicitudes_pendientes': solicitudes_pendientes,
            'cotizaciones_activas': cotizaciones_activas,
            'eventos_proximos_count': eventos_contratados,
            'total_recaudado_crc': float(total_ingresos),
            'total_gastos_crc': float(total_gastos),
            'balance_operativo_crc': float(total_ingresos - total_gastos),
            'proximos_eventos': EventoListSerializer(proximos, many=True).data,
        })
