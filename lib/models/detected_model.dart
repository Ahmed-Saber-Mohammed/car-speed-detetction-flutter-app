
class DetectedCar {
  final int id;
  final double speed;
  final String date;
  final String time;
  final String imageUrl; // New field for the car image

  DetectedCar({
    required this.id,
    required this.speed,
    required this.date,
    required this.time,
    required this.imageUrl,
  });
}

// Sample data for testing
List<DetectedCar> detectedCars = [
  
];
