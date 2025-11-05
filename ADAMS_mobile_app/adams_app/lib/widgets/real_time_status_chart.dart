import 'package:flutter/material.dart';
import 'package:pie_chart/pie_chart.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'config.dart';
import 'dart:async';

// ---------------- updated 28/10 --------------- //
Future<Map<String, double>> loadReportData(String? username) async {
  final url = Uri.parse('$baseUrl/real-time-status?username=$username');
  final response = await http.get(url);

  if (response.statusCode == 200) {
    final Map<String, dynamic> rawData = json.decode(response.body);
    return rawData.map(
      (key, value) => MapEntry(key, (value as num).toDouble()),
    );
  } else {
    throw Exception('Failed to load data');
  }
}

class RealTimeStatusReport extends StatefulWidget {
  final String? username;
  const RealTimeStatusReport({Key? key, required this.username}) : super(key: key);

  @override
  State<RealTimeStatusReport> createState() => _RealTimeStatusReportState();
}

class _RealTimeStatusReportState extends State<RealTimeStatusReport> {
  Map<String, double>? dataMap;
  final colorList = <Color>[
    const Color(0xff5409DA),
    const Color(0xff4E71FF),
    const Color(0xff8DD8FF),
    const Color(0xffBBFBFF),
  ];
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _loadData();

    // refresh every few seconds
    _timer = Timer.periodic(const Duration(seconds: 3), (timer) {
      _loadData();
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _loadData() async {
    try {
      final newData = await loadReportData(widget.username!);
      if (!mounted) return;
      setState(() {
        dataMap = newData;
      });
    } catch (e) {
      debugPrint("Error loading chart data: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    final bool hasData = dataMap != null && dataMap!.isNotEmpty;

    return Center(
      child: SizedBox(
        width: 350,
        height: 350,
        child: PieChart(
          dataMap: hasData ? dataMap! : {"": 1.0},
          animationDuration: const Duration(milliseconds: 800),
          chartLegendSpacing: 32,
          chartRadius: 150, // keep fixed
          colorList: hasData
              ? colorList
              : [
                  Colors.transparent, // keeps ring visible but neutral
                ],
          baseChartColor: Colors.grey.shade300, // gray background ring
          chartType: ChartType.ring,
          ringStrokeWidth: 32,
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
          centerText: hasData ? "" : "No data yet",
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
