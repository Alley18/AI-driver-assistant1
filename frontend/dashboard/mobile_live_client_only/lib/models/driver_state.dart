import 'package:flutter/material.dart';

class DriverState {
  final String timestamp;
  final String input;
  final String level;
  final String message;
  final bool buzzer;
  final String driverState;
  final String sourcePath;

  const DriverState({
    required this.timestamp,
    required this.input,
    required this.level,
    required this.message,
    required this.buzzer,
    required this.driverState,
    required this.sourcePath,
  });

  factory DriverState.fromJson(Map<String, dynamic> json) {
    return DriverState(
      timestamp: (json['timestamp'] ?? '').toString(),
      input: (json['input'] ?? '').toString(),
      level: (json['level'] ?? '').toString(),
      message: (json['message'] ?? '').toString(),
      buzzer: json['buzzer'] == true || (json['buzzer'] ?? '').toString().toLowerCase() == 'true',
      driverState: (json['driver_state'] ?? json['driverState'] ?? '').toString(),
      sourcePath: (json['source_path'] ?? '').toString(),
    );
  }

  Color get levelColor {
    switch (level.toUpperCase()) {
      case 'DANGER':
        return Colors.redAccent;
      case 'WARNING':
        return Colors.orangeAccent;
      case 'INFO':
        return Colors.greenAccent;
      default:
        return Colors.grey;
    }
  }
}
