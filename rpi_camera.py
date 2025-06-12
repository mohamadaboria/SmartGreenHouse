import picamera2
import time
import datetime
import os
import cv2
import numpy as np

class GH_Camera:
    def __init__(self):
        self.__last_path = ""
        self.__camera_1 = None
        self.__camera_2 = None

    def capture_store_image(self, cam_id=0):
        try:
            self.__last_path = f"image_c{cam_id}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
            with picamera2.Picamera2(cam_id) as camera:
                camera.start()
                camera.capture_file(self.__last_path)
                print(f"Image captured and saved as '{self.__last_path}'.")
                camera.stop()
            return self.__last_path
        except Exception as e:
            print(f"Error capturing image: {e}")
            return None

    def remove_image(self, path=None):
        try:
            if path:
                self.__last_path = path
            if self.__last_path:
                os.remove(self.__last_path)
                print(f"Image '{self.__last_path}' removed.")
            else:
                print("No image to remove.")
        except Exception as e:
            print(f"Error removing image: {e}")

    def init_camera_for_streaming(self, cam_id=0, resolution=(1280, 720)):
        try:
            # Stop any existing camera instance first
            if cam_id == 0 and self.__camera_1:
                self.stop_camera_1()

            elif cam_id == 1 and self.__camera_2:
                self.stop_camera_2()
                
            # Create new camera instance
            camera = picamera2.Picamera2(cam_id)
            config = camera.create_video_configuration(
                main={"size": resolution},  # 720p
                controls={"FrameRate": 15},  # Lower fps for stability
                encode="main"  # Enable H.264 hardware encoding            
            )
            camera.configure(config)
            camera.start()
            
            if cam_id == 0:
                self.__camera_1 = camera
            else:
                self.__camera_2 = camera
                
            print(f"Camera {cam_id+1} initialized for streaming with resolution {resolution}.")
            time.sleep(2)  # Increased delay for camera to initialize
            return True
        except Exception as e:
            print(f"Error initializing camera {cam_id+1}: {e}")
            return False

    def generate_video_stream_camera_1(self):
        if self.__camera_1 is None:
            self.init_camera_for_streaming(cam_id=0)

        if self.__camera_1 is None:
            print("Camera 1 is not initialized.")
            return
        while True:
            try:
                frame = self.__camera_1.capture_array()
                _, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            except Exception as e:
                print(f"Streaming error (camera 1): {e}")
                break

    def generate_video_stream_camera_2(self):
        if self.__camera_2 is None:
            self.init_camera_for_streaming(cam_id=1)

        if self.__camera_2 is None:
            print("Camera 2 is not initialized.")
            return
        while True:
            try:
                frame = self.__camera_2.capture_array()
                _, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            except Exception as e:
                print(f"Streaming error (camera 2): {e}")
                break

    def stop_camera_1(self):
        try:
            if self.__camera_1 is not None:
                self.__camera_1.stop()
                time.sleep(1)
                self.__camera_1.close()
                self.__camera_1 = None
                print("Camera 1 stopped.")
            else:
                print("No camera 1 to stop.")
        except Exception as e:
            print(f"Error stopping camera 1: {e}")

    def stop_camera_2(self):
        try:
            if self.__camera_2 is not None:
                self.__camera_2.stop()
                time.sleep(1)
                self.__camera_2.close()
                self.__camera_2 = None
                print("Camera 2 stopped.")
            else:
                print("No camera 2 to stop.")
        except Exception as e:
            print(f"Error stopping camera 2: {e}")
            
