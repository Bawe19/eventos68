class EventoItem {
  final int id;
  final int cotizacionId;
  final String clienteNombre;
  final String clienteTelefono;
  final String tipoEvento;
  final String fechaEvento;
  final int cantidadPersonas;
  final String estado;
  final double totalGeneral;
  final double totalAbonado;
  final double saldoPendiente;
  final int diasRestantes;

  EventoItem({
    required this.id,
    required this.cotizacionId,
    required this.clienteNombre,
    required this.clienteTelefono,
    required this.tipoEvento,
    required this.fechaEvento,
    required this.cantidadPersonas,
    required this.estado,
    required this.totalGeneral,
    required this.totalAbonado,
    required this.saldoPendiente,
    required this.diasRestantes,
  });

  factory EventoItem.fromJson(Map<String, dynamic> json) {
    return EventoItem(
      id: json['id'] ?? 0,
      cotizacionId: json['cotizacion'] ?? 0,
      clienteNombre: json['cliente_nombre'] ?? 'Cliente',
      clienteTelefono: json['cliente_telefono'] ?? '',
      tipoEvento: json['tipo_evento'] ?? 'Evento',
      fechaEvento: json['fecha_evento'] ?? '',
      cantidadPersonas: json['cantidad_personas'] ?? 0,
      estado: json['estado'] ?? 'Contratado',
      totalGeneral: double.tryParse(json['total_general']?.toString() ?? '0') ?? 0.0,
      totalAbonado: double.tryParse(json['total_abonado']?.toString() ?? '0') ?? 0.0,
      saldoPendiente: double.tryParse(json['saldo_pendiente']?.toString() ?? '0') ?? 0.0,
      diasRestantes: json['dias_restantes'] ?? 0,
    );
  }
}

class PagoItem {
  final int id;
  final int eventoId;
  final String descripcion;
  final double monto;
  final String fechaPago;
  final String? comprobantePagoUrl;

  PagoItem({
    required this.id,
    required this.eventoId,
    required this.descripcion,
    required this.monto,
    required this.fechaPago,
    this.comprobantePagoUrl,
  });

  factory PagoItem.fromJson(Map<String, dynamic> json) {
    return PagoItem(
      id: json['id'] ?? 0,
      eventoId: json['evento'] ?? 0,
      descripcion: json['descripcion'] ?? 'Abono',
      monto: double.tryParse(json['monto']?.toString() ?? '0') ?? 0.0,
      fechaPago: json['fecha_pago'] ?? '',
      comprobantePagoUrl: json['comprobante_pago'],
    );
  }
}
