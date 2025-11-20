import 'package:flutter/material.dart';

class BottomNav extends StatelessWidget{
  final int currentIndex;
  final Function(int) onTap;
  
  const BottomNav({
    super.key,
    required this.currentIndex,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return BottomNavigationBar(
      currentIndex: currentIndex,
      onTap: onTap,
      type: BottomNavigationBarType.fixed,
      selectedItemColor: Colors.blue.shade300,
      unselectedItemColor: Colors.grey,
      iconSize: 30,
      showSelectedLabels: true,
      items: [
        BottomNavigationBarItem(
          icon: Icon(Icons.home),
          label: "Home",
        ),
        BottomNavigationBarItem(
          icon: Icon(Icons.add_chart),
          label: "Reports",
        ),
        BottomNavigationBarItem(
          icon: Icon(Icons.access_time),
          label: "Weekly Activity",
        ),
        BottomNavigationBarItem(
          icon: Icon(Icons.settings),
          label: "Settings",
        ),
      ],
    );
  }
}
