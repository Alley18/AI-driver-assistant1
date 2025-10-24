import 'dart:async';
import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'config.dart';

class WeeklyAlertsChart extends StatefulWidget {
  final List<String> timeLabels;

  const WeeklyAlertsChart({super.key, required this.timeLabels});

  @override
  State<WeeklyAlertsChart> createState() => _WeeklyAlertChartState();
}

class _WeeklyAlertChartState extends State<WeeklyAlertsChart>
    with SingleTickerProviderStateMixin {
  // for animation to work - updates animation value continuously as time passes
  List<Color> barColors = [Colors.lightBlue, Colors.blue];
  List<int> _values = [];
  late List<String> _labels;
  late AnimationController _animationController;
  late Animation<double> _animation;
  bool _isLoading = true;
  Timer? _timer;

  // get data using flask api
  Future<void> _loadStoredData() async {
    final url = Uri.parse('$baseUrl/weekly-data'); // flask
    final response = await http.get(url);

    if (response.statusCode == 200) {
      final Map<String, dynamic> jsonData = json.decode(response.body);
      if (!mounted) return;
      setState(() {
        _values = jsonData.values.map((v) => v as int).toList();
        _labels = jsonData.keys.toList();
        _isLoading = false;
      });
    } else {
      print('Failed to load data');
    }
  }

  @override
  void initState() {
    super.initState();

    _animationController = AnimationController(
      vsync: this, // needs SingleTickerProviderStateMixin
      duration: const Duration(milliseconds: 800),
    );

    _animation = CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeOut,
    );

    // load data from flask
    _loadStoredData().then((_) {
      _animationController.forward(); // start animation
    });

    _timer = Timer.periodic(const Duration(seconds: 3), (timer){
      _loadStoredData();
    });
  }

  @override
  void dispose() {
    _animationController.dispose();
    _timer?.cancel();
    super.dispose();
  } // prevent memory leak

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator(color: Colors.blue));
    }
    if (_values.isEmpty) {
      return const Center(child: Text("No data available."));
    }
    final maxY = (_values.reduce((a, b) => a > b ? a : b) + 1).toDouble();
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      color: Colors.transparent,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Center(
            child: Text(
              "Weekly",
              style: TextStyle(fontSize: 40, fontWeight: FontWeight.bold),
            ),
          ),
          const SizedBox(height: 24),
          SizedBox(
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
                      return BarChartGroupData(
                        x: i,
                        barRods: [
                          BarChartRodData(
                            toY: _values[i] * _animation.value,
                            width: 40,
                            gradient: LinearGradient(colors: barColors),
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
          ),
        ],
      ),
    );
  }
}
