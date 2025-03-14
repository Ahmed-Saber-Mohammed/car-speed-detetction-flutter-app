import 'package:flutter/material.dart';
import '../models/detected_model.dart';
import 'car_detail_page.dart'; // Import the detail page

class DetectedCarsPage extends StatefulWidget {
  const DetectedCarsPage({super.key});

  @override
  _DetectedCarsPageState createState() => _DetectedCarsPageState();
}

class _DetectedCarsPageState extends State<DetectedCarsPage> {
  List<DetectedCar> carsList = List.from(detectedCars);

  void _deleteCar(int index) {
    setState(() {
      carsList.removeAt(index);
    });
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
          color:  Colors.white54, // Change back button color to red
        ),
      ),
      backgroundColor: Colors.black,
      body: carsList.isEmpty
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
                contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                title: Text(
                  "Speed: ${car.speed}",
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                ),
                subtitle: Text(
                  "Date: ${car.data}\nTime: ${car.time}",
                  style: TextStyle(color: Colors.white.withOpacity(0.8), fontSize: 15),
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
