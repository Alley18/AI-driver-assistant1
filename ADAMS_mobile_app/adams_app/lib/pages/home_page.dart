import 'package:flutter/material.dart';
import 'package:idas_app/pages/real_time_status_page.dart';
import 'package:idas_app/pages/reports_page.dart';
import 'package:idas_app/pages/settings_page.dart';
import 'package:idas_app/pages/weekly_activity_page.dart';
import 'package:idas_app/widgets/bottom_nav.dart';

class HomePage extends StatefulWidget {
  final String? username;
  const HomePage({super.key, this.username});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  int _selectedIndex = 0;
  late List<Widget> _pages;

  @override
  void initState() {
    super.initState();
    // now include username in every page
    _pages = [
      RealTimeStatus(username: widget.username),
      ReportsPage(username: widget.username),
      DailyReportAndEvent(username: widget.username),
      SettingsPage(username: widget.username),
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
        backgroundColor: Colors.lightBlue,
        centerTitle: true,
        title: Text(
          "ADAMS",
          style: const TextStyle(fontSize: 30, color: Colors.white),
        ),
      ),
      body: _pages[_selectedIndex],
    );
  }
}

