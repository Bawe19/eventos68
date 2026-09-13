from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.mail import EmailMessage
from django.conf import settings
from django.db.models import Sum, Q, Count
from django.utils import timezone

from core.models import (
    Cliente, TipoEvento, Servicio, DetalleServicio,
    Cotizacion, DetalleCotizacion, Evento, Gasto, Pago
)
from core.services import CotizacionService, EventoService
from core.pdf_service import generar_pdf_cotizacion


def home(request):
    """Página de inicio de Eventos68."""
    tipos_evento = TipoEvento.objects.filter(activo=True)
    servicios = Servicio.objects.filter(activo=True)
    return render(request, 'web/home.html', {
        'tipos_evento': tipos_evento,
        'servicios': servicios
    })


def solicitar_cotizacion(request):
    """
    Formulario interactivo de solicitud de cotización para clientes.
    Replica y moderniza la experiencia de usuario de La Parrillita de Ron.
    """
    if request.method == 'POST':
        try:
            # 1. Datos del cliente
            datos_cliente = {
                'identificacion': request.POST.get('identificacion', '').strip(),
                'nombre': request.POST.get('nombre', '').strip(),
                'telefono': request.POST.get('telefono', '').strip(),
                'correo': request.POST.get('correo', '').strip(),
                'direccion': request.POST.get('direccionCliente', '').strip(),
            }

            if not datos_cliente['identificacion'] or not datos_cliente['nombre'] or not datos_cliente['correo']:
                messages.error(request, 'Todos los campos de contacto son requeridos.')
                return redirect('web:solicitar')

            # 2. Datos del evento
            id_tipo_evento = int(request.POST.get('idTipoEvento', 0))
            fecha_evento = request.POST.get('fechaEvento')
            cantidad_personas = int(request.POST.get('cantidadPersonas', 0))
            direccion_evento = request.POST.get('direccionEvento', '').strip()

            if cantidad_personas <= 0:
                messages.error(request, 'La cantidad de comensales debe ser mayor que cero.')
                return redirect('web:solicitar')

            # 3. Servicios y opciones seleccionadas
            modalidad = request.POST.get('requiereSaloneros', 'Bufete')
            incluir_mobiliario = bool(request.POST.get('incluirMobiliario'))
            tipo_mobiliario = request.POST.get('tipoMobiliario', 'Redondas')
            incluir_vajilla = not bool(request.POST.get('noVajillaCristaleria'))
            km_transporte = int(request.POST.get('kilometrosTransporte', 1) or 1)
            detalle_otros = request.POST.get('DetalleOtrosAlimentacion', '').strip()
            imagen_decoracion = request.FILES.get('imagenDecoracion')

            # 4. Extraer checkboxes de componentes seleccionados
            items_seleccionados = []
            for key, val in request.POST.items():
                if key.startswith('item_sel_') and val == 'on':
                    id_det = int(key.replace('item_sel_', ''))
                    cant_especifica = request.POST.get(f'item_cant_{id_det}')
                    items_seleccionados.append({
                        'id_detalle': id_det,
                        'cantidad': int(cant_especifica) if cant_especifica and int(cant_especifica) > 0 else cantidad_personas
                    })

            # 5. Procesar creación con servicio de dominio
            cotizacion = CotizacionService.crear_solicitud(
                datos_cliente=datos_cliente,
                id_tipo_evento=id_tipo_evento,
                fecha_evento=fecha_evento,
                cantidad_personas=cantidad_personas,
                direccion_evento=direccion_evento,
                items_seleccionados=items_seleccionados,
                modalidad_servicio=modalidad,
                imagen_decoracion=imagen_decoracion,
                detalle_otros_alimentacion=detalle_otros,
                incluir_mobiliario=incluir_mobiliario,
                tipo_mobiliario=tipo_mobiliario,
                incluir_vajilla=incluir_vajilla,
                kilometros_transporte=km_transporte
            )

            return redirect('web:solicitud_enviada', cotizacion_id=cotizacion.id)

        except Exception as ex:
            messages.error(request, f"Error al procesar solicitud: {str(ex)}")
            return redirect('web:solicitar')

    # GET: Cargar catálogo
    tipos_evento = TipoEvento.objects.filter(activo=True)
    servicios = Servicio.objects.filter(activo=True).prefetch_related('detalles')
    
    # Agrupar detalles de alimentación por categorías
    detalles_alimentacion = DetalleServicio.objects.filter(
        servicio__nombre__icontains='aliment',
        activo=True
    )

    context = {
        'tipos_evento': tipos_evento,
        'servicios': servicios,
        'guarniciones': detalles_alimentacion.filter(categoria='Guarnicion'),
        'proteinas': detalles_alimentacion.filter(categoria='Proteina'),
        'ensaladas': detalles_alimentacion.filter(categoria='Ensalada'),
        'postres': detalles_alimentacion.filter(categoria='Postre'),
        'bebidas': detalles_alimentacion.filter(categoria='Bebida'),
        'salsas': detalles_alimentacion.filter(categoria='Salsa'),
    }
    return render(request, 'web/solicitar.html', context)


def solicitud_enviada(request, cotizacion_id):
    """Página de confirmación tras registrar la solicitud."""
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id)
    return render(request, 'web/solicitud_enviada.html', {'cotizacion': cotizacion})


def detalle_cotizacion(request, cotizacion_id):
    """Detalle completo del presupuesto con desglose y opciones administrativas."""
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id)
    return render(request, 'web/detalle_cotizacion.html', {'cotizacion': cotizacion})


def descargar_pdf(request, cotizacion_id):
    """Descarga el presupuesto formal en formato PDF."""
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id)
    pdf_bytes = generar_pdf_cotizacion(cotizacion)
    
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Cotizacion_EV68_{cotizacion.id:04d}.pdf"'
    return response


def enviar_correo_cotizacion(request, cotizacion_id):
    """Envía el presupuesto en PDF por correo electrónico al cliente."""
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id)
    try:
        pdf_bytes = generar_pdf_cotizacion(cotizacion)
        cliente = cotizacion.cliente

        asunto = f"Presupuesto Formal - Eventos68 Catering (EV68-{cotizacion.id:04d})"
        cuerpo = (
            f"Estimado(a) {cliente.nombre},\n\n"
            f"Adjuntamos el presupuesto formal detallado para su evento de tipo {cotizacion.tipo_evento.nombre}.\n\n"
            f"Detalles principales:\n"
            f"- Fecha: {cotizacion.fecha_evento.strftime('%d/%m/%Y')}\n"
            f"- Cantidad de invitados: {cotizacion.cantidad_personas}\n"
            f"- Total General: ₡{cotizacion.total_general:,.2f}\n"
            f"- Pago Inicial (Adelanto para reservar): ₡{cotizacion.monto_pago_inicial:,.2f}\n\n"
            f"Por favor revise el documento PDF adjunto. Quedamos a su completa disposición.\n\n"
            f"Atentamente,\n"
            f"Equipo Eventos68 Catering & Logística\n"
            f"+506 8888-6868 | contacto@eventos68.com"
        )

        email = EmailMessage(
            subject=asunto,
            body=cuerpo,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'Eventos68 <no-reply@eventos68.com>'),
            to=[cliente.correo]
        )
        email.attach(f"Presupuesto_Eventos68_{cotizacion.id:04d}.pdf", pdf_bytes, 'application/pdf')
        email.send(fail_silently=False)

        messages.success(request, f"Presupuesto enviado exitosamente al correo {cliente.correo}.")
    except Exception as ex:
        messages.error(request, f"Error al enviar correo: {str(ex)}")

    return redirect('web:detalle_cotizacion', cotizacion_id=cotizacion.id)


# ==============================================================================
# PORTAL DE ADMINISTRACIÓN Y GESTIÓN PARA EL PERSONAL (NO-TÉCNICO)
# ==============================================================================

def gestor_login(request):
    """Pantalla de inicio de sesión intuitiva para el personal de Eventos68."""
    if request.user.is_authenticated:
        return redirect('web:gestor_dashboard')

    if request.method == 'POST':
        usuario = request.POST.get('username', '').strip()
        clave = request.POST.get('password', '')
        user = authenticate(request, username=usuario, password=clave)
        if user is not None:
            auth_login(request, user)
            messages.success(request, f"¡Bienvenido(a), {user.get_full_name() or user.username}!")
            next_url = request.GET.get('next') or 'web:gestor_dashboard'
            return redirect(next_url)
        else:
            messages.error(request, "Credenciales incorrectas. Verifique su usuario y contraseña.")

    return render(request, 'web/gestor_login.html')


def gestor_logout(request):
    """Cierra la sesión del gestor."""
    auth_logout(request)
    messages.info(request, "Has cerrado sesión correctamente.")
    return redirect('web:home')


@login_required(login_url='web:gestor_login')
def gestor_dashboard(request):
    """
    Panel central de gestión:
    - KPIs clave (Cotizaciones pendientes, aprobadas, eventos, abonos recaudados)
    - Listado y control de cotizaciones
    - Listado de eventos y registro ágil de abonos
    """
    # 1. Filtros de búsqueda
    filtro_estado = request.GET.get('estado', 'Todas')
    busqueda = request.GET.get('q', '').strip()

    cotizaciones = Cotizacion.objects.select_related('cliente', 'tipo_evento').order_by('-fecha_registro')
    if filtro_estado != 'Todas':
        cotizaciones = cotizaciones.filter(estado=filtro_estado)
    if busqueda:
        cotizaciones = cotizaciones.filter(
            Q(cliente__nombre__icontains=busqueda) |
            Q(cliente__identificacion__icontains=busqueda) |
            Q(cliente__telefono__icontains=busqueda) |
            Q(id__icontains=busqueda)
        )

    # 2. Métricas Generales
    total_cotizaciones = Cotizacion.objects.count()
    cotizaciones_pendientes = Cotizacion.objects.filter(estado='Pendiente').count()
    cotizaciones_aprobadas = Cotizacion.objects.filter(estado='Aprobada').count()
    eventos_confirmados = Evento.objects.filter(estado__in=['Contratado', 'En Proceso']).count()
    
    total_recaudado = Pago.objects.aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    # 3. Próximos Eventos
    eventos_proximos = Evento.objects.select_related('cotizacion', 'cotizacion__cliente', 'cotizacion__tipo_evento')\
                                    .prefetch_related('pagos')\
                                    .order_by('fecha_evento')[:10]

    # Calcular saldo para cada evento
    for ev in eventos_proximos:
        ev.total_abonado = sum(p.monto for p in ev.pagos.all())
        ev.saldo_pendiente = max(Decimal('0.00'), ev.cotizacion.total_general - ev.total_abonado)
        ev.porcentaje_pagado = int((ev.total_abonado / ev.cotizacion.total_general * 100)) if ev.cotizacion.total_general > 0 else 0

    context = {
        'cotizaciones': cotizaciones[:50],
        'total_cotizaciones': total_cotizaciones,
        'cotizaciones_pendientes': cotizaciones_pendientes,
        'cotizaciones_aprobadas': cotizaciones_aprobadas,
        'eventos_confirmados': eventos_confirmados,
        'total_recaudado': total_recaudado,
        'eventos_proximos': eventos_proximos,
        'filtro_estado': filtro_estado,
        'busqueda': busqueda,
    }
    return render(request, 'web/gestor_dashboard.html', context)


@login_required(login_url='web:gestor_login')
@require_http_methods(['POST'])
def gestor_cambiar_estado(request, cotizacion_id):
    """Cambia el estado de una cotización con un solo clic."""
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id)
    nuevo_estado = request.POST.get('nuevo_estado')
    estados_validos = ['Pendiente', 'Aprobada', 'Rechazada', 'Cancelada']

    if nuevo_estado in estados_validos:
        cotizacion.estado = nuevo_estado
        cotizacion.save(update_fields=['estado'])
        messages.success(request, f"Cotización #EV68-{cotizacion.id:04d} actualizada a '{cotizacion.get_estado_display()}'.")
    else:
        messages.error(request, "Estado no válido.")

    return redirect('web:gestor_dashboard')


@login_required(login_url='web:gestor_login')
@require_http_methods(['POST'])
def gestor_convertir_evento(request, cotizacion_id):
    """Convierte una cotización aprobada en un Evento contratado en firme."""
    comprobante = request.FILES.get('comprobante_pago')
    notas = request.POST.get('notas_operativas', '').strip()

    try:
        evento = EventoService.contratar_evento(
            cotizacion_id=cotizacion_id,
            comprobante_pago=comprobante,
            notas_operativas=notas
        )
        messages.success(request, f"¡Éxito! La cotización #EV68-{cotizacion_id:04d} ha sido convertida en el Evento #{evento.id:04d}.")
    except Exception as ex:
        messages.error(request, f"No se pudo contratar el evento: {str(ex)}")

    return redirect('web:gestor_dashboard')


@login_required(login_url='web:gestor_login')
@require_http_methods(['POST'])
def gestor_registrar_abono(request, evento_id):
    """Registra un abono para un evento contratado."""
    monto = Decimal(request.POST.get('monto', '0') or '0')
    descripcion = request.POST.get('descripcion', '').strip()
    comprobante = request.FILES.get('comprobante')

    try:
        pago = EventoService.registrar_abono(
            evento_id=evento_id,
            monto=monto,
            descripcion=descripcion,
            comprobante=comprobante
        )
        messages.success(request, f"Abono por ₡{pago.monto:,.2f} registrado exitosamente para el Evento #{evento_id:04d}.")
    except Exception as ex:
        messages.error(request, f"Error al registrar abono: {str(ex)}")

    return redirect('web:gestor_dashboard')


@login_required(login_url='web:gestor_login')
def gestor_detalle_cotizacion(request, cotizacion_id):
    """Vista detallada exclusiva para el personal (muestra costos internos, margen y utilidades)."""
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id)
    return render(request, 'web/gestor_detalle.html', {'cotizacion': cotizacion})

