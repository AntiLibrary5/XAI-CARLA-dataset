"""
- Runs an ego vehicle on autopilot
- A lidar is used to get the object IDs in fov
- A camera is spawned to capture the camera view
- The objects are stored in a list
- The objects, vehicle control, and camera image pixels are stored in a df
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
os.system
import PIL
import PIL.Image as Image
import time
import argparse
import pandas as pd

# client creation
client = carla.Client('127.0.0.1', 2000)
client.set_timeout(10.0)  # seconds

# change map. note that this replaces the current world (is destroyed) with a new one
# world = client.load_world('Town02')

# connect to the current world
world = client.get_world()

# fixed time-step and synchronous mode ON
#TM needs to be in synchronous mode too
traffic_manager = client.get_trafficmanager(8000)
traffic_manager.set_synchronous_mode(True)

# set weather
# only intervenes with sensor.camera.rgb. Neither affect the actor's physics nor other sensors
weather = carla.WeatherParameters(
    cloudiness=80.0,
    precipitation=90.0,
    sun_altitude_angle=30.0)
world.set_weather(weather)

IM_WIDTH = 64
IM_HEIGHT = 64

font = cv2.FONT_HERSHEY_SIMPLEX
bottomLeftCornerOfText = (50,250)
fontScale = 0.5
fontColor = (255,255,255)
lineType = 2

#class adapted from PythonAPI/examples/synchronous_mode.py
#best implementation eeded to sunchronize the output different sensors
class CarlaSyncMode(object):
    """
    Context manager to synchronize output from different sensors. Synchronous
    mode is enabled as long as we are inside this context

        with CarlaSyncMode(world, sensors) as sync_mode:
            while True:
                data = sync_mode.tick(timeout=1.0)

    """

    def __init__(self, world, *sensors, **kwargs):
        self.world = world
        self.sensors = sensors
        self.frame = None
        self.delta_seconds = 1.0 / kwargs.get('fps', 20)
        self._queues = []
        self._settings = None

    def __enter__(self):
        self._settings = self.world.get_settings()
        self.frame = self.world.apply_settings(carla.WorldSettings(
            no_rendering_mode=False,
            synchronous_mode=True,
            fixed_delta_seconds=self.delta_seconds))

        def make_queue(register_event):
            q = queue.Queue()
            register_event(q.put)
            self._queues.append(q)

        make_queue(self.world.on_tick)
        for sensor in self.sensors:
            make_queue(sensor.listen)
        return self

    def tick(self, timeout):
        self.frame = self.world.tick()
        data = [self._retrieve_data(q, timeout) for q in self._queues]
        assert all(x.frame == self.frame for x in data)
        return data

    def __exit__(self, *args, **kwargs):
        self.world.apply_settings(self._settings)

    def _retrieve_data(self, sensor_queue, timeout):
        while True:
            data = sensor_queue.get(timeout=timeout)
            if data.frame == self.frame:
                return data

#function to display the camera view and vehicle control on
#a CV window
def process_img(image, text):
    #image.save_to_disk("input_image\im.jpg")
    i = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
    i2 = i.reshape((IM_WIDTH, IM_HEIGHT, 4))
    cv2.putText(i2, text, bottomLeftCornerOfText, font, fontScale, (255, 255, 255), lineType, cv2.LINE_AA)
    cv2.imshow("", i2)
    cv2.waitKey(1)
    return i2/255.0

#maintain spawning of multiple vehicles
class SpawnCar(object):
    def __init__(self, location, rotation, filter="vehicle.*", autopilot = False, velocity = None):
        self._filter = filter
        self._transform = carla.Transform(location, rotation)
        self._autopilot = autopilot
        self._velocity = velocity
        self._actor = None
        self._world = None

    def spawn(self, world):
        self._world = world
        actor_BP = world.get_blueprint_library().filter(self._filter)[0]
        self._actor = world.spawn_actor(actor_BP, self._transform)
        self._actor.set_autopilot(True)

        return self._actor

    def destroy(self):
        if self._actor != None:
            self._actor.destroy()

#NOTE: env becomes heavy by spwaning multiple vehicles
#decrease the number if need be
CarList = [
    SpawnCar(carla.Location(x=83,  y= -40, z=5),  carla.Rotation(yaw=-90),  filter= "*lincoln*", autopilot=True),
    SpawnCar(carla.Location(x=83,  y= -30, z=3),  carla.Rotation(yaw=-90),  filter= "*a2*", autopilot=True),
    SpawnCar(carla.Location(x=83,  y= -20, z=3),  carla.Rotation(yaw=-90),  filter= "*etron*", autopilot=True),
    SpawnCar(carla.Location(x=120, y= -3.5, z=2), carla.Rotation(yaw=+180), filter= "*isetta*", autopilot=True),
    SpawnCar(carla.Location(x=100, y= -3.5, z=2), carla.Rotation(yaw=+180), filter= "*etron*", autopilot=True),
    SpawnCar(carla.Location(x=140, y= -3.5, z=2), carla.Rotation(yaw=+180), filter= "*model3*", autopilot=True),
    SpawnCar(carla.Location(x=160, y= -3.5, z=2), carla.Rotation(yaw=+180), filter= "*impala*", autopilot=False),
    SpawnCar(carla.Location(x=180, y= -3.5, z=2), carla.Rotation(yaw=+180), filter= "*a2*", autopilot=True),
    SpawnCar(carla.Location(x=60,  y= +6, z=2),   carla.Rotation(yaw=+00),  filter= "*model3*", autopilot=True),
    SpawnCar(carla.Location(x=80,  y= +6, z=2),   carla.Rotation(yaw=+00),  filter= "*etron*", autopilot=True),
    SpawnCar(carla.Location(x=100, y= +6, z=2),   carla.Rotation(yaw=+00),  filter= "*mustan*", autopilot=True),
    SpawnCar(carla.Location(x=120, y= +6, z=2),   carla.Rotation(yaw=+00),  filter= "*lincoln*", autopilot=True),
    SpawnCar(carla.Location(x=140, y= +6, z=2),   carla.Rotation(yaw=+00),  filter= "*impala*", autopilot=True),
    SpawnCar(carla.Location(x=160, y= +6, z=2),   carla.Rotation(yaw=+00),  filter= "*prius*", autopilot=True),
    SpawnCar(carla.Location(x=234, y= +20,z=2),   carla.Rotation(yaw=+90),  filter= "*dodge*", autopilot=True),
    SpawnCar(carla.Location(x=234, y= +40,z=2),   carla.Rotation(yaw=+90),  filter= "*isetta*", autopilot=True),
    SpawnCar(carla.Location(x=234, y= +60,z=2),   carla.Rotation(yaw=+90),  filter= "*impala*", autopilot=True),
    SpawnCar(carla.Location(x=234, y= +80,z=2),   carla.Rotation(yaw=+90),  filter= "*tt*", autopilot=True),
    SpawnCar(carla.Location(x=243, y= -40,z=2),   carla.Rotation(yaw=-90),  filter= "*etron*", autopilot=True),
    SpawnCar(carla.Location(x=243, y= -20,z=2),   carla.Rotation(yaw=-90),  filter= "*mkz2017*", autopilot=True),
    SpawnCar(carla.Location(x=243, y= +00,z=2),   carla.Rotation(yaw=-90),  filter= "*mustan*", autopilot=True),
    SpawnCar(carla.Location(x=243, y= +20,z=2),   carla.Rotation(yaw=-90),  filter= "*dodge*", autopilot=True),
    SpawnCar(carla.Location(x=243, y= +40,z=2),   carla.Rotation(yaw=-90),  filter= "*isetta*", autopilot=True),
    SpawnCar(carla.Location(x=243, y= +60,z=2),   carla.Rotation(yaw=-90),  filter= "*a2*", autopilot=True),
    SpawnCar(carla.Location(x=243, y= +80,z=2),   carla.Rotation(yaw=-90),  filter= "*tt*", autopilot=True),
    SpawnCar(carla.Location(x=243, y=+100,z=2),   carla.Rotation(yaw=-90),  filter= "*etron*", autopilot=True),
    SpawnCar(carla.Location(x=243, y=+120,z=2),   carla.Rotation(yaw=-90),  filter= "*wrangler_rubicon*", autopilot=True),
    SpawnCar(carla.Location(x=243, y=+140,z=2),   carla.Rotation(yaw=-90),  filter= "*c3*", autopilot=True)]

#helper function to spawn vehicles
def spawn_prop_vehicles(world):
    for car in CarList:
        car.spawn(world)

#helper function to destroy vehicles
def destroy_prop_vehicles():
    for car in CarList:
        car.destroy()

#wait for spwaning to finish
def wait(world, frames=100, queue = None, slist = None):
    for i in range(0, frames):
        world.tick()

        if queue != None and slist != None:
            try:
                for _i in range (0, len(slist)):
                    s_frame = queue.get(True, 1.0)
            except Empty:
                print("Some of the sensor information is missed")

def main():
    print('Initializing...')
    # maintain a list of actors
    actor_list = []
    frame_list = []
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

        # spawn a RGB camera and attach it to the vehicle
        camera_bp = blueprint_library.find('sensor.camera.rgb')
        # change the dimensions of the image
        camera_bp.set_attribute('image_size_x', f'{IM_WIDTH}')
        camera_bp.set_attribute('image_size_y', f'{IM_HEIGHT}')
        camera_bp.set_attribute('fov', '110')
        relative_transform = carla.Transform(carla.Location(x=1.5, z=2.4))  # relative to vehicle
        camera_rgb = world.spawn_actor(camera_bp, relative_transform, attach_to=vehicle)  #carla.AttachmentType.Rigid)
        actor_list.append(camera_rgb)

        # spawn a SS camera and attach it to the vehicle
        camera_semseg = world.spawn_actor(
            blueprint_library.find('sensor.camera.semantic_segmentation'),
            carla.Transform(carla.Location(x=-5.5, z=2.8), carla.Rotation(pitch=-15)),
            attach_to=vehicle)
        actor_list.append(camera_semseg)

        # spawn a lidar
        lidar_bp = blueprint_library.find('sensor.lidar.ray_cast_semantic')
        lidar_bp.set_attribute('channels', '64')
        lidar_bp.set_attribute('points_per_second', '500000')
        lidar_bp.set_attribute('range', '100')
        lidar_bp.set_attribute('upper_fov', '10.0')
        lidar_bp.set_attribute('lower_fov', '-90.0')
        relative_transform = carla.Transform(carla.Location(x=1.5, z=2.4))  # relative to vehicle
        lidar = world.spawn_actor(lidar_bp, relative_transform, attach_to=vehicle)
        actor_list.append(lidar)

        #spawn additional vehicles_list
        #note memory intensive
        spawn_prop_vehicles(world)
        print('Spawning vehicles...')
        wait(world, 30)
        print('Spawned.')
        print('Simulation started...')
        # Create a synchronous mode context.
        with CarlaSyncMode(world, camera_rgb, camera_semseg, lidar, fps=30) as sync_mode:
            while True:
                # Advance the simulation and wait for the data.
                snapshot, image_rgb, image_semseg, lidar_data = sync_mode.tick(timeout=10.0)

                fps = round(1.0 / snapshot.timestamp.delta_seconds)

                world_frame = world.get_snapshot().frame

                #assert image_rgb.frame == lidar_data.frame == world_frame

                #get a top view of the vehicle
                transform = vehicle.get_transform()
                spectator.set_transform(carla.Transform(transform.location + carla.Location(z=20),
                                                        carla.Rotation(pitch=-90)))

                #get the Speed, Steer and Throttle input
                vehVelocity = round((3.6 * math.sqrt(vehicle.get_velocity().x**2 + vehicle.get_velocity().y**2 + vehicle.get_velocity().z**2)), 2)
                vehThrottle = round(vehicle.get_control().throttle, 2)
                vehSteering = round(vehicle.get_control().steer, 2)

                #to print on CV window
                text = "Speed : " + str(vehVelocity) + " Throttle : " + str(vehThrottle) + " Steering : " + str(vehSteering)

                #process lidar data
                lidar_data = np.frombuffer(lidar_data.raw_data, dtype=np.dtype([
                    ('x', np.float32), ('y', np.float32), ('z', np.float32),
                    ('CosAngle', np.float32), ('ObjIdx', np.int32), ('ObjTag', np.uint32)]))

                #get the IDs of objects in FOV of lidar
                obj_idx = list(set(lidar_data['ObjIdx']))
                #convert to int
                obj_idx = [int(i) for i in obj_idx]
                #remove the ego vehicle from the list
                obj_idx.remove(vehicle.id)
                #get the Actor.List object for the object IDs in FOV of the lidar
                actors_present = world.get_actors(obj_idx)

                im_pixels = np.frombuffer(image_rgb.raw_data, dtype=np.dtype("uint8"))#np.array(image_rgb.raw_data)

                world_snapshot = world.get_snapshot()
                c = world_snapshot.timestamp.frame

                if c%10 == 0:
                    current_frame = {'image': im_pixels, 'vel': vehVelocity, 'steer_pos': vehSteering,
                     'throttle_pos': vehThrottle, 'objects': actors_present}
                    frame_list.append(current_frame)

                #CV window for camera view
                #process_img(image_rgb, text)

                #for bounding boxes (need some work)
                """debug = world.debug
                for actor in actors_present:
                    #actual_actor = world.get_actor(actor)
                    debug.draw_box(carla.BoundingBox(actor.get_transform().location, carla.Vector3D(0.5, 0.5, 2)),
                        actor.get_transform().rotation, 0.05, carla.Color(255, 0, 0, 0), 0)"""

    finally:
        #destroy sensors
        print('Destroying actors...')
        for actor in actor_list:
            actor.destroy()

        #destroy vehicles
        destroy_prop_vehicles()
        print('Done.')
        print('Creating CSV...')
        #create df from frames list
        df_explain = pd.DataFrame(frame_list, columns=['image', 'vel', 'steer_pos', 'throttle_pos', 'objects'])
        #to avoid truncation of image-pixel array in CSV
        #np.set_printoptions(threshold=sys.maxsize)
        #save df as csv
        df_explain.to_csv('data/explain.csv',sep=',')
        print('Done.')
        print('Goodbye.')

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('User interrupt. Simulation ended.')
