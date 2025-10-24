import 'package:flutter/material.dart';
import 'package:idas_app/widgets/summary.dart';
import '../widgets/weekly_report.dart';
import '../widgets/monthly_report.dart';

class WeeklyMonthlyReports extends StatefulWidget {
  const WeeklyMonthlyReports({super.key});

  @override
  State<WeeklyMonthlyReports> createState() => _WeeklyMonthlyReportsState();
}

class _WeeklyMonthlyReportsState extends State<WeeklyMonthlyReports> {
  final PageController _pageController = PageController();
  int _currentpage = 0;

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      children: [
        // graph
        SizedBox(
          height: 375, // reduce height to avoid overflow
          child: PageView(
            controller: _pageController,
            onPageChanged: (index) {
              setState(() {
                _currentpage = index;
              });
            },
            children: const [
              WeeklyAlertsChart(
                timeLabels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
              ),
              MonthlyAlertsChart(
                timeLabels: [
                  "Jan",
                  "Feb",
                  "Mar",
                  "Apr",
                  "May",
                  "Jun",
                  "Jul",
                  "Aug",
                  "Sep",
                  "Oct",
                  "Nov",
                  "Dec",
                ],
              ),
            ],
          ),
        ),

        const SizedBox(height: 8),

        // dots indicator
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: List.generate(2, (index) {
            return AnimatedContainer(
              duration: const Duration(milliseconds: 300),
              margin: const EdgeInsets.symmetric(horizontal: 4),
              width: _currentpage == index ? 12 : 8,
              height: _currentpage == index ? 12 : 8,
              decoration: BoxDecoration(
                color: _currentpage == index ? Colors.lightBlue : Colors.grey,
                shape: BoxShape.circle,
              ),
            );
          }),
        ),

        const SizedBox(height: 24),

        // Summary
        Text(
          "Summary",
          style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 8),
        AlertSummary(isWeekly: _currentpage == 0),
      ],
    );
  }
}
