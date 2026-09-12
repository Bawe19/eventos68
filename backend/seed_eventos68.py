"""
Script para inicializar la base de datos de Eventos68 con el catálogo completo
de servicios, componentes, configuraciones financieras y tipos de evento.
"""

import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import (
    TipoEvento, Servicio, DetalleServicio,
    ConfiguracionGanancia, ConfiguracionPagoInicial
)


def seed():
    print("Iniciando carga de datos para Eventos68...")

    # 1. Configuraciones comerciales
    ConfiguracionGanancia.objects.get_or_create(porcentaje=Decimal('30.00'), defaults={'activa': True})
    ConfiguracionPagoInicial.objects.get_or_create(porcentaje=Decimal('10.00'), defaults={'activa': True})
    print("Configuraciones comerciales establecidas (Ganancia: 30%, Pago Inicial: 10%).")

    # 2. Tipos de Eventos
    tipos = [
        ('Boda', 'Celebraciones nupciales, ceremonias civiles y banquetes de gala.'),
        ('Cumpleaños / Quinceaños', 'Fiestas de aniversario, fiestas de 15 años y reuniones familiares.'),
        ('Graduación', 'Celebraciones de fin de cursos escolares y universitarios.'),
        ('Evento Corporativo', 'Lanzamientos de producto, aniversarios de empresa y convivios.'),
        ('Baby Shower / Bautizo', 'Reuniones íntimas y familiares diurnas.'),
        ('Parrillada al Aire Libre', 'Asados campestres, quintas y celebraciones informales.'),
    ]
    for nombre, desc in tipos:
        TipoEvento.objects.get_or_create(nombre=nombre, defaults={'descripcion': desc, 'activo': True})
    print(f"Se crearon/verificaron {len(tipos)} tipos de eventos.")

    # 3. Servicios Principales
    servicios_data = [
        ('Servicio de Alimentación', 'Menús completos de parrillada, platos fuertes, guarniciones y postres.', False),
        ('Servicio de Decoración', 'Montaje temático, centros de mesa, telas y arreglos florales.', False),
        ('Vajilla Básica', 'Platería, cubertería de acero inoxidable y servilletas de tela.', False),
        ('Cristalería Básica', 'Copas de brindis y vasos de cristal para bebidas.', False),
        ('Mobiliario y Mantelería', 'Sillas ejecutivas vestidas, mesas y manteles de gala.', False),
        ('Saloneros y Atención', 'Personal calificado para protocolo y servicio a la mesa.', True),
        ('Transporte y Logística', 'Traslado de equipo, vajilla e insumos según kilometraje.', True),
    ]

    servicios_dict = {}
    for nombre, desc, req_manual in servicios_data:
        s, _ = Servicio.objects.get_or_create(
            nombre=nombre,
            defaults={'descripcion': desc, 'requiere_cantidad_manual': req_manual, 'activo': True}
        )
        servicios_dict[nombre] = s
    print("Servicios principales creados.")

    # 4. Componentes y Detalles de Servicios
    detalles = [
        # ALIMENTACIÓN - PROTEÍNAS
        (servicios_dict['Servicio de Alimentación'], 'Lomito de res a la parrilla en salsa de hongos', Decimal('4500.00'), 'Porción', 'Proteina'),
        (servicios_dict['Servicio de Alimentación'], 'Costilla de cerdo en salsa BBQ ahumada artesanal', Decimal('3800.00'), 'Porción', 'Proteina'),
        (servicios_dict['Servicio de Alimentación'], 'Pechuga de pollo a las finas hierbas y crema blanca', Decimal('3200.00'), 'Porción', 'Proteina'),
        (servicios_dict['Servicio de Alimentación'], 'Churrasco clásico con chimichurri', Decimal('4200.00'), 'Porción', 'Proteina'),
        (servicios_dict['Servicio de Alimentación'], 'Parrillada mixta (Carne, Pollo y Chorizo artesanal)', Decimal('4900.00'), 'Porción', 'Proteina'),

        # ALIMENTACIÓN - GUARNICIONES
        (servicios_dict['Servicio de Alimentación'], 'Arroz con palmito tradicional gratinado', Decimal('950.00'), 'Porción', 'Guarnicion'),
        (servicios_dict['Servicio de Alimentación'], 'Arroz blanco aromático con finas hierbas', Decimal('700.00'), 'Porción', 'Guarnicion'),
        (servicios_dict['Servicio de Alimentación'], 'Papas asadas al romero con mantequilla de ajo', Decimal('850.00'), 'Porción', 'Guarnicion'),
        (servicios_dict['Servicio de Alimentación'], 'Puré de camote rústico caramelizado', Decimal('900.00'), 'Porción', 'Guarnicion'),
        (servicios_dict['Servicio de Alimentación'], 'Vegetales salteados al vapor en mantequilla clarificada', Decimal('800.00'), 'Porción', 'Guarnicion'),

        # ALIMENTACIÓN - ENSALADAS
        (servicios_dict['Servicio de Alimentación'], 'Ensalada verde mixta con aderezo de maracuyá', Decimal('750.00'), 'Porción', 'Ensalada'),
        (servicios_dict['Servicio de Alimentación'], 'Ensalada César clásica con crutones y queso parmesano', Decimal('850.00'), 'Porción', 'Ensalada'),
        (servicios_dict['Servicio de Alimentación'], 'Ensalada de papa con aderezo cremosa de eneldo', Decimal('800.00'), 'Porción', 'Ensalada'),

        # ALIMENTACIÓN - POSTRES
        (servicios_dict['Servicio de Alimentación'], 'Flan de caramelo artesanal', Decimal('1100.00'), 'Porción', 'Postre'),
        (servicios_dict['Servicio de Alimentación'], 'Tres leches tradicional costarricense', Decimal('1200.00'), 'Porción', 'Postre'),
        (servicios_dict['Servicio de Alimentación'], 'Tarta húmeda de chocolate belga', Decimal('1300.00'), 'Porción', 'Postre'),

        # ALIMENTACIÓN - BEBIDAS Y SALSAS
        (servicios_dict['Servicio de Alimentación'], 'Té frío natural con infusión de limón y hierbabuena', Decimal('500.00'), 'Vaso', 'Bebida'),
        (servicios_dict['Servicio de Alimentación'], 'Gaseosas variadas de lata', Decimal('800.00'), 'Unidad', 'Bebida'),
        (servicios_dict['Servicio de Alimentación'], 'Salsa Chimichurri casero especial', Decimal('200.00'), 'Porción', 'Salsa'),

        # DECORACIÓN
        (servicios_dict['Servicio de Decoración'], 'Decoración Temática Floral de Mesas', Decimal('25000.00'), 'Servicio', 'Otro'),
        (servicios_dict['Servicio de Decoración'], 'Arco de Entrada con Globos y Luces Vintage', Decimal('35000.00'), 'Servicio', 'Otro'),

        # VAJILLA
        (servicios_dict['Vajilla Básica'], 'Plato base y plato principal de porcelana', Decimal('300.00'), 'Por persona', 'Vajilla'),
        (servicios_dict['Vajilla Básica'], 'Juego de cubiertos (tenedor y cuchillo) de acero inoxidable', Decimal('150.00'), 'Por persona', 'Vajilla'),
        (servicios_dict['Vajilla Básica'], 'Servilleta de tela de gala', Decimal('100.00'), 'Por persona', 'Vajilla'),
        (servicios_dict['Vajilla Básica'], 'Plato para postre de porcelana', Decimal('200.00'), 'Por persona', 'Vajilla'),
        (servicios_dict['Vajilla Básica'], 'Cuchara para postre de acero inoxidable', Decimal('100.00'), 'Por persona', 'Vajilla'),

        # CRISTALERÍA
        (servicios_dict['Cristalería Básica'], 'Vaso de vidrio para bebida', Decimal('250.00'), 'Por persona', 'Cristaleria'),
        (servicios_dict['Cristalería Básica'], 'Copa de cristal para brindis', Decimal('350.00'), 'Por persona', 'Cristaleria'),

        # MOBILIARIO Y MANTELERÍA
        (servicios_dict['Mobiliario y Mantelería'], 'Silla vestida con lazo de gala', Decimal('500.00'), 'Por persona', 'Silla'),
        (servicios_dict['Mobiliario y Mantelería'], 'Mesa redonda (Capacidad 10 personas)', Decimal('3000.00'), 'Mesa', 'Mesa'),
        (servicios_dict['Mobiliario y Mantelería'], 'Mantel redondo blanco de gala', Decimal('1000.00'), 'Mantel', 'Mantel'),
        (servicios_dict['Mobiliario y Mantelería'], 'Mesa rectangular pequeña (Capacidad 8 personas)', Decimal('2500.00'), 'Mesa', 'Mesa'),
        (servicios_dict['Mobiliario y Mantelería'], 'Mantel rectangular pequeño de gala', Decimal('800.00'), 'Mantel', 'Mantel'),
        (servicios_dict['Mobiliario y Mantelería'], 'Mesa rectangular grande (Capacidad 12 personas)', Decimal('3500.00'), 'Mesa', 'Mesa'),
        (servicios_dict['Mobiliario y Mantelería'], 'Mantel rectangular grande de gala', Decimal('1200.00'), 'Mantel', 'Mantel'),

        # SALONEROS
        (servicios_dict['Saloneros y Atención'], 'Salonero profesional (Turno 5 horas)', Decimal('25000.00'), 'Turno', 'Otro'),

        # TRANSPORTE
        (servicios_dict['Transporte y Logística'], 'Transporte logístico de catering (Tarifa por km/invitado)', Decimal('30.00'), 'Km/persona', 'Transporte'),
    ]

    for serv, nombre_det, costo, unidad, cat in detalles:
        DetalleServicio.objects.get_or_create(
            servicio=serv,
            nombre_detalle=nombre_det,
            defaults={
                'costo_unitario': costo,
                'unidad_medida': unidad,
                'categoria': cat,
                'activo': True
            }
        )

    print(f"Se cargaron exitosamente {len(detalles)} componentes al catálogo de Eventos68.")
    print("¡Proceso de inicialización completado con éxito!")


if __name__ == '__main__':
    seed()
