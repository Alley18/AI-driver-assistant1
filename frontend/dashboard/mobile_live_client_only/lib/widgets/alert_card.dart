import 'package:flutter/material.dart';

import '../models/alert_item.dart';

class AlertCard extends StatelessWidget {
  final AlertItem item;
  const AlertCard({super.key, required this.item});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF111827),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: item.color.withOpacity(0.35)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          CircleAvatar(backgroundColor: item.color.withOpacity(0.16), child: Icon(Icons.record_voice_over, color: item.color)),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(item.spokenText, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 17, color: item.color)),
                const SizedBox(height: 6),
                Text(item.message, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15)),
                const SizedBox(height: 6),
                Text(item.recommendedAction, style: const TextStyle(color: Colors.white70)),
                const SizedBox(height: 10),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    _chip(item.level, item.color),
                    _chip(item.timestamp, Colors.lightBlueAccent),
                    _chip(item.input, Colors.purpleAccent),
                    _chip(item.buzzer ? 'Buzzer ON' : 'Buzzer OFF', item.buzzer ? Colors.orangeAccent : Colors.greenAccent),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _chip(String text, Color color) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        decoration: BoxDecoration(color: color.withOpacity(0.16), borderRadius: BorderRadius.circular(20)),
        child: Text(text, style: TextStyle(color: color, fontWeight: FontWeight.w600)),
      );
}
