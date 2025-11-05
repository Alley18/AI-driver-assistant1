import 'package:flutter/material.dart';
import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'config.dart';

class AlertSummary extends StatefulWidget {
  final bool isWeekly; // true = weekly, false = monthly
  final String? username;
  const AlertSummary({Key? key, this.isWeekly = true, required this.username})
    : super(key: key);

  @override
  State<AlertSummary> createState() => _AlertSummaryState();
}

class _AlertSummaryState extends State<AlertSummary> {
  // 1. RENAME to reflect 'Total' instead of 'Average'
  double _totalWeeklyAlerts = 0.0;
  double _totalMonthlyAlerts = 0.0;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _updateTotal(); // Changed method name
    // Refresh every 3 seconds
    _timer = Timer.periodic(const Duration(seconds: 3), (_) {
      _updateTotal(); // Changed method name
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _updateTotal() async {
    if (widget.username == null) return; // exit if username is not provided
    try {
      if (widget.isWeekly) {
        await _calculateWeeklyTotal(widget.username);
      } else {
        await _calculateMonthlyTotal(widget.username);
      }
    } catch (e) {
      debugPrint("Error updating total: $e");
    }
  }

  Future<void> _calculateWeeklyTotal(String? username) async {
    // Changed method name
    final url = Uri.parse('$baseUrl/thisweek?username=$username');
    final response = await http.get(url);

    if (response.statusCode == 200) {
      final Map<String, dynamic> jsonData = json.decode(response.body);

      final values = jsonData.values.map((v) => v as int).toList();

      // 2. CHANGE: Calculate the SUM (Total), not the average.
      final total = values.isEmpty
          ? 0.0
          : (values.reduce(
              (a, b) => a + b,
            )).toDouble(); // REMOVED: / values.length

      if (!mounted) return;
      setState(() {
        _totalWeeklyAlerts = total; // Changed variable name
      });

      debugPrint("Weekly total updated: $_totalWeeklyAlerts");
    }
  }

  Future<void> _calculateMonthlyTotal(String? username) async {
    // Changed method name
    final url = Uri.parse('$baseUrl/thismonth?username=$username');
    final response = await http.get(url);

    if (response.statusCode == 200) {
      final Map<String, dynamic> jsonData = json.decode(response.body);

      final values = jsonData.values.map((v) => v as int).toList();

      // 2. CHANGE: Calculate the SUM (Total), not the average.
      final total = values.isEmpty
          ? 0.0
          : (values.reduce(
              (a, b) => a + b,
            )).toDouble(); // REMOVED: / values.length

      if (!mounted) return;
      setState(() {
        _totalMonthlyAlerts = total; // Changed variable name
      });

      debugPrint("Monthly total updated: $_totalMonthlyAlerts");
    }
  }

  @override
  Widget build(BuildContext context) {
    String summary;
    final period = widget.isWeekly ? "week" : "month";
    final total = widget.isWeekly
        ? _totalWeeklyAlerts
        : _totalMonthlyAlerts; // Changed variable name

    // Determine alert level with the recommended total thresholds
    String alertLevel;
    if (widget.isWeekly) {
      // 3. UPDATE THRESHOLDS based on total APW (e.g., 10+ is High Risk)
      if (total >= 10) {
        alertLevel = "high";
      } else if (total >= 5) {
        alertLevel = "moderate";
      } else {
        alertLevel = "low";
      }
    } else {
      // Monthly thresholds (assuming ~4.3 weeks/month, so 4.3x the weekly thresholds)
      if (total >= 40) {
        alertLevel = "high";
      } else if (total >= 20) {
        alertLevel = "moderate";
      } else {
        alertLevel = "low";
      }
    }

    // 3. UPDATE SUMMARY TEXT to reflect the TOTAL number
    summary =
        "This $period, ${total.toStringAsFixed(0)} alerts were triggered.\n"
        "The driver has a $alertLevel risk level.\n\n"
        "${alertLevel == 'high'
            ? '🚨 IMMEDIATE ACTION: \nReview driver behavior and take necessary precautions to drive safer.'
            : alertLevel == 'moderate'
            ? '⚠️ WARNING: Stay alert and drive responsibly to reduce your total. Avoid High Risk!'
            : '✅ Great job – stay attentive and keep it up!'}";

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 16),
        Container(
          width: double.infinity, // takes full width of the parent
          padding: const EdgeInsets.all(12),
          margin: const EdgeInsets.symmetric(
            horizontal: 16,
          ), // optional padding from edges
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
      ],
    );
  }
}
