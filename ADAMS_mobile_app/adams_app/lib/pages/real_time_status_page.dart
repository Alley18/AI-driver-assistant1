import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:hive/hive.dart';
import 'package:http/http.dart' as http;
import 'package:idas_app/widgets/current_events_list.dart';
import 'package:idas_app/widgets/real_time_status_chart.dart';
import '../widgets/config.dart';

class RealTimeStatus extends StatefulWidget {
  const RealTimeStatus({super.key});

  @override
  State<RealTimeStatus> createState() => _RealTimeStatusState();
}

class _RealTimeStatusState extends State<RealTimeStatus> {
  String _driverStatus = "Loading...";
  Timer? _timer;

  String? username;
  String? userID;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadSessionAndStart();
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  // ------ load session from Hive and start periodic fetching ------ //
  Future<void> _loadSessionAndStart() async {
    final sessionBox = await Hive.openBox('session');
    setState(() {
      username = sessionBox.get('currentUser');
      userID = sessionBox.get('userID');
      _isLoading = false;
    });

    if (userID != null) {
      _fetchDriverStatus();
      _timer = Timer.periodic(const Duration(seconds: 3), (_) => _fetchDriverStatus());
    }
  }
  // ---------------------------------------------------------------- //

  // ------ get data from backend ------ //
  Future<void> _fetchDriverStatus() async {
    if (userID == null) return;

    try {
      final url = Uri.parse('$baseUrl/current-driver-status?userID=$userID');
      final response = await http.get(url);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (!mounted) return;
        setState(() {
          _driverStatus = data['driver_state'] ?? "Unknown";
        });
      } else {
        print("Failed to load driver status (${response.statusCode})");
      }
    } catch (e) {
      print("Error fetching driver status: $e");
    }
  }
  // ----------------------------------- //

  // ------ set color of driver status ------ //
  Color _getStatusColor(String status) {
    switch (status) {
      case "normal":
        return Colors.green;
      case "distracted":
        return Colors.orange;
      case "drowsy":
        return Colors.red;
      default:
        return Colors.grey;
    }
  }
  // ---------------------------------------- //

  // ------ design ------ //
  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            const SizedBox(height: 16),
            const Text(
              "Real-time Status",
              style: TextStyle(fontSize: 40, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),

            // Driver status
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  "${username ?? 'User'}'s Status: ",
                  style: const TextStyle(fontSize: 21, color: Colors.black),
                ),
                AnimatedDefaultTextStyle(
                  duration: const Duration(milliseconds: 500),
                  style: TextStyle(
                    fontSize: 21,
                    fontWeight: FontWeight.bold,
                    color: _getStatusColor(_driverStatus),
                  ),
                  child: Text(
                    _driverStatus.isNotEmpty
                        ? _driverStatus[0].toUpperCase() + _driverStatus.substring(1)
                        : _driverStatus,
                  ),
                ),
              ],
            ),

            const SizedBox(height: 24),

            Expanded(
              child: Column(
                children: [
                  Expanded(
                    flex: 2,
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      child: RealTimeStatusReport(),
                    ),
                  ),
                  const Text(
                    "Event Logs",
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  Expanded(flex: 1, child: CurrentEventsList()),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
