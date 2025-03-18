import 'dart:async';
import 'dart:typed_data';
import 'package:camera/camera.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

class CameraPage extends StatefulWidget {
  @override
  _CameraPageState createState() => _CameraPageState();
}

class _CameraPageState extends State<CameraPage> {
  CameraController? _controller;
  bool _isStreaming = false;
  Timer? _timer;
  final Dio _dio = Dio();
  final String _serverUrl = "http://172.30.103.210:5000/upload_video"; // Update IP

  @override
  void initState() {
    super.initState();
    _initializeCamera();
  }

  Future<void> _initializeCamera() async {
    final cameras = await availableCameras();
    if (cameras.isNotEmpty) {
      _controller = CameraController(cameras[0], ResolutionPreset.low);
      await _controller!.initialize();
      if (mounted) {
        setState(() {});
      }
    }
  }

  void _startStreaming() {
    if (_controller == null || !_controller!.value.isInitialized) return;

    setState(() {
      _isStreaming = true;
    });

    _timer = Timer.periodic(const Duration(milliseconds: 50), (timer) async {
      if (!_isStreaming) {
        timer.cancel();
        return;
      }

      try {
        final XFile file = await _controller!.takePicture();
        final Uint8List imageBytes = await file.readAsBytes();

        FormData formData = FormData.fromMap({
          "video": MultipartFile.fromBytes(imageBytes, filename: "frame.jpg"),
        });

        await _dio.post(_serverUrl, data: formData);
      } catch (e) {
        print("Error sending frame: $e");
      }
    });
  }

  void _stopStreaming() {
    setState(() {
      _isStreaming = false;
    });
    _timer?.cancel();
  }

  @override
  void dispose() {
    _stopStreaming();
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Camera Streaming")),
      body: Column(
        children: [
          Expanded(
            child: (_controller == null || !_controller!.value.isInitialized)
                ? const Center(child: CircularProgressIndicator())
                : CameraPreview(_controller!),
          ),
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: ElevatedButton(
              onPressed: _isStreaming ? _stopStreaming : _startStreaming,
              child: Text(_isStreaming ? "Stop Streaming" : "Start Streaming"),
            ),
          ),
        ],
      ),
    );
  }
}
