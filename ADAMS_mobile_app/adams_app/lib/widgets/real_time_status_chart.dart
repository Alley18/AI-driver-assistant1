import 'package:flutter/material.dart';
import 'package:pie_chart/pie_chart.dart';
import 'package:hive/hive.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'config.dart';
import 'dart:async';

class RealTimeStatusReport extends StatefulWidget {
  const RealTimeStatusReport({Key? key}) : super(key: key);

  @override
  State<RealTimeStatusReport> createState() => _RealTimeStatusReportState();
}

class _RealTimeStatusReportState extends State<RealTimeStatusReport> {
  Map<String, double>? dataMap;
  final colorList = <Color>[
    const Color.fromARGB(255, 49, 1, 131),
    const Color(0xff5409DA),
    const Color(0xff4E71FF),
    const Color(0xff8DD8FF),
    const Color(0xffBBFBFF),
  ];
  Timer? _timer;
  String? _userID;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();

    _timer = Timer.periodic(const Duration(seconds: 3), (_) {
      _loadData();
    });
  }

  // ------ get user-specific info and convert to pie chart values ------ //
  Future<Map<String, double>> loadReportData(String? userID) async {
    if (userID == null) return {};
    final url = Uri.parse('$baseUrl/real-time-status?userID=$userID');
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

  Future<void> _loadData() async {
    try {
      final sessionBox = await Hive.openBox('session');
      _userID = sessionBox.get('userID');

      final newData = await loadReportData(_userID);

      if (!mounted) return;
      setState(() {
        dataMap = newData;
        _isLoading = false;
      });
    } catch (e) {
      debugPrint("Error loading chart data: $e");
      if (!mounted) return;
      setState(() {
        _isLoading = false;
      });
    }
  }
  // -------------------------------------------------------------------- //

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  // ------ design ------ //
  @override
  Widget build(BuildContext context) {
    if (_isLoading) return const Center(child: CircularProgressIndicator());

    final bool hasData = dataMap != null && dataMap!.isNotEmpty;

    return Center(
      child: SizedBox(
        width: MediaQuery.of(context).size.width * 0.9,
        height: 500,
        child: PieChart(
          dataMap: hasData ? dataMap! : {"": 1.0},
          animationDuration: const Duration(milliseconds: 800),
          chartLegendSpacing: 32,
          chartRadius: 150,
          colorList: hasData ? colorList : [Colors.transparent],
          baseChartColor: Colors.grey.shade300,
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
