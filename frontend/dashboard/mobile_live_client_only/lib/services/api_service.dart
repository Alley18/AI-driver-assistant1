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
  final ValueNotifier<DateTime?> lastSync = ValueNotifier<DateTime?>(null);
  final ValueNotifier<int> updateCount = ValueNotifier<int>(0);
  final ValueNotifier<String> liveSpeech = ValueNotifier<String>('Waiting for live speech...');

  Timer? _timer;
  bool _busy = false;
  String? _lastStateKey;

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
      schema.value = null;
      refreshAll();
    }
  }

  Future<void> refreshAll() async {
    if (_busy) return;
    _busy = true;
    try {
      await Future.wait([
        _fetchHealth(),
        _fetchState(),
        _fetchAlerts(),
        _fetchSchema(),
      ]);
      lastSync.value = DateTime.now();
    } finally {
      _busy = false;
    }
  }

  Future<void> _fetchHealth() async {
    try {
      final response = await http.get(Uri.parse('${baseUrl.value}/health'));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        isHealthy.value = data['status'] == 'ok';
        rowsLoaded.value = int.tryParse('${data['rows_loaded'] ?? 0}') ?? 0;
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
        final state = DriverState.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
        currentState.value = state;
        liveSpeech.value = state.spokenText;
        if (_lastStateKey != state.eventKey) {
          _lastStateKey = state.eventKey;
          updateCount.value = updateCount.value + 1;
          _insertDerivedAlert(state);
        }
      }
    } catch (_) {}
  }

  void _insertDerivedAlert(DriverState state) {
    final item = AlertItem(
      id: state.eventKey,
      timestamp: state.timestamp,
      level: state.level,
      message: state.message,
      input: state.input,
      buzzer: state.buzzer,
      spokenText: state.spokenText,
      recommendedAction: state.recommendedAction,
    );
    final current = List<AlertItem>.from(alerts.value);
    current.removeWhere((e) => e.id == item.id);
    current.insert(0, item);
    if (current.length > 50) {
      current.removeRange(50, current.length);
    }
    alerts.value = current;
  }

  Future<void> _fetchAlerts() async {
    try {
      final response = await http.get(Uri.parse('${baseUrl.value}/alerts'));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as List<dynamic>;
        final incoming = data.map((e) => AlertItem.fromJson(e as Map<String, dynamic>)).toList();
        final merged = <String, AlertItem>{
          for (final item in alerts.value) item.id: item,
          for (final item in incoming) item.id: item,
        };
        final mergedList = merged.values.toList()
          ..sort((a, b) => b.timestamp.compareTo(a.timestamp));
        alerts.value = mergedList.take(50).toList();
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
