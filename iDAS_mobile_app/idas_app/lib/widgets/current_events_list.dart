import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'config.dart';
import 'dart:async';

// Fetch directly as a list of event objects
Future<List<Map<String, String>>> loadEventLog() async {
  final url = Uri.parse('$baseUrl/current-events-list'); // Flask endpoint
  final response = await http.get(url);

  if (response.statusCode == 200) {
    final List<dynamic> rawData = json.decode(response.body);

    // Convert to List<Map<String, String>>
    List<Map<String, String>> allEvents =
        rawData.map((e) => Map<String, String>.from(e)).toList();

    // Sort latest first (assuming 'time' is in HH:mm format)
    allEvents.sort((a, b) => b["time"]!.compareTo(a["time"]!));

    return allEvents;
  } else {
    throw Exception('Failed to load event log');
  }
}

class CurrentEventsList extends StatefulWidget {
  const CurrentEventsList({Key? key}) : super(key: key);

  @override
  State<CurrentEventsList> createState() => _CurrentEventsListState();
}

class _CurrentEventsListState extends State<CurrentEventsList> {
  List<Map<String, String>> events = [];
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _loadData();

    // refresh every 3 seconds
    _timer = Timer.periodic(const Duration(seconds: 3), (timer) {
      _loadData();
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _loadData() async {
    try {
      final data = await loadEventLog();
      if (!mounted) return;
      setState(() {
        events = data;
      });
    } catch (e) {
      debugPrint("Error loading event log: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    if (events.isEmpty) {
      return const Center(
        child: Text("No events logged.", style: TextStyle(fontSize: 16)),
      );
    }

    return ListView.separated(
      itemCount: events.length,
      separatorBuilder: (context, index) => const SizedBox(height: 8),
      itemBuilder: (context, index) {
        final e = events[index];
        return Container(
          margin: const EdgeInsets.symmetric(horizontal: 16),
          padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
          decoration: BoxDecoration(
            color: const Color.fromARGB(255, 225, 241, 242),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(e["time"] ?? "-", style: const TextStyle(fontSize: 16)),
              Text(e["type"] ?? "-", style: const TextStyle(fontSize: 16)),
            ],
          ),
        );
      },
    );
  }
}
