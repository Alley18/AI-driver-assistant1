import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

import '../models/alert_item.dart';
import '../models/driver_state.dart';

class ApiService {
  final ValueNotifier<String> baseUrl = ValueNotifier<String>('http://127.0.0.1:8000');
  final ValueNotifier<DriverState?> currentState = ValueNotifier<DriverState?>(null);
  final ValueNotifier<List<AlertItem>> alerts = ValueNotifier<List<AlertItem>>(<AlertItem>[]);
  final ValueNotifier<Map<String, dynamic>?> schema = ValueNotifier<Map<String, dynamic>?>(null);
  final ValueNotifier<bool> isHealthy = ValueNotifier<bool>(false);
  final ValueNotifier<int> rowsLoaded = ValueNotifier<int>(0);

  Timer? _timer;

  ApiService() {
    if (kIsWeb) {
      baseUrl.value = 'http://127.0.0.1:8000';
    }
    refreshAll();
    _timer = Timer.periodic(const Duration(seconds: 1), (_) => refreshAll());
  }

  void updateBaseUrl(String next) {
    if (next.isNotEmpty) {
      baseUrl.value = next;
      refreshAll();
    }
  }

  Future<void> refreshAll() async {
    await Future.wait([
      _fetchHealth(),
      _fetchState(),
      _fetchAlerts(),
      _fetchSchema(),
    ]);
  }

  Future<void> _fetchHealth() async {
    try {
      final response = await http.get(Uri.parse('${baseUrl.value}/health'));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        isHealthy.value = data['status'] == 'ok';
        rowsLoaded.value = (data['rows_loaded'] ?? 0) as int;
      } else {
        isHealthy.value = false;
      }
    } catch (_) {
      isHealthy.value = false;
    }
  }

  Future<void> _fetchState() async {
    try {
      final response = await http.get(Uri.parse('${baseUrl.value}/state'));
      if (response.statusCode == 200) {
        currentState.value = DriverState.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
      }
    } catch (_) {}
  }

  Future<void> _fetchAlerts() async {
    try {
      final response = await http.get(Uri.parse('${baseUrl.value}/alerts'));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as List<dynamic>;
        alerts.value = data.map((e) => AlertItem.fromJson(e as Map<String, dynamic>)).toList();
      }
    } catch (_) {}
  }

  Future<void> _fetchSchema() async {
    if (schema.value != null) return;
    try {
      final response = await http.get(Uri.parse('${baseUrl.value}/schema'));
      if (response.statusCode == 200) {
        schema.value = jsonDecode(response.body) as Map<String, dynamic>;
      }
    } catch (_) {}
  }

  void dispose() {
    _timer?.cancel();
  }
}
