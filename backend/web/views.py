import time
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.mail import EmailMessage
from django.core.validators import validate_email, ValidationError
from django.conf import settings
from django.db.models import Sum, Q, Count
from django.utils import timezone
from django.utils.html import strip_tags

from core.models import (
    Cliente, TipoEvento, Servicio, DetalleServicio,
    Cotizacion, DetalleCotizacion, Evento, Gasto, Pago
)
from core.services import CotizacionService, EventoService
from core.pdf_service import generar_pdf_cotizacion

ALLOWED_UPLOAD_EXTS = ('.png', '.jpg', '.jpeg', '.webp', '.pdf')
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB


def validar_archivo_seguro(archivo):
    """Valida que un archivo subido tenga extensión y peso seguros para evitar abusos o DoS."""
    if not archivo:
        return True, ""
    nombre = archivo.name.lower()
    if not any(nombre.endswith(ext) for ext in ALLOWED_UPLOAD_EXTS):
        return False, "Tipo de archivo no permitido. Solo se aceptan imágenes (.jpg, .png, .webp) o documentos (.pdf)."
    if archivo.size > MAX_UPLOAD_SIZE:
        return False, f"El archivo excede el tamaño máximo permitido de 5 MB ({archivo.size / (1024*1024):.1f} MB)."
    return True, ""


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
    Formulario interactivo de solicitud de cotización para clientes con defensas de seguridad:
    - Trampa Honeypot anti-bots automatizados.
    - Limitación de frecuencia (Rate limiting por sesión para prevenir spam y saturación).
    - Sanitización profunda de entradas (previene Stored XSS e inyecciones).
    - Validación rigurosa de tipos, correos y archivos adjuntos (hasta 5MB).
    """
    if request.method == 'POST':
        # 0. Defensa Anti-Bot: Trampa Honeypot (campo oculto a humanos)
        if request.POST.get('web_site_hp'):
            return redirect('web:home')

        # 0.1 Throttling / Rate Limiting por sesión
        now = time.time()
        last_sub = request.session.get('last_quote_time', 0)
        sub_count = request.session.get('quote_count_10m', 0)
        first_sub = request.session.get('first_quote_10m', now)

        if (now - first_sub) > 600:
            request.session['quote_count_10m'] = 1
            request.session['first_quote_10m'] = now
        else:
            if sub_count >= 8:
                messages.error(request, 'Has alcanzado el límite de solicitudes por el momento. Por favor espera unos minutos o escríbenos directamente a WhatsApp.')
                return redirect('web:solicitar')
            request.session['quote_count_10m'] = sub_count + 1

        if (now - last_sub) < 3:
            messages.warning(request, 'Por favor espera unos segundos antes de enviar otra solicitud.')
            return redirect('web:solicitar')
        request.session['last_quote_time'] = now

        try:
            # 1. Sanitización y validación de datos del cliente
            identificacion = strip_tags(request.POST.get('identificacion', ''))[:30].strip()
            nombre = strip_tags(request.POST.get('nombre', ''))[:120].strip()
            telefono = strip_tags(request.POST.get('telefono', ''))[:25].strip()
            correo = strip_tags(request.POST.get('correo', ''))[:120].strip().lower()
            direccion_cliente = strip_tags(request.POST.get('direccionCliente', ''))[:250].strip()

            if not identificacion or not nombre or not correo or not telefono:
                messages.error(request, 'Todos los campos de contacto marcados con asterisco (*) son requeridos.')
                return redirect('web:solicitar')

            try:
                validate_email(correo)
            except ValidationError:
                messages.error(request, 'El correo electrónico ingresado no tiene un formato válido.')
                return redirect('web:solicitar')

            datos_cliente = {
                'identificacion': identificacion,
                'nombre': nombre,
                'telefono': telefono,
                'correo': correo,
                'direccion': direccion_cliente,
            }

            # 2. Validación de datos del evento
            try:
                id_tipo_evento = int(request.POST.get('idTipoEvento', 0))
                cantidad_personas = int(request.POST.get('cantidadPersonas', 0))
                km_transporte = max(1, min(1000, int(request.POST.get('kilometrosTransporte', 1) or 1)))
            except (ValueError, TypeError):
                messages.error(request, 'Los valores numéricos especificados no son válidos.')
                return redirect('web:solicitar')

            fecha_evento = request.POST.get('fechaEvento')
            direccion_evento = strip_tags(request.POST.get('direccionEvento', ''))[:250].strip()

            if cantidad_personas <= 0 or cantidad_personas > 5000:
                messages.error(request, 'La cantidad de comensales debe ser entre 1 y 5,000 personas.')
                return redirect('web:solicitar')

            if not fecha_evento:
                messages.error(request, 'Debe seleccionar la fecha deseada para el evento.')
                return redirect('web:solicitar')

            # 3. Servicios y opciones seleccionadas
            modalidad = request.POST.get('requiereSaloneros', 'Bufete')
            if modalidad not in ['Bufete', 'Saloneros']:
                modalidad = 'Bufete'

            incluir_mobiliario = bool(request.POST.get('incluirMobiliario'))
            tipo_mobiliario = request.POST.get('tipoMobiliario', 'Redondas')
            if tipo_mobiliario not in ['Redondas', 'Rectangulares_8', 'Rectangulares_12']:
                tipo_mobiliario = 'Redondas'

            incluir_vajilla = not bool(request.POST.get('noVajillaCristaleria'))
            detalle_otros = strip_tags(request.POST.get('DetalleOtrosAlimentacion', ''))[:500].strip()
            imagen_decoracion = request.FILES.get('imagenDecoracion')

            # Validar seguridad de archivo subido
            if imagen_decoracion:
                es_valido, error_msg = validar_archivo_seguro(imagen_decoracion)
                if not es_valido:
                    messages.error(request, error_msg)
                    return redirect('web:solicitar')

            # 4. Extraer checkboxes de componentes seleccionados de forma controlada
            items_seleccionados = []
            for key, val in request.POST.items():
                if key.startswith('item_sel_') and val == 'on':
                    try:
                        id_det = int(key.replace('item_sel_', ''))
                        cant_especifica = request.POST.get(f'item_cant_{id_det}')
                        cant_num = int(cant_especifica) if cant_especifica and int(cant_especifica) > 0 else cantidad_personas
                        cant_num = min(10000, max(1, cant_num))
                        items_seleccionados.append({
                            'id_detalle': id_det,
                            'cantidad': cant_num
                        })
                    except (ValueError, TypeError):
                        continue

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
    
    # Agrupar detalles de gastronomía por categorías
    detalles_comida = DetalleServicio.objects.filter(activo=True)

    context = {
        'tipos_evento': tipos_evento,
        'servicios': servicios,
        'proteinas': detalles_comida.filter(categoria='Proteina'),
        'guarniciones': detalles_comida.filter(categoria='Guarnicion'),
        'ensaladas': detalles_comida.filter(categoria='Ensalada'),
        'postres': detalles_comida.filter(categoria='Postre'),
        'bebidas': detalles_comida.filter(categoria='Bebida'),
        'salsas': detalles_comida.filter(categoria='Salsa'),
        'barras_fuertes': detalles_comida.filter(categoria='Barra_Fuerte'),
        'fast_food': detalles_comida.filter(categoria='Fast_Food'),
        'snacks': detalles_comida.filter(categoria='Snack'),
        'saludable': detalles_comida.filter(categoria='Saludable'),
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
    """
    Pantalla de inicio de sesión intuitiva para el personal de Eventos68,
    reforzada con protección contra ataques de fuerza bruta y bots.
    """
    if request.user.is_authenticated:
        return redirect('web:gestor_dashboard')

    # Throttling de intentos fallidos para mitigar fuerza bruta
    failed_attempts = request.session.get('failed_login_attempts', 0)
    last_failed_time = request.session.get('last_failed_login_time', 0)
    now = time.time()

    if failed_attempts >= 5 and (now - last_failed_time) < 300:
        minutos_restantes = int((300 - (now - last_failed_time)) / 60) + 1
        messages.error(request, f"Demasiados intentos fallidos. Por seguridad, el acceso está bloqueado por {minutos_restantes} minuto(s).")
        return render(request, 'web/gestor_login.html')

    if request.method == 'POST':
        # Trampa honeypot para login
        if request.POST.get('login_hp'):
            return redirect('web:home')

        usuario = strip_tags(request.POST.get('username', '')).strip()[:50]
        clave = request.POST.get('password', '')[:128]
        user = authenticate(request, username=usuario, password=clave)

        if user is not None:
            auth_login(request, user)
            request.session['failed_login_attempts'] = 0
            messages.success(request, f"¡Bienvenido(a), {user.get_full_name() or user.username}!")
            next_url = request.GET.get('next') or 'web:gestor_dashboard'
            return redirect(next_url)
        else:
            request.session['failed_login_attempts'] = failed_attempts + 1
            request.session['last_failed_login_time'] = now
            intentos_restantes = max(0, 5 - (failed_attempts + 1))
            if intentos_restantes > 0:
                messages.error(request, f"Credenciales incorrectas. Intentos restantes antes del bloqueo: {intentos_restantes}.")
            else:
                messages.error(request, "Límite de intentos alcanzado. Acceso bloqueado temporalmente por 5 minutos.")

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
    # 1. Filtros de búsqueda sanitizados
    filtro_estado = strip_tags(request.GET.get('estado', 'Todas'))[:20]
    busqueda = strip_tags(request.GET.get('q', ''))[:80].strip()

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
    nuevo_estado = strip_tags(request.POST.get('nuevo_estado', ''))[:20]
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
    """Convierte una cotización aprobada en un Evento contratado en firme con validación de comprobante."""
    comprobante = request.FILES.get('comprobante_pago')
    notas = strip_tags(request.POST.get('notas_operativas', ''))[:500].strip()

    if comprobante:
        es_valido, error_msg = validar_archivo_seguro(comprobante)
        if not es_valido:
            messages.error(request, error_msg)
            return redirect('web:gestor_dashboard')

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
    """Registra un abono para un evento contratado con validación de montos y archivos."""
    try:
        monto_raw = request.POST.get('monto', '0') or '0'
        monto = Decimal(monto_raw)
        if monto <= 0 or monto > Decimal('50000000.00'):
            messages.error(request, "El monto del abono debe ser un valor positivo válido.")
            return redirect('web:gestor_dashboard')
    except Exception:
        messages.error(request, "El monto ingresado no tiene un formato numérico válido.")
        return redirect('web:gestor_dashboard')

    descripcion = strip_tags(request.POST.get('descripcion', ''))[:250].strip()
    comprobante = request.FILES.get('comprobante')

    if comprobante:
        es_valido, error_msg = validar_archivo_seguro(comprobante)
        if not es_valido:
            messages.error(request, error_msg)
            return redirect('web:gestor_dashboard')

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


def studio68_landing(request):
    """
    Landing page oficial de Studio 68 (División creativa de diseño y desarrollo digital para eventos).
    """
    return render(request, 'web/studio68_landing.html', {
        'titulo': 'Studio 68 — Diseño & Desarrollo Digital de Eventos',
    })


def studio68_demo_boda(request):
    """
    Muestra interactiva en vivo de Invitación Digital de Boda (Maxwell & Zahilin),
    modernizada con estándares y tendencias 2026.
    """
    return render(request, 'web/studio68_demo_boda.html', {
        'titulo': 'Maxwell & Zahilin — Invitación de Boda Digital (Demo Studio 68)',
        'pareja': 'Maxwell & Zahilin',
        'fecha_evento': '2026-12-06T15:30:00',
        'fecha_texto': 'Domingo 6 de Diciembre, 2026',
        'hora_texto': '3:30 PM',
        'lugar_nombre': 'Quinta el Portal',
        'lugar_ciudad': 'San Rafael, Heredia, Costa Rica',
        'waze_url': 'https://waze.com/ul/hd1u1nush2',
        'maps_url': 'https://maps.app.goo.gl/wYyM3q8F7Q8G7uTCA',
        'telefono_rsvp': '50672010362',
        'telefono_cotizar': '50672010362',
        'sinpe_numero': '7201-0362',
        'sinpe_raw': '72010362',
        'sinpe_titular': 'Maxwell C.',
    })

