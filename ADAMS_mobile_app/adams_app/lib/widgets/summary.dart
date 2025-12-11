import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:hive/hive.dart';
import 'dart:async';
import 'config.dart';

class AlertSummary extends StatefulWidget {
  const AlertSummary({Key? key}) : super(key: key);

  @override
  State<AlertSummary> createState() => _AlertSummaryState();
}

class _AlertSummaryState extends State<AlertSummary> {
  String? _feedback;
  String? _recommendedAction;
  bool _isLoading = true;
  String? _userID;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _timer = Timer.periodic(const Duration(seconds: 3), (_) {
      _loadSummary();
    });
  }

  // ------ load user-specific data from backen ------ //
  Future<void> _loadSummary() async {
    try {
      // Get userID from Hive
      final sessionBox = await Hive.openBox('session');
      _userID = sessionBox.get('userID');

      // Fetch summary from backend
      final url = Uri.parse(
        '$baseUrl/feedback?userID=$_userID',
      ); // adjust endpoint
      final response = await http.get(url).timeout(const Duration(seconds: 3));

      if (response.statusCode == 200) {
        final Map<String, dynamic> jsonData = json.decode(response.body);

        if (!mounted) return;
        setState(() {
          _feedback = jsonData['feedback'] ?? 'No feedback available';
          _recommendedAction =
              jsonData['recommended_action'] ??
              'No recommended action available.';
          _isLoading = false;
        });
      }
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _feedback =
            'Error connecting to server.. [$e]';
        _recommendedAction =
            'Error connecting to server.. [$e]';
        _isLoading = false;
      });
    }
  }
  // ------------------------------------------------- //

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  // ------ design ------ //
  @override
  Widget build(BuildContext context) {
    if (_isLoading) return const Center(child: CircularProgressIndicator());

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [

          // Feedback Section
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(12),
            margin: const EdgeInsets.only(bottom: 16),
            decoration: BoxDecoration(
              color: Colors.blue.shade50,
              borderRadius: BorderRadius.circular(12),
            ),
            child: RichText(
              text: TextSpan(
                style: const TextStyle(fontSize: 16, color: Colors.black, fontFamily: 'AlanSans'),
                children: [
                  const TextSpan(
                    text: "💭 Feedback:\n\n",
                    style: TextStyle(fontWeight: FontWeight.bold, fontFamily: 'AlanSans'),
                  ),
                  TextSpan(
                    text: _feedback ?? '',
                    style: const TextStyle(fontWeight: FontWeight.normal, fontFamily: 'AlanSans'),
                  ),
                ],
              ),
            ),
          ),

          // Recommended Action Section
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.green.shade50,
              borderRadius: BorderRadius.circular(12),
            ),
            child: RichText(
              text: TextSpan(
                style: const TextStyle(fontSize: 16, color: Colors.black, fontFamily: 'AlanSans'),
                children: [
                  const TextSpan(
                    text: "✅ Recommended Action:\n\n",
                    style: TextStyle(fontWeight: FontWeight.bold, fontFamily: 'AlanSans'),
                  ),
                  TextSpan(
                    text: _recommendedAction ?? '',
                    style: const TextStyle(fontWeight: FontWeight.normal, fontFamily: 'AlanSans'),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
