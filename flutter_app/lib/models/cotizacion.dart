class CotizacionItem {
  final int id;
  final String clienteNombre;
  final String clienteTelefono;
  final String tipoEventoNombre;
  final String fechaEvento;
  final int cantidadPersonas;
  final String estado;
  final double totalGeneral;
  final double montoPagoInicial;
  final String fechaRegistro;

  CotizacionItem({
    required this.id,
    required this.clienteNombre,
    required this.clienteTelefono,
    required this.tipoEventoNombre,
    required this.fechaEvento,
    required this.cantidadPersonas,
    required this.estado,
    required this.totalGeneral,
    required this.montoPagoInicial,
    required this.fechaRegistro,
  });

  factory CotizacionItem.fromJson(Map<String, dynamic> json) {
    return CotizacionItem(
      id: json['id'] ?? 0,
      clienteNombre: json['cliente_nombre'] ?? 'Cliente sin nombre',
      clienteTelefono: json['cliente_telefono'] ?? '',
      tipoEventoNombre: json['tipo_evento_nombre'] ?? 'Evento',
      fechaEvento: json['fecha_evento'] ?? '',
      cantidadPersonas: json['cantidad_personas'] ?? 0,
      estado: json['estado'] ?? 'Solicitud',
      totalGeneral: double.tryParse(json['total_general']?.toString() ?? '0') ?? 0.0,
      montoPagoInicial: double.tryParse(json['monto_pago_inicial']?.toString() ?? '0') ?? 0.0,
      fechaRegistro: json['fecha_registro'] ?? '',
    );
  }
}
