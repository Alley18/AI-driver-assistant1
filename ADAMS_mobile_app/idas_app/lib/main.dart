import 'package:flutter/material.dart';
import 'package:idas_app/pages/home_page.dart';
import 'pages/login_page.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ADAMS Demo',
      initialRoute: '/login',
      routes: {
        '/login': (context) => const LoginPage(),
        '/homepage': (context) => const HomePage(),
      },
      theme: ThemeData(
        fontFamily: 'AlanSans',
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.white),
      ),
    );
  }
}