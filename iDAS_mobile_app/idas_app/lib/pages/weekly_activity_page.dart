import 'package:flutter/material.dart';
import 'package:idas_app/widgets/event_log_list.dart';
import 'package:idas_app/widgets/weekly_activity.dart';

class DailyReportAndEvent extends StatefulWidget {
  const DailyReportAndEvent({super.key});

  @override
  State<DailyReportAndEvent> createState() => _DailyReportAndEventState();
}

class _DailyReportAndEventState extends State<DailyReportAndEvent> {
  late PageController _pageController;
  late int _currentPage;

  final List<String> _dayLabels = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
  ];

  @override
  void initState() {
    super.initState();
    _currentPage = DateTime.now().weekday - 1; // get current day
    _pageController = PageController(initialPage: _currentPage);
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          const SizedBox(height: 16),
          const Text(
            "Weekly Activity",
            style: TextStyle(fontSize: 40, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 24),

          Text(_dayLabels[_currentPage], style: const TextStyle(fontSize: 22)),
          const SizedBox(height: 8),

          // dots indicator
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(_dayLabels.length, (index) {
              return AnimatedContainer(
                duration: const Duration(milliseconds: 300),
                margin: const EdgeInsets.symmetric(horizontal: 4),
                width: _currentPage == index ? 12 : 8,
                height: _currentPage == index ? 12 : 8,
                decoration: BoxDecoration(
                  color: _currentPage == index ? Colors.lightBlue : Colors.grey,
                  shape: BoxShape.circle,
                ),
              );
            }),
          ),

          // pie chart + event log list container
          const SizedBox(height: 30),
          Expanded(
            child: PageView.builder(
              controller: _pageController,
              onPageChanged: (index) {
                setState(() {
                  _currentPage = index; // update day label and dot
                });
              },
              itemCount: _dayLabels.length,
              itemBuilder: (context, index) {
                // actual graph here
                final day = _dayLabels[index];
                return Column(
                  children: [
                    Expanded(
                      child: Padding(
                        padding: const EdgeInsets.only(top: 16, bottom: 16),
                        child: DailyReport(day: day),
                      ), // pie chart
                    ),
                    const SizedBox(height: 16),
                    Text(
                        "Event Logs",
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    const SizedBox(height: 8),
                    Expanded(child: EventLogList(day: day)), // event log list
                  ],
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
