import 'package:flutter/material.dart';
import 'package:pie_chart/pie_chart.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:hive_flutter/hive_flutter.dart';
import 'config.dart';
import 'dart:async';

Future<Map<String, Map<String, double>>> fetchWeeklyActivityData(String userID) async {
  final url = Uri.parse('$baseUrl/weekly-activity?userID=$userID');
  final response = await http.get(url);

  if (response.statusCode == 200) {
    final Map<String, dynamic> rawData = json.decode(response.body);
    return rawData.map((day, values) {
      final map = Map<String, double>.fromEntries(
        (values as Map<String, dynamic>).entries.map(
          (e) => MapEntry(e.key, (e.value as num).toDouble()),
        ),
      );
      return MapEntry(day, map);
    });
  } else {
    throw Exception('Failed to load weekly activity data');
  }
}

class WeeklyActivity extends StatefulWidget {
  final String day;
  final String? userID; // optional, fetched from Hive if null
  const WeeklyActivity({Key? key, required this.day, this.userID}) : super(key: key);

  @override
  State<WeeklyActivity> createState() => _WeeklyActivityState();
}

class _WeeklyActivityState extends State<WeeklyActivity> {
  Map<String, double>? dataMap;
  final List<Color> colorList = [
    const Color(0xff5409DA),
    const Color(0xff4E71FF),
    const Color(0xff8DD8FF),
    const Color(0xffBBFBFF),
  ];
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _loadDataForDay(widget.day);

    // Refresh every 3 seconds
    _timer = Timer.periodic(const Duration(seconds: 3), (_) {
      _loadDataForDay(widget.day);
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _loadDataForDay(String day) async {
    try {
      final sessionBox = await Hive.openBox('session');
      final userID = widget.userID ?? sessionBox.get('userID');
      if (userID == null) return;

      final allData = await fetchWeeklyActivityData(userID);
      if (!mounted) return;

      setState(() {
        dataMap = allData[day];
      });

      debugPrint("WeeklyActivity refreshed for $day at ${DateTime.now()}");
      debugPrint("Data: $dataMap");
    } catch (e) {
      debugPrint("Error fetching weekly activity: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    final bool hasData = dataMap != null && dataMap!.isNotEmpty;
    final chartData = hasData ? dataMap! : {"No data yet": 1.0};
    final chartColors = hasData ? colorList : [Colors.grey.shade300];

    return Center(
      child: SizedBox(
        width: 350,
        height: 350,
        child: PieChart(
          dataMap: chartData,
          animationDuration: const Duration(milliseconds: 800),
          chartLegendSpacing: 32,
          chartRadius: 150,
          colorList: chartColors,
          chartType: ChartType.ring,
          ringStrokeWidth: 32,
          baseChartColor: Colors.grey.shade300,
          legendOptions: LegendOptions(
            showLegends: hasData,
            legendPosition: LegendPosition.bottom,
            showLegendsInRow: true,
            legendTextStyle: const TextStyle(fontWeight: FontWeight.bold),
          ),
          chartValuesOptions: ChartValuesOptions(
            showChartValues: hasData,
            showChartValuesInPercentage: true,
            showChartValueBackground: false,
          ),
          centerText: hasData ? "" : "Start logging today!",
          centerTextStyle: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: Colors.grey.shade700,
          ),
        ),
      ),
    );
  }
}
