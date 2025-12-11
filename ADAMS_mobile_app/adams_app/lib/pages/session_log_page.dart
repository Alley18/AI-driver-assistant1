import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:hive/hive.dart';
import 'package:http/http.dart' as http;
import '../widgets/config.dart';

class SessionLogPage extends StatefulWidget {
  const SessionLogPage({super.key});

  @override
  State<SessionLogPage> createState() => _SessionLogPageState();
}

class _SessionLogPageState extends State<SessionLogPage> {
  String? userID;
  bool _isLoading = true;

  List<Map<String, dynamic>> sessions = [];

  @override
  void initState() {
    super.initState();
    _loadSession();
  }

  // ------ get user info from backend ------ //
  Future<void> _loadSession() async {
    try {
      setState(() => _isLoading = true);

      final sessionBox = await Hive.openBox('session');
      userID = sessionBox.get('userID');

      final url = Uri.parse("$baseUrl/sessions?userID=$userID");
      final response = await http.get(url).timeout(const Duration(seconds: 8));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);

        setState(() {
          if (data is List) {
            sessions = List<Map<String, dynamic>>.from(data).reversed.toList();
          } else {
            sessions = [];
          }
          _isLoading = false;
        });
      } else {
        setState(() => _isLoading = false);
      }
    } catch (e) {
      debugPrint("SESSION ERROR: $e");
      if (mounted) {
        setState(() {
          _isLoading = false;
          sessions = [];
        });
      }
    }
  }
  // ---------------------------------------- //

  // ------ design ------ //
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.blue.shade300,
        centerTitle: true,
        leading: IconButton(
          onPressed: () => Navigator.pop(context),
          icon: const Icon(Icons.arrow_back, color: Colors.white),
        ),
        title: const Text(
          "ADAMS",
          style: TextStyle(fontSize: 30, color: Colors.white),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: double.infinity),
            child: Column(
              children: [
                const SizedBox(height: 16),
                Text(
                  "Session Logs",
                  style: TextStyle(fontSize: 40, fontWeight: FontWeight.bold),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 16),

                if (_isLoading) ...[
                  const CircularProgressIndicator(),
                ] else if (sessions.isEmpty) ...[
                  Padding(
                    padding: const EdgeInsets.only(top: 16),
                    child: Text(
                      "No session data available.",
                      style: TextStyle(fontSize: 20, color: Colors.grey),
                      textAlign: TextAlign.center,
                    ),
                  ),
                ],

                // >>> show the session list ONLY if data exists
                if (sessions.isNotEmpty)
                  Column(
                    children: sessions.map((session) {
                      final date = session['date'];
                      final start = session['start'];
                      final end = session['end'];
                      final events = session['events'] as List;

                      return Container(
                        margin: const EdgeInsets.symmetric(vertical: 8),
                        decoration: BoxDecoration(
                          color: Colors.blue.shade50,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Theme(
                          data: Theme.of(context).copyWith(
                            dividerColor: Colors.transparent,
                            splashColor: Colors.transparent,
                            highlightColor: Colors.transparent,
                            hoverColor: Colors.transparent,
                            focusColor: Colors.transparent,
                          ),
                          child: ExpansionTile(
                            iconColor: Colors.black,
                            collapsedIconColor: Colors.black,
                            title: Text(
                              "$date [$start - $end]",
                              style: const TextStyle(
                                fontSize: 16,
                                color: Colors.black,
                              ),
                            ),
                            children: [
                              Container(
                                padding: const EdgeInsets.all(16),
                                width: double.infinity,
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: events.map<Widget>((e) {
                                    return Text(
                                      "${e['time']}  ${e['event']}",
                                      style: const TextStyle(fontSize: 16),
                                    );
                                  }).toList(),
                                ),
                              ),
                            ],
                          ),
                        ),
                      );
                    }).toList(),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
