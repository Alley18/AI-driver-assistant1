import 'package:flutter/material.dart';
import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:hive/hive.dart';
import 'config.dart';

class AlertSummary extends StatefulWidget {
  final bool isWeekly; // true = weekly, false = monthly
  const AlertSummary({Key? key, this.isWeekly = true}) : super(key: key);

  @override
  State<AlertSummary> createState() => _AlertSummaryState();
}

class _AlertSummaryState extends State<AlertSummary> {
  double _totalAlerts = 0.0;
  Timer? _timer;
  String? _userID;

  @override
  void initState() {
    super.initState();
    _loadSessionAndData();

    // Refresh every 3 seconds
    _timer = Timer.periodic(const Duration(seconds: 3), (_) {
      _updateTotal();
    });
  }

  // ------ load current user info ------ //
  Future<void> _loadSessionAndData() async {
    final sessionBox = await Hive.openBox('session');
    _userID = sessionBox.get('userID');
    await _updateTotal();
  }
  // ------------------------------------ //

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  // ------ update total alerts for summary ------ //
  Future<void> _updateTotal() async {
    if (_userID == null) return;

    try {
      final endpoint = widget.isWeekly ? 'thisweek' : 'thismonth';
      final url = Uri.parse('$baseUrl/$endpoint?userID=$_userID');
      final response = await http.get(url);

      if (response.statusCode == 200) {
        final Map<String, dynamic> jsonData = json.decode(response.body);
        final values = jsonData.values.map((v) => v as int).toList();
        final total = values.isEmpty ? 0.0 : values.reduce((a, b) => a + b).toDouble();

        if (!mounted) return;
        setState(() {
          _totalAlerts = total;
        });
      }
    } catch (e) {
      debugPrint("Error updating total alerts: $e");
    }
  }
  // --------------------------------------------- //

  // ------ design ------//
  @override
  Widget build(BuildContext context) {
    final period = widget.isWeekly ? "week" : "month";
    final total = _totalAlerts;

    String alertLevel;
    if (widget.isWeekly) {
      if (total >= 10) {
        alertLevel = "high";
      } else if (total >= 5) {
        alertLevel = "moderate";
      } else {
        alertLevel = "low";
      }
    } else {
      if (total >= 40) {
        alertLevel = "high";
      } else if (total >= 20) {
        alertLevel = "moderate";
      } else {
        alertLevel = "low";
      }
    }

    final summary =
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
          width: double.infinity,
          padding: const EdgeInsets.all(12),
          margin: const EdgeInsets.symmetric(horizontal: 16),
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
