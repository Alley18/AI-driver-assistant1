import 'package:flutter/material.dart';

class AlertItem {
  final String id;
  final String timestamp;
  final String level;
  final String message;
  final String input;
  final bool buzzer;
  final String spokenText;
  final String recommendedAction;

  const AlertItem({
    required this.id,
    required this.timestamp,
    required this.level,
    required this.message,
    required this.input,
    required this.buzzer,
    required this.spokenText,
    required this.recommendedAction,
  });

  factory AlertItem.fromJson(Map<String, dynamic> json) {
    final message = (json['message'] ?? '').toString();
    final input = (json['input'] ?? '').toString();
    final level = (json['level'] ?? '').toString();
    final spokenText = (json['spoken_text'] ?? json['speech'] ?? json['tts'] ?? '').toString();
    return AlertItem(
      id: (json['id'] ?? '${json['timestamp'] ?? ''}|$message|$input').toString(),
      timestamp: (json['timestamp'] ?? '').toString(),
      level: level,
      message: message,
      input: input,
      buzzer: json['buzzer'] == true || (json['buzzer'] ?? '').toString().toLowerCase() == 'true',
      spokenText: spokenText.isNotEmpty ? spokenText : _deriveSpeech(message, level, input),
      recommendedAction: (json['recommended_action'] ?? _deriveAction(message, level, input)).toString(),
    );
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
    if (text.contains('sleep') || text.contains('drows') || text.contains('eyes closed')) return 'Take a break and do not continue while sleepy.';
    if (text.contains('panic') || text.contains('distress') || text.contains('erratic')) return 'Reduce speed, stay calm, and stabilize the vehicle.';
    if (level.toUpperCase() == 'INFO') return 'Continue monitoring normally.';
    return 'Follow the assistant guidance immediately.';
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
