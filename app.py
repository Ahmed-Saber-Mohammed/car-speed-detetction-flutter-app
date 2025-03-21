
from flask import Flask, request, jsonify, send_from_directory
import cv2
import numpy as np
import threading
import dlib
import time
import os
from datetime import datetime
import requests


base_url = "http://172.30.103.210:5000" 

app = Flask(__name__)

# Load the car cascade classifier
carCascade = cv2.CascadeClassifier('HaarCascadeClassifier.xml')

# Global frame storage
latest_frame = None
frame_lock = threading.Lock()

# Tracking variables
carTracker = {}
currentCarID = 0
rectangleColor = (255, 0, 0)
frameCounter = 0

# Speed calculation variables
mark_line = 250  # Single detection line
markGap = 10  # Distance in meters for speed calculation
fpsFactor = 3  # Speed adjustment factor
speedLimit = 30  # Speed limit in km/h
crossingTime = {}  # Store crossing times for cars

speed_limit_lock = threading.Lock()  # Lock to prevent race conditions

def update_speed_limit():
    """ Fetches the latest speed limit from an external API and updates the global variable. """
    global speedLimit
    api_url = f"{base_url}/setspeedlimit"  # Replace with actual API URL

    while True:
        try:
            response = requests.get(api_url, timeout=5)  # Fetch new speed limit
            if response.status_code == 200:
                data = response.json()
                print(f"🔍 API Response (Fetched Speed): {data}")  # Log API response

                if "max_speed" in data:
                    new_limit = int(data["max_speed"])  # Extract speed limit

                    if not (10 <= new_limit <= 200):  # Ensure valid range
                        print(f"🚨 Ignored invalid speed limit: {new_limit}")
                        continue
                    
                    with speed_limit_lock:  # Ensure safe update
                        if new_limit != speedLimit:
                            speedLimit = new_limit
                            print(f"✅ Updated speed limit to {speedLimit} km/h")
        except requests.RequestException as e:
            print(f"⚠️ Failed to fetch speed limit: {e}")

        time.sleep(60)  # Check for updates every 60 seconds

# Create directory for saving overspeeding cars
if not os.path.exists('overspeeding/cars/'):
    os.makedirs('overspeeding/cars/')

overspeeding_cars = []  # Global list to store detected overspeeding cars

def saveCar(carID, speed, frame, tx, ty, tw, th):
    """ Saves an image of an overspeeding car with speed info. """
    now = datetime.now()
    filename = now.strftime("%d-%m-%Y-%H-%M-%S-%f")
    filepath = f'overspeeding/cars/{filename}.jpeg'

    # Draw red box and overlay speed on the image
    car_image = frame[ty:ty + th, tx:tx + tw]
    cv2.rectangle(frame, (tx, ty), (tx + tw, ty + th), (0, 0, 255), 3)
    cv2.putText(frame, f"OVERSPEEDING {speed} km/h", (tx, ty - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    # Save the image
    cv2.imwrite(filepath, car_image)
    # Store in global list
    overspeeding_cars.append({
        "image_path": filepath,  # Send relative path
        "speed": speed,
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
    })
    print(f"🚨 Car {carID} is OVERSPEEDING at {speed} km/h! Screenshot saved.")

def estimateSpeed(timeDiff):
    """ Calculates speed based on time taken between crossings. """
    if timeDiff > 0:  # Avoid division by zero
        speed = round((markGap / timeDiff) * fpsFactor * 3.6, 2)  # Convert to km/h
        return speed
    return 0

def detect_and_track():
    """ Detects and tracks cars, checks for overspeeding, and saves screenshots. """
    global latest_frame, carTracker, currentCarID, frameCounter

    while True:
        print(speedLimit)
        with frame_lock:
            if latest_frame is None:
                time.sleep(0.01)
                continue
            frame = latest_frame.copy()

        frameCounter += 1
        frameTime = time.time()  # Timestamp for speed calculation

        # Convert frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect cars every 30 frames
        if frameCounter % 30 == 0:
            cars = carCascade.detectMultiScale(gray, 1.1, 5, minSize=(24, 24))

            for (_x, _y, _w, _h) in cars:
                x, y, w, h = int(_x), int(_y), int(_w), int(_h)
                xbar, ybar = x + 0.5 * w, y + 0.5 * h

                matchCarID = None
                for carID in carTracker.keys():
                    trackedPosition = carTracker[carID].get_position()
                    tx, ty, tw, th = int(trackedPosition.left()), int(trackedPosition.top()), int(trackedPosition.width()), int(trackedPosition.height())
                    txbar, tybar = tx + 0.5 * tw, ty + 0.5 * th

                    # If detected car matches a tracked car, use the same ID
                    if ((tx <= xbar <= (tx + tw)) and (ty <= ybar <= (ty + th)) and (x <= txbar <= (x + w)) and (y <= tybar <= (y + h))):
                        matchCarID = carID

                # If it's a new car, start tracking
                if matchCarID is None:
                    tracker = dlib.correlation_tracker()
                    tracker.start_track(frame, dlib.rectangle(x, y, x + w, y + h))
                    carTracker[currentCarID] = tracker
                    matchCarID = currentCarID
                    currentCarID += 1

        # Draw single speed measurement line
        cv2.line(frame, (0, mark_line), (frame.shape[1], mark_line), (0, 255, 255), 2)  # Yellow line

        # Update trackers and draw bounding boxes
        carIDsToDelete = []
        for carID in list(carTracker.keys()):
            trackingQuality = carTracker[carID].update(frame)

            if trackingQuality < 7:
                carIDsToDelete.append(carID)
            else:
                trackedPosition = carTracker[carID].get_position()
                tx, ty, tw, th = int(trackedPosition.left()), int(trackedPosition.top()), int(trackedPosition.width()), int(trackedPosition.height())

                # Draw bounding box
                cv2.rectangle(frame, (tx, ty), (tx + tw, ty + th), rectangleColor, 2)

                # Detect when the car crosses the line twice
                if carID not in crossingTime and ty + th > mark_line > ty:
                    crossingTime[carID] = frameTime  # Store first crossing time
                elif carID in crossingTime and ty > mark_line:
                    timeDiff = frameTime - crossingTime[carID]
                    speed = estimateSpeed(timeDiff)

                    # Display speed on frame
                    cv2.putText(frame, f"Speed: {speed} km/h", (tx, ty - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                    # Highlight overspeeding cars in red and save screenshots
                    if speed > speedLimit:
                        saveCar(carID, speed, frame, tx, ty, tw, th)

                    # Remove car from tracking after speed calculation
                    del crossingTime[carID]

        # Remove lost trackers
        for carID in carIDsToDelete:
            del carTracker[carID]

        # Display processed frame
        cv2.imshow("Car Detection with Speed", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()

@app.route('/set_speed_limit', methods=['POST'])
def set_speed_limit():
    global speedLimit
    try:
        data = request.get_json()
        print(f"📥 Received API request: {data}")  # Debugging print

        new_limit = int(data['max_speed'])  # Extract speed limit
        if not (10 <= new_limit <= 200):  # Validate range
            print(f"🚨 Rejected invalid speed limit: {new_limit}")
            return {"error": "Invalid speed limit range (must be between 10 and 200 km/h)"}, 400
        
        with speed_limit_lock:  # Use lock to safely update
            speedLimit = new_limit

        print(f"✅ Speed limit manually set to {speedLimit} km/h")
        return {"message": "Speed limit updated", "speedLimit": speedLimit}, 200
    except (KeyError, ValueError):
        print("❌ Invalid request format")
        return {"error": "Invalid speed limit value"}, 400

@app.route('/upload_video', methods=['POST'])
def upload_video():
    """ Receives video frames and updates the latest frame in memory. """
    global latest_frame

    file = request.files['video']
    nparr = np.frombuffer(file.read(), np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame is None:
        return "Failed to decode frame", 400

    frame = cv2.resize(frame, (640, 480))  # Resize for performance

    with frame_lock:
        latest_frame = frame  # Store latest frame

    return "Frame received", 200


@app.route('/overspeeding_cars', methods=['GET'])
def get_overspeeding_cars(): 
    image_folder = "overspeeding/cars/"

    overspeeding_cars = []
    for filename in os.listdir(image_folder):
        if filename.endswith(".jpeg"):
            overspeeding_cars.append({
                "image_path": f"{base_url}/{image_folder}{filename}",  # ✅ Full URL
                "speed": filename.split("_")[1] if "_" in filename else "Unknown",
                "date": filename.split("-")[0] if "-" in filename else "Unknown",
                "time": filename.split("-")[1] if "-" in filename else "Unknown",
            })

    return jsonify({"overspeeding_cars": overspeeding_cars})

@app.route('/overspeeding/cars/<path:filename>')
def serve_image(filename):
    return send_from_directory("overspeeding/cars", filename)


if __name__ == '__main__':
    threading.Thread(target=update_speed_limit, daemon=True).start()  # Start speed limit updater
    threading.Thread(target=detect_and_track, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)  # Prevent duplicate threads