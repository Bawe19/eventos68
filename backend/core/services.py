from decimal import Decimal
import math
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import (
    Cliente, TipoEvento, Servicio, DetalleServicio,
    Cotizacion, DetalleCotizacion, Evento, Gasto, Pago,
    ConfiguracionGanancia, ConfiguracionPagoInicial
)


class CotizacionService:
    """
    Servicio integral para creación, automatización de componentes y costeo de cotizaciones.
    """

    @classmethod
    @transaction.atomic
    def crear_solicitud(cls, datos_cliente: dict, id_tipo_evento: int, fecha_evento,
                        cantidad_personas: int, direccion_evento: str,
                        items_seleccionados: list, modalidad_servicio: str = 'Bufete',
                        imagen_decoracion=None, detalle_otros_alimentacion: str = '',
                        incluir_mobiliario: bool = True, tipo_mobiliario: str = 'Redondas',
                        incluir_vajilla: bool = True, kilometros_transporte: int = 1,
                        alergias_restricciones: str = 'No presenta / No aplica') -> Cotizacion:
        """
        Crea una solicitud pública de cotización con todas las automatizaciones inteligentes
        de vajilla, cristalería, mantelería, mobiliario, transporte y registro de alergias alimentarias.
        """
        if cantidad_personas <= 0:
            raise ValidationError('La cantidad de personas debe ser mayor a cero.')

        # 1. Obtener o crear el cliente por identificación
        identificacion = datos_cliente.get('identificacion', '').strip()
        cliente, _ = Cliente.objects.update_or_create(
            identificacion=identificacion,
            defaults={
                'nombre': datos_cliente.get('nombre', '').strip(),
                'telefono': datos_cliente.get('telefono', '').strip(),
                'correo': datos_cliente.get('correo', '').strip(),
                'direccion': datos_cliente.get('direccion', '').strip() or direccion_evento,
            }
        )

        # 2. Obtener tipo de evento
        tipo_evento = TipoEvento.objects.get(id=id_tipo_evento)

        # 3. Crear cabecera de cotización
        cotizacion = Cotizacion.objects.create(
            cliente=cliente,
            tipo_evento=tipo_evento,
            fecha_evento=fecha_evento,
            cantidad_personas=cantidad_personas,
            direccion_evento=direccion_evento,
            estado='Solicitud',
            modalidad_servicio=modalidad_servicio,
            alergias_restricciones=alergias_restricciones or 'No presenta / No aplica',
            porcentaje_ganancia=ConfiguracionGanancia.obtener_activa(),
            porcentaje_pago_inicial=ConfiguracionPagoInicial.obtener_activa(),
            porcentaje_iva=Decimal('13.00')
        )

        tiene_postre = False
        detalles_a_crear = []

        # 4. Procesar componentes seleccionados por el cliente (comida, extras, etc.)
        for item in items_seleccionados:
            id_detalle = item.get('id_detalle')
            if not id_detalle:
                continue

            try:
                detalle_obj = DetalleServicio.objects.select_related('servicio').get(id=id_detalle, activo=True)
            except DetalleServicio.DoesNotExist:
                continue

            cant = item.get('cantidad') or cantidad_personas
            if detalle_obj.categoria == 'Transporte':
                cant = cantidad_personas * max(1, kilometros_transporte)

            if detalle_obj.categoria == 'Postre':
                tiene_postre = True

            costo = detalle_obj.costo_unitario
            sub = (costo * Decimal(cant)).quantize(Decimal('0.01'))

            detalles_a_crear.append(DetalleCotizacion(
                cotizacion=cotizacion,
                servicio=detalle_obj.servicio,
                detalle_servicio=detalle_obj,
                costo_unitario=costo,
                cantidad=cant,
                subtotal=sub,
                requiere_saloneros=(modalidad_servicio == 'Saloneros'),
                es_bufete=(modalidad_servicio == 'Bufete'),
                imagen_referencia=imagen_decoracion if detalle_obj.servicio.nombre.lower().startswith('decor') else None,
                detalle_personalizado=item.get('notas', '')
            ))

        # 5. Agregar detalle personalizado de alimentación si aplica
        if detalle_otros_alimentacion:
            try:
                servicio_alim = Servicio.objects.filter(nombre__icontains='aliment').first()
                if servicio_alim:
                    detalles_a_crear.append(DetalleCotizacion(
                        cotizacion=cotizacion,
                        servicio=servicio_alim,
                        detalle_servicio=None,
                        nombre_personalizado='Menú / Requerimiento Especial de Alimentación',
                        costo_unitario=Decimal('0.00'),  # Se cotiza manualmente en gastos
                        cantidad=cantidad_personas,
                        subtotal=Decimal('0.00'),
                        detalle_personalizado=detalle_otros_alimentacion
                    ))
            except Exception:
                pass

        # 6. Automatización de Vajilla y Cristalería Básica
        if incluir_vajilla:
            cls._agregar_vajilla_automatica(cotizacion, cantidad_personas, tiene_postre, detalles_a_crear)

        # 7. Automatización de Mobiliario y Mantelería
        if incluir_mobiliario:
            cls._agregar_mobiliario_automatico(cotizacion, cantidad_personas, tipo_mobiliario, detalles_a_crear)

        # Guardar detalles y calcular totales
        DetalleCotizacion.objects.bulk_create(detalles_a_crear)
        cotizacion.recalcular_totales(save=True)

        return cotizacion

    @classmethod
    def _agregar_vajilla_automatica(cls, cotizacion, personas: int, tiene_postre: bool, detalles_lista: list):
        """Agrega automáticamente platos, cubiertos, servilletas, vasos y copas por comensal."""
        vajilla_items = DetalleServicio.objects.filter(categoria__in=['Vajilla', 'Cristaleria'], activo=True)
        for item in vajilla_items:
            # Excluir vajilla de postre si no hay postre
            if 'postre' in item.nombre_detalle.lower() and not tiene_postre:
                continue
            sub = (item.costo_unitario * Decimal(personas)).quantize(Decimal('0.01'))
            detalles_lista.append(DetalleCotizacion(
                cotizacion=cotizacion,
                servicio=item.servicio,
                detalle_servicio=item,
                costo_unitario=item.costo_unitario,
                cantidad=personas,
                subtotal=sub
            ))

    @classmethod
    def _agregar_mobiliario_automatico(cls, cotizacion, personas: int, tipo_mobiliario: str, detalles_lista: list):
        """Calcula sillas por persona y mesas/manteles según la capacidad seleccionada."""
        # 1. Sillas (1 por persona)
        silla = DetalleServicio.objects.filter(categoria='Silla', activo=True).first()
        if silla:
            sub = (silla.costo_unitario * Decimal(personas)).quantize(Decimal('0.01'))
            detalles_lista.append(DetalleCotizacion(
                cotizacion=cotizacion,
                servicio=silla.servicio,
                detalle_servicio=silla,
                costo_unitario=silla.costo_unitario,
                cantidad=personas,
                subtotal=sub
            ))

        # 2. Mesas y manteles según capacidad
        capacidad_por_mesa = 10  # Por defecto Redondas
        filtro_nombre = 'redonda'
        if tipo_mobiliario == 'RectangularesPequenas':
            capacidad_por_mesa = 8
            filtro_nombre = 'pequeña'
        elif tipo_mobiliario == 'RectangularesGrandes':
            capacidad_por_mesa = 12
            filtro_nombre = 'grande'

        cant_mesas = math.ceil(personas / capacidad_por_mesa)

        mesa = DetalleServicio.objects.filter(categoria='Mesa', nombre_detalle__icontains=filtro_nombre, activo=True).first()
        if not mesa:
            mesa = DetalleServicio.objects.filter(categoria='Mesa', activo=True).first()

        mantel = DetalleServicio.objects.filter(categoria='Mantel', nombre_detalle__icontains=filtro_nombre, activo=True).first()
        if not mantel:
            mantel = DetalleServicio.objects.filter(categoria='Mantel', activo=True).first()

        if mesa and cant_mesas > 0:
            sub_m = (mesa.costo_unitario * Decimal(cant_mesas)).quantize(Decimal('0.01'))
            detalles_lista.append(DetalleCotizacion(
                cotizacion=cotizacion,
                servicio=mesa.servicio,
                detalle_servicio=mesa,
                costo_unitario=mesa.costo_unitario,
                cantidad=cant_mesas,
                subtotal=sub_m
            ))

        if mantel and cant_mesas > 0:
            sub_mt = (mantel.costo_unitario * Decimal(cant_mesas)).quantize(Decimal('0.01'))
            detalles_lista.append(DetalleCotizacion(
                cotizacion=cotizacion,
                servicio=mantel.servicio,
                detalle_servicio=mantel,
                costo_unitario=mantel.costo_unitario,
                cantidad=cant_mesas,
                subtotal=sub_mt
            ))


class EventoService:
    """
    Servicio para contratación de eventos y gestión de pagos/abonos.
    """

    @classmethod
    @transaction.atomic
    def contratar_evento(cls, cotizacion_id: int, comprobante_pago=None, notas_operativas: str = '') -> Evento:
        """
        Contrata una cotización:
        - Valida que la fecha no esté ocupada (1 evento por día).
        - Cambia el estado a Evento.
        - Crea el registro de Evento.
        - Registra el abono del adelanto mínimo si se adjunta comprobante.
        - Vincula los gastos presupuestados al evento.
        """
        cotizacion = Cotizacion.objects.select_for_update().get(id=cotizacion_id)

        # Validar si ya hay evento en esa fecha
        if Evento.objects.filter(fecha_evento=cotizacion.fecha_evento).exists():
            raise ValidationError(f'Ya existe un evento contratado para la fecha {cotizacion.fecha_evento}. '
                                  'Eventos68 no programa dos eventos el mismo día.')

        if cotizacion.detalles.count() == 0:
            raise ValidationError('No se puede contratar una cotización sin servicios ni detalles asociados.')

        # Actualizar estado de cotización
        cotizacion.estado = 'Evento'
        cotizacion.recalcular_totales(save=True)

        # Crear Evento
        evento = Evento.objects.create(
            cotizacion=cotizacion,
            fecha_evento=cotizacion.fecha_evento,
            cantidad_personas=cotizacion.cantidad_personas,
            estado='Contratado',
            notas_operativas=notas_operativas
        )

        # Vincular gastos directos de la cotización al evento
        Gasto.objects.filter(cotizacion=cotizacion).update(evento=evento)

        # Registrar pago inicial si se sube comprobante
        if comprobante_pago:
            Pago.objects.create(
                evento=evento,
                descripcion='Adelanto de Cotización (Pago Inicial)',
                monto=cotizacion.monto_pago_inicial,
                fecha_pago=timezone.now(),
                comprobante_pago=comprobante_pago
            )

        return evento

    @classmethod
    def registrar_abono(cls, evento_id: int, monto: Decimal, descripcion: str, comprobante=None) -> Pago:
        """
        Registra un abono y envía un correo electrónico de confirmación con el saldo y cuenta regresiva.
        """
        if monto <= Decimal('0.00'):
            raise ValidationError('El monto del abono debe ser mayor a cero.')

        evento = Evento.objects.get(id=evento_id)
        pago = Pago.objects.create(
            evento=evento,
            descripcion=descripcion or 'Abono a evento',
            monto=monto,
            fecha_pago=timezone.now(),
            comprobante_pago=comprobante
        )

        # Enviar notificación por correo
        cls.notificar_abono_por_correo(pago)

        return pago

    @classmethod
    def notificar_abono_por_correo(cls, pago: Pago):
        """Envía resumen del abono y saldo pendiente al cliente."""
        try:
            evento = pago.evento
            cliente = evento.cotizacion.cliente
            total_abonado = evento.total_abonado
            saldo_pendiente = evento.saldo_pendiente
            dias_restantes = evento.dias_restantes

            asunto = f"Confirmación de Abono - Eventos68 ({evento.cotizacion.tipo_evento.nombre})"
            cuerpo = (
                f"Estimado(a) {cliente.nombre},\n\n"
                f"Hemos registrado su abono correctamente para su evento el {evento.fecha_evento.strftime('%d/%m/%Y')}:\n"
                f"- Concepto: {pago.descripcion}\n"
                f"- Monto abonado: ₡{pago.monto:,.2f}\n"
                f"- Fecha: {pago.fecha_pago.strftime('%d/%m/%Y %H:%M')}\n\n"
                f"Estado de su cuenta:\n"
                f"- Total abonado acumulado: ₡{total_abonado:,.2f}\n"
                f"- Saldo restante pendiente: ₡{saldo_pendiente:,.2f}\n"
                f"- Días restantes para el gran día: {dias_restantes} días\n\n"
                f"¡Gracias por confiar en Eventos68!\n"
                f"Para consultas: contacto@eventos68.com | +506 8888-6868"
            )

            send_mail(
                subject=asunto,
                message=cuerpo,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'Eventos68 <no-reply@eventos68.com>'),
                recipient_list=[cliente.correo],
                fail_silently=True
            )
        except Exception:
            pass  # No interrumpir la transacción si falla el servicio de correo
