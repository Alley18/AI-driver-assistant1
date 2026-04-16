import 'package:flutter/material.dart';

class AlertItem {
  final String timestamp;
  final String level;
  final String message;
  final String input;
  final bool buzzer;

  const AlertItem({
    required this.timestamp,
    required this.level,
    required this.message,
    required this.input,
    required this.buzzer,
  });

  factory AlertItem.fromJson(Map<String, dynamic> json) {
    return AlertItem(
      timestamp: (json['timestamp'] ?? '').toString(),
      level: (json['level'] ?? '').toString(),
      message: (json['message'] ?? '').toString(),
      input: (json['input'] ?? '').toString(),
      buzzer: json['buzzer'] == true || (json['buzzer'] ?? '').toString().toLowerCase() == 'true',
    );
  }

  Color get color {
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
