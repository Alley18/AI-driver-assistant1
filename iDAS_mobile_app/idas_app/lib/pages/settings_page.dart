import 'package:flutter/material.dart';

class SettingsPage extends StatelessWidget {
  // not dynamic
  const SettingsPage({super.key});

  void _logout(BuildContext context) {
    Navigator.pushReplacementNamed(context, '/login');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            ListTile(
              leading: const Icon(Icons.logout, size:25),
              title: const Text("Log out", style: TextStyle(fontSize: 24)),
              onTap: () => _logout(context),
            ),
            ListTile(
              leading: const Icon(Icons.contact_page, size:25),
              title: const Text("Contact support", style: TextStyle(fontSize: 24)),
              onTap: () => _logout(context),
            ),
          ],
        ),
      ),
    );
  }
}
