import 'package:flutter/material.dart';
import 'package:idas_app/pages/home_page.dart';
import 'pages/login_page.dart';
import 'package:hive_flutter/hive_flutter.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Hive.initFlutter();

  final sessionBox = await Hive.openBox('session');
  final currentUser = sessionBox.get('currentUser');

  runApp(MyApp(initialUser: currentUser));
}

class MyApp extends StatelessWidget {
  final String? initialUser;
  const MyApp({super.key, this.initialUser});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ADAMS Demo',
      home: initialUser == null
          ? const LoginPage()
          : NavigationBarBottom(username: initialUser!),
      theme: ThemeData(
        fontFamily: 'AlanSans',
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.white),
      ),
    );
  }
}
