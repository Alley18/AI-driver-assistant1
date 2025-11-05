import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'config.dart';
import 'dart:async';

Future<Map<String, List<Map<String, String>>>> loadEventLog(String? username) async {
  final url = Uri.parse('$baseUrl/event-log-list?username=$username'); // flask
  final response = await http.get(url);

  if (response.statusCode == 200) {
    final Map<String, dynamic> rawData = json.decode(response.body);
    return rawData.map((day, events) {
      final list = (events as List)
          .map((e) => Map<String, String>.from(e))
          .toList();
      return MapEntry(day, list);
    });
  } else {
    throw Exception('Failed to load event log');
  }
}

class EventLogList extends StatefulWidget {
  final String day;
  final String? username;
  const EventLogList({Key? key, required this.day, required this.username}) : super(key: key);

  @override
  State<EventLogList> createState() => _EventLogListState();
}

class _EventLogListState extends State<EventLogList> {
  List<Map<String, String>> events = [];
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _loadData(widget.day);

    _timer = Timer.periodic(const Duration(seconds: 3), (timer) {
      _loadData(widget.day); // refresh
    });
  }

  @override
  void dispose() {
    _timer?.cancel(); // clean up timer when page closes
    super.dispose();
  }

  Future<void> _loadData(String day) async {
    try {
      final allData = await loadEventLog(widget.username);
      if (!mounted) return; // prevent setState after dispose
      setState(() {
        events = (allData[day] ?? []).reversed.toList();
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
      // scrollable list with a separator ----- between items
      itemCount: events.length,
      separatorBuilder: (context, index) => const SizedBox(height: 8),
      itemBuilder: (context, index) {
        final e = events[index];
        return Container(
          margin: const EdgeInsets.symmetric(horizontal: 16),
          padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
          decoration: BoxDecoration(
            color: Colors.blue.shade50,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(e["time"]!, style: const TextStyle(fontSize: 16)),
              Text(e["type"]!, style: const TextStyle(fontSize: 16)),
            ],
          ),
        );
      },
    );
  }
}
