#!/usr/bin/env python

import glob
import os
import sys
import re
import pandas as pd

#STEP 1: run CARLA
# CarlaUE4.exe -quality-level=Low -carla-rpc-port=2000

#STEP 2: run a scenario in scenic and save the simulation log
# scenic ..\..\Scenic-master\examples\carla\Carla_Challenge\carlaChallenge3_dynamic.scenic --simulate --model scenic.simulators.carla.model --time 200 --param record C:\Vaibhav\AI_ParisSaclay\TER\CARLA_0.9.11\WindowsNoEditor\PythonAPI\XAI-CARLA-dataset\log\

#STEP 3: run the parser which converts the log file into text and then gets the vehicle state and objects in each frame
# python scenario.py -f C:\Vaibhav\AI_ParisSaclay\TER\CARLA_0.9.11\WindowsNoEditor\PythonAPI\XAI-CARLA-dataset\log\scenario1.log -a -s parsed\scenario1_replay.txt

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla
import argparse

#from show_recorder.py
def main():
    argparser = argparse.ArgumentParser(
        description=__doc__)
    argparser.add_argument(
        '--host',
        metavar='H',
        default='127.0.0.1',
        help='IP of the host server (default: 127.0.0.1)')
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=2000,
        type=int,
        help='TCP port to listen to (default: 2000)')
    argparser.add_argument(
        '-f', '--recorder_filename',
        metavar='F',
        default="test1.rec",
        help='recorder filename (test1.rec)')
    argparser.add_argument(
        '-a', '--show_all',
        action='store_true',
        help='show detailed info about all frames content')
    argparser.add_argument(
        '-s', '--save_to_file',
        metavar='S',
        help='save result to file (specify name and extension)')

    args = argparser.parse_args()

    try:
        client = carla.Client(args.host, args.port)
        client.set_timeout(60.0)
        if args.save_to_file:
            print('saving...')
            doc = open(args.save_to_file, "w+")
            doc.write(client.show_recorder_file_info(args.recorder_filename, args.show_all))
            doc.close()
        else:
            print(client.show_recorder_file_info(args.recorder_filename, args.show_all))
    finally:
        # Strip the multiline string, split into lines, then strip each line
        with open(r"parsed\scenario1_replay.txt", "r") as f:
            log = [line.rstrip('\n') for line in f]
        r_state = re.compile(r'\bVehicle animations\b')
        r_objects = re.compile(r'\bPositions\b')
        r_traffic = re.compile(r'\bState traffic lights\b')

        # get the vehicle state at each frame and store as a df
        steering = []
        throttle = []
        brake = []
        gear = []
        for i in range(len(log)):
            if r_state.findall(log[i]):
                state = log[i+1].split()
                steering.append(state[3])
                throttle.append(state[5])
                brake.append(state[7])
                gear.append(state[11])
        df = {'Steering': steering, 'Throttle': throttle, 'Brake': brake, 'Gear': gear}
        df = pd.DataFrame.from_dict(df)

        # get the objects in each frame and store in the df
        objects = []
        for i in range(len(log)):
            if r_objects.findall(log[i]):
                current = i
                count = 1
                objects_frame = []
                while not r_traffic.findall(log[current+count]):
                    state = log[current+count].split()
                    objects_frame.append(state)
                    count = count + 1
                objects.append(objects_frame)

        df['Objects'] = objects
        print(df.head())
        df.to_csv('parsed/scenario1.csv')

if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print('\ndone.')
