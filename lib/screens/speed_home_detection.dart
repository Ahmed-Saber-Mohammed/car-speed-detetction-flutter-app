import 'dart:developer'; // Import the developer package
import 'package:flutter/material.dart';

import 'detected_cars_page.dart';


class SpeedDetectionHome extends StatefulWidget {
  const SpeedDetectionHome({super.key});

  @override
  // ignore: library_private_types_in_public_api
  _SpeedDetectionHomeState createState() => _SpeedDetectionHomeState();
}

class _SpeedDetectionHomeState extends State<SpeedDetectionHome> {
  final TextEditingController _maxSpeedController = TextEditingController();


  void _saveMaxSpeed() {
    String maxSpeed = _maxSpeedController.text;
    log("Max Speed Saved: $maxSpeed"); // Use log() instead of print()
  }

  void _openOverSpeedFolder() {
    // Navigate to the detected cars page
    Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => const DetectedCarsPage()),
    );
  }

  void _recordVideo() {
    log("Playing Video"); // Use log()
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          "Speed Car Detection",
          style: TextStyle(color: Colors.white),
        ),
        centerTitle: true,
        backgroundColor: Colors.black,
      ),
      backgroundColor: Colors.black,
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            TextField(
              controller: _maxSpeedController,
              keyboardType: TextInputType.number,
              style: const TextStyle(color: Colors.white),
              cursorColor: Colors.white, // Cursor color changed to white
              decoration: InputDecoration(
                labelText: "Enter Max Speed",
                labelStyle:
                const TextStyle(color: Color.fromARGB(255, 177, 18, 7)),
                border: const OutlineInputBorder(
                  borderSide:
                  BorderSide(color: Color.fromARGB(255, 177, 18, 7)),
                ),
                enabledBorder: const OutlineInputBorder(
                  borderSide:
                  BorderSide(color: Color.fromARGB(255, 177, 18, 7)),
                ),
                focusedBorder: const OutlineInputBorder(
                  borderSide: BorderSide(
                      color: Color.fromARGB(255, 177, 18, 7), width: 2),
                ),
                suffixIcon: Padding(
                  padding: const EdgeInsets.only(right: 10), // Adjust spacing
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(
                        width: 2, // Line width
                        height: 24, // Line height
                        color: const Color.fromARGB(255, 82, 8, 8), // Line color
                        margin: const EdgeInsets.symmetric(horizontal: 8),
                      ),
                      const Text(
                        "km/h",
                        style: TextStyle(
                            color: Colors.white, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: _saveMaxSpeed,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color.fromARGB(255, 177, 18, 7),
                foregroundColor: Colors.white,
              ),
              child: const Text("Save Max Speed"),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: _openOverSpeedFolder,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color.fromARGB(255, 177, 18, 7),
                foregroundColor: Colors.white,
              ),
              child: const Text("View Detected Cars"),
            ),
          ],
        ),
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerFloat,
      floatingActionButton: Column(
        mainAxisSize: MainAxisSize.min, // Ensures column only takes needed space
        children: [
          // Push button slightly higher for better visibility
          SizedBox(height: MediaQuery.of(context).size.height * 0.1),

          // Floating Action Button (Large Size)
          FloatingActionButton(
            onPressed: _recordVideo,
            backgroundColor: Color.fromARGB(255, 177, 18, 7),
            shape: CircleBorder(),
            heroTag: "record_video", // Avoids conflicts if using multiple FABs
            elevation: 8, // Adds shadow for better UX
            mini: false,
            child: Icon(
              Icons.video_camera_back_outlined,
              color: Colors.white,
              size: 40, // Larger icon for visibility
            ), // Ensures large button
          ),

          SizedBox(height: 10), // Space between button and text

          // Text Below the Button
          Text(
            "Start detecting", // User-friendly text
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w600,
              color: Colors.white38,
            ),
          ),
        ],
      ),

    );
  }
}
