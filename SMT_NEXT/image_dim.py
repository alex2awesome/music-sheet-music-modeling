import cv2

def get_image_dimensions(image_path):
    # Read the image using OpenCV
    image = cv2.imread(image_path)
    
    # Check if the image was loaded successfully
    if image is None:
        raise ValueError(f"Could not open or find the image: {image_path}")
    
    # Get dimensions
    height, width, channels = image.shape
    return width, height

# Example usage
image_path = 'Data/GrandStaff/grandstaff_dataset/piano-sonatas/sonata28-4/min3_up_m-169-173.jpg'
try:
    width, height = get_image_dimensions(image_path)
    print(f'The dimensions of the image are {width}x{height}')
except ValueError as e:
    print(e)