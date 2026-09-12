from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    Cliente, TipoEvento, Servicio, DetalleServicio,
    ConfiguracionGanancia, ConfiguracionPagoInicial,
    Cotizacion, DetalleCotizacion, Evento, Gasto, Pago
)


admin.site.site_header = "Eventos68 - Administración de Catering & Eventos"
admin.site.site_title = "Eventos68 Portal"
admin.site.index_title = "Panel de Control Operativo"


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('identificacion', 'nombre', 'telefono', 'correo', 'fecha_registro')
    search_fields = ('identificacion', 'nombre', 'telefono', 'correo')
    list_per_page = 25


@admin.register(TipoEvento)
class TipoEventoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo')
    list_editable = ('activo',)
    search_fields = ('nombre',)


class DetalleServicioInline(admin.TabularInline):
    model = DetalleServicio
    extra = 1
    fields = ('nombre_detalle', 'costo_unitario', 'unidad_medida', 'categoria', 'activo')


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'requiere_cantidad_manual', 'activo', 'cantidad_componentes')
    list_filter = ('activo', 'requiere_cantidad_manual')
    search_fields = ('nombre', 'descripcion')
    inlines = [DetalleServicioInline]

    def cantidad_componentes(self, obj):
        return obj.detalles.count()
    cantidad_componentes.short_description = "Componentes"


@admin.register(DetalleServicio)
class DetalleServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre_detalle', 'servicio', 'categoria', 'costo_unitario_formateado', 'unidad_medida', 'activo')
    list_filter = ('servicio', 'categoria', 'activo')
    search_fields = ('nombre_detalle', 'servicio__nombre')
    list_editable = ('activo',)

    def costo_unitario_formateado(self, obj):
        return f"₡{obj.costo_unitario:,.2f}"
    costo_unitario_formateado.short_description = "Costo Unitario"


class DetalleCotizacionInline(admin.TabularInline):
    model = DetalleCotizacion
    extra = 0
    fields = ('servicio', 'detalle_servicio', 'cantidad', 'costo_unitario', 'subtotal')
    readonly_fields = ('subtotal',)


class GastoInline(admin.TabularInline):
    model = Gasto
    extra = 0
    fields = ('descripcion', 'monto', 'fecha_gasto', 'comprobante')


@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = ('numero_cotizacion', 'cliente', 'tipo_evento', 'fecha_evento',
                    'cantidad_personas', 'estado_badge', 'total_general_formateado',
                    'adelanto_formateado', 'acciones_pdf')
    list_filter = ('estado', 'tipo_evento', 'fecha_evento')
    search_fields = ('id', 'cliente__nombre', 'cliente__identificacion', 'cliente__telefono')
    readonly_fields = ('subtotal_servicios', 'total_gastos', 'monto_ganancia',
                       'monto_iva', 'total_general', 'total_por_persona',
                       'monto_pago_inicial', 'fecha_registro')
    inlines = [DetalleCotizacionInline, GastoInline]
    actions = ['recalcular_seleccionadas']

    def numero_cotizacion(self, obj):
        return f"EV68-{obj.id:04d}"
    numero_cotizacion.short_description = "# Cotización"

    def estado_badge(self, obj):
        colores = {
            'Solicitud': 'orange',
            'Cotizacion': '#0284c7',
            'Evento': 'green',
            'Cancelada': 'red',
        }
        color = colores.get(obj.estado, 'gray')
        return format_html(f'<span style="background-color: {color}; color: white; padding: 3px 8px; border-radius: 12px; font-weight: bold; font-size: 11px;">{obj.get_estado_display()}</span>')
    estado_badge.short_description = "Estado"

    def total_general_formateado(self, obj):
        return f"₡{obj.total_general:,.2f}"
    total_general_formateado.short_description = "Total General"

    def adelanto_formateado(self, obj):
        return f"₡{obj.monto_pago_inicial:,.2f}"
    adelanto_formateado.short_description = "Pago Inicial (Adelanto)"

    def acciones_pdf(self, obj):
        url = reverse('web:descargar_pdf', args=[obj.id])
        return format_html(f'<a class="button" href="{url}" target="_blank" style="background:#b45309; color:white; padding:4px 8px; border-radius:4px; text-decoration:none;">📄 Ver PDF</a>')
    acciones_pdf.short_description = "Presupuesto"

    def recalcular_seleccionadas(self, request, queryset):
        for cot in queryset:
            cot.recalcular_totales(save=True)
        self.message_user(request, f"Se recalcularon exitosamente {queryset.count()} cotizaciones.")
    recalcular_seleccionadas.short_description = "Recalcular totales financieros"


class PagoInline(admin.TabularInline):
    model = Pago
    extra = 1
    fields = ('descripcion', 'monto', 'fecha_pago', 'comprobante_pago')


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente_nombre', 'tipo_evento', 'fecha_evento',
                    'cantidad_personas', 'estado', 'total_general', 'total_abonado_display',
                    'saldo_pendiente_display', 'dias_restantes_display')
    list_filter = ('estado', 'fecha_evento')
    search_fields = ('cotizacion__cliente__nombre', 'cotizacion__cliente__identificacion')
    inlines = [PagoInline, GastoInline]

    def cliente_nombre(self, obj):
        return obj.cotizacion.cliente.nombre
    cliente_nombre.short_description = "Cliente"

    def tipo_evento(self, obj):
        return obj.cotizacion.tipo_evento.nombre
    tipo_evento.short_description = "Tipo de Evento"

    def total_general(self, obj):
        return f"₡{obj.cotizacion.total_general:,.2f}"
    total_general.short_description = "Total Presupuesto"

    def total_abonado_display(self, obj):
        return f"₡{obj.total_abonado:,.2f}"
    total_abonado_display.short_description = "Abonado"

    def saldo_pendiente_display(self, obj):
        color = 'red' if obj.saldo_pendiente > 0 else 'green'
        return format_html(f'<b style="color:{color};">₡{obj.saldo_pendiente:,.2f}</b>')
    saldo_pendiente_display.short_description = "Saldo Pendiente"

    def dias_restantes_display(self, obj):
        dias = obj.dias_restantes
        if dias < 0:
            return format_html('<span style="color:gray;">Finalizado</span>')
        elif dias <= 7:
            return format_html(f'<span style="color:red; font-weight:bold;">¡{dias} días!</span>')
        return f"{dias} días"
    dias_restantes_display.short_description = "Días Faltantes"


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('id', 'evento', 'monto_formateado', 'fecha_pago', 'comprobante_link')
    list_filter = ('fecha_pago',)
    search_fields = ('descripcion', 'evento__cotizacion__cliente__nombre')

    def monto_formateado(self, obj):
        return f"₡{obj.monto:,.2f}"
    monto_formateado.short_description = "Monto Abonado"

    def comprobante_link(self, obj):
        if obj.comprobante_pago:
            return format_html(f'<a href="{obj.comprobante_pago.url}" target="_blank">Ver Recibo</a>')
        return "Sin comprobante"
    comprobante_link.short_description = "Comprobante"


@admin.register(Gasto)
class GastoAdmin(admin.ModelAdmin):
    list_display = ('id', 'descripcion', 'monto_formateado', 'fecha_gasto', 'cotizacion', 'evento')
    list_filter = ('fecha_gasto',)
    search_fields = ('descripcion',)

    def monto_formateado(self, obj):
        return f"₡{obj.monto:,.2f}"
    monto_formateado.short_description = "Monto"


@admin.register(ConfiguracionGanancia)
class ConfiguracionGananciaAdmin(admin.ModelAdmin):
    list_display = ('porcentaje', 'activa', 'fecha_registro')
    list_editable = ('activa',)


@admin.register(ConfiguracionPagoInicial)
class ConfiguracionPagoInicialAdmin(admin.ModelAdmin):
    list_display = ('porcentaje', 'activa', 'fecha_registro')
    list_editable = ('activa',)
