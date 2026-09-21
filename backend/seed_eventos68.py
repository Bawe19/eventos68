"""
Script para inicializar la base de datos de Eventos68 con el catálogo completo
de servicios, componentes, configuraciones financieras y tipos de evento.
Incluye:
- Catering Tradicional y Banquetes
- Barras y Estaciones de Comida (Chifrijo, Sopa Azteca, Desayunos)
- Carritos y Barras de Fast Food (Hot Dogs Gourmet)
- Carritos de Snacks & Golosinas (Palomitas, Churros, Waffles, Galletas Suizas, Elotes/Esquites)
- Estaciones Saludables (Bowls de Ensalada, Barra de Yogurt & Granola)
- Vajilla, Cristalería, Mobiliario, Mantelería, Saloneros y Transporte
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
        ('Evento Corporativo', 'Lanzamientos de producto, aniversarios de empresa y convivios ejecutivos.'),
        ('Baby Shower / Revelación de Sexo', 'Celebraciones de bienvenida al bebé, revelaciones de sexo y momentos familiares íntimos.'),
        ('Fiesta Temática / Estaciones', 'Celebraciones dinámicas con carritos interactivos, barras en tendencia y estaciones de snacks.'),
    ]
    for nombre, desc in tipos:
        TipoEvento.objects.update_or_create(nombre=nombre, defaults={'descripcion': desc, 'activo': True})
    
    # Desactivar 'Parrillada al Aire Libre' si existía
    TipoEvento.objects.filter(nombre__icontains='parrillada').update(activo=False)
    print(f"Se crearon/verificaron {len(tipos)} tipos de eventos.")

    # 3. Servicios Principales
    servicios_data = [
        ('Catering Tradicional y Banquetes', 'Menús completos de gala para banquetes, con proteínas finas, guarniciones, ensaladas frescas y postres artesanales.', False),
        ('Barras y Estaciones Típicas', 'Estaciones gastronómicas interactivas para autoservicio guiado (Chifrijo, Sopa Azteca, Desayunos típicos).', False),
        ('Carritos de Fast Food & Snacks', 'Carritos temáticos en tendencia de perros calientes, palomitas, churros, waffles, galletas suizas y esquites.', False),
        ('Estaciones Saludables', 'Barras frescas de bowls de ensaladas personalizables y estaciones de yogurt griego con granola y frutas.', False),
        ('Estaciones de Manualidades y Creatividad', '¡Entretén a tus invitados o equipos, desarrolla su creatividad! Talleres interactivos de arte, pintura y manualidades guiadas.', False),
        ('Servicio de Decoración', 'Montaje temático, centros de mesa, telas y arreglos florales.', False),
        ('Vajilla Básica', 'Platería, platos de porcelana, cubertería de acero inoxidable y servilletas de tela.', False),
        ('Cristalería Básica', 'Copas de brindis y vasos de cristal para bebidas.', False),
        ('Mobiliario y Mantelería', 'Sillas vestidas con lazo de gala, mesas redondas o rectangulares y manteles de gala.', False),
        ('Saloneros y Atención', 'Personal calificado para protocolo, barra y servicio a la mesa.', True),
        ('Transporte y Logística', 'Traslado de equipo, vajilla e insumos según kilometraje.', True),
    ]

    servicios_dict = {}
    for nombre, desc, req_manual in servicios_data:
        s, _ = Servicio.objects.update_or_create(
            nombre=nombre,
            defaults={'descripcion': desc, 'requiere_cantidad_manual': req_manual, 'activo': True}
        )
        servicios_dict[nombre] = s

    # Asegurar compatibilidad con referencias previas a "Servicio de Alimentación"
    s_alim, _ = Servicio.objects.get_or_create(
        nombre='Servicio de Alimentación',
        defaults={'descripcion': 'Catering tradicional y gastronomía integral.', 'activo': True}
    )
    servicios_dict['Servicio de Alimentación'] = s_alim
    print("Servicios principales creados y actualizados.")

    # 4. Desactivar ítems de parrillada de proyectos anteriores si existen
    DetalleServicio.objects.filter(
        nombre_detalle__icontains='parrilla'
    ).update(activo=False)
    DetalleServicio.objects.filter(
        nombre_detalle__icontains='churrasco'
    ).update(activo=False)

    # 5. Componentes y Detalles de Servicios
    detalles = [
        # --- CATERING TRADICIONAL: PROTEÍNAS (Opciones Generales y Versátiles) ---
        (servicios_dict['Catering Tradicional y Banquetes'], 'Pollo: A la plancha marinada, al horno finas hierbas o fajitas salteadas', Decimal('3600.00'), 'Porción', 'Proteina'),
        (servicios_dict['Catering Tradicional y Banquetes'], 'Cerdo: Costilla tierna caramelizada/BBQ, medallones de lomo o chicharrón colombiano crocante', Decimal('4200.00'), 'Porción', 'Proteina'),
        (servicios_dict['Catering Tradicional y Banquetes'], 'Res: Corte selecto a la parrilla, fajitas mixtas salteadas o medallones en salsa vino tinto', Decimal('4500.00'), 'Porción', 'Proteina'),
        (servicios_dict['Catering Tradicional y Banquetes'], 'Pescado o Salmón: Filete al ajillo / finas hierbas o salmón glaseado', Decimal('4200.00'), 'Porción', 'Proteina'),

        # --- CATERING TRADICIONAL: GUARNICIONES (Opciones Generales) ---
        (servicios_dict['Catering Tradicional y Banquetes'], 'Arroz: Con palmito gratinado, aromático con almendras y pasas, o tradicional finas hierbas', Decimal('950.00'), 'Porción', 'Guarnicion'),
        (servicios_dict['Catering Tradicional y Banquetes'], 'Papas: Puré rústico gratinado con parmesano, pastel horneado o papitas al romero', Decimal('850.00'), 'Porción', 'Guarnicion'),
        (servicios_dict['Catering Tradicional y Banquetes'], 'Vegetales: Salteados en mantequilla clarificada o al vapor gourmet', Decimal('800.00'), 'Porción', 'Guarnicion'),

        # --- CATERING TRADICIONAL: ENSALADAS ---
        (servicios_dict['Catering Tradicional y Banquetes'], 'Ensalada Verde Gourmet: Mix hidropónico, espinaca, cherry y vinagreta maracuyá', Decimal('800.00'), 'Porción', 'Ensalada'),
        (servicios_dict['Catering Tradicional y Banquetes'], 'Ensalada César Clásica: Lechuga romana, aderezo césar artesanal, crutones y parmesano', Decimal('850.00'), 'Porción', 'Ensalada'),
        (servicios_dict['Catering Tradicional y Banquetes'], 'Ensalada Waldorf o Tropical: Manzana, apio, nueces o toques frutales con aderezo fino', Decimal('900.00'), 'Porción', 'Ensalada'),

        # --- CATERING TRADICIONAL: POSTRES ---
        (servicios_dict['Catering Tradicional y Banquetes'], 'Postre Tradicional: Tres leches costarricense con merengue flameado', Decimal('1200.00'), 'Porción', 'Postre'),
        (servicios_dict['Catering Tradicional y Banquetes'], 'Cheesecake Artesanal: Coulis de frutos del bosque o reducción de maracuyá', Decimal('1400.00'), 'Porción', 'Postre'),
        (servicios_dict['Catering Tradicional y Banquetes'], 'Tarta Húmeda de Chocolate o Mousse Ligero de la Casa', Decimal('1250.00'), 'Porción', 'Postre'),

        # --- CATERING TRADICIONAL: BEBIDAS Y SALSAS ---
        (servicios_dict['Catering Tradicional y Banquetes'], 'Té frío natural con infusión de limón y hierbabuena', Decimal('500.00'), 'Vaso', 'Bebida'),
        (servicios_dict['Catering Tradicional y Banquetes'], 'Gaseosas variadas y agua embotellada', Decimal('800.00'), 'Unidad', 'Bebida'),
        (servicios_dict['Catering Tradicional y Banquetes'], 'Estación de café costarricense chorreado e infusiones', Decimal('600.00'), 'Taza', 'Bebida'),
        (servicios_dict['Catering Tradicional y Banquetes'], 'Salsas gourmet y aderezos especiales de la casa', Decimal('250.00'), 'Porción', 'Salsa'),

        # --- BARRAS FUERTES / TÍPICAS EN TENDENCIA ---
        (servicios_dict['Barras y Estaciones Típicas'], 'Barra de Chifrijo (Chicharrón de cerdo carnoso, arroz blanco, frijoles tiernos, pico de gallo, aguacate y chips de tortilla)', Decimal('3800.00'), 'Por persona', 'Barra_Fuerte'),
        (servicios_dict['Barras y Estaciones Típicas'], 'Barra de Sopa Azteca (Caldo de tomate y chipotle artesanal, pollo desmechado, aguacate, queso tierno, natilla y tiritas de maíz)', Decimal('3500.00'), 'Por persona', 'Barra_Fuerte'),
        (servicios_dict['Barras y Estaciones Típicas'], 'Barra de Desayunos Típicos (Gallo pinto tradicional, huevos al gusto, plátano maduro, queso frito o turrialba, natilla y tortillas palmeadas)', Decimal('3900.00'), 'Por persona', 'Barra_Fuerte'),

        # --- CARRITOS FAST FOOD ---
        (servicios_dict['Carritos de Fast Food & Snacks'], 'Carrito de Perros Calientes (Salchicha premium, pan artesanal, tocineta crocante, papitas tostadas, queso fundido y salsas premium)', Decimal('2800.00'), 'Por persona', 'Fast_Food'),

        # --- CARRITOS DE SNACKS & GOLOSINAS ---
        (servicios_dict['Carritos de Fast Food & Snacks'], 'Carrito de Palomitas de Maíz (Crispetas recién estalladas en máquina vintage, saladas y acarameladas en conos temáticos)', Decimal('1200.00'), 'Por persona', 'Snack'),
        (servicios_dict['Carritos de Fast Food & Snacks'], 'Carrito de Churros Artesanales (Churros crujientes al momento con azúcar y canela, acompañados de dulce de leche y chocolate)', Decimal('1600.00'), 'Por persona', 'Snack'),
        (servicios_dict['Carritos de Fast Food & Snacks'], 'Estación de Waffles Belgas (Waffles dorados con miel de maple, nutella, fresas frescas, banano y crema chantilly)', Decimal('1800.00'), 'Por persona', 'Snack'),
        (servicios_dict['Carritos de Fast Food & Snacks'], 'Estación de Galletas Suizas Artesanales (Galletas finas horneadas tradicionales con rellenos y decoraciones selectas)', Decimal('1300.00'), 'Por persona', 'Snack'),
        (servicios_dict['Carritos de Fast Food & Snacks'], 'Carrito de Elotes Locos & Esquites (Mazorcas con salsas, queso rallado, limón y vasitos de esquites con mayonesa y chile piquín)', Decimal('1600.00'), 'Por persona', 'Snack'),

        # --- ESTACIONES SALUDABLES ---
        (servicios_dict['Estaciones Saludables'], 'Barra de Bowls de Ensaladas Gourmet (Mix de lechugas hidropónicas, espinacas, quinua, cherry, queso feta, frutos secos y vinagretas)', Decimal('2600.00'), 'Por persona', 'Saludable'),
        (servicios_dict['Estaciones Saludables'], 'Barra de Yogurt Griego, Granola & Frutas (Yogurt natural griego cremoso, granola artesanal horneada con miel, fresas, arándanos, kiwi y chía)', Decimal('2400.00'), 'Por persona', 'Saludable'),

        # --- ESTACIONES DE MANUALIDADES Y CREATIVIDAD (¡Entretén a tus invitados o equipos!) ---
        (servicios_dict['Estaciones de Manualidades y Creatividad'], 'Taller Creativo de Pintura & Mini Caballetes (Pintura guiada sobre lienzos, acrílicos y pinceles)', Decimal('2800.00'), 'Por persona', 'Manualidades'),
        (servicios_dict['Estaciones de Manualidades y Creatividad'], 'Taller de Slime & Arte Sensorial para Niños (Materiales seguros, brillos y accesorios)', Decimal('2200.00'), 'Por persona', 'Manualidades'),
        (servicios_dict['Estaciones de Manualidades y Creatividad'], 'Estación de Bisutería, Pulseras & Llaveros Artesanales (Cuentas temáticas y dijes)', Decimal('2400.00'), 'Por persona', 'Manualidades'),
        (servicios_dict['Estaciones de Manualidades y Creatividad'], 'Dinámica de Arte & Team Building Corporativo (Mural colaborativo e integración para equipos)', Decimal('35000.00'), 'Servicio', 'Manualidades'),

        # --- DECORACIÓN ---
        (servicios_dict['Servicio de Decoración'], 'Decoración Temática Floral de Mesas', Decimal('25000.00'), 'Servicio', 'Otro'),
        (servicios_dict['Servicio de Decoración'], 'Arco de Entrada con Luces Vintage y Arreglos Florales', Decimal('35000.00'), 'Servicio', 'Otro'),

        # --- VAJILLA BÁSICA ---
        (servicios_dict['Vajilla Básica'], 'Plato base y plato principal de porcelana', Decimal('300.00'), 'Por persona', 'Vajilla'),
        (servicios_dict['Vajilla Básica'], 'Juego de cubiertos (tenedor y cuchillo) de acero inoxidable', Decimal('150.00'), 'Por persona', 'Vajilla'),
        (servicios_dict['Vajilla Básica'], 'Servilleta de tela de gala', Decimal('100.00'), 'Por persona', 'Vajilla'),
        (servicios_dict['Vajilla Básica'], 'Plato para postre de porcelana', Decimal('200.00'), 'Por persona', 'Vajilla'),
        (servicios_dict['Vajilla Básica'], 'Cuchara para postre de acero inoxidable', Decimal('100.00'), 'Por persona', 'Vajilla'),

        # --- CRISTALERÍA BÁSICA ---
        (servicios_dict['Cristalería Básica'], 'Vaso de vidrio para bebida', Decimal('250.00'), 'Por persona', 'Cristaleria'),
        (servicios_dict['Cristalería Básica'], 'Copa de cristal para brindis', Decimal('350.00'), 'Por persona', 'Cristaleria'),

        # --- MOBILIARIO Y MANTELERÍA ---
        (servicios_dict['Mobiliario y Mantelería'], 'Silla vestida con lazo de gala', Decimal('500.00'), 'Por persona', 'Silla'),
        (servicios_dict['Mobiliario y Mantelería'], 'Mesa redonda (Capacidad 10 personas)', Decimal('3000.00'), 'Mesa', 'Mesa'),
        (servicios_dict['Mobiliario y Mantelería'], 'Mantel redondo blanco de gala', Decimal('1000.00'), 'Mantel', 'Mantel'),
        (servicios_dict['Mobiliario y Mantelería'], 'Mesa rectangular pequeña (Capacidad 8 personas)', Decimal('2500.00'), 'Mesa', 'Mesa'),
        (servicios_dict['Mobiliario y Mantelería'], 'Mantel rectangular pequeño de gala', Decimal('800.00'), 'Mantel', 'Mantel'),
        (servicios_dict['Mobiliario y Mantelería'], 'Mesa rectangular grande (Capacidad 12 personas)', Decimal('3500.00'), 'Mesa', 'Mesa'),
        (servicios_dict['Mobiliario y Mantelería'], 'Mantel rectangular grande de gala', Decimal('1200.00'), 'Mantel', 'Mantel'),

        # --- SALONEROS ---
        (servicios_dict['Saloneros y Atención'], 'Salonero profesional (Turno 5 horas)', Decimal('25000.00'), 'Turno', 'Otro'),

        # --- TRANSPORTE ---
        (servicios_dict['Transporte y Logística'], 'Transporte logístico de catering (Tarifa por km/invitado)', Decimal('30.00'), 'Km/persona', 'Transporte'),
    ]

    for serv, nombre_det, costo, unidad, cat in detalles:
        DetalleServicio.objects.update_or_create(
            nombre_detalle=nombre_det,
            defaults={
                'servicio': serv,
                'costo_unitario': costo,
                'unidad_medida': unidad,
                'categoria': cat,
                'activo': True
            }
        )

    print(f"Se cargaron y actualizaron exitosamente los componentes del catálogo de Eventos68.")
    print("¡Proceso de inicialización completado con éxito!")


if __name__ == '__main__':
    seed()

