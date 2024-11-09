import PIL
import sys
from PIL import Image
import numpy as np

def invert(img):
    return Image.eval(img, lambda x: 255 - x)

def compute_plane_equation(point1, point2, point3):
    # Calculate vectors
    v1 = point2 - point1
    v2 = point3 - point1
    # Calculate normal vector using cross product
    normal = np.cross(v1, v2)
    # Calculate D
    D = -np.dot(normal, point1)
    return normal, D

def calculate_distance_to_plane(points, normal, D):
    # Calculate distance of points to the plane
    distances = np.abs(np.dot(points, normal) + D) / np.linalg.norm(normal)
    return distances

def calculate_distance_from_point(img_array, point):
    # Calculate Euclidean distance from each pixel to the specified point
    distances = np.sqrt(np.sum((img_array - point) ** 2, axis=-1))
    return distances

def extract_cmy(img_points, colors_plane1, colors_plane2):

    # Compute plane equations for both sets of colors
    normal1, D1 = compute_plane_equation(np.array(colors_plane1[0]), np.array(colors_plane1[1]), np.array(colors_plane1[2]))
    normal2, D2 = compute_plane_equation(np.array(colors_plane2[0]), np.array(colors_plane2[1]), np.array(colors_plane2[2]))

    # Calculate distances to both planes
    distances1 = calculate_distance_to_plane(img_points, normal1, D1)
    distances2 = calculate_distance_to_plane(img_points, normal2, D2)

    # Calculate grayscale values based on distances
    ratio = distances1 / (distances1 + distances2)
    grayscale_values = ratio.reshape(img_array.shape[:2])

    # Normalize and convert to uint8
    grayscale_image = (grayscale_values * 255).astype(np.uint8)

    # Return the grayscale image
    return invert(Image.fromarray(grayscale_image))


def extract_k(img_array, color):
    img_array = np.array(img, dtype=float)

    # Calculate distances from each pixel to the specified color
    distances = calculate_distance_from_point(img_array, np.array(color))

    # Normalize distances to [0, 255]
    normalized_distances = (distances - distances.min()) / (distances.max() - distances.min()) * 255
    grayscale_image = normalized_distances.astype(np.uint8)

    # Return the grayscale image
    return invert(Image.fromarray(grayscale_image))

def extract_k2(img_array, color_a, color_b):
    # Convert colors to numpy arrays
    a = np.array(color_a, dtype=float)
    b = np.array(color_b, dtype=float)

    # Vector from A to B
    ab = b - a

    # Normalize AB for position calculation
    ab_normalized = ab / np.linalg.norm(ab)

    # Function to calculate distance and position
    def calculate_distance_and_position(pixel_color):
        # Vector from A to the current pixel color
        ac = pixel_color - a

        # Projection of AC on AB to find the position
        projection_length = np.dot(ac, ab_normalized)
        projection_vector = projection_length * ab_normalized

        # Calculate position as 0-255 along AB
        position = np.clip(projection_length / np.linalg.norm(ab), 0, 1) * 255

        # Distance from the pixel color to the AB line
        distance_vector = ac - projection_vector
        distance = np.linalg.norm(distance_vector)

        # Normalize distance based on some scale to fit into 0-255
        # Here, we'll assume the max possible distance fits into 0-255
        #max_distance = 255
        #distance_normalized = np.clip(distance / max_distance * 255, 0, 255)

        # Combine distance and position into a single value
        return position + (distance/2)

    # Apply the calculation to each pixel
    grayscale_values = np.apply_along_axis(calculate_distance_and_position, -1, img_array)

    # Normalize combined values to fit into 0-255
    grayscale_values_normalized = np.clip(grayscale_values, 0, 255).astype(np.uint8)

    # Convert to grayscale image
    grayscale_img = Image.fromarray(grayscale_values_normalized, mode='L')
    return grayscale_img


def remove_black(img_cmy, img_k):
    # Convert images to numpy arrays for processing
    arr_k = np.array(img_k)
    arr_cmy = np.array(img_cmy)

    # Set pixels in B to 0 where corresponding pixel in A is > 229 (90% of 255)
    arr_cmy[arr_k > 229] = 0

    # Convert the processed array back to an image
    return Image.fromarray(arr_cmy)

def stretch_levels(image, lower_percent, upper_percent):
    """
    Stretch the levels of a grayscale image.

    :param image: Pillow Image object in grayscale mode
    :param lower_percent: Lower bound percentage to map to 0
    :param upper_percent: Upper bound percentage to map to 255
    :return: Image object with stretched levels
    """
    if image.mode != 'L':
        raise ValueError('Image must be in grayscale mode')

    # Calculate input min and max based on percentages
    input_min = (255 * lower_percent) / 100
    input_max = (255 * upper_percent) / 100

    # Define output min and max
    output_min = 0
    output_max = 255

    # Linear transformation function
    def transform(value):
        return int((value - input_min) / (input_max - input_min) * (output_max - output_min) + output_min)

    # Apply transformation to all pixels
    for y in range(image.height):
        for x in range(image.width):
            value = image.getpixel((x, y))
            new_value = max(min(transform(value), 255), 0)  # Ensure new value is within 0-255
            image.putpixel((x, y), new_value)

    return image


PIL.Image.MAX_IMAGE_PIXELS = 933120000

color_c  = [ 38, 140, 165] # C  = cyan
color_cm = [ 36,  44,  79] # CM = blue
color_cy = [ 42, 109,  44] # CY = green
color_m  = [192,  37,  66] # M  = magenta
color_my = [185,  34,  31] # MY = red
color_y  = [201, 159,  61] # Y  = yellow
color_k  = [ 16,  17,  17] # K = black
color_w  = [201, 195, 188] # W = white

input_image_path = sys.argv[1]
# Load image and convert to numpy array
img = Image.open(input_image_path)
img_array = np.array(img, dtype=float)


#img_k = extract_k2(img_array, color_k, color_w)
#img_k.save('4p-k_.5.png')
#exit(0)

img_points = img_array.reshape(-1, 3)

img_k = extract_k(img_array, color_k)

img_c = extract_cmy(img_points, [color_c, color_cm, color_cy], [color_m, color_y, color_w])
img_m = extract_cmy(img_points, [color_m, color_cm, color_my], [color_c, color_y, color_w])
img_y = extract_cmy(img_points, [color_y, color_cy, color_my], [color_c, color_m, color_w])

#img_c = remove_black(img_c, img_k)
#img_m = remove_black(img_m, img_k)
#img_y = remove_black(img_y, img_k)

#img_c = stretch_levels(img_c, 30, 70)
#img_m = stretch_levels(img_m, 30, 70)
#img_y = stretch_levels(img_y, 30, 70)
#img_k = stretch_levels(img_k, 90, 95)

cmyk_image = Image.merge("CMYK", (img_c, img_m, img_y, img_k))

# Save the combined image as a CMYK TIFF
cmyk_image.save(sys.argv[2], 'TIFF')

# C 64%
# M 54%
# Y 42%
# K 89%


# 50/50/50/90

# cyan wavelength: 15.6805 -> Gaussian blur 7.8
