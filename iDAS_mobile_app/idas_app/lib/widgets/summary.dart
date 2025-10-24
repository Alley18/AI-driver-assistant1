import 'package:flutter/material.dart';
import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'config.dart';

class AlertSummary extends StatefulWidget {
  final bool isWeekly; // true = weekly, false = monthly

  const AlertSummary({Key? key, this.isWeekly = true}) : super(key: key);

  @override
  State<AlertSummary> createState() => _AlertSummaryState();
}

class _AlertSummaryState extends State<AlertSummary> {
  double _average = 0.0;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _updateAverage();

    // Refresh every 3 seconds
    _timer = Timer.periodic(const Duration(seconds: 3), (_) {
      _updateAverage();
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _updateAverage() async {
    try {
      if (widget.isWeekly) {
        await _calculateWeeklyAverage();
      } else {
        await _calculateMonthlyAverage();
      }
    } catch (e) {
      debugPrint("Error updating average: $e");
    }
  }

  Future<void> _calculateWeeklyAverage() async {
    final url = Uri.parse('$baseUrl/thisweek');
    final response = await http.get(url);

    if (response.statusCode == 200) {
      final Map<String, dynamic> jsonData = json.decode(response.body);

      final values = jsonData.values.map((v) => v as int).toList();
      final average = values.isEmpty
          ? 0.0
          : (values.reduce((a, b) => a + b) / values.length).toDouble();

      if (!mounted) return;
      setState(() {
        _average = average;
      });

      debugPrint("Weekly average updated: $_average");
    }
  }

  Future<void> _calculateMonthlyAverage() async {
    final url = Uri.parse('$baseUrl/thismonth');
    final response = await http.get(url);

    if (response.statusCode == 200) {
      final Map<String, dynamic> jsonData = json.decode(response.body);

      final values = jsonData.values.map((v) => v as int).toList();
      final average = values.isEmpty
          ? 0.0
          : (values.reduce((a, b) => a + b) / values.length).toDouble();

      if (!mounted) return;
      setState(() {
        _average = average;
      });

      debugPrint("Monthly average updated: $_average");
    }
  }

  @override
  Widget build(BuildContext context) {
    String summary;
    final period = widget.isWeekly ? "week" : "month";

    // Use the average to determine alert level
    String alertLevel;
    if (_average >= 3) {
      alertLevel = "high";
    } else if (_average > 0) {
      alertLevel = "moderate";
    } else {
      alertLevel = "low";
    }

    // Construct a 2–3 sentence summary
    summary =
        "This $period, the driver has triggered an average of ${_average.toStringAsFixed(1)} alerts per ${widget.isWeekly ? "day" : "interval"}.\n"
        "The alert level is considered $alertLevel.\n"
        "${alertLevel == 'high'
            ? 'Please review driver behavior and take the necessary precautions to drive safer.'
            : alertLevel == 'moderate'
            ? 'Stay alert and drive responsibly.'
            : 'Great job - stay attentive and keep it up!'}";

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 16),
        Center(
          child: SizedBox(
            width: 300, // fixed width
            height: 120, // slightly taller for longer text
            child: Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.blue.shade50,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                summary,
                style: const TextStyle(fontSize: 16),
                textAlign: TextAlign.left,
              ),
            ),
          ),
        ),
      ],
    );
  }
}
