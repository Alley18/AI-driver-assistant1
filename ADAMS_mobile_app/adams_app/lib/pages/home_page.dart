import 'package:flutter/material.dart';
import 'package:idas_app/pages/real_time_status_page.dart';
import 'package:idas_app/pages/reports_page.dart';
import 'package:idas_app/pages/settings_page.dart';
import 'package:idas_app/pages/weekly_activity_page.dart';
import 'package:idas_app/widgets/bottom_nav.dart';

class HomePage extends StatefulWidget {
  final String username;
  final String? userID;
  const HomePage({super.key, required this.username, this.userID});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  int _selectedIndex = 0;
  late List<Widget> _pages;

  @override
  void initState() {
    super.initState();
    _pages = [
      RealTimeStatus(),
      ReportsPage(),
      WeeklyActivityPage(),
      SettingsPage()
    ];
  }

  void _onNavTapped(int index) {
    setState(() {
      _selectedIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      bottomNavigationBar: BottomNav(
        currentIndex: _selectedIndex,
        onTap: _onNavTapped,
      ),
      appBar: AppBar(
        backgroundColor: Colors.blue.shade300,
        centerTitle: true,
        automaticallyImplyLeading: false,
        title: Text(
          "ADAMS",
          style: const TextStyle(fontSize: 30, color: Colors.white),
        ),
      ),
      body: _pages[_selectedIndex],
    );
  }
}

