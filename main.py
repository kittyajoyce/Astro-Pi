# import the multiple libraries needed
from logzero import logger, logfile     
from ephem import readtle, degree       
from picamera import PiCamera
from datetime import datetime, timedelta
from time import sleep
from pathlib import Path
import csv

# directory to file
# variable __file__ contains the path to the module imported
dir_path = Path(__file__).parent.resolve()      

# create and set a logfile name
logfile(dir_path / "jinro.log")

# latest TLE data for ISS(ZARYA) postition
name = "ISS (ZARYA)"
line1 = "1 25544U 98067A   20316.41516162  .00001589  00000+0  36499-4 0  9995"
line2 = "2 25544  51.6454 339.9628 0001882  94.8340 265.2864 15.49409479254842"

iss = readtle(name, line1, line2)
iss.compute()

# assign PiCamera to cam
cam = PiCamera()

# set resolution V1 camera
cam.resolution = (1296, 972)

# CSV file
def create_csv_file(data_file):
    # create a new CSV file and adding the header row
    with open(data_file, 'w') as f:
        writer = csv.writer(f)
        header = ("Time", "Photo Counter", "Latitude", "Longitude", "Temperature")
        writer.writerow(header)

def add_csv_data(data_file, data):
    # add a row of data from the while() loop to the data_file CSV
    with open(data_file, 'a') as f:
        writer = csv.writer(f)
        writer.writerow(data)

# return current lat/long to degrees
def get_latlon():
    iss.compute() 
    return (iss.sublat / degree, iss.sublong / degree)

# assign variables convert
def convert(angle):
    # convert ephem angle to EXIF appropriate representation
    degrees, minutes, seconds = (float(field) for field in str(angle).split(":"))
    exif_angle = f'{abs(degrees):.0f}/1,{minutes:.0f}/1,{seconds*10:.0f}/10'
    return degrees < 0, exif_angle

# capture image with lat/long EXIF tags
def capture(camera, image):
    # getting lat/long
    iss.compute()

    # convert lat/long to be used in the EXIF tags
    south, exif_latitude = convert(iss.sublat)
    west, exif_longitude = convert(iss.sublong)

    # set the EXIF tags specifying the current location
    camera.exif_tags['GPS.GPSLatitude'] = exif_latitude
    camera.exif_tags['GPS.GPSLatitudeRef'] = "S" if south else "N"
    camera.exif_tags['GPS.GPSLongitude'] = exif_longitude
    camera.exif_tags['GPS.GPSLongitudeRef'] = "W" if west else "E"

    # capture the image
    camera.capture(image)


# assign variable data_file
data_file = dir_path / "data.csv"

# initialise the CSV file
create_csv_file(data_file)

# initialise the photo_counter
photo_counter = 1

# assign variable start_time
start_time = datetime.now()

# assign variable now_time
now_time = datetime.now()

# assign variable i
i = 0

# run a loop for (almost) three hours
while (now_time < start_time + timedelta(minutes=178)):
    try:
    
        # get latitude and longitude
        lat, long = get_latlon()
        
        # update the variables
        data = (
            datetime.now(),
            photo_counter,
            lat,
            long
        )
        
        # add the data to the CSV file
        add_csv_data(data_file, data)
        
        # capture 4 images of same area
        for i in range(4):
            # assign variable image_file to the string
            image_file = dir_path / f"photo_{photo_counter:03d}.jpeg"
            
            # capture image using image_file as file name
            capture(cam, str(image_file))
            
            # update photo_counter
            photo_counter += 1
            
            # update logfile
            logger.info(f"iteration{photo_counter}")
        
        # time between each four images
        sleep(15)
        
        # update the current time
        now_time = datetime.now()
      
    # any errors logged in format
    except Exception as e:
        logger.error('{}: {})'.format(e.__class__.__name__, e))
