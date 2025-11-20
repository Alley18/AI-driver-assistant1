import 'package:flutter/material.dart';
import 'package:hive/hive.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'config.dart';
import 'dart:async';

// Fetch all events grouped by day
Future<Map<String, List<Map<String, String>>>> loadEventLog(String? userID) async {
  if (userID == null) return {};
  final url = Uri.parse('$baseUrl/event-log-list?userID=$userID'); 
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
  const EventLogList({Key? key, required this.day}) : super(key: key); // removed userID

  @override
  State<EventLogList> createState() => _EventLogListState();
}

class _EventLogListState extends State<EventLogList> {
  List<Map<String, String>> events = [];
  String? _userID;
  bool _isLoading = true;
  Timer? _timer;

  @override
  void initState() {
    super.initState();

    _timer = Timer.periodic(const Duration(seconds: 3), (_) {
      _loadData(); // refresh
    });
  }

  // ------ get user-specific info ------ //
  Future<void> _loadData() async {
  try {
    final sessionBox = await Hive.openBox('session');
    _userID = sessionBox.get('userID');

    final allData = await loadEventLog(_userID);

    if (!mounted) return;
    setState(() {
      events = (allData[widget.day] ?? []).reversed.toList();
      _isLoading = false; 
    });
  } catch (e) {
    debugPrint("Error loading event log: $e");
    if (!mounted) return;
    setState(() {
      _isLoading = false;
    });
  }
}
// -------------------------------------- //

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  // ------ design ------ //
  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (events.isEmpty) {
      return const Center(
        child: Text("No events logged.", style: TextStyle(fontSize: 16)),
      );
    }

    return ListView.separated(
      itemCount: events.length,
      separatorBuilder: (_, __) => const SizedBox(height: 8),
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
              Text(e["time"] ?? "-", style: const TextStyle(fontSize: 16)),
              Text(e["type"] ?? "-", style: const TextStyle(fontSize: 16)),
            ],
          ),
        );
      },
    );
  }
}
