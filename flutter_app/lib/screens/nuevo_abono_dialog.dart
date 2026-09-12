import 'package:flutter/material.dart';
import '../services/api_service.dart';

class NuevoAbonoDialog extends StatefulWidget {
  final int eventoId;
  final String clienteNombre;
  final double saldoPendiente;

  const NuevoAbonoDialog({
    super.key,
    required this.eventoId,
    required this.clienteNombre,
    required this.saldoPendiente,
  });

  @override
  State<NuevoAbonoDialog> createState() => _NuevoAbonoDialogState();
}

class _NuevoAbonoDialogState extends State<NuevoAbonoDialog> {
  final _formKey = GlobalKey<FormState>();
  final _montoController = TextEditingController();
  final _descController = TextEditingController(text: 'Abono por transferencia SINPE');
  bool _isLoading = false;
  final ApiService _apiService = ApiService();

  @override
  void dispose() {
    _montoController.dispose();
    _descController.dispose();
    super.dispose();
  }

  Future<void> _guardarAbono() async {
    if (!_formKey.currentState!.validate()) return;

    final monto = double.tryParse(_montoController.text.trim()) ?? 0.0;
    if (monto <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('El monto debe ser mayor que cero')),
      );
      return;
    }

    setState(() => _isLoading = true);
    try {
      final ok = await _apiService.registrarAbono(
        widget.eventoId,
        monto,
        _descController.text.trim(),
      );
      if (!mounted) return;
      if (ok) {
        Navigator.pop(context, true);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Abono registrado y correo de confirmación enviado.')),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Error al registrar el abono')),
        );
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error de conexión: $e')),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Registrar Abono', style: TextStyle(fontWeight: FontWeight.bold)),
          Text(
            'Cliente: ${widget.clienteNombre}',
            style: const TextStyle(fontSize: 13, color: Colors.grey),
          ),
          Text(
            'Saldo Pendiente: ₡${widget.saldoPendiente.toStringAsFixed(2)}',
            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Colors.red),
          ),
        ],
      ),
      content: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextFormField(
              controller: _montoController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: 'Monto a Abonar (₡)',
                prefixText: '₡ ',
                border: OutlineInputBorder(),
              ),
              validator: (v) => (v == null || v.isEmpty) ? 'Requerido' : null,
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _descController,
              decoration: const InputDecoration(
                labelText: 'Concepto / Método',
                border: OutlineInputBorder(),
              ),
              validator: (v) => (v == null || v.isEmpty) ? 'Requerido' : null,
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _isLoading ? null : () => Navigator.pop(context, false),
          child: const Text('Cancelar'),
        ),
        ElevatedButton(
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFFB45309),
            foregroundColor: Colors.white,
          ),
          onPressed: _isLoading ? null : _guardarAbono,
          child: _isLoading
              ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
              : const Text('Registrar'),
        ),
      ],
    );
  }
}
