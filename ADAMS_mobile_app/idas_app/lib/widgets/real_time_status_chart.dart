import 'package:flutter/material.dart';
import 'package:pie_chart/pie_chart.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'config.dart';
import 'dart:async';

Future<Map<String, double>> loadReportData() async {
  final url = Uri.parse('$baseUrl/real-time-status'); // Flask endpoint
  final response = await http.get(url);

  if (response.statusCode == 200) {
    // Expect backend to return a simple map like {"Active": 50, "Idle": 30, "Error": 20}
    final Map<String, dynamic> rawData = json.decode(response.body);
    return rawData.map((key, value) => MapEntry(key, (value as num).toDouble()));
  } else {
    throw Exception('Failed to load data');
  }
}

class RealTimeStatusReport extends StatefulWidget {
  const RealTimeStatusReport({Key? key}) : super(key: key);

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
      final newData = await loadReportData();
      if (!mounted) return;
      setState(() {
        dataMap = newData;
      });
      debugPrint("Refreshed chart data: $dataMap");
    } catch (e) {
      debugPrint("Error loading chart data: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    final chartData = (dataMap == null || dataMap!.isEmpty)
        ? <String, double>{"No data": 1}
        : dataMap!;

    return Center(
      child: PieChart(
        dataMap: chartData,
        animationDuration: const Duration(milliseconds: 800),
        chartLegendSpacing: 32,
        chartRadius: MediaQuery.of(context).size.width / 2.0,
        colorList: (dataMap == null || dataMap!.isEmpty)
            ? [Colors.grey.shade300]
            : colorList,
        chartType: ChartType.ring,
        ringStrokeWidth: 32,
        legendOptions: LegendOptions(
          showLegends: !(dataMap == null || dataMap!.isEmpty),
          legendPosition: LegendPosition.right,
          legendTextStyle: const TextStyle(fontWeight: FontWeight.bold),
        ),
        chartValuesOptions: ChartValuesOptions(
          showChartValueBackground: false,
          showChartValues: dataMap != null && dataMap!.isNotEmpty,
          showChartValuesInPercentage: true,
          decimalPlaces: 1,
        ),
        centerText: (dataMap == null || dataMap!.isEmpty) ? "No data." : "",
        centerTextStyle: TextStyle(
          fontSize: 16,
          fontWeight: FontWeight.bold,
          color: Colors.grey.shade700,
        ),
      ),
    );
  }
}
