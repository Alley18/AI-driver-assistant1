import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:hive/hive.dart';
import 'package:http/http.dart' as http;
import 'package:idas_app/pages/home_page.dart';
import '../widgets/config.dart';

class DeviceLinkPage extends StatefulWidget {
  const DeviceLinkPage({super.key});

  @override
  State<DeviceLinkPage> createState() => _DeviceLinkPageState();
}

class _DeviceLinkPageState extends State<DeviceLinkPage> {
  String? username;
  String? userID;
  final TextEditingController _hardwareID = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadSession();
  }

  // ------ load current user info ------ //
  Future<void> _loadSession() async {
    final sessionBox = await Hive.openBox('session');
    setState(() {
      username = sessionBox.get('currentUser');
      userID = sessionBox.get('userID');
      _isLoading = false;
    });
  }
  // ------------------------------------ //

  // ------ send user id and device id to backend ------ //
  void _hardware() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _isLoading = true);
    final hardwareID = _hardwareID.text.trim();

    try {
      final url = Uri.parse('$baseUrl/register-device');
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'user_id': userID, 'device_id': hardwareID}),
      );

      if (response.statusCode == 200) {
        final sessionBox = await Hive.openBox('session');
        await sessionBox.put('hardwareID', hardwareID);

        if (!mounted) return;
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (_) => HomePage(username: username!, userID: userID),
          ),
        );
      
       ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("Connected to $hardwareID."),
            backgroundColor: Colors.green,
          ),
        );
        
      }

      if (response.statusCode == 403) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text("Hardware not registered."),
            backgroundColor: Colors.red,
          ),
        );
      }
    } catch (e) {
      debugPrint("Error linking hardware: $e");
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("Failed to link hardware"),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      setState(() => _isLoading = false);
      _hardwareID.clear();
    }
  }
  // --------------------------------------------------- //

  // ------ design ------ //
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.blue.shade300,
        centerTitle: true,
        leading: IconButton(
          onPressed: () => Navigator.pop(context),
          icon: const Icon(Icons.arrow_back, color: Colors.white),
        ),
        title: const Text(
          "ADAMS",
          style: TextStyle(fontSize: 30, color: Colors.white),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Center(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              const SizedBox(height: 16), // top spacing
              // Big title
              Text(
                "Link Your Hardware",
                style: const TextStyle(
                  fontSize: 40,
                  fontWeight: FontWeight.bold,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),

              Text(
                "Hello, $username!",
                style: const TextStyle(fontSize: 35),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),

              Text(
                "Start monitoring your driving habits today.",
                style: const TextStyle(fontSize: 20),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),

              // Fixed-size form card
              SizedBox(
                width: 500,
                height: 300,
                child: Card(
                  elevation: 2,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Form(
                      key: _formKey,
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Text(
                            "Enter your hardware ID",
                            style: TextStyle(fontSize: 20),
                          ),
                          const SizedBox(height: 16),
                          TextFormField(
                            controller: _hardwareID,
                            decoration: InputDecoration(
                              labelText: "Hardware ID",
                              border: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                            ),
                            validator: (value) => value!.isEmpty
                                ? "Please enter hardware ID"
                                : null,
                          ),
                          const SizedBox(height: 24),
                          SizedBox(
                            width: 150,
                            height: 40,
                            child: ElevatedButton(
                              onPressed: _isLoading
                                  ? null
                                  : _hardware, // disable button while loading
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.lightBlue,
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(12),
                                ),
                              ),
                              child: _isLoading
                                  ? const SizedBox(
                                      width: 24,
                                      height: 24,
                                      child: CircularProgressIndicator(
                                        color: Colors.black,
                                        strokeWidth: 2,
                                      ),
                                    )
                                  : const Text(
                                      "Connect",
                                      style: TextStyle(
                                        fontSize: 16,
                                        color: Colors.black,
                                      ),
                                    ),
                            ),
                          ),
                        ],
                      ),
                    ),
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
