import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'config.dart';
import 'dart:async';

Future<Map<String, List<Map<String, String>>>> loadEventLog() async {
  final url = Uri.parse('$baseUrl/event-log-list'); // flask
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
  const EventLogList({Key? key, required this.day}) : super(key: key);

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
      final allData = await loadEventLog();
      if (!mounted) return; // prevent setState after dispose
      setState(() {
        events = allData[day] ?? [];
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
            color: Color.fromARGB(255, 225, 241, 242),
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
