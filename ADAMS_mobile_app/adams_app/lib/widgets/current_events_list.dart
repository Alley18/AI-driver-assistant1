import 'package:flutter/material.dart';
import 'package:hive/hive.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'config.dart';
import 'dart:async';

class CurrentEventsList extends StatefulWidget {
  const CurrentEventsList({Key? key}) : super(key: key);

  @override
  State<CurrentEventsList> createState() => _CurrentEventsListState();
}

class _CurrentEventsListState extends State<CurrentEventsList> {
  List<Map<String, String>> events = [];
  String? _userID;
  bool _isLoading = true;
  Timer? _timer;

  @override
  void initState() {
    super.initState();

    // ------ refresh every 3 seconds ------ //
    _timer = Timer.periodic(const Duration(seconds: 3), (_) {
      _loadData();
    });
    // ------------------------------------- //
  }

  // ------ get user-specific event log ------ //
  Future<List<Map<String, String>>> loadEventLog(String? userID) async {
    if (userID == null) return [];

    final url = Uri.parse('$baseUrl/current-events-list?userID=$userID');
    final response = await http.get(url);

    if (response.statusCode == 200) {
      final List<dynamic> rawData = json.decode(response.body);

      List<Map<String, String>> allEvents = rawData
          .map((e) => Map<String, String>.from(e))
          .toList();

      // ------ sort latest first (assuming 'time' in HH:mm format) ------ //
      allEvents.sort((a, b) => b["time"]!.compareTo(a["time"]!));
      return allEvents;
      // ----------------------------------------------------------------- //
    } else {
      throw Exception('Failed to load event log');
    }
  }
  // ----------------------------------------- //

  // ------ get user-specific info ------ //
  Future<void> _loadData() async {
    try {
      final sessionBox = await Hive.openBox('session');
      _userID = sessionBox.get('userID');

      if (_userID != null) {
        final data = await loadEventLog(_userID);

        if (!mounted) return;
        setState(() {
          events = data;
        });
      }
    } catch (e) {
      debugPrint("Error loading session/events: $e");
    } finally {
      if (!mounted) return;
      setState(() {
        _isLoading = false;
      });
    }
  }
  // ------------------------------------ //

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
