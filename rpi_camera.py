import picamera2
import time
import datetime
import os

class GH_Camera:
    def __init__(self):
        self.__last_path = ""
        
    def capture_store_image(self, cam_id=0):
        try:
            self.__last_path = f"image_c{cam_id}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
            # Initialize the camera
            with picamera2.Picamera2(cam_id) as camera:
                camera.start()            
                # Capture an image and save it
                camera.capture_file(self.__last_path)
                print(f"Image captured and saved as '{self.__last_path}'.")
                # Stop the camera preview
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