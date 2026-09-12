from decimal import Decimal
from datetime import date, timedelta
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import Cliente, TipoEvento, Servicio, DetalleServicio, Cotizacion, Evento


class Eventos68APITestCase(APITestCase):
    def setUp(self):
        self.tipo_evento = TipoEvento.objects.create(nombre='Graduación', activo=True)
        self.servicio = Servicio.objects.create(nombre='Alimentación General', activo=True)
        self.detalle = DetalleServicio.objects.create(
            servicio=self.servicio,
            nombre_detalle='Pechuga en salsa blanca',
            costo_unitario=Decimal('3500.00'),
            categoria='Proteina',
            activo=True
        )

    def test_endpoint_dashboard_stats(self):
        url = reverse('dashboard-stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('solicitudes_pendientes', response.data)
        self.assertIn('total_recaudado_crc', response.data)
        self.assertIn('proximos_eventos', response.data)

    def test_endpoint_crear_solicitud_publica(self):
        url = reverse('cotizacion-crear-solicitud')
        payload = {
            'identificacion': '3-0123-0456',
            'nombre': 'Sofía Brenes',
            'telefono': '7777-8888',
            'correo': 'sofia@evento.com',
            'direccion_cliente': 'Cartago Centro',
            'id_tipo_evento': self.tipo_evento.id,
            'fecha_evento': (date.today() + timedelta(days=60)).strftime('%Y-%m-%d'),
            'cantidad_personas': 40,
            'direccion_evento': 'Salón El Mirador',
            'modalidad_servicio': 'Bufete',
            'incluir_mobiliario': False,
            'incluir_vajilla': False,
            'kilometros_transporte': 5,
            'items': [
                {'id_detalle': self.detalle.id, 'cantidad': 40}
            ]
        }
        response = self.client.post(url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['cliente']['nombre'], 'Sofía Brenes')
        self.assertEqual(response.data['cantidad_personas'], 40)
        self.assertEqual(response.data['estado'], 'Solicitud')
        self.assertGreater(Decimal(str(response.data['total_general'])), Decimal('0.00'))

    def test_endpoint_listar_servicios_para_flutter(self):
        url = reverse('servicio-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        self.assertIn('detalles', response.data[0])
