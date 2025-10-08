import 'package:flutter/material.dart';
import 'package:idas_app/pages/settings_page.dart';
import 'package:idas_app/pages/weekly_monthly_reports_page.dart';
import 'package:idas_app/pages/daily_report_event_page.dart';
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
    const DailyReportAndEvent(),
    const WeeklyMonthlyReports(),
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
          "iDAS: Driver Alert Monitoring System",
          style: TextStyle(
            fontSize: 21,
            color: Colors.white,
          ),
        ),
      ),
      body: _pages[_selectedIndex],
    );
  }
}
