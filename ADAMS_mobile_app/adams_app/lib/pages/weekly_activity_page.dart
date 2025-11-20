import 'package:flutter/material.dart';
import 'package:hive/hive.dart';
import 'package:idas_app/widgets/event_log_list.dart';
import 'package:idas_app/widgets/weekly_activity.dart';

class WeeklyActivityPage extends StatefulWidget {
  const WeeklyActivityPage({super.key}); // no userID needed

  @override
  State<WeeklyActivityPage> createState() => _WeeklyActivityPageState();
}

class _WeeklyActivityPageState extends State<WeeklyActivityPage> {
  late PageController _pageController;
  late int _currentPage;
  String? _userID;
  bool _isLoading = true;

  // ------ labels for graph ------ //
  final List<String> _dayLabels = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
  ];
  // ------------------------------ //

  @override
  void initState() {
    super.initState();
    _currentPage = DateTime.now().weekday - 1;
    _pageController = PageController(initialPage: _currentPage);
    _loadSession();
  }

  // ------ load current user info ------ //
  Future<void> _loadSession() async {
    final sessionBox = await Hive.openBox('session');
    setState(() {
      _userID = sessionBox.get('userID');
      _isLoading = false;
    });
  }
  // ------------------------------------ //

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  // ------ design ------ //
  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          const SizedBox(height: 16),
          const Text(
            "Weekly Activity",
            style: TextStyle(fontSize: 40, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 16),

          Text(_dayLabels[_currentPage], style: const TextStyle(fontSize: 22)),
          const SizedBox(height: 8),

          // ------ dots indicator ------ //
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(_dayLabels.length, (index) {
              return AnimatedContainer(
                duration: const Duration(milliseconds: 300),
                margin: const EdgeInsets.symmetric(horizontal: 4),
                width: _currentPage == index ? 12 : 8,
                height: _currentPage == index ? 12 : 8,
                decoration: BoxDecoration(
                  color: _currentPage == index ? Colors.blue.shade300 : Colors.grey,
                  shape: BoxShape.circle,
                ),
              );
            }),
          ),
          // ---------------------------- //

          const SizedBox(height: 30),

          Expanded(
            child: PageView.builder(
              controller: _pageController,
              onPageChanged: (index) {
                setState(() {
                  _currentPage = index;
                });
              },
              itemCount: _dayLabels.length,
              itemBuilder: (context, index) {
                final day = _dayLabels[index];
                return Column(
                  children: [
                    Expanded(
                      flex: 2,
                      child: Padding(
                        padding: const EdgeInsets.only(top: 16, bottom: 16),
                        child: WeeklyActivity(
                          day: day,
                          userID: _userID,
                        ),
                      ),
                    ),
                    const Text(
                      "Event Logs",
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Expanded(
                      flex: 1,
                      child: EventLogList(day: day),
                    ),
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
