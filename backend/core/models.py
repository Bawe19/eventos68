from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class Cliente(models.Model):
    identificacion = models.CharField('Identificación (Cédula/Pasaporte)', max_length=50, unique=True, db_index=True)
    nombre = models.CharField('Nombre Completo', max_length=150)
    telefono = models.CharField('Teléfono', max_length=50)
    correo = models.EmailField('Correo Electrónico')
    direccion = models.TextField('Dirección Habitual', blank=True, default='')
    fecha_registro = models.DateTimeField('Fecha de Registro', auto_now_add=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.identificacion})"


class TipoEvento(models.Model):
    nombre = models.CharField('Tipo de Evento', max_length=100, unique=True)
    descripcion = models.TextField('Descripción', blank=True, default='')
    activo = models.BooleanField('Activo', default=True)

    class Meta:
        verbose_name = 'Tipo de Evento'
        verbose_name_plural = 'Tipos de Eventos'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Servicio(models.Model):
    nombre = models.CharField('Nombre del Servicio', max_length=150, unique=True)
    descripcion = models.TextField('Descripción', blank=True, default='')
    requiere_cantidad_manual = models.BooleanField('¿Requiere cantidad manual?', default=False)
    activo = models.BooleanField('Activo', default=True)

    class Meta:
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'
        ordering = ['id']

    def __str__(self):
        return self.nombre


class DetalleServicio(models.Model):
    CATEGORIA_CHOICES = [
        ('Guarnicion', 'Guarnición'),
        ('Proteina', 'Proteína'),
        ('Ensalada', 'Ensalada'),
        ('Postre', 'Postre'),
        ('Bebida', 'Bebida'),
        ('Salsa', 'Salsa'),
        ('Barra_Fuerte', 'Barra Fuerte / Típica'),
        ('Fast_Food', 'Carrito Fast Food'),
        ('Snack', 'Carrito de Snacks & Dulces'),
        ('Saludable', 'Estación Saludable'),
        ('Manualidades', 'Estación de Manualidades & Creatividad'),
        ('Mesa', 'Mesa'),
        ('Silla', 'Silla'),
        ('Mantel', 'Mantel'),
        ('Vajilla', 'Vajilla'),
        ('Cristaleria', 'Cristalería'),
        ('Transporte', 'Transporte'),
        ('Otro', 'Otro Componente'),
    ]

    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE, related_name='detalles')
    nombre_detalle = models.CharField('Nombre del Componente', max_length=150)
    costo_unitario = models.DecimalField('Costo Unitario (CRC)', max_digits=12, decimal_places=2, default=0.00)
    unidad_medida = models.CharField('Unidad de Medida', max_length=50, default='Por persona')
    categoria = models.CharField('Categoría', max_length=50, choices=CATEGORIA_CHOICES, blank=True, null=True)
    activo = models.BooleanField('Activo', default=True)

    class Meta:
        verbose_name = 'Componente de Servicio'
        verbose_name_plural = 'Componentes de Servicios'
        ordering = ['servicio', 'categoria', 'nombre_detalle']

    def __str__(self):
        return f"{self.servicio.nombre} - {self.nombre_detalle} (₡{self.costo_unitario:,.2f})"


class ConfiguracionGanancia(models.Model):
    porcentaje = models.DecimalField('Porcentaje de Ganancia (%)', max_digits=5, decimal_places=2, default=30.00)
    activa = models.BooleanField('Activa', default=True)
    fecha_registro = models.DateTimeField('Fecha de Registro', auto_now_add=True)

    class Meta:
        verbose_name = 'Configuración de Ganancia'
        verbose_name_plural = 'Configuraciones de Ganancia'
        ordering = ['-fecha_registro']

    def save(self, *args, **kwargs):
        if self.activa:
            ConfiguracionGanancia.objects.filter(activa=True).update(activa=False)
        super().save(*args, **kwargs)

    @classmethod
    def obtener_activa(cls):
        config = cls.objects.filter(activa=True).first()
        return config.porcentaje if config else Decimal('30.00')

    def __str__(self):
        return f"{self.porcentaje}% ({'Activa' if self.activa else 'Inactiva'})"


class ConfiguracionPagoInicial(models.Model):
    porcentaje = models.DecimalField('Porcentaje Pago Inicial (%)', max_digits=5, decimal_places=2, default=10.00)
    activa = models.BooleanField('Activa', default=True)
    fecha_registro = models.DateTimeField('Fecha de Registro', auto_now_add=True)

    class Meta:
        verbose_name = 'Configuración Pago Inicial'
        verbose_name_plural = 'Configuraciones Pago Inicial'
        ordering = ['-fecha_registro']

    def save(self, *args, **kwargs):
        if self.activa:
            ConfiguracionPagoInicial.objects.filter(activa=True).update(activa=False)
        super().save(*args, **kwargs)

    @classmethod
    def obtener_activa(cls):
        config = cls.objects.filter(activa=True).first()
        return config.porcentaje if config else Decimal('10.00')

    def __str__(self):
        return f"{self.porcentaje}% ({'Activa' if self.activa else 'Inactiva'})"


class Cotizacion(models.Model):
    ESTADO_CHOICES = [
        ('Solicitud', 'Solicitud Pendiente'),
        ('Cotizacion', 'Cotización Formal'),
        ('Evento', 'Evento Contratado'),
        ('Cancelada', 'Cancelada'),
    ]

    MODALIDAD_CHOICES = [
        ('Saloneros', 'Servicio a la mesa con Saloneros'),
        ('Bufete', 'Tipo bufete (Autoservicio)'),
        ('NoAplica', 'No Aplica'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='cotizaciones')
    tipo_evento = models.ForeignKey(TipoEvento, on_delete=models.PROTECT, related_name='cotizaciones')
    fecha_evento = models.DateField('Fecha del Evento')
    cantidad_personas = models.PositiveIntegerField('Cantidad de Personas / Invitados')
    direccion_evento = models.TextField('Dirección Exacta del Evento', blank=True, default='')
    punto_salida = models.CharField('Punto o Dirección de Salida / Origen', max_length=255, blank=True, default='')
    estado = models.CharField('Estado', max_length=20, choices=ESTADO_CHOICES, default='Solicitud', db_index=True)
    modalidad_servicio = models.CharField('Modalidad', max_length=20, choices=MODALIDAD_CHOICES, default='Bufete')
    fecha_registro = models.DateTimeField('Fecha de Registro', auto_now_add=True)
    alergias_restricciones = models.TextField('Alergias o Restricciones Alimentarias', blank=True, default='No presenta / No aplica')
    detalles_preparacion = models.TextField('Preferencias de Preparación, Salsas y Guarniciones', blank=True, default='')
    notas_adicionales = models.TextField('Notas Adicionales', blank=True, default='')

    # Campos financieros calculados y persistidos
    subtotal_servicios = models.DecimalField('Subtotal Servicios (CRC)', max_digits=14, decimal_places=2, default=0.00)
    total_gastos = models.DecimalField('Total Gastos Directos (CRC)', max_digits=14, decimal_places=2, default=0.00)
    porcentaje_ganancia = models.DecimalField('% Ganancia', max_digits=5, decimal_places=2, default=30.00)
    monto_ganancia = models.DecimalField('Monto Ganancia (CRC)', max_digits=14, decimal_places=2, default=0.00)
    porcentaje_iva = models.DecimalField('% IVA', max_digits=5, decimal_places=2, default=13.00)
    monto_iva = models.DecimalField('Monto IVA (CRC)', max_digits=14, decimal_places=2, default=0.00)
    total_general = models.DecimalField('Total General (CRC)', max_digits=14, decimal_places=2, default=0.00)
    total_por_persona = models.DecimalField('Total por Persona (CRC)', max_digits=14, decimal_places=2, default=0.00)
    porcentaje_pago_inicial = models.DecimalField('% Pago Inicial', max_digits=5, decimal_places=2, default=10.00)
    monto_pago_inicial = models.DecimalField('Monto Pago Inicial / Adelanto (CRC)', max_digits=14, decimal_places=2, default=0.00)

    class Meta:
        verbose_name = 'Cotización'
        verbose_name_plural = 'Cotizaciones'
        ordering = ['-fecha_registro']

    def __str__(self):
        return f"Cotización #{self.id} - {self.cliente.nombre} ({self.tipo_evento.nombre} - {self.fecha_evento})"

    def recalcular_totales(self, save=True):
        """
        Calcula rigurosamente los totales financieros del presupuesto:
        Subtotal Servicios + Gastos + Ganancia + IVA 13% = Total General
        """
        # 1. Subtotal de servicios
        detalles = self.detalles.all()
        subtotal_servicios = sum((d.subtotal for d in detalles), Decimal('0.00'))

        # 2. Total de gastos directos asociados
        gastos = self.gastos.all()
        total_gastos = sum((g.monto for g in gastos), Decimal('0.00'))

        # 3. Ganancia
        pct_ganancia = Decimal(str(self.porcentaje_ganancia if self.porcentaje_ganancia and self.porcentaje_ganancia > 0 else ConfiguracionGanancia.obtener_activa()))
        base_imponible = subtotal_servicios + total_gastos
        monto_ganancia = (base_imponible * (pct_ganancia / Decimal('100.00'))).quantize(Decimal('0.01'))

        # 4. Subtotal neto e IVA (13%)
        subtotal_neto = base_imponible + monto_ganancia
        pct_iva = Decimal(str(self.porcentaje_iva if self.porcentaje_iva and self.porcentaje_iva > 0 else '13.00'))
        monto_iva = (subtotal_neto * (pct_iva / Decimal('100.00'))).quantize(Decimal('0.01'))
        total_general = subtotal_neto + monto_iva

        # 5. Costo por persona
        cant_personas = self.cantidad_personas if self.cantidad_personas > 0 else 1
        total_por_persona = (total_general / Decimal(cant_personas)).quantize(Decimal('0.01'))

        # 6. Pago Inicial requerido
        pct_pago_inicial = Decimal(str(self.porcentaje_pago_inicial if self.porcentaje_pago_inicial and self.porcentaje_pago_inicial > 0 else ConfiguracionPagoInicial.obtener_activa()))
        monto_pago_inicial = (total_general * (pct_pago_inicial / Decimal('100.00'))).quantize(Decimal('0.01'))

        # Actualizar valores
        self.subtotal_servicios = subtotal_servicios
        self.total_gastos = total_gastos
        self.porcentaje_ganancia = pct_ganancia
        self.monto_ganancia = monto_ganancia
        self.porcentaje_iva = pct_iva
        self.monto_iva = monto_iva
        self.total_general = total_general
        self.total_por_persona = total_por_persona
        self.porcentaje_pago_inicial = pct_pago_inicial
        self.monto_pago_inicial = monto_pago_inicial

        if save:
            self.save(update_fields=[
                'subtotal_servicios', 'total_gastos', 'porcentaje_ganancia',
                'monto_ganancia', 'porcentaje_iva', 'monto_iva', 'total_general',
                'total_por_persona', 'porcentaje_pago_inicial', 'monto_pago_inicial'
            ])
        return self


class DetalleCotizacion(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='detalles')
    servicio = models.ForeignKey(Servicio, on_delete=models.PROTECT, related_name='detalles_cotizacion')
    detalle_servicio = models.ForeignKey(DetalleServicio, on_delete=models.SET_NULL, null=True, blank=True, related_name='detalles_cotizacion')
    nombre_personalizado = models.CharField('Nombre Personalizado', max_length=150, blank=True, default='')
    costo_unitario = models.DecimalField('Costo Unitario (CRC)', max_digits=12, decimal_places=2, default=0.00)
    cantidad = models.PositiveIntegerField('Cantidad', default=1)
    subtotal = models.DecimalField('Subtotal (CRC)', max_digits=14, decimal_places=2, default=0.00)
    requiere_saloneros = models.BooleanField('¿Requiere Saloneros?', null=True, blank=True)
    es_bufete = models.BooleanField('¿Es Bufete?', null=True, blank=True)
    imagen_referencia = models.ImageField('Imagen de Referencia (Decoración)', upload_to='imagenes_referencia/', blank=True, null=True)
    detalle_personalizado = models.TextField('Detalle Personalizado / Notas', blank=True, null=True)

    class Meta:
        verbose_name = 'Detalle de Cotización'
        verbose_name_plural = 'Detalles de Cotización'
        ordering = ['servicio', 'detalle_servicio']

    def save(self, *args, **kwargs):
        if not self.costo_unitario and self.detalle_servicio:
            self.costo_unitario = self.detalle_servicio.costo_unitario
        self.subtotal = (self.costo_unitario * Decimal(self.cantidad)).quantize(Decimal('0.01'))
        super().save(*args, **kwargs)

    def __str__(self):
        nombre = self.detalle_servicio.nombre_detalle if self.detalle_servicio else self.nombre_personalizado or self.servicio.nombre
        return f"{self.servicio.nombre} - {nombre} x {self.cantidad} = ₡{self.subtotal:,.2f}"


class Evento(models.Model):
    ESTADO_CHOICES = [
        ('Contratado', 'Contratado'),
        ('EnProceso', 'En Preparación'),
        ('Finalizado', 'Finalizado'),
        ('Cancelado', 'Cancelado'),
    ]

    cotizacion = models.OneToOneField(Cotizacion, on_delete=models.PROTECT, related_name='evento')
    fecha_evento = models.DateField('Fecha del Evento', unique=True,
                                    error_messages={'unique': 'Ya existe un evento contratado para esta fecha. Eventos68 solo atiende un evento exclusivo por día.'})
    cantidad_personas = models.PositiveIntegerField('Cantidad de Personas')
    estado = models.CharField('Estado', max_length=20, choices=ESTADO_CHOICES, default='Contratado')
    fecha_contratacion = models.DateTimeField('Fecha de Contratación', auto_now_add=True)
    notas_operativas = models.TextField('Notas de Logística / Montaje', blank=True, default='')

    class Meta:
        verbose_name = 'Evento Contratado'
        verbose_name_plural = 'Eventos Contratados'
        ordering = ['fecha_evento']

    def clean(self):
        if self.fecha_evento < timezone.now().date():
            raise ValidationError('La fecha del evento no puede ser en el pasado.')
        # Validar unicidad de fecha
        conflicto = Evento.objects.filter(fecha_evento=self.fecha_evento).exclude(id=self.id).exists()
        if conflicto:
            raise ValidationError('Ya existe un evento contratado para esta fecha.')

    @property
    def total_abonado(self):
        return sum((p.monto for p in self.pagos.all()), Decimal('0.00'))

    @property
    def saldo_pendiente(self):
        return max(Decimal('0.00'), self.cotizacion.total_general - self.total_abonado)

    @property
    def dias_restantes(self):
        hoy = timezone.now().date()
        return (self.fecha_evento - hoy).days

    def __str__(self):
        return f"Evento #{self.id}: {self.cotizacion.cliente.nombre} ({self.fecha_evento})"


class Gasto(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='gastos')
    evento = models.ForeignKey(Evento, on_delete=models.SET_NULL, null=True, blank=True, related_name='gastos')
    descripcion = models.CharField('Descripción del Gasto', max_length=250)
    monto = models.DecimalField('Monto del Gasto (CRC)', max_digits=12, decimal_places=2)
    comprobante = models.ImageField('Comprobante de Gasto', upload_to='comprobantes_gastos/', blank=True, null=True)
    fecha_gasto = models.DateField('Fecha del Gasto', default=timezone.now)

    class Meta:
        verbose_name = 'Gasto Directo'
        verbose_name_plural = 'Gastos Directos'
        ordering = ['-fecha_gasto']

    def __str__(self):
        return f"{self.descripcion}: ₡{self.monto:,.2f}"


class Pago(models.Model):
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name='pagos')
    descripcion = models.CharField('Descripción / Concepto', max_length=250, default='Abono a presupuesto de evento')
    monto = models.DecimalField('Monto Abonado (CRC)', max_digits=12, decimal_places=2)
    fecha_pago = models.DateTimeField('Fecha de Pago', default=timezone.now)
    comprobante_pago = models.ImageField('Comprobante de Transferencia / Recibo', upload_to='comprobantes_pago/', blank=True, null=True)

    class Meta:
        verbose_name = 'Abono / Pago'
        verbose_name_plural = 'Abonos y Pagos'
        ordering = ['-fecha_pago']

    def __str__(self):
        return f"Pago ₡{self.monto:,.2f} ({self.evento})"
