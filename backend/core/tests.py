from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from core.models import (
    Cliente, TipoEvento, Servicio, DetalleServicio,
    Cotizacion, DetalleCotizacion, Evento, Gasto, Pago,
    ConfiguracionGanancia, ConfiguracionPagoInicial
)
from core.services import CotizacionService, EventoService
from core.pdf_service import generar_pdf_cotizacion


class Eventos68DomainTestCase(TestCase):
    def setUp(self):
        # Configuraciones
        ConfiguracionGanancia.objects.create(porcentaje=Decimal('30.00'), activa=True)
        ConfiguracionPagoInicial.objects.create(porcentaje=Decimal('10.00'), activa=True)

        # Tipo de evento
        self.tipo_evento = TipoEvento.objects.create(nombre='Boda', activo=True)

        # Servicios
        self.serv_alim = Servicio.objects.create(nombre='Servicio de Alimentación', activo=True)
        self.serv_vajilla = Servicio.objects.create(nombre='Vajilla Básica', activo=True)
        self.serv_mobi = Servicio.objects.create(nombre='Mobiliario y Mantelería', activo=True)

        # Componentes
        self.plomito = DetalleServicio.objects.create(
            servicio=self.serv_alim,
            nombre_detalle='Lomito a la parrilla',
            costo_unitario=Decimal('4000.00'),
            categoria='Proteina',
            activo=True
        )
        self.postre = DetalleServicio.objects.create(
            servicio=self.serv_alim,
            nombre_detalle='Flan de caramelo',
            costo_unitario=Decimal('1000.00'),
            categoria='Postre',
            activo=True
        )
        self.plato = DetalleServicio.objects.create(
            servicio=self.serv_vajilla,
            nombre_detalle='Plato base',
            costo_unitario=Decimal('300.00'),
            categoria='Vajilla',
            activo=True
        )
        self.silla = DetalleServicio.objects.create(
            servicio=self.serv_mobi,
            nombre_detalle='Silla vestida',
            costo_unitario=Decimal('500.00'),
            categoria='Silla',
            activo=True
        )
        self.mesa = DetalleServicio.objects.create(
            servicio=self.serv_mobi,
            nombre_detalle='Mesa redonda',
            costo_unitario=Decimal('3000.00'),
            categoria='Mesa',
            activo=True
        )
        self.mantel = DetalleServicio.objects.create(
            servicio=self.serv_mobi,
            nombre_detalle='Mantel redondo',
            costo_unitario=Decimal('1000.00'),
            categoria='Mantel',
            activo=True
        )

    def test_creacion_solicitud_y_calculo_financiero(self):
        """Prueba que el motor financiero y las automatizaciones calculan rigurosamente los totales."""
        fecha = date.today() + timedelta(days=30)
        datos_cliente = {
            'identificacion': '1-2345-6789',
            'nombre': 'Carlos Rodríguez',
            'telefono': '8888-9999',
            'correo': 'carlos@test.com',
            'direccion': 'San José, Curridabat'
        }

        cotizacion = CotizacionService.crear_solicitud(
            datos_cliente=datos_cliente,
            id_tipo_evento=self.tipo_evento.id,
            fecha_evento=fecha,
            cantidad_personas=50,
            direccion_evento='Hacienda El Prado',
            items_seleccionados=[
                {'id_detalle': self.plomito.id, 'cantidad': 50},
                {'id_detalle': self.postre.id, 'cantidad': 50},
            ],
            modalidad_servicio='Bufete',
            incluir_mobiliario=True,
            tipo_mobiliario='Redondas',
            incluir_vajilla=True
        )

        # Verificaciones del cliente
        self.assertEqual(cotizacion.cliente.nombre, 'Carlos Rodríguez')
        self.assertEqual(cotizacion.cantidad_personas, 50)
        self.assertEqual(cotizacion.estado, 'Solicitud')

        # Verificaciones de componentes automáticos
        detalles = cotizacion.detalles.all()
        nombres = [d.detalle_servicio.nombre_detalle for d in detalles if d.detalle_servicio]
        self.assertIn('Plato base', nombres)
        self.assertIn('Silla vestida', nombres)
        self.assertIn('Mesa redonda', nombres)
        self.assertIn('Mantel redondo', nombres)

        # Para 50 personas con mesas redondas (10 pax c/u) deben ser 5 mesas y 5 manteles
        mesa_det = detalles.filter(detalle_servicio=self.mesa).first()
        self.assertIsNotNone(mesa_det)
        self.assertEqual(mesa_det.cantidad, 5)

        # Verificación financiera
        # Total General = Subtotal + Gastos + 30% Ganancia + 13% IVA
        self.assertGreater(cotizacion.subtotal_servicios, Decimal('0.00'))
        self.assertGreater(cotizacion.total_general, cotizacion.subtotal_servicios)
        self.assertGreater(cotizacion.monto_pago_inicial, Decimal('0.00'))
        # Pago inicial debe ser 10% del total general
        esperado_adelanto = (cotizacion.total_general * Decimal('0.10')).quantize(Decimal('0.01'))
        self.assertEqual(cotizacion.monto_pago_inicial, esperado_adelanto)

    def test_regla_negocio_exclusividad_fecha_evento(self):
        """Verifica que el sistema rechace dos eventos contratados el mismo día."""
        fecha = date.today() + timedelta(days=45)
        cli1 = Cliente.objects.create(identificacion='111', nombre='Cliente 1', telefono='11', correo='c1@t.com')
        cli2 = Cliente.objects.create(identificacion='222', nombre='Cliente 2', telefono='22', correo='c2@t.com')

        cot1 = Cotizacion.objects.create(
            cliente=cli1, tipo_evento=self.tipo_evento, fecha_evento=fecha,
            cantidad_personas=100, estado='Cotizacion'
        )
        DetalleCotizacion.objects.create(cotizacion=cot1, servicio=self.serv_alim, cantidad=100, costo_unitario=1000)
        cot1.recalcular_totales(save=True)

        cot2 = Cotizacion.objects.create(
            cliente=cli2, tipo_evento=self.tipo_evento, fecha_evento=fecha,
            cantidad_personas=80, estado='Cotizacion'
        )
        DetalleCotizacion.objects.create(cotizacion=cot2, servicio=self.serv_alim, cantidad=80, costo_unitario=1000)
        cot2.recalcular_totales(save=True)

        # Contratar el primer evento debe funcionar
        ev1 = EventoService.contratar_evento(cot1.id)
        self.assertIsNotNone(ev1)
        self.assertEqual(ev1.estado, 'Contratado')

        # Intentar contratar el segundo evento para la MISMA fecha DEBE lanzar ValidationError
        with self.assertRaises(ValidationError):
            EventoService.contratar_evento(cot2.id)

    def test_generacion_pdf(self):
        """Prueba que el servicio de PDF genere bytes válidos con encabezado PDF."""
        cli = Cliente.objects.create(identificacion='999', nombre='Ana Soto', telefono='888', correo='ana@t.com')
        cot = Cotizacion.objects.create(
            cliente=cli, tipo_evento=self.tipo_evento, fecha_evento=date.today() + timedelta(days=20),
            cantidad_personas=30, estado='Cotizacion'
        )
        DetalleCotizacion.objects.create(
            cotizacion=cot, servicio=self.serv_alim, detalle_servicio=self.plomito,
            cantidad=30, costo_unitario=Decimal('4000.00')
        )
        cot.recalcular_totales(save=True)

        pdf_bytes = generar_pdf_cotizacion(cot)
        self.assertTrue(len(pdf_bytes) > 500)
        self.assertTrue(pdf_bytes.startswith(b'%PDF-'))
