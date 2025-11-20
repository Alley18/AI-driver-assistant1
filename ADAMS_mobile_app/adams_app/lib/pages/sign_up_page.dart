import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:http/http.dart' as http;
import 'package:idas_app/pages/login_page.dart';
import 'package:idas_app/pages/home_page.dart';
import '../widgets/config.dart';

class SignUpPage extends StatefulWidget {
  const SignUpPage({super.key});

  @override
  State<SignUpPage> createState() => _SignUpPageState();
}

class _SignUpPageState extends State<SignUpPage> {
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _usernameController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  final TextEditingController _confirmPasswordController = TextEditingController();

  final _formKey = GlobalKey<FormState>();
  bool _isLoading = false;

  // ------ save current user info from text field ------ //
  Future<void> saveSession(String username, String userID) async {
    final sessionBox = await Hive.openBox('session');
    await sessionBox.put('currentUser', username);
    await sessionBox.put('userID', userID);
  }
  // ---------------------------------------------------- //

  // ------ sign up function - send user info to db ------ //
  void _signup() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    final email = _emailController.text.trim();
    final username = _usernameController.text.trim();
    final password = _passwordController.text.trim();

    try {
      final url = Uri.parse('$baseUrl/signup-route');
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email': email, 'username': username, 'password': password}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final userID = data['user_id'];

        await saveSession(username, userID);

        if (!mounted) return;
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (_) => HomePage(username: username, userID: userID)),
        );
      } else if (response.statusCode == 409) {
        final data = jsonDecode(response.body);
        _showSnackBar(data['message'] ?? "User already exists.");
      } else {
        _showSnackBar("Signup failed: ${response.statusCode}");
      }
    } catch (e) {
      debugPrint("Error contacting backend: $e");
      _showSnackBar("Network error. Try again later.");
    } finally {
      setState(() => _isLoading = false);
    }
  }
  // ----------------------------------------------------- //

  // ------ function for back button - go to login page ------ //
  void _goToLogin() {
    Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const LoginPage()));
  }
  // --------------------------------------------------------- //

  // ------ helper function to show error in snackbar ------ //
  void _showSnackBar(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(msg), backgroundColor: Colors.red),
    );
  }
  // ------------------------------------------------------- //

  @override
  void dispose() {
    _emailController.dispose();
    _usernameController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  // ------ design ------ //
  @override
  Widget build(BuildContext context) {
    final bottomPadding = MediaQuery.of(context).viewInsets.bottom;

    return Scaffold(
      body: GestureDetector(
        onTap: () => FocusScope.of(context).unfocus(),
        child: LayoutBuilder(
          builder: (context, constraints) {
            return SingleChildScrollView(
              padding: EdgeInsets.only(left: 16, right: 16, top: 32, bottom: bottomPadding + 32),
              child: ConstrainedBox(
                constraints: BoxConstraints(minHeight: constraints.maxHeight),
                child: IntrinsicHeight(
                  child: Form(
                    key: _formKey,
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        const Text(
                          "Sign Up for ADAMS",
                          style: TextStyle(fontSize: 36, fontWeight: FontWeight.bold),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 4),
                        const Text(
                          "Advanced Driver Alertness Monitoring System",
                          style: TextStyle(fontSize: 17),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 24),

                        TextFormField(
                          controller: _emailController,
                          decoration: InputDecoration(
                            labelText: "Email",
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                            contentPadding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
                          ),
                          validator: (value) => value!.isEmpty ? "Please enter email" : null,
                        ),
                        const SizedBox(height: 12),

                        TextFormField(
                          controller: _usernameController,
                          decoration: InputDecoration(
                            labelText: "Username",
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                            contentPadding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
                          ),
                          validator: (value) => value!.isEmpty ? "Please enter username" : null,
                        ),
                        const SizedBox(height: 12),

                        TextFormField(
                          controller: _passwordController,
                          decoration: InputDecoration(
                            labelText: "Password",
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                            contentPadding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
                          ),
                          obscureText: true,
                          validator: (value) => value!.isEmpty ? "Please enter password" : null,
                        ),
                        const SizedBox(height: 12),

                        TextFormField(
                          controller: _confirmPasswordController,
                          decoration: InputDecoration(
                            labelText: "Confirm Password",
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                            contentPadding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
                          ),
                          obscureText: true,
                          validator: (value) {
                            if (value == null || value.isEmpty) return "Please confirm password";
                            if (value != _passwordController.text) return "Password does not match";
                            return null;
                          },
                        ),
                        const SizedBox(height: 24),

                        SizedBox(
                          width: double.infinity,
                          child: ElevatedButton(
                            onPressed: _isLoading ? null : _signup,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.lightBlue,
                              padding: const EdgeInsets.symmetric(vertical: 12),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                              elevation: 4,
                            ),
                            child: _isLoading
                                ? const SizedBox(
                                    height: 20,
                                    width: 20,
                                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black),
                                  )
                                : const Text("Sign Up", style: TextStyle(fontSize: 18, color: Colors.black)),
                          ),
                        ),
                        const SizedBox(height: 8),

                        SizedBox(
                          width: double.infinity,
                          child: ElevatedButton(
                            onPressed: _goToLogin,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.grey.shade300,
                              padding: const EdgeInsets.symmetric(vertical: 12),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                              elevation: 2,
                            ),
                            child: Text("Back", style: TextStyle(fontSize: 18, color: Colors.grey.shade700)),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}
