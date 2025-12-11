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
  String? latestEventKey; // unique key for highlighting
  late Box sessionBox;
  bool useMock = false; // debug

  @override
  void initState() {
    super.initState();
    Hive.openBox('session').then((box) {
      sessionBox = box;
      _userID = sessionBox.get('userID');
      _loadData();
      _timer = Timer.periodic(const Duration(seconds: 3), (_) => _loadData());
    });
  }

  // ------ mock data for debugging ------ //
  // int mockCounter = 0;
  // String hhmm(DateTime dt) => "${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}";

  // Future<List<Map<String, String>>> _mockEvents() async {
  //   await Future.delayed(const Duration(seconds: 2)); // simulate backend delay
  //   mockCounter++;

  //   final now = DateTime.now();

  //   List<Map<String, String>> list = [
  //     {"time": hhmm(now.subtract(Duration(minutes: 2))), "type": "Yawning"},
  //     {"time": hhmm(now.subtract(Duration(minutes: 1))), "type": "Drowsy"},
  //     {"time": hhmm(now.subtract(Duration(minutes: 1))), "type": "Drowsy"}, // same time & type
  //     {"time": hhmm(now.add(Duration(seconds: mockCounter))), "type": "NEW Event #$mockCounter"},
  //   ];

  //   list.sort((a, b) => b["time"]!.compareTo(a["time"]!));
  //   return list;
  // }
  // --------------------------------------- //

  // ------ load user-specific data ------ //
  Future<List<Map<String, String>>> loadEventLog(String? userID) async {
    // if (useMock) return _mockEvents();
    if (userID == null) return [];

    final url = Uri.parse('$baseUrl/current-events-list?userID=$userID');
    final response = await http.get(url);

    if (response.statusCode == 200) {
      final List<dynamic> rawData = json.decode(response.body);
      return rawData.map((e) => Map<String, String>.from(e)).toList();
    } else {
      throw Exception('Failed to load event log');
    }
  }
  // ------------------------------------- //

  // ------ update widget ------ //
  Future<void> _loadData() async {
    try {
      _userID = sessionBox.get('userID');

      if (_userID != null) {
        final data = await loadEventLog(_userID);
        if (!mounted) return;

        setState(() {
          events = data.reversed.toList();

          if (data.isNotEmpty) {
            latestEventKey = "${data.first['time']}_${data.first['type']}_${DateTime.now().millisecondsSinceEpoch}";
          }
        });
      }
    } catch (e) {
      debugPrint("Error loading events: $e");
    } finally {
      if (!mounted) return;
      _isLoading = false;
    }
  }
  // --------------------------- //

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  // ------ design ------ //
  @override
  Widget build(BuildContext context) {
    if (_isLoading) return const Center(child: CircularProgressIndicator());
    if (events.isEmpty) return const Center(child: Text("No events logged.", style: TextStyle(fontSize: 16)));

    return ListView.separated(
      itemCount: events.length,
      separatorBuilder: (_, __) => const SizedBox(height: 8),
      itemBuilder: (context, index) {
        final e = events[index];
        final eventKey = "${e['time']}_${e['type']}_$index"; // ensures duplicates have unique keys
        final isLatest = index == 0; // only highlight first item
        return TweenAnimationBuilder<Color?>(
          key: ValueKey(eventKey + (isLatest ? latestEventKey ?? '' : '')),
          duration: const Duration(seconds: 5),
          tween: ColorTween(
            begin: isLatest ? Colors.orange.shade100 : Colors.blue.shade50,
            end: Colors.blue.shade50,
          ),
          builder: (context, color, child) {
            return Container(
              margin: const EdgeInsets.symmetric(horizontal: 16),
              padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
              decoration: BoxDecoration(
                color: color,
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
      },
    );
  }
}
