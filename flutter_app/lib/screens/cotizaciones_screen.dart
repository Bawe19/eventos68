import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models/cotizacion.dart';
import '../services/api_service.dart';

class CotizacionesScreen extends StatefulWidget {
  const CotizacionesScreen({super.key});

  @override
  State<CotizacionesScreen> createState() => _CotizacionesScreenState();
}

class _CotizacionesScreenState extends State<CotizacionesScreen> {
  final ApiService _apiService = ApiService();
  late Future<List<CotizacionItem>> _futureCotizaciones;
  String _filtroEstado = '';

  @override
  void initState() {
    super.initState();
    _cargarCotizaciones();
  }

  void _cargarCotizaciones() {
    setState(() {
      _futureCotizaciones = _apiService.fetchCotizaciones(
        estado: _filtroEstado.isEmpty ? null : _filtroEstado,
      );
    });
  }

  Future<void> _abrirPdf(int id) async {
    final url = Uri.parse(_apiService.getPdfDownloadUrl(id));
    if (await canLaunchUrl(url)) {
      await launchUrl(url, mode: LaunchMode.externalApplication);
    } else {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('No se pudo abrir el PDF')),
      );
    }
  }

  Future<void> _contratar(int id) async {
    final confirmar = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Contratar Evento'),
        content: const Text('¿Desea formalizar esta cotización como un evento contratado?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.green, foregroundColor: Colors.white),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Contratar'),
          ),
        ],
      ),
    );

    if (confirmar == true) {
      try {
        final ok = await _apiService.contratarCotizacion(id);
        if (ok) {
          if (!mounted) return;
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('¡Evento contratado con éxito!')),
          );
          _cargarCotizaciones();
        }
      } catch (e) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Cotizaciones & Presupuestos', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: const Color(0xFF0F172A),
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _cargarCotizaciones,
          ),
        ],
      ),
      body: Column(
        children: [
          // Filter Chips
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Row(
              children: [
                _buildFilterChip('Todas', ''),
                _buildFilterChip('Solicitudes', 'Solicitud'),
                _buildFilterChip('Cotizaciones', 'Cotizacion'),
                _buildFilterChip('Eventos', 'Evento'),
              ],
            ),
          ),
          // List
          Expanded(
            child: FutureBuilder<List<CotizacionItem>>(
              future: _futureCotizaciones,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (snapshot.hasError) {
                  return Center(
                    child: Text('Error al cargar datos: ${snapshot.error}', style: const TextStyle(color: Colors.red)),
                  );
                }
                final items = snapshot.data ?? [];
                if (items.isEmpty) {
                  return const Center(
                    child: Text('No hay cotizaciones registradas en este filtro.', style: TextStyle(color: Colors.grey)),
                  );
                }

                return ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: items.length,
                  itemBuilder: (context, index) {
                    final item = items[index];
                    return Card(
                      elevation: 2,
                      margin: const EdgeInsets.only(bottom: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.between,
                              children: [
                                Text(
                                  'EV68-${item.id.toString().padLeft(4, '0')}',
                                  style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFFB45309)),
                                ),
                                _buildBadge(item.estado),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Text(
                              item.clienteNombre,
                              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                            ),
                            Text(
                              '${item.tipoEventoNombre} • ${item.cantidadPersonas} invitados • Fecha: ${item.fechaEvento}',
                              style: const TextStyle(color: Colors.grey, fontSize: 13),
                            ),
                            const Divider(height: 20),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.between,
                              children: [
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    const Text('Total Presupuesto:', style: TextStyle(fontSize: 11, color: Colors.grey)),
                                    Text(
                                      '₡${item.totalGeneral.toStringAsFixed(2)}',
                                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
                                    ),
                                  ],
                                ),
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.end,
                                  children: [
                                    const Text('Adelanto Requerido:', style: TextStyle(fontSize: 11, color: Colors.grey)),
                                    Text(
                                      '₡${item.montoPagoInicial.toStringAsFixed(2)}',
                                      style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: Color(0xFFB45309)),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                            const SizedBox(height: 12),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.end,
                              children: [
                                OutlinedButton.icon(
                                  icon: const Icon(Icons.picture_as_pdf, size: 16),
                                  label: const Text('PDF'),
                                  onPressed: () => _abrirPdf(item.id),
                                ),
                                const SizedBox(width: 8),
                                if (item.estado != 'Evento')
                                  ElevatedButton.icon(
                                    style: ElevatedButton.styleFrom(
                                      backgroundColor: const Color(0xFF0F172A),
                                      foregroundColor: Colors.white,
                                    ),
                                    icon: const Icon(Icons.check_circle_outline, size: 16),
                                    label: const Text('Contratar'),
                                    onPressed: () => _contratar(item.id),
                                  ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterChip(String label, String value) {
    final selected = _filtroEstado == value;
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: FilterChip(
        label: Text(label),
        selected: selected,
        selectedColor: const Color(0xFFB45309),
        labelStyle: TextStyle(color: selected ? Colors.white : Colors.black87),
        onSelected: (val) {
          setState(() {
            _filtroEstado = value;
            _cargarCotizaciones();
          });
        },
      ),
    );
  }

  Widget _buildBadge(String estado) {
    Color bg = Colors.grey;
    if (estado == 'Solicitud') bg = Colors.orange;
    if (estado == 'Cotizacion') bg = Colors.blue;
    if (estado == 'Evento') bg = Colors.green;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(12)),
      child: Text(
        estado,
        style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold),
      ),
    );
  }
}
