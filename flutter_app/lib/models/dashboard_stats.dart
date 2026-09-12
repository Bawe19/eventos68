class DashboardStats {
  final int solicitudesPendientes;
  final int cotizacionesActivas;
  final int eventosProximosCount;
  final double totalRecaudadoCrc;
  final double totalGastosCrc;
  final double balanceOperativoCrc;
  final List<dynamic> proximosEventos;

  DashboardStats({
    required this.solicitudesPendientes,
    required this.cotizacionesActivas,
    required this.eventosProximosCount,
    required this.totalRecaudadoCrc,
    required this.totalGastosCrc,
    required this.balanceOperativoCrc,
    required this.proximosEventos,
  });

  factory DashboardStats.fromJson(Map<String, dynamic> json) {
    return DashboardStats(
      solicitudesPendientes: json['solicitudes_pendientes'] ?? 0,
      cotizacionesActivas: json['cotizaciones_activas'] ?? 0,
      eventosProximosCount: json['eventos_proximos_count'] ?? 0,
      totalRecaudadoCrc: (json['total_recaudado_crc'] as num?)?.toDouble() ?? 0.0,
      totalGastosCrc: (json['total_gastos_crc'] as num?)?.toDouble() ?? 0.0,
      balanceOperativoCrc: (json['balance_operativo_crc'] as num?)?.toDouble() ?? 0.0,
      proximosEventos: json['proximos_eventos'] ?? [],
    );
  }
}
