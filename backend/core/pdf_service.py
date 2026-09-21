import io
from decimal import Decimal
from pathlib import Path
from django.conf import settings
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


def generar_pdf_cotizacion(cotizacion) -> bytes:
    """
    Genera un presupuesto profesional en PDF con la identidad de marca de Eventos68.
    Retorna los bytes del PDF para descarga o adjunto en correo.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette - Eventos68 Official Brand Identity
    c_primary = colors.HexColor('#C8860A')    # Brand Gold
    c_secondary = colors.HexColor('#1C1B19')  # Brand Charcoal Black
    c_light = colors.HexColor('#FAF6F0')      # Brand Warm Cream
    c_accent = colors.HexColor('#262523')     # Deep Espresso
    c_border = colors.HexColor('#E8E2D8')     # Warm Border Tint

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=c_primary
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#64748B')
    )

    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=c_secondary,
        spaceAfter=6
    )

    cell_style = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=c_accent
    )

    cell_bold = ParagraphStyle(
        'CellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=c_secondary
    )

    cell_right = ParagraphStyle(
        'CellRight',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        alignment=2,
        textColor=c_accent
    )

    cell_right_bold = ParagraphStyle(
        'CellRightBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        alignment=2,
        textColor=c_secondary
    )

    elements = []

    # 1. Header Banner with Official Logo
    logo_path = Path(settings.BASE_DIR) / 'static' / 'images' / 'logos' / 'logo_transparente_negro.png'
    logo_cell = ""
    if logo_path.exists():
        try:
            logo_cell = RLImage(str(logo_path), width=1.3 * inch, height=0.95 * inch)
        except Exception:
            logo_cell = ""

    header_data = [
        [
            logo_cell if logo_cell else Paragraph("<b>E68</b>", title_style),
            Paragraph("<b>EVENTOS68</b><br/><font size=8 color='#C8860A'>CATERING SERVICE & LOGÍSTICA</font><br/><font size=7 color='#736E67'>San José, Costa Rica • Tel: +506 6168-0639</font>", title_style),
            Paragraph(
                "<b>PRESUPUESTO FORMAL</b><br/>"
                f"<b>Cotización #:</b> EV68-{cotizacion.id:04d}<br/>"
                f"<b>Fecha de Emisión:</b> {cotizacion.fecha_registro.strftime('%d/%m/%Y')}<br/>"
                f"<b>Estado:</b> {cotizacion.get_estado_display()}",
                cell_right
            )
        ]
    ]
    t_header = Table(header_data, colWidths=[1.3 * inch, 3.2 * inch, 3.0 * inch])
    t_header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(t_header)
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceAfter=12))

    # 2. Client & Event Information Grid
    cliente = cotizacion.cliente
    info_data = [
        [
            Paragraph("<b>DATOS DEL CLIENTE</b>", cell_bold),
            Paragraph("<b>DATOS DEL EVENTO</b>", cell_bold)
        ],
        [
            Paragraph(
                f"<b>Nombre:</b> {cliente.nombre}<br/>"
                f"<b>Identificación:</b> {cliente.identificacion}<br/>"
                f"<b>Teléfono:</b> {cliente.telefono}<br/>"
                f"<b>Correo:</b> {cliente.correo}",
                cell_style
            ),
            Paragraph(
                f"<b>Tipo de Evento:</b> {cotizacion.tipo_evento.nombre}<br/>"
                f"<b>Fecha del Evento:</b> {cotizacion.fecha_evento.strftime('%d/%m/%Y')}<br/>"
                f"<b>Cantidad de Personas:</b> {cotizacion.cantidad_personas} invitados<br/>"
                f"<b>Modalidad:</b> {cotizacion.get_modalidad_servicio_display()}<br/>"
                f"<b>Ubicación:</b> {cotizacion.direccion_evento or 'Por definir'}<br/>"
                f"<b>Alergias / Restricciones:</b> {getattr(cotizacion, 'alergias_restricciones', 'No presenta / No aplica')}",
                cell_style
            )
        ]
    ]
    t_info = Table(info_data, colWidths=[3.75 * inch, 3.75 * inch])
    t_info.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_light),
        ('BOX', (0, 0), (-1, -1), 0.5, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(t_info)
    elements.append(Spacer(1, 14))

    # 3. Items / Services Table (Client-Facing Package Presentation)
    elements.append(Paragraph("Componentes y Menú Incluido en la Propuesta", section_style))
    items_data = [
        [
            Paragraph("<b>Servicio / Componente Solicitado</b>", cell_bold),
            Paragraph("<b>Categoría</b>", cell_bold),
            Paragraph("<b>Cantidad</b>", cell_right_bold),
            Paragraph("<b>Modalidad</b>", cell_right_bold),
        ]
    ]

    for d in cotizacion.detalles.all():
        nombre_item = d.detalle_servicio.nombre_detalle if d.detalle_servicio else d.nombre_personalizado or d.servicio.nombre
        cat = d.detalle_servicio.categoria if d.detalle_servicio and d.detalle_servicio.categoria else d.servicio.nombre
        modalidad = "Bufete" if d.es_bufete else ("Saloneros" if d.requiere_saloneros else "Incluido")
        items_data.append([
            Paragraph(f"<b>{d.servicio.nombre}</b>: {nombre_item}", cell_style),
            Paragraph(str(cat), cell_style),
            Paragraph(str(d.cantidad), cell_right),
            Paragraph(modalidad, cell_right),
        ])

    t_items = Table(items_data, colWidths=[4.0 * inch, 1.8 * inch, 0.8 * inch, 0.9 * inch])
    t_items.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_light),
        ('BOX', (0, 0), (-1, -1), 0.5, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(t_items)
    elements.append(Spacer(1, 14))

    # 4. Financial Summary Box (Professional Package Proposal)
    subtotal_paquete = cotizacion.subtotal_servicios + cotizacion.monto_ganancia
    totales_data = [
        [
            Paragraph("<b>Términos y Condiciones del Servicio</b><br/>"
                      "• Los precios están expresados en colones costarricenses (CRC).<br/>"
                      "• Para reservar la fecha en firme se requiere el comprobante del adelanto inicial.<br/>"
                      "• El saldo restante se cancela mediante abonos programados previo al evento.<br/>"
                      "• Pagos por transferencia SINPE Móvil al <b>+506 6168-0639</b> o cuenta bancaria.<br/>"
                      "• Contáctenos al <b>+506 6168-0639</b> | <b>info@eventos68.lat</b> | <b>eventos68.lat</b><br/>"
                      "• Síganos en Instagram: <b>@eventos68_cr</b> | Facebook: <b>Eventos68</b>",
                      subtitle_style),
            Table([
                [Paragraph("Subtotal Paquete Integral:", cell_style), Paragraph(f"₡{subtotal_paquete:,.2f}", cell_right)],
                [Paragraph(f"IVA ({cotizacion.porcentaje_iva}%):", cell_style), Paragraph(f"₡{cotizacion.monto_iva:,.2f}", cell_right)],
                [Paragraph("<b>TOTAL DEL EVENTO:</b>", cell_bold), Paragraph(f"<b>₡{cotizacion.total_general:,.2f}</b>", cell_right_bold)],
                [Paragraph("Inversión por Persona:", cell_style), Paragraph(f"₡{cotizacion.total_por_persona:,.2f}", cell_right)],
                [Paragraph(f"<b>Adelanto Inicial ({cotizacion.porcentaje_pago_inicial}%):</b>", cell_bold),
                 Paragraph(f"<font color='#B45309'><b>₡{cotizacion.monto_pago_inicial:,.2f}</b></font>", cell_right_bold)],
            ], colWidths=[1.8 * inch, 1.4 * inch])
        ]
    ]

    t_summary = Table(totales_data, colWidths=[4.3 * inch, 3.2 * inch])
    t_summary.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, c_border),
        ('BACKGROUND', (1, 0), (1, 0), c_light),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(t_summary)

    # Build Document
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
