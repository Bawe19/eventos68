import 'package:flutter/material.dart';
import '../models/evento.dart';
import '../services/api_service.dart';
import 'nuevo_abono_dialog.dart';

class EventosScreen extends StatefulWidget {
  const EventosScreen({super.key});

  @override
  State<EventosScreen> createState() => _EventosScreenState();
}

class _EventosScreenState extends State<EventosScreen> {
  final ApiService _apiService = ApiService();
  late Future<List<EventoItem>> _futureEventos;

  @override
  void initState() {
    super.initState();
    _cargarEventos();
  }

  void _cargarEventos() {
    setState(() {
      _futureEventos = _apiService.fetchEventos();
    });
  }

  Future<void> _abrirDialogoAbono(EventoItem evento) async {
    final actualizado = await showDialog<bool>(
      context: context,
      builder: (ctx) => NuevoAbonoDialog(
        eventoId: evento.id,
        clienteNombre: evento.clienteNombre,
        saldoPendiente: evento.saldoPendiente,
      ),
    );

    if (actualizado == true) {
      _cargarEventos();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Eventos Contratados', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: const Color(0xFF0F172A),
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _cargarEventos,
          ),
        ],
      ),
      body: FutureBuilder<List<EventoItem>>(
        future: _futureEventos,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(
              child: Text('Error al cargar eventos: ${snapshot.error}', style: const TextStyle(color: Colors.red)),
            );
          }
          final eventos = snapshot.data ?? [];
          if (eventos.isEmpty) {
            return const Center(
              child: Text('No hay eventos contratados activos actualmente.', style: TextStyle(color: Colors.grey)),
            );
          }

          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: eventos.length,
            itemBuilder: (context, index) {
              final ev = eventos[index];
              return Card(
                elevation: 2,
                margin: const EdgeInsets.only(bottom: 14),
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
                            'Evento #${ev.id} • ${ev.tipoEvento}',
                            style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFFB45309)),
                          ),
                          _buildCountdownBadge(ev.diasRestantes),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Text(
                        ev.clienteNombre,
                        style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
                      ),
                      Text(
                        'Fecha: ${ev.fechaEvento} • ${ev.cantidadPersonas} personas • Tel: ${ev.clienteTelefono}',
                        style: const TextStyle(color: Colors.grey, fontSize: 13),
                      ),
                      const Divider(height: 20),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          _buildCol('Total Contrato', '₡${ev.totalGeneral.toStringAsFixed(2)}', Colors.black87),
                          _buildCol('Abonado', '₡${ev.totalAbonado.toStringAsFixed(2)}', Colors.green),
                          _buildCol('Saldo Pendiente', '₡${ev.saldoPendiente.toStringAsFixed(2)}', Colors.red),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.end,
                        children: [
                          ElevatedButton.icon(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: const Color(0xFFB45309),
                              foregroundColor: Colors.white,
                            ),
                            icon: const Icon(Icons.add_card, size: 16),
                            label: const Text('Registrar Abono'),
                            onPressed: () => _abrirDialogoAbono(ev),
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
    );
  }

  Widget _buildCol(String titulo, String valor, Color color) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(titulo, style: const TextStyle(fontSize: 11, color: Colors.grey)),
        Text(valor, style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: color)),
      ],
    );
  }

  Widget _buildCountdownBadge(int dias) {
    Color bg = Colors.blue;
    String texto = '$dias días';
    if (dias < 0) {
      bg = Colors.grey;
      texto = 'Finalizado';
    } else if (dias <= 7) {
      bg = Colors.red;
      texto = '¡Faltan $dias días!';
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(12)),
      child: Text(
        texto,
        style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold),
      ),
    );
  }
}
