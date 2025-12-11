import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:http/http.dart' as http;
import 'package:idas_app/pages/home_page.dart';
import 'package:idas_app/pages/sign_up_page.dart';
import '../widgets/config.dart';

class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final TextEditingController _usernameOrEmailController =
      TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  bool _isLoading = false;

  // ------ hive to save current user info ------ //
  Future<void> saveSession(String username, String userID, String hardwareID) async {
    final sessionBox = await Hive.openBox('session');
    await sessionBox.put('currentUser', username);
    await sessionBox.put('userID', userID);
    await sessionBox.put('hardwareID', hardwareID);
  }
  // -------------------------------------------- //

  // ------ push sign up button to go to sign up page ------ //
  void _signup() {
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (_) => const SignUpPage()),
    );
  }
  // ------------------------------------------------------- //

  // ------ login function ------ //
  void _login() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    final usernameOrEmail = _usernameOrEmailController.text.trim();
    final password = _passwordController.text.trim();

    try {
      final url = Uri.parse('$baseUrl/login-route');
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'username': usernameOrEmail, 'password': password}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final userID = data['user_id'];
        final username = data['username'];
        final hardwareID = data['device_id'];

        await saveSession(username, userID, hardwareID);

        if (!mounted) return;
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (_) => NavigationBarBottom(username: username, userID: userID),
          ),
        );
      } else if (response.statusCode == 404) {
        _showSnackBar("Login failed - ${response.statusCode}");
      }
    } catch (e) {
      debugPrint("Login error: $e");
      _showSnackBar("Network error. Please try again later.");
    } finally {
      setState(() => _isLoading = false);
    }
  }
  // ---------------------------- //

  // ------ helper function to display error messages ------ //
  void _showSnackBar(String msg) {
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(msg), backgroundColor: Colors.red));
  }
  // ------------------------------------------------------- //

  // ------ design ------ //
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Text(
                "ADAMS",
                style: TextStyle(fontSize: 45, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 4),
              const Text(
                "Advanced Driver Alertness Monitoring System",
                style: TextStyle(fontSize: 17),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),

              TextFormField(
                controller: _usernameOrEmailController,
                decoration: InputDecoration(
                  labelText: "Username or Email",
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                validator: (value) =>
                    value!.isEmpty ? "Please enter username" : null,
              ),
              const SizedBox(height: 8),

              TextFormField(
                controller: _passwordController,
                obscureText: true,
                decoration: InputDecoration(
                  labelText: "Password",
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                validator: (value) =>
                    value!.isEmpty ? "Please enter password" : null,
              ),
              const SizedBox(height: 24),

              SizedBox(
                height: 40,
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _login,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.lightBlue,
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: _isLoading
                      ? const SizedBox(
                          height: 40,
                          width: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.black,
                          ),
                        )
                      : const Text(
                          "Login",
                          style: TextStyle(fontSize: 16, color: Colors.black),
                        ),
                ),
              ),

              const SizedBox(height: 8),
              Row(
                children: const [
                  Expanded(child: Divider(thickness: 1, color: Colors.grey)),
                  Padding(
                    padding: EdgeInsets.symmetric(horizontal: 8),
                    child: Text(
                      "or",
                      style: TextStyle(color: Colors.grey, fontSize: 16),
                    ),
                  ),
                  Expanded(child: Divider(thickness: 1, color: Colors.grey)),
                ],
              ),
              const SizedBox(height: 8),

              SizedBox(
                width: double.infinity,
                height: 40,
                child: ElevatedButton(
                  onPressed: _signup,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.grey.shade300,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: Text(
                    "Sign Up",
                    style: TextStyle(fontSize: 16, color: Colors.grey.shade700),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
