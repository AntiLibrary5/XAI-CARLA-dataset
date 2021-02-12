"""
A basic start script to verify your environment
"""

# Import the neccesary libraries
import glob
import os
import sys

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

try:
    import queue
except ImportError:
    import Queue as queue

import carla
import random
import time
import numpy as np
import cv2
import math
#!/usr/bin/env python
from subprocess import call
os.system
import PIL
import PIL.Image as Image
import time
import argparse

# client creation
client = carla.Client('127.0.0.1', 2000)
client.set_timeout(10.0)  # seconds

# change map. note that this replaces the current world (is destroyed) with a new one
# world = client.load_world('Town02')

# connect to the current world
world = client.get_world()

# fixed time-step and synchronous mode ON
settings = world.get_settings()
traffic_manager = client.get_trafficmanager(8000)
traffic_manager.set_synchronous_mode(True)
synchronous_master = True
settings.fixed_delta_seconds = 0.1
settings.synchronous_mode = True
world.apply_settings(settings)

# We create the sensor queue in which we keep track of the information
# already received. This structure is thread safe and can be
# accessed by all the sensors callback concurrently without problem.
sensor_queue = queue.Queue()

# set weather
# only intervenes with sensor.camera.rgb. Neither affect the actor's physics nor other sensors
weather = carla.WeatherParameters(
    cloudiness=80.0,
    precipitation=90.0,
    sun_altitude_angle=30.0)
world.set_weather(weather)

IM_WIDTH = 300
IM_HEIGHT = 300

font = cv2.FONT_HERSHEY_SIMPLEX
bottomLeftCornerOfText = (50,250)
fontScale = 0.5
fontColor = (255,255,255)
lineType = 2

def process_img(image, text):
    #image.save_to_disk("input_image\im.jpg")
    i = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
    i2 = i.reshape((IM_WIDTH, IM_HEIGHT, 4))
    cv2.putText(i2, text, bottomLeftCornerOfText, font, fontScale, (255, 255, 255), lineType, cv2.LINE_AA)
    cv2.imshow("", i2)
    cv2.waitKey(1)
    return i2/255.0

def main():
    # maintain a list of actors
    actor_list = []

    try:

        # get the list of blueprints of all actors
        blueprint_library = world.get_blueprint_library()

        # find the blueprint for a model 3
        vehicle_bp = random.choice(blueprint_library.filter('model3'))
        vehicle_bp.set_attribute('color', '255,0,0')
        # spawning a vehicle
        transform = random.choice(world.get_map().get_spawn_points())
        #transform = carla.Transform(carla.Location(x=230, y=195, z=0), carla.Rotation(yaw=180))
        vehicle = world.spawn_actor(vehicle_bp, transform)
        actor_list.append(vehicle)
        vehicle.set_autopilot(True)

        spectator = world.get_spectator()

        # spawn a camera and attach it to the vehicle
        camera_bp = blueprint_library.find('sensor.camera.rgb')
        #camera_bp = blueprint_library.find('sensor.camera.semantic_segmentation')
        #camera_bp.set_attribute('sensor_tick', '1.0')
        # change the dimensions of the image
        camera_bp.set_attribute('image_size_x', f'{IM_WIDTH}')
        camera_bp.set_attribute('image_size_y', f'{IM_HEIGHT}')
        camera_bp.set_attribute('fov', '110')
        relative_transform = carla.Transform(carla.Location(x=1.5, z=2.4))  # relative to vehicle
        camera = world.spawn_actor(camera_bp, relative_transform, attach_to=vehicle)  #carla.AttachmentType.Rigid)
        actor_list.append(camera)
        camera.listen(lambda data: sensor_queue.put(data))

        try:
            counter = 0
            while True:
                world.tick()

                transform = vehicle.get_transform()
                spectator.set_transform(carla.Transform(transform.location + carla.Location(z=20),
                                                        carla.Rotation(pitch=-90)))

                vehVelocity = round((3.6 * math.sqrt(vehicle.get_velocity().x**2 + vehicle.get_velocity().y**2 + vehicle.get_velocity().z**2)), 2)
                vehThrottle = round(vehicle.get_control().throttle, 2)
                vehSteering = round(vehicle.get_control().steer, 2)

                text = "Speed : " + str(vehVelocity) + " Throttle : " + str(vehThrottle) + " Steering : " + str(vehSteering)

                image = sensor_queue.get(True, 1.0)
                process_img(image, text)

        except KeyboardInterrupt:
            pass

    finally:
        print('destroying actors \n')
        for actor in actor_list:
            actor.destroy()

        print('Settings \n')
        settings = world.get_settings()
        settings.synchronous_mode = False
        world.apply_settings(settings)

        print('done.')


if __name__ == '__main__':
    main()
