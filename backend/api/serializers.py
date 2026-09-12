from decimal import Decimal
from rest_framework import serializers
from core.models import (
    Cliente, TipoEvento, Servicio, DetalleServicio,
    Cotizacion, DetalleCotizacion, Evento, Gasto, Pago
)


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'


class TipoEventoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoEvento
        fields = '__all__'


class DetalleServicioSerializer(serializers.ModelSerializer):
    servicio_nombre = serializers.CharField(source='servicio.nombre', read_only=True)

    class Meta:
        model = DetalleServicio
        fields = ['id', 'servicio', 'servicio_nombre', 'nombre_detalle', 'costo_unitario', 'unidad_medida', 'categoria', 'activo']


class ServicioSerializer(serializers.ModelSerializer):
    detalles = DetalleServicioSerializer(many=True, read_only=True)

    class Meta:
        model = Servicio
        fields = ['id', 'nombre', 'descripcion', 'requiere_cantidad_manual', 'activo', 'detalles']


class DetalleCotizacionSerializer(serializers.ModelSerializer):
    servicio_nombre = serializers.CharField(source='servicio.nombre', read_only=True)
    nombre_item = serializers.SerializerMethodField()

    class Meta:
        model = DetalleCotizacion
        fields = [
            'id', 'servicio', 'servicio_nombre', 'detalle_servicio',
            'nombre_item', 'costo_unitario', 'cantidad', 'subtotal',
            'requiere_saloneros', 'es_bufete', 'imagen_referencia',
            'detalle_personalizado'
        ]

    def get_nombre_item(self, obj):
        return obj.detalle_servicio.nombre_detalle if obj.detalle_servicio else obj.nombre_personalizado or obj.servicio.nombre


class GastoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gasto
        fields = ['id', 'cotizacion', 'evento', 'descripcion', 'monto', 'fecha_gasto', 'comprobante']


class PagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pago
        fields = ['id', 'evento', 'descripcion', 'monto', 'fecha_pago', 'comprobante_pago']


class CotizacionListSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)
    cliente_telefono = serializers.CharField(source='cliente.telefono', read_only=True)
    tipo_evento_nombre = serializers.CharField(source='tipo_evento.nombre', read_only=True)

    class Meta:
        model = Cotizacion
        fields = [
            'id', 'cliente', 'cliente_nombre', 'cliente_telefono',
            'tipo_evento', 'tipo_evento_nombre', 'fecha_evento',
            'cantidad_personas', 'estado', 'total_general',
            'monto_pago_inicial', 'fecha_registro'
        ]


class CotizacionDetailSerializer(serializers.ModelSerializer):
    cliente = ClienteSerializer(read_only=True)
    tipo_evento = TipoEventoSerializer(read_only=True)
    detalles = DetalleCotizacionSerializer(many=True, read_only=True)
    gastos = GastoSerializer(many=True, read_only=True)

    class Meta:
        model = Cotizacion
        fields = '__all__'


class EventoListSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source='cotizacion.cliente.nombre', read_only=True)
    cliente_telefono = serializers.CharField(source='cotizacion.cliente.telefono', read_only=True)
    tipo_evento = serializers.CharField(source='cotizacion.tipo_evento.nombre', read_only=True)
    total_general = serializers.DecimalField(source='cotizacion.total_general', max_digits=14, decimal_places=2, read_only=True)
    total_abonado = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    saldo_pendiente = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    dias_restantes = serializers.IntegerField(read_only=True)

    class Meta:
        model = Evento
        fields = [
            'id', 'cotizacion', 'cliente_nombre', 'cliente_telefono',
            'tipo_evento', 'fecha_evento', 'cantidad_personas', 'estado',
            'fecha_contratacion', 'total_general', 'total_abonado',
            'saldo_pendiente', 'dias_restantes'
        ]


class EventoDetailSerializer(serializers.ModelSerializer):
    cotizacion = CotizacionDetailSerializer(read_only=True)
    pagos = PagoSerializer(many=True, read_only=True)
    gastos = GastoSerializer(many=True, read_only=True)
    total_abonado = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    saldo_pendiente = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    dias_restantes = serializers.IntegerField(read_only=True)

    class Meta:
        model = Evento
        fields = '__all__'


class ItemSolicitudPayloadSerializer(serializers.Serializer):
    id_detalle = serializers.IntegerField()
    cantidad = serializers.IntegerField(required=False, allow_null=True)
    notas = serializers.CharField(required=False, allow_blank=True, default='')


class SolicitudPublicaInputSerializer(serializers.Serializer):
    identificacion = serializers.CharField(max_length=50)
    nombre = serializers.CharField(max_length=150)
    telefono = serializers.CharField(max_length=50)
    correo = serializers.EmailField()
    direccion_cliente = serializers.CharField(required=False, allow_blank=True, default='')

    id_tipo_evento = serializers.IntegerField()
    fecha_evento = serializers.DateField()
    cantidad_personas = serializers.IntegerField(min_value=1)
    direccion_evento = serializers.CharField(max_length=255)

    modalidad_servicio = serializers.ChoiceField(choices=['Bufete', 'Saloneros', 'NoAplica'], default='Bufete')
    incluir_mobiliario = serializers.BooleanField(default=True)
    tipo_mobiliario = serializers.CharField(default='Redondas')
    incluir_vajilla = serializers.BooleanField(default=True)
    kilometros_transporte = serializers.IntegerField(default=1, min_value=1)
    detalle_otros_alimentacion = serializers.CharField(required=False, allow_blank=True, default='')

    items = ItemSolicitudPayloadSerializer(many=True, default=[])
