import 'package:flutter/material.dart';

class DriverState {
  final String timestamp;
  final String input;
  final String level;
  final String message;
  final bool buzzer;
  final String driverState;
  final String sourcePath;
  final String spokenText;
  final String recommendedAction;

  const DriverState({
    required this.timestamp,
    required this.input,
    required this.level,
    required this.message,
    required this.buzzer,
    required this.driverState,
    required this.sourcePath,
    required this.spokenText,
    required this.recommendedAction,
  });

  factory DriverState.fromJson(Map<String, dynamic> json) {
    final message = (json['message'] ?? '').toString();
    final input = (json['input'] ?? '').toString();
    final level = (json['level'] ?? '').toString();
    final spoken = (json['spoken_text'] ?? json['speech'] ?? json['tts'] ?? '').toString();
    return DriverState(
      timestamp: (json['timestamp'] ?? '').toString(),
      input: input,
      level: level,
      message: message,
      buzzer: json['buzzer'] == true || (json['buzzer'] ?? '').toString().toLowerCase() == 'true',
      driverState: (json['driver_state'] ?? json['driverState'] ?? _deriveDriverState(input, message, level)).toString(),
      sourcePath: (json['source_path'] ?? '').toString(),
      spokenText: spoken.isNotEmpty ? spoken : _deriveSpeech(message, level, input),
      recommendedAction: (json['recommended_action'] ?? _deriveAction(message, level, input)).toString(),
    );
  }

  static String _deriveDriverState(String input, String message, String level) {
    final text = '$input $message $level'.toLowerCase();
    if (text.contains('phone')) return 'Distracted';
    if (text.contains('drows') || text.contains('sleep') || text.contains('eyes closed') || text.contains('yawn')) return 'Drowsy';
    if (text.contains('panic') || text.contains('distress') || text.contains('calm')) return 'Distressed';
    if (text.contains('attentive') || text.contains('focused') || text.contains('normal')) return 'Focused';
    return 'Monitoring';
  }

  static String _deriveSpeech(String message, String level, String input) {
    final text = '$message $input'.toLowerCase();
    if (text.contains('sleep') || text.contains('drows') || text.contains('eyes closed')) return 'Wake up';
    if (text.contains('phone') || text.contains('distract')) return 'Focus on the road';
    if (text.contains('panic') || text.contains('distress') || text.contains('erratic')) return 'Stay calm';
    if (level.toUpperCase() == 'INFO') return 'You are safe';
    return message.isNotEmpty ? message : 'Driver monitoring active';
  }

  static String _deriveAction(String message, String level, String input) {
    final text = '$message $input'.toLowerCase();
    if (text.contains('phone')) return 'Keep both eyes on the road and put the phone away.';
    if (text.contains('sleep') || text.contains('drows') || text.contains('eyes closed')) return 'Stop safely, get fresh air, and rest before continuing.';
    if (text.contains('panic') || text.contains('distress') || text.contains('erratic')) return 'Slow down, breathe, and regain control before continuing.';
    if (level.toUpperCase() == 'INFO') return 'Continue driving carefully.';
    return 'Monitor the driver and be ready to intervene.';
  }

  String get eventKey => '$timestamp|$level|$message|$input|$spokenText|$buzzer';

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
