import 'package:flutter/material.dart';
import 'package:pie_chart/pie_chart.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'config.dart';
import 'dart:async';

Future<Map<String, Map<String, double>>> loadReportData(String? username) async {
  final url = Uri.parse('$baseUrl/weekly-activity?username=$username'); // flask
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
    throw Exception('Failed to load data');
  }
}

enum LegendShape { circle, rectangle }

class DailyReport extends StatefulWidget {
  final String day;
  final String? username;
  const DailyReport({Key? key, required this.day, required this.username}) : super(key: key);

  @override
  State<DailyReport> createState() => _DailyReportState();
}

class _DailyReportState extends State<DailyReport> {
  Map<String, double>? dataMap;
  final colorList = <Color>[
    const Color(0xff5409DA),
    const Color(0xff4E71FF),
    const Color(0xff8DD8FF),
    const Color(0xffBBFBFF),
  ];
  Timer? _timer; // time variable
  ChartType _chartType = ChartType.ring; // default chart type

  @override
  void initState() {
    super.initState();
    _loadDataforToday(widget.day);

    _timer = Timer.periodic(const Duration(seconds: 3), (timer) {
      _loadDataforToday(widget.day); // refresh
    });
  }

  @override
  void dispose() {
    _timer?.cancel(); // clean up timer when page closes
    super.dispose();
  }

  Future<void> _loadDataforToday(String day) async {
    try {
      final allData = await loadReportData(widget.username!);
      if (!mounted) return;
      setState(() {
        dataMap = allData[day];
      });

      debugPrint("Refreshed daily data at ${DateTime.now()} for day: $day");
      debugPrint("Data: $dataMap");
    } catch (e) {
      debugPrint("Error fetching daily data: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    final bool hasData = dataMap != null && dataMap!.isNotEmpty;
    final chartData = hasData ? dataMap! : {"": 1};

    return Center( // ---------------- updated 28/10 --------------- //
      child: SizedBox(
        width: 350, // increase width
        height: 350, // increase height
        child: PieChart(
          dataMap: hasData ? dataMap! : {"No data yet.": 1},
          animationDuration: const Duration(milliseconds: 800),
          chartLegendSpacing: 32,
          chartRadius: 150, // keep fixed
          colorList: hasData
              ? colorList
              : [
                  Colors.transparent,
                ], 
          chartType: ChartType.ring,
          ringStrokeWidth: 32,
          baseChartColor:
              Colors.grey.shade300, 
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
          centerText: hasData ? "" : "Start logging",
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
