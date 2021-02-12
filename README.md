# XAI-CARLA-dataset
The purpose of this repository is for automated creation of dataset of various scenarios in CARLA towards explainability in Reinforcement Learning in AVs.

#### Tested with:<br>
Python: 3.7<br>
CARLA: 0.9.11

### Follow these steps to set up the env:
1. Get the latest release of v0.9.11 from the following link (preferable over cloning the master repo since new changes might break your environment (source:devs)): 
https://carla-releases.s3.eu-west-3.amazonaws.com/Windows/CARLA_0.9.11.zip

2. Unzip the folder to a desired directory.

3. Clone this repo in ..\CARLA_0.9.11\WindowsNoEditor\PythonAPI\

4. Preferably set up a virtual environment at ..\CARLA_0.9.11\WindowsNoEditor\venv. With conda>4.6, in your Anaconda prompt:<br>
   4.1. >> conda cd ..\CARLA_0.9.11\WindowsNoEditor\
   4.2. >> conda create -n venv python=3.7<br>
   4.3. >> conda activate venv<br>
   4.4. >> pip install -r PythonAPI/XAI-CARLA-dataset-master/requirements.txt<br>
   
5. To open CARLA, cmd: >> CarlaUE4.exe -quality-level=Low -carla-rpc-port=2000
 
6. From conda venv, run: >> python start.py

If the script runs, your CARLA environment is ready. 

### csv.py:
Using the lidar cloud points to detect the objects in the current FOV of the vehicle, the script serves the folowing purpose:
   1. At every 1 second of simulation time:
         - record the image pixels from camera-sensor
         - vehicle speed
         - vehicle steering angle
         - vehicle throttle position
         - list of objects in the FOV of the lidar
   2. Save as a .csv in data/explain.csv
Currently, the vehicle is spawaned at a random point in the map and managed by the 'auto-pilot' feature of the Traffic Manager (TM). Around 15 other vehicles are also spawned in 
the simulation.

### To-do:
- [ ] Add the MobileSSD object-detection module
- [ ] Integrate 'scenic' for scenario creation
- [ ] Visualize the vehicles in FOV and create bounding boxes around the objects (tentative, not needed but good for visualization)
- [ ] Create specific custom scenarios using 'scenic'
- [ ] Implement a RL agent
- [ ] Analyze control input of the RL agent vs the TM's 'auto-pilot' for a specific scenario
- [ ] Implement Grad-CAM to see which features in the scene were given importance in the camera image input
