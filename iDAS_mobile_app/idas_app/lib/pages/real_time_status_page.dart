import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:idas_app/widgets/current_events_list.dart';
import 'package:idas_app/widgets/real_time_status_chart.dart';
import '../widgets/config.dart'; // for baseUrl

class RealTimeStatus extends StatefulWidget {
  const RealTimeStatus({super.key});

  @override
  State<RealTimeStatus> createState() => _RealTimeStatusState();
}

class _RealTimeStatusState extends State<RealTimeStatus> {
  String _driverStatus = "Loading..."; // initial placeholder
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _fetchDriverStatus(); // fetch immediately
    // refresh every 3 seconds
    _timer = Timer.periodic(const Duration(seconds: 3), (_) {
      _fetchDriverStatus();
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _fetchDriverStatus() async {
    try {
      final url = Uri.parse('$baseUrl/current-driver-status');
      final response = await http.get(url);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (!mounted) return;
        setState(() {
          _driverStatus = data['status'] ?? "Unknown";
        });
      } else {
        print("Failed to load driver status");
      }
    } catch (e) {
      print("Error fetching driver status: $e");
    }
  }

  // returns color based on driver status
  Color _getStatusColor(String status) {
    switch (status) {
      case "Neutral":
        return Colors.grey;
      case "Mildly Fatigued":
        return Colors.amber;
      case "Moderately Fatigued":
        return Colors.orange;
      case "Severely Fatigued":
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  @override
  Widget build(BuildContext context) {
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

            // Driver status with smooth color change
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Text(
                  "Driver Status: ",
                  style: TextStyle(fontSize: 21, color: Colors.black),
                ),
                AnimatedDefaultTextStyle(
                  duration: const Duration(milliseconds: 500),
                  style: TextStyle(
                    fontSize: 21,
                    fontWeight: FontWeight.bold,
                    color: _getStatusColor(_driverStatus),
                  ),
                  child: Text(_driverStatus),
                ),
              ],
            ),

            const SizedBox(height: 24),

            // Pie chart + event log
            Expanded(
              child: Column(
                children:  [
                  Expanded(
                    child: Padding(
                      padding: EdgeInsets.symmetric(vertical: 16),
                      child: RealTimeStatusReport(),
                    ),
                  ),
                  SizedBox(height: 16),
                  Text(
                    "Event Logs",
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                  SizedBox(height: 8),
                  Expanded(child: CurrentEventsList()),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
