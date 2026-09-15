from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone

from core.models import Cliente, TipoEvento, Cotizacion, Servicio


class WebAndGestorTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='colaborador', password='password123')
        self.tipo = TipoEvento.objects.create(nombre='Boda Nupcial', descripcion='Boda', activo=True)
        self.servicio = Servicio.objects.create(nombre='Alimentación', descripcion='Servicios de alimentación', activo=True)
        self.cliente = Cliente.objects.create(
            identificacion='1-2345-6789',
            nombre='Sofía Fernández',
            telefono='8888-9999',
            correo='sofia@example.com'
        )
        self.cotizacion = Cotizacion.objects.create(
            cliente=self.cliente,
            tipo_evento=self.tipo,
            fecha_evento=timezone.now().date() + timezone.timedelta(days=30),
            cantidad_personas=60,
            direccion_evento='Heredia centro',
            subtotal_servicios=Decimal('500000.00'),
            monto_ganancia=Decimal('175000.00'),
            monto_iva=Decimal('87750.00'),
            total_general=Decimal('762750.00'),
            monto_pago_inicial=Decimal('228825.00'),
            estado='Pendiente'
        )

    def test_home_page_renders_successfully(self):
        """La página de inicio debe responder 200 OK con SEO y marca."""
        res = self.client.get(reverse('web:home'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Eventos68')
        self.assertContains(res, 'Catering Service')
        self.assertContains(res, 'schema.org')
        self.assertContains(res, 'Panel Gestor')

    def test_gestor_login_redirect_unauthenticated(self):
        """Si un usuario no autenticado entra al gestor, debe ser redirigido al login."""
        res = self.client.get(reverse('web:gestor_dashboard'))
        self.assertEqual(res.status_code, 302)
        self.assertTrue('/gestor/login/' in res.url)

    def test_gestor_authenticated_access(self):
        """Un colaborador logueado accede correctamente al dashboard del gestor."""
        self.client.login(username='colaborador', password='password123')
        res = self.client.get(reverse('web:gestor_dashboard'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Panel de Gestión')
        self.assertContains(res, 'Sofía Fernández')
        self.assertContains(res, 'Pendiente')

    def test_gestor_cambiar_estado_cotizacion(self):
        """El gestor puede cambiar el estado de una cotización con 1 clic."""
        self.client.login(username='colaborador', password='password123')
        url = reverse('web:gestor_cambiar_estado', kwargs={'cotizacion_id': self.cotizacion.id})
        res = self.client.post(url, {'nuevo_estado': 'Aprobada'})
        self.assertEqual(res.status_code, 302)
        self.cotizacion.refresh_from_db()
        self.assertEqual(self.cotizacion.estado, 'Aprobada')

    def test_client_detail_view_hides_margins(self):
        """La vista del cliente no debe exponer márgenes ni desglose interno de ganancias."""
        res = self.client.get(reverse('web:detalle_cotizacion', kwargs={'cotizacion_id': self.cotizacion.id}))
        self.assertEqual(res.status_code, 200)
        self.assertNotContains(res, 'Margen Ganancia')
        self.assertNotContains(res, 'Gastos Directos Presupuestados')
        self.assertContains(res, 'Garantía de Servicio & Logística Eventos68')

    def test_studio68_landing_renders_successfully(self):
        """La página de Studio 68 debe responder 200 OK con catálogo y planes."""
        res = self.client.get(reverse('web:studio68'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Studio 68')
        self.assertContains(res, 'Invitaciones Web')
        self.assertContains(res, 'Plan Signature Interactivo')

    def test_studio68_demo_boda_renders_successfully(self):
        """La demo de la boda Maxwell & Zahilin debe responder 200 OK con datos nupciales."""
        res = self.client.get(reverse('web:studio68_demo_boda'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Maxwell &amp; Zahilin')
        self.assertContains(res, 'Quinta el Portal')
        self.assertContains(res, 'waze.com')
        self.assertContains(res, '7201-0362')
