import 'package:flutter/material.dart';
import 'package:idas_app/pages/real_time_status_page.dart';
import 'package:idas_app/pages/reports_page.dart';
import 'package:idas_app/pages/settings_page.dart';
import 'package:idas_app/pages/weekly_activity_page.dart';
import 'package:idas_app/widgets/bottom_nav.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  // bottom navigation bar
  int _selectedIndex = 0;
  final List<Widget> _pages = [
    const RealTimeStatus(),
    const ReportsPage(),
    const DailyReportAndEvent(),
    const SettingsPage(),
  ];

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
        backgroundColor: Colors.lightBlue,
        centerTitle: true,
        title: Text(
          "ADAMS",
          style: TextStyle(
            fontSize: 30,
            color: Colors.white,
          ),
        ),
      ),
      body: _pages[_selectedIndex],
    );
  }
}
