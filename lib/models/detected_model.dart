class DetectedCar {
  final String speed;
  final String data;
  final String time;
  final String imageUrl; // New field for the car image

  DetectedCar({
    required this.speed,
    required this.data,
    required this.time,
    required this.imageUrl,
  });
}

// Sample data for testing
List<DetectedCar> detectedCars = [
  DetectedCar(
    speed: "120 km/h",
    data: "2024-03-14",
    time: "14:35",
    imageUrl: "https://scontent.fcai19-3.fna.fbcdn.net/v/t39.30808-6/480965109_122103106994779689_7558256279983202286_n.jpg?_nc_cat=101&ccb=1-7&_nc_sid=833d8c&_nc_eui2=AeF0pvXj-R8zyQwknDSc--wcsE7aDz4gUPiwTtoPPiBQ-LDdhn6gs_uKYohQ3ksfXXrt3TjHxkkhh2--GA-4I61P&_nc_ohc=UlTcoiVZIcgQ7kNvgH0QSGB&_nc_oc=AdhiTj6ONlBrqAccNb7094JFwbKhniVfIYcS-uX2CeDmMa4VXPn5_DEVlq-RPmu1ib0&_nc_zt=23&_nc_ht=scontent.fcai19-3.fna&_nc_gid=UHpMuWRjCdk0Ip0y7hd_5Q&oh=00_AYFxjyOz-ocG8QilZJWjOVGhtvRfdRh_KjVAzMZRSYHPyw&oe=67D9EB49", // Placeholder image URL
  ),
  DetectedCar(
    speed: "98 km/h",
    data: "2024-03-13",
    time: "16:20",
    imageUrl: "https://via.placeholder.com/300",
  ),
];
