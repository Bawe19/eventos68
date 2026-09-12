import 'package:flutter/material.dart';
import '../models/dashboard_stats.dart';
import '../services/api_service.dart';
import 'cotizaciones_screen.dart';
import 'eventos_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final ApiService _apiService = ApiService();
  late Future<DashboardStats> _futureStats;
  int _currentIndex = 0;

  @override
  void initState() {
    super.initState();
    _cargarStats();
  }

  void _cargarStats() {
    setState(() {
      _futureStats = _apiService.fetchDashboardStats();
    });
  }

  @override
  Widget build(BuildContext context) {
    final screens = [
      _buildDashboardHome(),
      const CotizacionesScreen(),
      const EventosScreen(),
    ];

    return Scaffold(
      body: screens[_currentIndex],
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        selectedItemColor: const Color(0xFFB45309),
        unselectedItemColor: Colors.grey,
        onTap: (idx) => setState(() => _currentIndex = idx),
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.dashboard_outlined), label: 'Inicio'),
          BottomNavigationBarItem(icon: Icon(Icons.receipt_long_outlined), label: 'Cotizaciones'),
          BottomNavigationBarItem(icon: Icon(Icons.event_available_outlined), label: 'Eventos'),
        ],
      ),
    );
  }

  Widget _buildDashboardHome() {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Eventos68 • Portal Gerencial', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: const Color(0xFF0F172A),
        foregroundColor: Colors.white,
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _cargarStats),
        ],
      ),
      body: FutureBuilder<DashboardStats>(
        future: _futureStats,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24.0),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.error_outline, color: Colors.red, size: 48),
                    const SizedBox(height: 12),
                    Text('No se pudo conectar al servidor Django: ${snapshot.error}', textAlign: TextAlign.center),
                    const SizedBox(height: 16),
                    ElevatedButton(onPressed: _cargarStats, child: const Text('Reintentar')),
                  ],
                ),
              ),
            );
          }

          final stats = snapshot.data!;
          return RefreshIndicator(
            onRefresh: () async => _cargarStats(),
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                // Header Banner
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [Color(0xFF0F172A), Color(0xFF1E293B)],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Resumen Financiero Acumulado',
                        style: TextStyle(color: Colors.white70, fontSize: 13),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        '₡${stats.totalRecaudadoCrc.toStringAsFixed(2)}',
                        style: const TextStyle(color: Colors.white, fontSize: 26, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          _buildMiniBadge('Gastos: ₡${stats.totalGastosCrc.toStringAsFixed(0)}', Colors.redAccent),
                          const SizedBox(width: 8),
                          _buildMiniBadge('Balance: ₡${stats.balanceOperativoCrc.toStringAsFixed(0)}', Colors.greenAccent),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),

                // Grid of 3 Indicators
                Row(
                  children: [
                    Expanded(
                      child: _buildMetricCard(
                        'Solicitudes',
                        '${stats.solicitudesPendientes}',
                        Icons.hourglass_empty,
                        Colors.orange,
                        () => setState(() => _currentIndex = 1),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: _buildMetricCard(
                        'Cotizaciones',
                        '${stats.cotizacionesActivas}',
                        Icons.description_outlined,
                        Colors.blue,
                        () => setState(() => _currentIndex = 1),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: _buildMetricCard(
                        'Eventos',
                        '${stats.eventosProximosCount}',
                        Icons.check_circle_outline,
                        Colors.green,
                        () => setState(() => _currentIndex = 2),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 24),

                // Upcoming Events Header
                Row(
                  mainAxisAlignment: MainAxisAlignment.between,
                  children: [
                    const Text(
                      'Próximos Eventos en Agenda',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
                    ),
                    TextButton(
                      onPressed: () => setState(() => _currentIndex = 2),
                      child: const Text('Ver todos'),
                    ),
                  ],
                ),
                const SizedBox(height: 8),

                if (stats.proximosEventos.isEmpty)
                  const Card(
                    child: Padding(
                      padding: EdgeInsets.all(24.0),
                      child: Center(child: Text('No hay eventos programados para los próximos días.', style: TextStyle(color: Colors.grey))),
                    ),
                  )
                else
                  ...stats.proximosEventos.map((e) {
                    final ev = e as Map<String, dynamic>;
                    return Card(
                      margin: const EdgeInsets.only(bottom: 10),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      child: ListTile(
                        leading: const CircleAvatar(
                          backgroundColor: Color(0xFFFEF3C7),
                          child: Icon(Icons.event, color: Color(0xFFB45309)),
                        ),
                        title: Text(ev['cliente_nombre'] ?? 'Cliente', style: const TextStyle(fontWeight: FontWeight.bold)),
                        subtitle: Text('${ev['tipo_evento']} • ${ev['fecha_evento']} • ${ev['cantidad_personas']} personas'),
                        trailing: Text(
                          '${ev['dias_restantes']} d',
                          style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFFB45309)),
                        ),
                        onTap: () => setState(() => _currentIndex = 2),
                      ),
                    );
                  }),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildMiniBadge(String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(color: Colors.white12, borderRadius: BorderRadius.circular(8)),
      child: Text(text, style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.bold)),
    );
  }

  Widget _buildMetricCard(String title, String count, IconData icon, Color color, VoidCallback onTap) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Card(
        elevation: 1,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 8),
          child: Column(
            children: [
              Icon(icon, color: color, size: 28),
              const SizedBox(height: 8),
              Text(count, style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: color)),
              const SizedBox(height: 2),
              Text(title, style: const TextStyle(fontSize: 11, color: Colors.grey), textAlign: TextAlign.center),
            ],
          ),
        ),
      ),
    );
  }
}
