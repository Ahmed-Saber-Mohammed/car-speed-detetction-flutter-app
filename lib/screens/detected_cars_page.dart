import 'package:flutter/material.dart';
import '../models/detected_model.dart';
import 'car_detail_page.dart'; // Import the detail page
import 'package:dio/dio.dart';

String baseUrl = "https://f0-bg-removal.rivo.gallery"; // Your Flask server URL

class DetectedCarsPage extends StatefulWidget {
  const DetectedCarsPage({super.key});

  @override
  _DetectedCarsPageState createState() => _DetectedCarsPageState();
}

class _DetectedCarsPageState extends State<DetectedCarsPage> {
  List<DetectedCar> carsList = [];

  @override
  void initState() {
    super.initState();
    fetchDetectedCars(); // Fetch cars from the backend on page load
  }

  Future<void> fetchDetectedCars() async {
    try {
      var response = await Dio().get("$baseUrl/overspeeding_cars");

      print("Response status: ${response.statusCode}");
      print("Response data: ${response.data}");
      if (response.statusCode == 200) {
        List<dynamic> fetchedCars =
            response.data; // Since the API returns a list directly

        setState(() {
          carsList =
              fetchedCars.map((car) {
                print("Car data: $car");

                return DetectedCar(
                  id: car["id"] as int,
                  imageUrl:
                      car["image_path"] != null
                          ? car["image_path"]
                          : "$baseUrl/default.jpg",
                  speed:
                      (car["speed"] as num)
                          .toDouble(), // Fix: Ensure speed is double

                  date: car["date"] ?? "Unknown",
                  time: car["time"] ?? "Unknown",
                );
              }).toList();
        });
      } else {
        print("Error: Status code ${response.statusCode}");
      }
    } catch (e) {
      print("Error fetching detected cars: $e");
    }
  }

void _deleteCar(int index) async {
  final car = carsList[index];
  final int carId = car.id;

  try {
    print("🚗 Attempting to delete car ID: $carId");

    var response = await Dio().delete("$baseUrl/overspeeding_cars/$carId");

    if (response.statusCode == 200) {
      print("✅ Car deleted from Supabase: $carId");

      setState(() {
        carsList.removeAt(index); // Remove from UI immediately
      });

      // Ensure full refresh by calling fetchDetectedCars()
      fetchDetectedCars(); 
    } else {
      print("⚠️ Error deleting car from Supabase: ${response.data}");
    }
  } catch (e) {
    print("⚠️ Failed to delete car: $e");
  }
}


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          "Detected Cars",
          style: TextStyle(color: Colors.white),
        ),
        centerTitle: true,
        backgroundColor: Colors.black,
        iconTheme: const IconThemeData(
          color: Colors.white54, // Change back button color to red
        ),
      ),
      backgroundColor: Colors.black,
      body:
          carsList.isEmpty
              ? const Center(
                child: Text(
                  "No detected cars",
                  style: TextStyle(color: Colors.white54, fontSize: 18),
                ),
              )
              : ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: carsList.length,
                itemBuilder: (context, index) {
                  final car = carsList[index];

                  return GestureDetector(
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => CarDetailPage(car: car),
                        ),
                      );
                    },
                    child: Container(
                      margin: const EdgeInsets.symmetric(vertical: 8),
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(12),
                        gradient: const LinearGradient(
                          colors: [Color(0xFF1C1C1C), Color(0xFF630D14)],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(0.3),
                            blurRadius: 8,
                            offset: const Offset(2, 4),
                          ),
                        ],
                      ),
                      child: ListTile(
                        contentPadding: const EdgeInsets.symmetric(
                          horizontal: 16,
                          vertical: 12,
                        ),
                        title: Text(
                          "Speed: ${car.speed}",
                          style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        subtitle: Text(
                          "Date: ${car.date}\nTime: ${car.time}",
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.8),
                            fontSize: 15,
                          ),
                        ),
                        trailing: IconButton(
                          icon: const Icon(Icons.delete, color: Colors.red),
                          onPressed: () => _deleteCar(index),
                        ),
                      ),
                    ),
                  );
                },
              ),
    );
  }
}
