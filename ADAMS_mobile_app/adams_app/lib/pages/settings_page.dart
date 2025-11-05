import 'package:flutter/material.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:idas_app/pages/login_page.dart';

class SettingsPage extends StatefulWidget {
  final String? username;
  const SettingsPage({super.key, this.username});

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  String? username;

  @override
  void initState() {
    super.initState();
    _loadUser(); // load username from Hive
  }

  Future<void> _loadUser() async {
    final sessionBox = await Hive.openBox('session');
    setState(() {
      username = sessionBox.get('currentUser');
    });
  }

  Future<void> _logout(BuildContext context) async {
    final sessionBox = await Hive.openBox('session');
    await sessionBox.delete('currentUser');

    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (_) => const LoginPage()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.spaceBetween, // pushes bottom text down
          children: [
            Column(
              children: [
                ListTile(
                  leading: const Icon(Icons.logout, size: 25),
                  title: const Text("Log out", style: TextStyle(fontSize: 24)),
                  onTap: () => _logout(context),
                ),
                ListTile(
                  leading: const Icon(Icons.contact_page, size: 25),
                  title: const Text("Contact support", style: TextStyle(fontSize: 24)),
                  onTap: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text("Support page coming soon!")),
                    );
                  },
                ),
              ],
            ),
            // bottom welcome message
            Padding(
              padding: const EdgeInsets.only(bottom: 32),
              child: Text(
                username != null
                    ? "Welcome, $username!"
                    : "Welcome!",
                style: const TextStyle(
                  fontSize: 30,
                  color: Colors.blueGrey,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
