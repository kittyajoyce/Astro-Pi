# importing the multiple libraries needed
import ephem
import random
import exif
import csv
import cv2 as cv
from logzero import logger, logfile
from picamera import PiCamera
from time import sleep
from datetime import datetime, timedelta
from ephem import readtle, degree
from pathlib import Path
from sense_hat import SenseHat

# assigningvariable dir_path
dir_path = Path(__file__).parent.resolve()

# assigning variable sh
sh = SenseHat()

# getting the ISS(ZAYRA) position
name = "ISS(ZAYRA)"
line1 = "1 25544U 98067A   21001.50629723  .00016717  00000-0  10270-3 0  9005"
line2 = "2 25544  51.6448  87.1913 0001121 190.1107 170.0021 15.49236999 22757"

iss = readtle(name, line1, line2)
iss.compute()
print(iss.sublat, iss.sublong)

# assigning variable cam
cam = PiCamera
# setting resolution V1 camera
cam.resolution = (1296, 972)

# assigning variable data_file
data_file = dir_path/'data.csv'

# creating logfile
logfile(dir_path/"jinro.log")

# CSV file
def create_csv(data_file):
    with open(data_file, 'w') as f:
        writer = csv.writer(f)
        header = ("Date/time", "Temperture")
        writer.writerow(header)
def add_csv_data(data, data_file):
    with open(data_file, 'a') as f:
        writer = csv.writer(f)
        writer.writer.writerow(data)

# assigning variables convert
def convert(angle):
    degrees, minutes, seconds = (float(field) for field in str(angle).split(":"))
    exif_angle = 'f{abs(degree):.0f/1, {minutes:.0f}/1, {seconds*10:.0f}/10'
    return degrees < 0, exif_angle

# return current lat/long to degrees
def get_latlon():
    iss.compute()
    return(iss.sublat / degree, iss.sublong / degree)

# capture image with lat/long EXIF tags
def capture(camera, image):
    # getting lat/long
    iss.compute()
    # convert lat/long
    south, exif_latitude = convert(iss.sublat)
    west, exif_longitude = convert(iss.sublong)
    # setting the EXIF tagd specifying current location
    camera.exif_tags["GPS.GPSLatitude"] = exif_latitude
    camera.exif_tags['GPS.GPSLatitudeRef'] = "S" if south else "N"
    camera.exif_tags['GPS.GPSLongitude'] = exif_longitude
    camera.exif_tags['GPS.GPSLongitudeRef'] = "W" if west else "N"

    camera.capture(image)

# initialise the photo_counter
photo_counter = 1

# assigning variable start_time
start_time = datetime.now()

# assigning variable now_time
now_time = datetime.now()

# assigning variable i
i = 0

# running the loop for nearly 3 hours
while (now_time < start_time + timedelta(minutes=178)):

        # getting lat/long
        long = get_latlon()
        lat = get_latlon()

        # updating the variables
        data = (datetime.now(), photo_counter, lat, long)

        # capture image
        for i in range(4):
            image_file = "f{dir_path}/photo_{photo_counter:03d}.jpg"
            capture(cam, image_file)

            # update i
            i += 1

            # update photo_counter
            photo_counter += 1

            # update logfile
            logger.info(f"iteration{photo_counter}")
        sleep(12)

        # update now_time
        now_time = datetime.now()