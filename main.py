from logzero import logger, logfile
from ephem import readtle, degree
from picamera import PiCamera
from datetime import datetime, timedelta
from time import sleep
import random
from pathlib import Path
import csv
import cv2 as cv

dir_path = Path(__file__).parent.resolve()

# Set a log file name
logfile(dir_path + /"jinro.log")

# Latest TLE data for ISS location
name = "ISS (ZARYA)"
line1 = "1 25544U 98067A   20316.41516162  .00001589  00000+0  36499-4 0  9995"
line2 = "2 25544  51.6454 339.9628 0001882  94.8340 265.2864 15.49409479254842"

iss = readtle(name, line1, line2)
iss.compute()

# Set up camera
cam = PiCamera()
# Setting resolution V1 camera
cam.resolution = (1296, 972)

# CSV file
def create_csv_file(data_file):
    # Create a new CSV file and add the header row
    with open(data_file, 'w') as f:
        writer = csv.writer(f)
        header = ("Date/time", "Temperature")
        writer.writerow(header)

def add_csv_data(data_file, data):
    # Add a row of data to the data_file CSV
    with open(data_file, 'a') as f:
        writer = csv.writer(f)
        writer.writer.writerow(data)


# assigning variables convert
def convert(angle):
    degrees, minutes, seconds = (float(field) for field in str(angle).split(":"))
    exif_angle = f'{abs(degrees):.0f}/1,{minutes:.0f}/1,{seconds*10:.0f}/10'
    return degrees < 0, exif_angle

# return current lat/long to degrees
def get_latlon():
    iss.compute() 
    return (iss.sublat / degree, iss.sublong / degree)

# capture image with lat/long EXIF tags
def capture(camera, image):
    # getting lat/long
    iss.compute()

    # convert lat/long
    south, exif_latitude = convert(iss.sublat)
    west, exif_longitude = convert(iss.sublong)

    # set the EXIF tags specifying the current location
    camera.exif_tags['GPS.GPSLatitude'] = exif_latitude
    camera.exif_tags['GPS.GPSLatitudeRef'] = "S" if south else "N"
    camera.exif_tags['GPS.GPSLongitude'] = exif_longitude
    camera.exif_tags['GPS.GPSLongitudeRef'] = "W" if west else "E"

    # capture the image
    camera.capture(image)


# assigning variable data_file
data_file = dir_path/"data.csv"

# initialise the CSV file
create_csv_file(data_file)

# initialise the photo_counter
photo_counter = 1

# rassigning variable start_time
start_time = datetime.now()

#assigning variable now_time
now_time = datetime.now()

# assigning variable i
i = 1

# run a loop for (almost) three hours
while (now_time < start_time + timedelta(minutes=178)):
    '''try:'''
    
        # get latitude and longitude
        lat, long = get_latlon()
        
        # Save the data to the file
        data = (
            datetime.now(),
            photo_counter,
            lat,
            long
        )
        
        add_csv_data(data_file, data)
        
        # capture images
        for i in range(4):
            image_file = f"{dir_path}/photo_{photo_counter:03d}.jpg"
            capture(cam, image_file)
            
            # update i
            i += 1
            
            # update photo_counter
            photo_counter += 1
            
            # update logfile
            logger.info(f"iteration{photo_counter}")
            
        sleep(12)
        
        # update the current time
        now_time = datetime.now()
        
    '''except Exception as e:
        logger.error('{}: {})'.format(e.__class__.__name__, e))'''
