import 'dart:async';
import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'config.dart';

class ReportsBarChart extends StatefulWidget {
  final String category; // from dropdown
  const ReportsBarChart({super.key, required this.category});

  @override
  State<ReportsBarChart> createState() => _ReportsBarChartState();
}

class _ReportsBarChartState extends State<ReportsBarChart>
    with SingleTickerProviderStateMixin {
  final Map<String, String> categoryEndpoint = {
    "This Week": "thisweek",
    "This Month": "thismonth",
  };

  List<Color> barColors = [Colors.lightBlue, Colors.blue];
  List<int> _values = [];
  late List<String> _labels;
  bool _isLoading = true;

  late AnimationController _animationController;
  late Animation<double> _animation;

  int getCurrentIndex() {
    final today = DateTime.now();

    if (widget.category == "This Week") {
      // Monday = 1, Sunday = 7
      return today.weekday - 1; // 0-based index for Mon-Sun
    } else {
      // For month, find which interval today falls into
      final day = today.day;
      for (int i = 0; i < _labels.length; i++) {
        final parts = _labels[i].split('-');
        final start = int.parse(parts[0]);
        final end = int.parse(parts[1]);
        if (day >= start && day <= end) {
          return i;
        }
      }
    }
    return -1; // default if not found
  }

  @override
  void initState() {
    super.initState();

    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );

    _animation = CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeOut,
    );

    _loadStoredData();
  }

  @override
  void didUpdateWidget(covariant ReportsBarChart oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.category != widget.category) {
      _loadStoredData(); // reload chart if dropdown changes
    }
  }

  List<String> getThisWeekLabels() {
    final today = DateTime.now();
    // Monday as start of week
    final startOfWeek = today.subtract(Duration(days: today.weekday - 1));
    return List.generate(7, (i) {
      final date = startOfWeek.add(Duration(days: i));
      return ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][i];
    });
  }

  List<String> getThisMonthWeekLabels() {
    final today = DateTime.now();
    final daysInMonth = DateTime(today.year, today.month + 1, 0).day;

    // Define 4 or 5 intervals
    final intervals = <String>[];
    int start = 1;
    while (start <= daysInMonth) {
      int end = (start + 6 > daysInMonth) ? daysInMonth : start + 6;
      intervals.add("$start-$end");
      start = end + 1;
    }
    return intervals;
  }

  List<int> aggregateMonthlyData(Map<String, dynamic> jsonData) {
    final today = DateTime.now();
    final daysInMonth = DateTime(today.year, today.month + 1, 0).day;

    final intervals = getThisMonthWeekLabels();
    final aggregatedValues = <int>[];

    for (var interval in intervals) {
      final parts = interval.split('-');
      int start = int.parse(parts[0]);
      int end = int.parse(parts[1]);

      int sum = 0;
      for (int day = start; day <= end; day++) {
        final key =
            "${day.toString().padLeft(2, '0')}/${today.month.toString().padLeft(2, '0')}";
        sum += jsonData[key] as int? ?? 0;
      }
      aggregatedValues.add(sum);
    }

    return aggregatedValues;
  }

  Future<void> _loadStoredData() async {
    final endpoint = categoryEndpoint[widget.category];
    if (endpoint == null) {
      print("Category '${widget.category}' not found");
      return;
    }

    final url = Uri.parse('$baseUrl/$endpoint');

    try {
      final response = await http.get(url);
      if (response.statusCode == 200) {
        final Map<String, dynamic> jsonData = json.decode(response.body);

        List<String> labels;
        List<int> values;

        if (widget.category == "This Week") {
          labels = getThisWeekLabels();
          values = labels.map((label) => jsonData[label] as int? ?? 0).toList();
        } else {
          labels = getThisMonthWeekLabels();
          values = aggregateMonthlyData(jsonData);
        }

        if (!mounted) return;
        setState(() {
          _labels = labels;
          _values = values;
          _isLoading = false;
        });

        _animationController.forward(from: 0);
      } else {
        print('Failed to load data: ${response.statusCode}');
      }
    } catch (e) {
      print('Error loading data: $e');
    }
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator(color: Colors.blue));
    }
    if (_values.isEmpty) {
      return const Center(child: Text("No data available."));
    }

    final maxY = (_values.reduce((a, b) => a > b ? a : b) + 1).toDouble();
    final currentIndex = getCurrentIndex();
    final maxValue = (_values.reduce((a, b) => a > b ? a : b) + 1).toDouble();
    return SizedBox(
      height: MediaQuery.of(context).size.height * 0.35,
      child: AnimatedBuilder(
        animation: _animation,
        builder: (context, child) {
          return BarChart(
            BarChartData(
              maxY: maxY,
              gridData: FlGridData(show: false),
              titlesData: FlTitlesData(
                leftTitles: AxisTitles(
                  sideTitles: SideTitles(showTitles: false),
                ),
                bottomTitles: AxisTitles(
                  sideTitles: SideTitles(showTitles: false),
                ),
                rightTitles: AxisTitles(
                  sideTitles: SideTitles(showTitles: false),
                ),
                topTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    reservedSize: 30,
                    getTitlesWidget: (value, _) {
                      int index = value.toInt();
                      if (index >= 0 && index < _labels.length) {
                        return Text(
                          _labels[index],
                          textAlign: TextAlign.center,
                          style: const TextStyle(fontSize: 16),
                        );
                      }
                      return const Text("");
                    },
                  ),
                ),
              ),
              borderData: FlBorderData(show: false),

              barGroups: List.generate(_values.length, (i) {
                double barHeight;
                Color barStartColor;
                Color barEndColor;

                if (_values[i] == 0) {
                  // No data: full height, grey
                  barHeight = maxValue;
                  barStartColor = Colors.grey.shade300;
                  barEndColor = Colors.grey.shade300;
                } else if (i == currentIndex) {
                  // Current day/interval
                  barHeight = _values[i] * _animation.value;
                  barStartColor = Colors.orange;
                  barEndColor = Colors.deepOrange;
                } else {
                  // Past days/intervals with data
                  barHeight = _values[i] * _animation.value;
                  barStartColor = Colors.lightBlue;
                  barEndColor = Colors.blue;
                }

                return BarChartGroupData(
                  x: i,
                  barRods: [
                    BarChartRodData(
                      toY: barHeight,
                      width: 40,
                      gradient: LinearGradient(
                        colors: [barStartColor, barEndColor],
                      ),
                      borderRadius: const BorderRadius.only(
                        topLeft: Radius.circular(3),
                        topRight: Radius.circular(3),
                      ),
                    ),
                  ],
                );
              }),
            ),
          );
        },
      ),
    );
  }
}
