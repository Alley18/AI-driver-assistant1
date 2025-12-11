import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:http/http.dart' as http;
import 'package:idas_app/pages/device_link_page.dart';
import 'package:idas_app/pages/login_page.dart';
import 'package:idas_app/pages/session_log_page.dart';
import 'package:idas_app/widgets/config.dart';

class SettingsPage extends StatefulWidget {
  const SettingsPage({super.key}); // no username needed

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  String? _username;
  String? _hardwareID;
  bool _isLoading = true;
  bool _isHardwareOn = false;
  late Box sessionBox;

  @override
  void initState() {
    super.initState();
    Hive.openBox('session').then((box) {
    sessionBox = box;
    _loadSession();
  });
  }

  // ------ load current user info ------ //
  Future<void> _loadSession() async {
    final sessionBox = await Hive.openBox('session');
    setState(() {
      _username = sessionBox.get('currentUser');
      _hardwareID = sessionBox.get('hardwareID');
      _isHardwareOn = sessionBox.get('isHardwareOn') ?? false;
      _hardwareID = sessionBox.get('hardwareID');
      _isLoading = false;
    });
  }
  // ------------------------------------ //

  // ------- function to logout (clear current session info) ------ //
  Future<void> _logout(BuildContext context) async {
    final sessionBox = await Hive.openBox('session');
    await sessionBox.clear(); // clear all session data

    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (_) => const LoginPage()),
    );
  }
  // -------------------------------------------------------------- //

  // ------ turn hardware on  ------ //
  Future<void> _on() async {
    debugPrint(_hardwareID);
    if (_hardwareID == null || _hardwareID.toString().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            "No hardware connected. Please link your device first.",
          ),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }
    try {
      final url = Uri.parse('$baseUrl/on-route');
      final response = await http.get(url);
      await sessionBox.put('isHardwareOn', true);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text("$_hardwareID turned ON!"),
          backgroundColor: Colors.green,
          duration: Duration(seconds: 1),
        ),
      );
      debugPrint("Hardware turned on!");
      setState(() {
        _isHardwareOn = true;
      });
    } catch (e) {
      debugPrint("Error: $e");
    }
  }
  // ------------------------------- //

  // ------ turn hardware off  ------ //
  Future<void> _off() async {
    debugPrint(_hardwareID);
    if (_hardwareID == null || _hardwareID.toString().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            "No hardware connected. Please link your device first.",
          ),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }
    try {
      final url = Uri.parse('$baseUrl/off-route');
      final response = await http.get(url);
      await sessionBox.put('isHardwareOn', false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text("$_hardwareID turned OFF!"),
          backgroundColor: Colors.red,
          duration: Duration(seconds: 1),
        ),
      );
      debugPrint("Hardware turned off!");
      setState(() {
        _isHardwareOn = false;
      });
    } catch (e) {
      debugPrint("Error: $e");
    }
  }
  // -------------------------------- //

  // ------ design ------ //
  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Column(
              children: [
                const Text(
                  "Settings",
                  style: TextStyle(fontSize: 40, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 10),
                // SizedBox(
                //   width: 200,
                //   height: 40,
                //   child: ElevatedButton(
                //     onPressed: _isHardwareOn ? _off : _on,
                //     style: ElevatedButton.styleFrom(
                //       backgroundColor: _isHardwareOn
                //           ? Colors.red
                //           : Colors.lightBlue,
                //       shape: RoundedRectangleBorder(
                //         borderRadius: BorderRadius.circular(12),
                //       ),
                //     ),
                //     child: Text(
                //       _isHardwareOn ? "Turn OFF Hardware" : "Turn ON Hardware",
                //       style: TextStyle(fontSize: 16, color: Colors.white),
                //     ),
                //   ),
                // ),

                const SizedBox(height: 16),
                ListTile(
                  leading: const Icon(Icons.add_circle_outline, size: 25),
                  title: const Text(
                    "Link to your hardware",
                    style: TextStyle(fontSize: 24),
                  ),
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const DeviceLinkPage()),
                    ).then((_) => _loadSession());
                  },
                ),
                ListTile(
                  leading: const Icon(Icons.analytics_outlined, size: 25),
                  title: const Text(
                    "Session Logs",
                    style: TextStyle(fontSize: 24),
                  ),
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const SessionLogPage()),
                    );
                  },
                ),
                ListTile(
                  leading: const Icon(Icons.logout, size: 25),
                  title: const Text("Log out", style: TextStyle(fontSize: 24)),
                  onTap: () => _logout(context),
                ),
                ListTile(
                  leading: const Icon(Icons.contact_page, size: 25),
                  title: const Text(
                    "Contact support",
                    style: TextStyle(fontSize: 24),
                  ),
                  onTap: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text("Support page coming soon!"),
                      ),
                    );
                  },
                ),
              ],
            ),
            Padding(
              padding: const EdgeInsets.only(bottom: 32),
              child: Text(
                _username != null ? "Welcome, $_username!" : "Welcome!",
                style: const TextStyle(fontSize: 30, color: Colors.blueGrey),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
