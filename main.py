from logzero import logger, logfile
from sense_hat import SenseHat
from ephem import readtle, degree
from picamera import PiCamera
from datetime import datetime, timedelta
from time import sleep
import random
from pathlib import Path
import csv

dir_path = Path(__file__).parent.resolve()

# Set a log file name
logfile(dir_path + "/teamname.log")

# Latest TLE data for ISS location
name = "ISS (ZARYA)"
line1 = "1 25544U 98067A   20316.41516162  .00001589  00000+0  36499-4 0  9995"
line2 = "2 25544  51.6454 339.9628 0001882  94.8340 265.2864 15.49409479254842"
iss = readtle(name, line1, line2)

# Set up Sense Hat
sh = SenseHat()

# Set up camera
cam = PiCamera()
cam.resolution = (1296, 972)

def create_csv_file(data_file):
    """Create a new CSV file and add the header row"""
    with open(data_file, 'w') as f:
        writer = csv.writer(f)
        header = ("Date/time", "Temperature", "Humidity")
        writer.writerow(header)

def add_csv_data(data_file, data):
    """Add a row of data to the data_file CSV"""
    with open(data_file, 'a') as f:
        writer = csv.writer(f)
        writer.writerow(data)

def get_latlon():
    """Return the current latitude and longitude, in degrees"""
    iss.compute() # Get the lat/long values from ephem
    return (iss.sublat / degree, iss.sublong / degree)

def convert(angle):
    """
    Convert an ephem angle (degrees, minutes, seconds) to
    an EXIF-appropriate representation (rationals)
    e.g. '51:35:19.7' to '51/1,35/1,197/10'
    Return a tuple containing a boolean and the converted angle,
    with the boolean indicating if the angle is negative.
    """
    degrees, minutes, seconds = (float(field) for field in str(angle).split(":"))
    exif_angle = f'{abs(degrees):.0f}/1,{minutes:.0f}/1,{seconds*10:.0f}/10'
    return degrees < 0, exif_angle

def capture(camera, image):
    """Use `camera` to capture an `image` file with lat/long EXIF data."""
    iss.compute() # Get the lat/long values from ephem

    # convert the latitude and longitude to EXIF-appropriate representations
    south, exif_latitude = convert(iss.sublat)
    west, exif_longitude = convert(iss.sublong)

    # set the EXIF tags specifying the current location
    camera.exif_tags['GPS.GPSLatitude'] = exif_latitude
    camera.exif_tags['GPS.GPSLatitudeRef'] = "S" if south else "N"
    camera.exif_tags['GPS.GPSLongitude'] = exif_longitude
    camera.exif_tags['GPS.GPSLongitudeRef'] = "W" if west else "E"

    # capture the image
    camera.capture(image)


# initialise the CSV file
data_file = dir_path + "/data.csv"
create_csv_file(data_file)
# initialise the photo counter
photo_counter = 1
# record the start and current time
start_time = datetime.now()
now_time = datetime.now()
# run a loop for (almost) three hours
while (now_time < start_time + timedelta(minutes=178)):
    try:
        humidity = round(sh.humidity, 4)
        temperature = round(sh.temperature, 4)
        # get latitude and longitude
        latitude, longitude = get_latlon()
        # Save the data to the file
        data = (
            datetime.now(),
            photo_counter,
            humidity,
            temperature,
            latitude,
            longitude
        )
        add_csv_data(data_file, data)
        # capture image
        image_file = f"{dir_path}/photo_{photo_counter:03d}.jpg"
        capture(cam, image_file)
        logger.info(f"iteration {photo_counter}")
        photo_counter += 1
        sleep(30)
        # update the current time
        now_time = datetime.now()
    except Exception as e:
        logger.error('{}: {})'.format(e.__class__.__name__, e))
