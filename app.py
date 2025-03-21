from flask import Flask, request, jsonify
import cv2
import numpy as np
import threading
import dlib
import time
import os
from datetime import datetime
import requests
import asyncio
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME", "your-bucket-name")  # Default bucket

if not all([SUPABASE_URL, SUPABASE_KEY, BUCKET_NAME]):
    raise ValueError("Supabase credentials not found in .env")


supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Base URL (Consider making this configurable via .env)
base_url = "http://172.30.103.210:5000"

app = Flask(__name__)

# Load the car cascade classifier
carCascade = cv2.CascadeClassifier("HaarCascadeClassifier.xml")

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

# Global list to store detected overspeeding cars (now stores URLs)
overspeeding_cars = []


def update_speed_limit():
    """Fetches the latest speed limit from an external API and updates the global variable."""
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

async def saveCar(carID, speed, frame, tx, ty, tw, th):
    """Saves a cropped image of an overspeeding car to Supabase storage."""
    now = datetime.now()
    filename = now.strftime(f"%d-%m-%Y-%H-%M-{speed}")
    image_filename = f"{filename}.jpeg"

    try:
        # Crop the car image from the frame
        car_image = frame[ty : ty + th, tx : tx + tw]

        # Check if the cropped image is valid
        if car_image.size == 0:
            print(f"⚠️ Error: Cropped car image is empty. Skipping upload.")
            return None

        # Draw red box on the *cropped* car image
        cv2.rectangle(car_image, (0, 0), (tw, th), (0, 0, 255), 3)

        # Calculate text position *relative to original frame* and then adjust for crop
        text_x = 5 # tx - tx  # Position the text a little to the left of the car
        text_y = -5 #ty - ty - 10  # Position the text above the car

        # Ensure text position is within cropped image boundaries
        if 0 <= text_x < car_image.shape[1] and 0 <= text_y < car_image.shape[0]:
            # Overlay text on the *cropped* car image
            cv2.putText(
                car_image,
                f"OVERSPEEDING {speed} km/h",
                (text_x, text_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,  # Adjusted scale for the cropped image
                (0, 0, 255),
                2,
            )
        else:
            print(
                "⚠️ Warning: Text position is outside the cropped image "
                f"boundaries.  Text_x: {text_x}, text_y: {text_y},  Shape: {car_image.shape}"
            )

        # Convert the cropped car image to JPEG bytes
        _, img_encoded = cv2.imencode(".jpeg", car_image)
        image_bytes = img_encoded.tobytes()

        # Upload the image to Supabase storage
        response = supabase.storage.from_(BUCKET_NAME).upload(
            image_filename,
            image_bytes,
            file_options={
                "cacheControl": "3600",
                "upsert": False,
                "contentType": "image/jpeg",
            },
        )  # Set contentType

        if response.status_code == 200:
            # Construct the public URL
            image_url = supabase.storage.from_(BUCKET_NAME).get_public_url(image_filename)

            print(
                f"🚨 Car {carID} is OVERSPEEDING at {speed} km/h!  Cropped image "
                f"uploaded to Supabase: {image_url}"
            )
            return image_url  # Return the URL
        else:
            print(f"Error uploading cropped image: {response.status_code} - {response.error}")
            return None  # Indicate failure

    except Exception as e:
        print(f"An error occurred during cropping/upload: {e}")
        return None  # Indicate failure

def estimateSpeed(timeDiff):
    """Calculates speed based on time taken between crossings."""
    if timeDiff > 0:  # Avoid division by zero
        speed = round((markGap / timeDiff) * fpsFactor * 3.6, 2)  # Convert to km/h
        return speed
    return 0


def detect_and_track():
    """Detects and tracks cars, checks for overspeeding, and uploads to Supabase."""
    global latest_frame, carTracker, currentCarID, frameCounter, overspeeding_cars

    while True:
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
                    tx, ty, tw, th = (
                        int(trackedPosition.left()),
                        int(trackedPosition.top()),
                        int(trackedPosition.width()),
                        int(trackedPosition.height()),
                    )
                    txbar, tybar = tx + 0.5 * tw, ty + 0.5 * th

                    # If detected car matches a tracked car, use the same ID
                    if (
                        (tx <= xbar <= (tx + tw))
                        and (ty <= ybar <= (ty + th))
                        and (x <= txbar <= (x + w))
                        and (y <= tybar <= (y + h))
                    ):
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
                tx, ty, tw, th = (
                    int(trackedPosition.left()),
                    int(trackedPosition.top()),
                    int(trackedPosition.width()),
                    int(trackedPosition.height()),
                )

                # Draw bounding box
                cv2.rectangle(frame, (tx, ty), (tx + tw, ty + th), rectangleColor, 2)

                # Detect when the car crosses the line twice
                if carID not in crossingTime and ty + th > mark_line > ty:
                    crossingTime[carID] = frameTime  # Store first crossing time
                elif carID in crossingTime and ty > mark_line:
                    timeDiff = frameTime - crossingTime[carID]
                    speed = estimateSpeed(timeDiff)

                    # Display speed on frame
                    cv2.putText(
                        frame,
                        f"Speed: {speed} km/h",
                        (tx, ty - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 0, 255),
                        2,
                    )

                    # Highlight overspeeding cars in red and save screenshots
                    if speed > speedLimit:
                        loop = asyncio.new_event_loop()  # Create an event loop
                        asyncio.set_event_loop(loop)  # Set the current event loop
                        image_url = loop.run_until_complete(saveCar(carID, speed, frame, tx, ty, tw, th))
                        loop.close()  # Close the loop

                        if image_url:
                            with speed_limit_lock:
                                overspeeding_cars.append(
                                    {
                                        "image_url": image_url,
                                        "speed": speed,
                                        "date": datetime.now().strftime("%d/%m/%Y"),
                                        "time": datetime.now().strftime("%H:%M"),
                                    }
                                )
                                print(
                                    f"Added overspeeding car to list: {overspeeding_cars[-1]}"
                                )  # Debug
                        else:
                            print("Failed to save image to Supabase.")

                    # Remove car from tracking after speed calculation
                    del crossingTime[carID]

        # Remove lost trackers
        for carID in carIDsToDelete:
            del carTracker[carID]

        # Display processed frame
        cv2.imshow("Car Detection with Speed", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cv2.destroyAllWindows()


@app.route("/set_speed_limit", methods=["POST"])
def set_speed_limit():
    global speedLimit
    try:
        data = request.get_json()
        print(f"📥 Received API request: {data}")  # Debugging print

        new_limit = int(data["max_speed"])  # Extract speed limit
        if not (10 <= new_limit <= 200):  # Validate range
            print(f"🚨 Rejected invalid speed limit: {new_limit}")
            return {
                "error": "Invalid speed limit range (must be between 10 and 200 km/h)"
            }, 400

        with speed_limit_lock:  # Use lock to safely update
            speedLimit = new_limit

        print(f"✅ Speed limit manually set to {speedLimit} km/h")
        return {"message": "Speed limit updated", "speedLimit": speedLimit}, 200
    except (KeyError, ValueError):
        print("❌ Invalid request format")
        return {"error": "Invalid speed limit value"}, 400


@app.route("/upload_video", methods=["POST"])
def upload_video():
    """Receives video frames and updates the latest frame in memory."""
    global latest_frame

    file = request.files["video"]
    nparr = np.frombuffer(file.read(), np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame is None:
        return "Failed to decode frame", 400

    frame = cv2.resize(frame, (640, 480))  # Resize for performance

    with frame_lock:
        latest_frame = frame  # Store latest frame

    return "Frame received", 200


@app.route("/overspeeding_cars", methods=["GET"])
def get_overspeeding_cars():
    """Returns a list of overspeeding cars with Supabase URLs."""
    global overspeeding_cars  # Access the global list

    return jsonify({"overspeeding_cars": overspeeding_cars})


if __name__ == "__main__":
    threading.Thread(target=update_speed_limit, daemon=True).start()  # Start speed limit updater
    threading.Thread(target=detect_and_track, daemon=True).start()
    app.run(
        host="0.0.0.0", port=5000, debug=True, use_reloader=False
    )  # Prevent duplicate threads
