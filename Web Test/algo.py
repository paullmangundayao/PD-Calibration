import cv2
import numpy as np
import random
import datetime
import logging
from serv_cam import ServoCamera

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class VisionOptimizer:
    def __init__(self):
        # Camera calibration constants
        self.PIXEL_TO_CM_RATIO_FRONT = 0.06035
        self.PIXEL_TO_CM_RATIO_SIDE = 0.049
        
        # Genetic algorithm parameters
        self.POPULATION_SIZE = 10
        self.GENERATIONS = 50
        self.SEALING_MARGIN = 2
        self.MUTATION_RATE = 0.1
        
        # Hardware controller
        self.hardware = HardwareController()
    
    def detect_front_dimensions(self, camera):
        """Detects object width and height from front camera"""
        ret, frame = camera.read()
        if not ret:
            logging.error("Failed to read frame from front camera.")
            return None, None, None

        # Image processing
        frame = cv2.convertScaleAbs(frame, alpha=1.5, beta=50)
        frame_blurred = cv2.GaussianBlur(frame, (5, 5), 0)
        height, width, _ = frame_blurred.shape
        
        # ROI cropping
        roi = frame_blurred[int(height*0.2):int(height*0.8), int(width*0.2):int(width*0.8)]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # Thresholding and morphology
        _, mask_white = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        kernel = np.ones((7,7), np.uint8)
        mask_final = cv2.morphologyEx(mask_white, cv2.MORPH_OPEN, kernel, iterations=2)
        mask_final = cv2.morphologyEx(mask_final, cv2.MORPH_CLOSE, kernel, iterations=2)

        # Contour detection
        contours, _ = cv2.findContours(mask_final, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            logging.error("No contours found in front camera frame.")
            return None, None, None

        largest_contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest_contour) < 5000:
            logging.error("Largest contour too small in front camera frame.")
            return None, None, None

        # Measurement conversion
        x, y, w, h = cv2.boundingRect(largest_contour)
        width_cm = round(w * self.PIXEL_TO_CM_RATIO_FRONT + 0.2, 1)
        height_cm = round(h * self.PIXEL_TO_CM_RATIO_FRONT - 0.2, 1)

        # Save image for verification
        image_path = f'images/front_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.png'
        cv2.imwrite(image_path, roi)

        return width_cm, height_cm, image_path
    
    def detect_side_dimension(self, camera):
        """Detects object length from side camera"""
        self.hardware.adjust_side_camera_position()
        
        for attempt in range(3):
            ret, frame = camera.read()
            if not ret:
                continue
                
            # Image processing (similar to front camera)
            frame = cv2.convertScaleAbs(frame, alpha=1.5, beta=50)
            frame_blurred = cv2.GaussianBlur(frame, (5, 5), 0)
            height, width, _ = frame_blurred.shape
            roi = frame_blurred[int(height*0.2):int(height*0.8), int(width*0.2):int(width*0.8)]
            
            # Thresholding and contour detection
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            _, mask_white = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
            kernel = np.ones((7,7), np.uint8)
            mask_final = cv2.morphologyEx(mask_white, cv2.MORPH_OPEN, kernel, iterations=2)
            
            contours, _ = cv2.findContours(mask_final, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                continue
                
            largest_contour = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest_contour) < 5000:
                continue
                
            # Measurement conversion
            x, y, w, h = cv2.boundingRect(largest_contour)
            length_cm = round(w * self.PIXEL_TO_CM_RATIO_SIDE - 0.4, 1)
            
            image_path = f'images/side_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.png'
            cv2.imwrite(image_path, roi)
            
            return length_cm, image_path
            
        return None, None
    
    def fitness_function(self, candidate_solution, object_dimensions):
        """Evaluates fitness of a candidate solution"""
        candidate_l, candidate_w, candidate_h = candidate_solution
        min_l = object_dimensions[0] + self.SEALING_MARGIN
        min_w = object_dimensions[1] + self.SEALING_MARGIN
        min_h = object_dimensions[2] + self.SEALING_MARGIN
        
        penalty = max(0, candidate_l - min_l) + max(0, candidate_w - min_w) + max(0, candidate_h - min_h)
        return penalty
    
    def genetic_algorithm(self, object_dimensions):
        """Runs genetic algorithm to find optimal packaging dimensions"""
        population = [
            np.array([
                object_dimensions[0] + self.SEALING_MARGIN + random.uniform(0, 0.1),
                object_dimensions[1] + self.SEALING_MARGIN + random.uniform(0, 0.1),
                object_dimensions[2] + self.SEALING_MARGIN + random.uniform(0, 0.1)
            ])
            for _ in range(self.POPULATION_SIZE)
        ]
        
        for generation in range(self.GENERATIONS):
            population.sort(key=lambda x: self.fitness_function(x, object_dimensions))
            best_solution = population[0]
            
            new_population = []
            while len(new_population) < self.POPULATION_SIZE:
                parent1, parent2 = random.sample(population[:5], 2)
                child = (parent1 + parent2) / 2
                if random.random() < self.MUTATION_RATE:
                    child += np.random.normal(0, 0.1, 3)
                new_population.append(child)
            
            population = new_population
        
        return {
            "Optimal Length": population[0][0],
            "Optimal Width": population[0][1],
            "Optimal Height": population[0][2]
        }
    
    def calculate_bubble_wrap_size(self, optimal_dimensions):
        """Calculates required bubble wrap dimensions"""
        l = optimal_dimensions["Optimal Length"]
        w = optimal_dimensions["Optimal Width"]
        h = optimal_dimensions["Optimal Height"]
        
        return {
            "length": (2 * h) + (2 * w),
            "width": (2 * l) + (2 * w)
        }
    
    def measure_and_optimize(self):
        """Main function to measure object and calculate optimal packaging"""
        front_cam = cv2.VideoCapture(0, cv2.CAP_V4L2)
        side_cam = cv2.VideoCapture(2, cv2.CAP_V4L2)
        
        try:
            # Front measurement
            width, height, front_img = self.detect_front_dimensions(front_cam)
            if None in (width, height):
                return None
                
            # Side measurement
            length, side_img = self.detect_side_dimension(side_cam)
            if length is None:
                return None
                
            # Optimization
            object_dims = (length, width, height)
            optimal_dims = self.genetic_algorithm(object_dims)
            bubble_wrap = self.calculate_bubble_wrap_size(optimal_dims)
            
            return {
                "object_dimensions": object_dims,
                "optimized_dimensions": optimal_dims,
                "bubble_wrap_size": bubble_wrap,
                "front_image_path": front_img,
                "side_image_path": side_img
            }
        finally:
            front_cam.release()
            side_cam.release()
            self.hardware.cleanup()

if __name__ == "__main__":
    try:
        optimizer = VisionOptimizer()
        result = optimizer.measure_and_optimize()
        
        if result:
            print("\n--- Results ---")
            print(f"Object Dimensions (L, W, H): {result['object_dimensions']}")
            print(f"Optimal Dimensions: {result['optimized_dimensions']}")
            print(f"Bubble Wrap Size: {result['bubble_wrap_size']}")
            print(f"Front Image: {result['front_image_path']}")
            print(f"Side Image: {result['side_image_path']}")
        else:
            print("Measurement failed")
            
    except KeyboardInterrupt:
        print("Program interrupted")
    finally:
        print("Cleanup complete")