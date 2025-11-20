import 'package:flutter/material.dart';
import 'package:hive/hive.dart';
import 'package:idas_app/widgets/reports_bar_chart.dart';
import 'package:idas_app/widgets/summary.dart';

class ReportsPage extends StatefulWidget {
  const ReportsPage({super.key}); // no userID needed

  @override
  State<ReportsPage> createState() => _ReportsPageState();
}

class _ReportsPageState extends State<ReportsPage> {
  String? userID;
  bool _isLoading = true;

  String _selectedCategory = "This Week";
  final List<String> _categories = ["This Week", "This Month"];

  @override
  void initState() {
    super.initState();
    _loadSession();
  }

  // ------ load current user info ------ //
  Future<void> _loadSession() async {
    final sessionBox = await Hive.openBox('session');
    setState(() {
      userID = sessionBox.get('userID');
      _isLoading = false;
    });
  }
  // ------------------------------------ //

  // ------ get current month name ------ //
  String getCurrentMonthName() {
    final now = DateTime.now();
    const monthNames = [
      "January", "February", "March", "April", "May", "June",
      "July", "August", "September", "October", "November", "December"
    ];
    return monthNames[now.month - 1];
  }
  // ------------------------------------ //

  // ------- design ------ //
  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text(
          "Reports",
          style: TextStyle(fontSize: 40, fontWeight: FontWeight.bold),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 8),

        // dropdown menu
        Center(
          child: DropdownButton<String>(
            value: _selectedCategory,
            items: _categories
                .map((cat) => DropdownMenuItem(value: cat, child: Text(cat)))
                .toList(),
            onChanged: (value) {
              if (value != null) {
                setState(() {
                  _selectedCategory = value;
                });
              }
            },
            borderRadius: BorderRadius.circular(12),
          ),
        ),

        const SizedBox(height: 8),

        // Current month title (only for "This Month")
        if (_selectedCategory == "This Month")
          Center(
            child: Text(
              getCurrentMonthName(),
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w500),
            ),
          ),

        const SizedBox(height: 16),

        // Chart
        ReportsBarChart(category: _selectedCategory),

        const SizedBox(height: 16),

        // Summary text
        AlertSummary(isWeekly: _selectedCategory == "This Week"),
      ],
    );
  }
}
