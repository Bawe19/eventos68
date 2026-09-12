import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/dashboard_stats.dart';
import '../models/cotizacion.dart';
import '../models/evento.dart';

class ApiService {
  // Cambiar esta URL cuando se despliegue en producción en Render.com
  // Para Android Emulator usar 'http://10.0.2.2:8000'
  // Para Web / Desktop / iOS usar 'http://127.0.0.1:8000'
  static const String baseUrl = 'http://127.0.0.1:8000';

  final http.Client _client = http.Client();

  Future<DashboardStats> fetchDashboardStats() async {
    final response = await _client.get(Uri.parse('$baseUrl/api/dashboard-stats/'));
    if (response.statusCode == 200) {
      return DashboardStats.fromJson(jsonDecode(utf8.decode(response.bodyBytes)));
    } else {
      throw Exception('Error al cargar estadísticas: ${response.statusCode}');
    }
  }

  Future<List<CotizacionItem>> fetchCotizaciones({String? estado}) async {
    String url = '$baseUrl/api/cotizaciones/';
    if (estado != null && estado.isNotEmpty) {
      url += '?estado=$estado';
    }
    final response = await _client.get(Uri.parse(url));
    if (response.statusCode == 200) {
      final data = jsonDecode(utf8.decode(response.bodyBytes));
      final List results = data is Map ? (data['results'] ?? []) : data;
      return results.map((item) => CotizacionItem.fromJson(item)).toList();
    } else {
      throw Exception('Error al listar cotizaciones');
    }
  }

  Future<List<EventoItem>> fetchEventos() async {
    final response = await _client.get(Uri.parse('$baseUrl/api/eventos/'));
    if (response.statusCode == 200) {
      final data = jsonDecode(utf8.decode(response.bodyBytes));
      final List results = data is Map ? (data['results'] ?? []) : data;
      return results.map((item) => EventoItem.fromJson(item)).toList();
    } else {
      throw Exception('Error al listar eventos');
    }
  }

  Future<bool> contratarCotizacion(int cotizacionId) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/cotizaciones/$cotizacionId/contratar/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'notas_operativas': 'Contratado desde Flutter App'}),
    );
    return response.statusCode == 200 || response.statusCode == 201;
  }

  Future<bool> registrarAbono(int eventoId, double monto, String descripcion) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/eventos/$eventoId/abonar/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'monto': monto,
        'descripcion': descripcion,
      }),
    );
    return response.statusCode == 200 || response.statusCode == 201;
  }

  String getPdfDownloadUrl(int cotizacionId) {
    return '$baseUrl/cotizacion/$cotizacionId/pdf/';
  }
}
