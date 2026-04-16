import 'package:flutter/material.dart';

import 'models/alert_item.dart';
import 'models/driver_state.dart';
import 'services/api_service.dart';
import 'widgets/alert_card.dart';
import 'widgets/info_tile.dart';
import 'widgets/status_chip.dart';

class AdamsLiveApp extends StatelessWidget {
  const AdamsLiveApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'ADAMS Live Mobile',
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF0B1220),
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.blue,
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),
      home: const LiveShell(),
    );
  }
}

class LiveShell extends StatefulWidget {
  const LiveShell({super.key});

  @override
  State<LiveShell> createState() => _LiveShellState();
}

class _LiveShellState extends State<LiveShell> {
  int _index = 0;
  final ApiService _api = ApiService();

  @override
  void dispose() {
    _api.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final screens = [
      DashboardScreen(api: _api),
      MonitoringScreen(api: _api),
      AlertsScreen(api: _api),
      HistoryScreen(api: _api),
      SchemaScreen(api: _api),
    ];

    return Scaffold(
      appBar: AppBar(
        backgroundColor: const Color(0xFF111827),
        title: const Text('ADAMS Live Monitor'),
        actions: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: Center(
              child: ValueListenableBuilder<bool>(
                valueListenable: _api.isHealthy,
                builder: (_, healthy, __) => StatusChip(
                  label: healthy ? 'Backend Online' : 'Backend Offline',
                  color: healthy ? Colors.greenAccent : Colors.redAccent,
                ),
              ),
            ),
          ),
          IconButton(
            onPressed: _showBackendDialog,
            icon: const Icon(Icons.settings_ethernet),
            tooltip: 'Backend URL',
          ),
        ],
      ),
      body: screens[_index],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (value) => setState(() => _index = value),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.dashboard), label: 'Dashboard'),
          NavigationDestination(icon: Icon(Icons.videocam), label: 'Monitor'),
          NavigationDestination(icon: Icon(Icons.warning_amber_rounded), label: 'Alerts'),
          NavigationDestination(icon: Icon(Icons.history), label: 'History'),
          NavigationDestination(icon: Icon(Icons.description), label: 'Schema'),
        ],
      ),
    );
  }

  Future<void> _showBackendDialog() async {
    final controller = TextEditingController(text: _api.baseUrl.value);
    await showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Backend URL'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(
            hintText: 'http://192.168.0.10:8000',
            labelText: 'Base URL',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () {
              _api.updateBaseUrl(controller.text.trim());
              Navigator.pop(context);
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );
  }
}

class DashboardScreen extends StatelessWidget {
  final ApiService api;
  const DashboardScreen({super.key, required this.api});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<DriverState?>(
      valueListenable: api.currentState,
      builder: (_, state, __) {
        if (state == null) {
          return const Center(child: CircularProgressIndicator());
        }
        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _HeroCard(state: state, api: api),
            const SizedBox(height: 16),
            GridView.count(
              crossAxisCount: 2,
              crossAxisSpacing: 12,
              mainAxisSpacing: 12,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              children: [
                InfoTile.card(title: 'Risk Level', value: state.level, icon: Icons.shield, color: state.levelColor),
                InfoTile.card(title: 'Driver State', value: state.driverState, icon: Icons.person, color: state.levelColor),
                InfoTile.card(title: 'Message', value: state.message, icon: Icons.message, color: Colors.lightBlueAccent),
                InfoTile.card(title: 'Buzzer', value: state.buzzer ? 'ON' : 'OFF', icon: Icons.notifications_active, color: state.buzzer ? Colors.orangeAccent : Colors.greenAccent),
              ],
            ),
            const SizedBox(height: 16),
            Card(
              color: const Color(0xFF111827),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Live Source', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 12),
                    _Row(label: 'Backend URL', value: api.baseUrl.value),
                    _Row(label: 'Timestamp', value: state.timestamp),
                    _Row(label: 'Raw input', value: state.input),
                    _Row(label: 'Source file', value: state.sourcePath),
                  ],
                ),
              ),
            ),
          ],
        );
      },
    );
  }
}

class MonitoringScreen extends StatelessWidget {
  final ApiService api;
  const MonitoringScreen({super.key, required this.api});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<DriverState?>(
      valueListenable: api.currentState,
      builder: (_, state, __) {
        if (state == null) {
          return const Center(child: CircularProgressIndicator());
        }
        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Container(
              height: 240,
              decoration: BoxDecoration(
                color: const Color(0xFF111827),
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: Colors.blueAccent.withOpacity(0.3)),
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(state.buzzer ? Icons.warning_amber_rounded : Icons.videocam, size: 72, color: state.levelColor),
                  const SizedBox(height: 12),
                  Text(state.driverState, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  Text(state.message, textAlign: TextAlign.center),
                  const SizedBox(height: 12),
                  StatusChip(label: 'Polling every 1 second', color: Colors.lightBlueAccent),
                ],
              ),
            ),
            const SizedBox(height: 16),
            InfoTile.list(title: 'Current level', subtitle: state.level, icon: Icons.flag, color: state.levelColor),
            InfoTile.list(title: 'Alert action', subtitle: state.buzzer ? 'Alarm should trigger on desktop side' : 'No alarm needed', icon: Icons.volume_up, color: state.buzzer ? Colors.orangeAccent : Colors.greenAccent),
            InfoTile.list(title: 'Camera interpretation', subtitle: state.input, icon: Icons.center_focus_strong, color: Colors.lightBlueAccent),
            InfoTile.list(title: 'System note', subtitle: 'This app listens to the backend, not directly to the camera.', icon: Icons.info_outline, color: Colors.purpleAccent),
          ],
        );
      },
    );
  }
}

class AlertsScreen extends StatelessWidget {
  final ApiService api;
  const AlertsScreen({super.key, required this.api});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<List<AlertItem>>(
      valueListenable: api.alerts,
      builder: (_, alerts, __) {
        if (alerts.isEmpty) {
          return const Center(child: CircularProgressIndicator());
        }
        return ListView.separated(
          padding: const EdgeInsets.all(16),
          itemCount: alerts.length,
          separatorBuilder: (_, __) => const SizedBox(height: 12),
          itemBuilder: (_, index) => AlertCard(item: alerts[index]),
        );
      },
    );
  }
}

class HistoryScreen extends StatelessWidget {
  final ApiService api;
  const HistoryScreen({super.key, required this.api});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<List<AlertItem>>(
      valueListenable: api.alerts,
      builder: (_, alerts, __) {
        if (alerts.isEmpty) {
          return const Center(child: CircularProgressIndicator());
        }
        return ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: alerts.length,
          itemBuilder: (_, index) {
            final item = alerts[index];
            return Card(
              color: const Color(0xFF111827),
              child: ListTile(
                leading: CircleAvatar(backgroundColor: item.color.withOpacity(0.15), child: Icon(Icons.history, color: item.color)),
                title: Text(item.message),
                subtitle: Text('${item.timestamp} • ${item.input}'),
                trailing: Text(item.level, style: TextStyle(color: item.color, fontWeight: FontWeight.bold)),
              ),
            );
          },
        );
      },
    );
  }
}

class SchemaScreen extends StatelessWidget {
  final ApiService api;
  const SchemaScreen({super.key, required this.api});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<Map<String, dynamic>?>(
      valueListenable: api.schema,
      builder: (_, schema, __) {
        if (schema == null) {
          return const Center(child: CircularProgressIndicator());
        }
        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Card(
              color: const Color(0xFF111827),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Text(schema.toString(), style: const TextStyle(height: 1.6)),
              ),
            ),
          ],
        );
      },
    );
  }
}

class _HeroCard extends StatelessWidget {
  final DriverState state;
  final ApiService api;
  const _HeroCard({required this.state, required this.api});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(colors: [state.levelColor.withOpacity(0.85), const Color(0xFF1D4ED8)]),
        borderRadius: BorderRadius.circular(24),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Current Live Driver State', style: TextStyle(color: Colors.white70)),
          const SizedBox(height: 12),
          Text(state.driverState, style: const TextStyle(fontSize: 26, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Text(state.message),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              StatusChip(label: state.level, color: state.levelColor),
              StatusChip(label: state.buzzer ? 'Buzzer ON' : 'Buzzer OFF', color: state.buzzer ? Colors.orangeAccent : Colors.greenAccent),
              StatusChip(label: 'Rows loaded: ${api.rowsLoaded.value}', color: Colors.lightBlueAccent),
            ],
          ),
        ],
      ),
    );
  }
}

class _Row extends StatelessWidget {
  final String label;
  final String value;
  const _Row({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(width: 110, child: Text(label, style: const TextStyle(color: Colors.white70))),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }
}
