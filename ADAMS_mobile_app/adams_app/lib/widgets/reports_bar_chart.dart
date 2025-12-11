import 'dart:async';
import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:hive/hive.dart';
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

  List<int> _values = [];
  late List<String> _labels;
  bool _isLoading = true;
  String? _userID;

  late AnimationController _animationController;
  late Animation<double> _animation;

  int getCurrentIndex() {
    final today = DateTime.now();
    if (widget.category == "This Week") {
      return today.weekday - 1;
    } else {
      final day = today.day;
      for (int i = 0; i < _labels.length; i++) {
        final parts = _labels[i].split('-');
        final start = int.parse(parts[0]);
        final end = int.parse(parts[1]);
        if (day >= start && day <= end) return i;
      }
    }
    return -1;
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

    _loadSessionAndData();
  }

  // ------ load current user info ------ //
  Future<void> _loadSessionAndData() async {
    final sessionBox = await Hive.openBox('session');
    _userID = sessionBox.get('userID');
    await _loadStoredData();
    if (!mounted) return;
    setState(() {
      _isLoading = false;
    });
  }
  // ------------------------------------ //

  // ------ load data from backend to insert into graphs ------ //
  Future<void> _loadStoredData() async {
    final endpoint = categoryEndpoint[widget.category];
    if (endpoint == null) return;

    final url = Uri.parse(
      '$baseUrl/$endpoint?userID=$_userID&category=${widget.category}',
    );

    try {
      final response = await http.get(url).timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        final Map<String, dynamic> jsonData = json.decode(response.body);

        List<String> labels = [];
        List<int> values = [];

        if (widget.category == "This Week") {
          labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
          values = labels.map((label) => jsonData[label] as int? ?? 0).toList();
        } else {
          final today = DateTime.now();
          final daysInMonth = DateTime(today.year, today.month + 1, 0).day;

          labels = [];
          final aggregatedValues = <int>[];
          int start = 1;
          while (start <= daysInMonth) {
            int end = (start + 6 > daysInMonth) ? daysInMonth : start + 6;
            labels.add("$start-$end");

            int sum = 0;
            for (int day = start; day <= end; day++) {
              final key =
                  "${day.toString().padLeft(2, '0')}/${today.month.toString().padLeft(2, '0')}";
              sum += jsonData[key] as int? ?? 0;
            }
            aggregatedValues.add(sum);
            start = end + 1;
          }
          values = aggregatedValues;
        }

        if (!mounted) return;
        setState(() {
          _labels = labels;
          _values = values;
        });

        _animationController.forward(from: 0);
      } else {
        _setEmptyData();
      }
    } catch (e) {
      _setEmptyData();
    }
  }
  // ---------------------------------------------------------- //

  // ------ create empty graph when no data ------ //
  void _setEmptyData() {
    if (!mounted) return;
    setState(() {
      _labels = widget.category == "This Week"
          ? ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
          : _generateMonthWeekLabels();
      _values = List.filled(_labels.length, 0);
    });
  }
  // --------------------------------------------- //

  // ------ creat labels for month (week intervals) ------ //
  List<String> _generateMonthWeekLabels() {
    final today = DateTime.now();
    final daysInMonth = DateTime(today.year, today.month + 1, 0).day;
    final intervals = <String>[];
    int start = 1;
    while (start <= daysInMonth) {
      int end = (start + 6 > daysInMonth) ? daysInMonth : start + 6;
      intervals.add("$start-$end");
      start = end + 1;
    }
    return intervals;
  }
  // ----------------------------------------------------- //

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  // ------ design ------ //
  @override
  Widget build(BuildContext context) {
    if (_isLoading) return const Center(child: CircularProgressIndicator());

    if (_values.isEmpty) {
      _values = List.filled(_labels.length, 0);
    }

    final maxDataValue = _values.reduce((a, b) => a > b ? a : b);
    final maxY = (maxDataValue > 0 ? maxDataValue * 1.2 : 1)
        .toDouble(); // 20% padding
    final currentIndex = getCurrentIndex();

    return SizedBox(
      height: MediaQuery.of(context).size.height * 0.35,
      child: AnimatedBuilder(
        animation: _animation,
        builder: (context, child) {
          return BarChart(
            BarChartData(
              maxY: maxY,
              gridData: FlGridData(show: false),
              borderData: FlBorderData(show: false),
              titlesData: FlTitlesData(
                leftTitles: AxisTitles(
                  sideTitles: SideTitles(showTitles: false),
                ),
                rightTitles: AxisTitles(
                  sideTitles: SideTitles(showTitles: false),
                ),
                bottomTitles: AxisTitles(
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
              barGroups: List.generate(_values.length, (i) {
                double targetHeight = _values[i].toDouble();
                double barHeight = targetHeight == 0
                    ? maxY
                    : targetHeight * _animation.value;

                Color barStartColor;
                Color barEndColor;

                if (_values[i] == 0) {
                  barStartColor = Colors.grey.shade300;
                  barEndColor = Colors.grey.shade300;
                } else if (i == currentIndex) {
                  barStartColor = Colors.orange;
                  barEndColor = Colors.deepOrange;
                } else {
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
              // Add barTouchData here, outside the loop
              barTouchData: BarTouchData(
                enabled: true,
                touchTooltipData: BarTouchTooltipData(
                  getTooltipItem: (group, groupIndex, rod, rodIndex) {
                    // Disable tooltip for grey bars
                    if (_values[groupIndex] == 0) return null;

                    return BarTooltipItem(
                      '${_values[groupIndex]}',
                      const TextStyle(color: Colors.white),
                    );
                  },
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
