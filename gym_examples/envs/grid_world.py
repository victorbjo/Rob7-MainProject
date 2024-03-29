import gym
from gym import spaces
import pygame
import numpy as np
import random
from .envTools import *
class GridWorldEnv(gym.Env):
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 4}

    def __init__(self, render_mode='human', size = 6):
        self.fail_battery = 0
        self.fail_collision = 0
        self.fail_longEpisode = 0
        self.fail_noChange = 0
        self.success = 0
        self.episodeFailed = False
        self.failsInARow = 0
        self.episodeLength = 0
        self.size = size  # The size of the square grid
        self.window_size = 512  # The size of the PyGame window
        self.pixSize = self.window_size / self.size
        self.numOfTurtles = 3 
        self.numOfTargets = 3
        self.numOfChargingStations = 1
        self.spawnableSpace = []
        self.turtles : list[Turtle] = []
        self.targets : list[WorkStation] = []
        self.chargingStations : list[ChargingStation] = []
        self.observation_space = spaces.Dict({})
        for i in range(self.numOfTurtles):
            self.turtles.append(Turtle(i+1, self.size))
            self.observation_space["agent" + str(i)] = spaces.Box(low=np.array([0, 0, 0, 0]), high=np.array([size-1, size-1, 100, 5]), dtype=int)
        for i in range(self.numOfTargets):
            self.targets.append(WorkStation(i+1, self.size))
            self.observation_space["target" + str(i)] = spaces.Box(low=np.array([0, 0, 0,]), high=np.array([size-1, size-1, 5]), dtype=int)
        for i in range(self.numOfChargingStations):
            self.chargingStations.append(ChargingStation(self.size))
            self.observation_space["charging_station" + str(i)] = spaces.Box(0, size - 1, shape=(2,), dtype=int)
        for x in range(size):
            for y in range(size):
                self.spawnableSpace.append([x,y])
        # Observations are dictionaries with the agent's and the target's location.
        # Each location is encoded as an element of {0, ..., `size`}^2, i.e. MultiDiscrete([size, size]).
        #"agent": spaces.Box(low=np.array([0, 0, 0, 1]), high=np.array([size-1, size-1, 100, 5]), dtype=int),  
        #We have 4 actions, corresponding to "right", "up", "left", "down", "right"
        actionSpaceArray = []
        for i in range(self.numOfTurtles):
            actionSpaceArray.append(5)
        #self.action_space = spaces.MultiDiscrete(actionSpaceArray)
        self.action_space = spaces.MultiDiscrete(actionSpaceArray)
        """
        The following dictionary maps abstract actions from `self.action_space` to 
        the direction we will walk in if that action is taken.
        I.e. 0 corresponds to "right", 1 to "up" etc.
        # """

        """ 8 directions action space
        self._action_to_direction = {
            0: np.array([1, 0]),
            1: np.array([1, 1]),
            2: np.array([0, 1]),
            3: np.array([-1, 1]),
            4: np.array([-1, 0]),
            5: np.array([-1, -1]),
            6: np.array([0, -1]),
            7: np.array([1, -1]),
        }"""


        assert render_mode is None or render_mode in self.metadata["render_modes"]
        self.render_mode = render_mode

        """
        If human-rendering is used, `self.window` will be a reference
        to the window that we draw to. `self.clock` will be a clock that is used
        to ensure that the environment is rendered at the correct framerate in
        human-mode. They will remain `None` until human-mode is used for the
        first time.
        """
        self.window = None
        self.clock = None

    def _get_obs(self):
        obs = {}
        for i in range(self.numOfTurtles):
            obs["agent" + str(i)] = self.turtles[i].getState()
        for i in range(self.numOfTargets):
            obs["target" + str(i)] = self.targets[i].getState()
        for i in range(self.numOfChargingStations):
            obs["charging_station" + str(i)] = self.chargingStations[i].location
        return obs

    def _get_info(self):
        return {
            "distance": np.linalg.norm(
                self.turtles[0].location[0] - self.targets[0].location[0]
            )
        }

    def reset(self):
        a  = self.spawnableSpace.copy()
        self.episodeFailed = False
        if self.episodeFailed: 
            self.failsInARow += 1
            if self.failsInARow > 3:
                self.episodeFailed = False
                print("Too many fails in a row, resetting environment")
                return self.reset()
            for turtle in self.turtles:
                turtle.restart()
            for target in self.targets:
                target.taskCompleted = False
        else:
            self.failsInARow = 0
            #print("Success")
            for turtle in self.turtles:
                turtle.reset(a)
                turtle.origLoc = turtle.location.copy()
            for target in self.targets:
                target.reset(a)
            for chargingStation in self.chargingStations:
                chargingStation.reset(a)
        self.episodeLength = 0
        observation = self._get_obs()
        info = self._get_info()
        self.episodeFailed = False
        if self.render_mode == "human":
            pass
            #self._render_frame()
        return observation

    def step(self, action):
        self.episodeLength += 1

        #Terminate with low rewards if
        #1. One turtle is dead
        #2. Two turtles collide

        #Terminate with high rewards if
        #1. All targets have been met

        #General positive reward if
        #1. One turtle is closer to the target or charging station
        #2. Turtle is standing still 

        #General negative reward if
        #1. One turtle is further away from the target and battery station
        #2. Turtle is driving without a target
        #3. Turtle is standing still and battery is low or target is available
        #4. Turtle is standing still on charging station with full battery
        terminated = False
        reward = 0
        #Movement of turtles
        for idx, turtle in enumerate(self.turtles):
            turtle.move(action[idx])

        #Check if robot moves closer to target
        tempReward = 0
        for turtle in self.turtles:
            turtleReward = 0
            #Check if turtle driving towards target
            turtleHasTask = False
            '''
            for target in self.targets:
                if turtle.battery > turtle.lowBattery and turtle.type == target.type:
                    if target.taskCompleted == False:
                        turtleHasTask = True
                    if manhattenDist(turtle.location, target.location) < manhattenDist(turtle.oldLoc, target.location):
                        if target.taskCompleted is False:
                            turtleReward += 0.1
                    else:
                        if target.taskCompleted is False:
                            #reward -= 10
                            pass
            '''


            #Check if turtle reaches target
            for target in self.targets:
                if equal(turtle.location, target.location):
                    if turtle.type == target.type and target.taskCompleted == False and turtle.battery > turtle.lowBattery:
                        target.taskCompleted = True
                        turtleReward += 1
                        tempLength = self.episodeLength-5
                        turtleReward -= tempLength/50
                    else:
                        turtleReward -= 0.1
                        pass
                else:
                    #Check if turtle is driving closer to the goal
                    if turtle.battery > turtle.lowBattery and turtle.type == target.type:
                        if target.taskCompleted == False:
                            turtleHasTask = True
                        if manhattenDist(turtle.location, target.location) < manhattenDist(turtle.oldLoc, target.location):
                            if target.taskCompleted is False:
                                turtleReward += 0.8
                        else:
                            if target.taskCompleted is False:
                                turtleReward -= 1
                                pass
            
            #Penalize if turtle is driving without a task
            if turtleHasTask is False and turtle.battery > turtle.lowBattery:
                if equal(turtle.location, turtle.oldLoc):
                    turtleReward += 1
                else:
                    turtleReward -= 1
                    #turtleReward -= turtle.lowBattery/turtle.battery
                    pass
            
            #Check if turtle moves closer to charging station
            if (turtleHasTask or turtle.battery < turtle.lowBattery) and equal(turtle.location, turtle.oldLoc):
                #turtleReward -= 0.8
                pass

            #Check if turtle reaches charging station
            for chargingStation in self.chargingStations:
                if equal(turtle.location, chargingStation.location):
                    #print("Turtle is on charging station")
                    if turtle.battery < turtle.lowBattery:
                        #print("HEYROOKASKJASDInj")
                        turtle.charge()
                        turtleReward += 1
                    else:
                        turtleReward -= 0.05
                        pass

            for chargingStation in self.chargingStations:
                if turtle.battery < turtle.lowBattery:
                    if manhattenDist(turtle.location, chargingStation.location) < manhattenDist(turtle.oldLoc, chargingStation.location):
                        turtleReward += 0.8
                    else:
                        #pass
                        turtleReward -= 0.8
            for turtle2 in self.turtles:
                if turtle != turtle2:
                    if manhattenDist(turtle.location, turtle2.location) < 3:
                        turtleReward -= 0.3*(3-manhattenDist(turtle.location, turtle2.location))
                    if manhattenDist(turtle.oldLoc, turtle2.oldLoc) < manhattenDist(turtle.location, turtle2.location):
                        if manhattenDist(turtle.oldLoc, turtle2.oldLoc) < 3:
                            turtleReward += 0.1
            tempReward += turtleReward
        turtleReward = tempReward
        epLen = max(max(self.episodeLength, 7)-7, 0)                
        episodic_reward = epLen*0.03
        episodic_reward = min(1, episodic_reward)

        if any(turtle.battery <= 0 for turtle in self.turtles):
            reward -= 10
            reward -= episodic_reward
            self.episodeFailed = True
            self.fail_battery += 1
            return self._get_obs(), reward, True, self._get_info()
        
        if any(equal(turtle.location, turtle2.location) and turtle != turtle2 for turtle in self.turtles for turtle2 in self.turtles):
            reward = -100
            reward += episodic_reward 
            self.episodeFailed = True
            self.fail_collision += 1
            return self._get_obs(), reward, True, self._get_info()

        if all(target.taskCompleted for target in self.targets):
            episodic_reward = epLen*0.03
            reward += 100
            reward -= episodic_reward
            self.success += 1 
            return self._get_obs(), reward, True, self._get_info()
        if all(equal(turtle.location, turtle.oldLoc) for turtle in self.turtles):
        #if all(act == 4 for act in action):
            if not terminated:
                reward = -1
                self.episodeFailed = True
                self.fail_noChange += 1
                return self._get_obs(), reward, True, self._get_info()
        if self.episodeLength > 100:
            reward -= 10
            self.episodeFailed = True
            self.fail_longEpisode += 1
            return self._get_obs(), reward, True, self._get_info()

        observation = self._get_obs()
        info = self._get_info()
        
        reward = turtleReward / len(self.turtles)
        reward -= episodic_reward
        #reward = max(reward, 0) 
        if terminated and reward < 50:
            #self.episodeFailed = True
            pass
        return observation, reward, terminated, info



    def render(self, mode):
        if self.render_mode == "rgb_array":
            return self._render_frame()
        return self._render_frame()

    def _drawTextCentered(self, surface, text, loc, color):
        font = pygame.freetype.SysFont("monospace", 0) 
        x = (loc[0]*self.pixSize)+self.pixSize/2
        y = (loc[1]*self.pixSize)+self.pixSize/2
        pos = (x, y)
        text_rect = font.get_rect(text, size = 50)
        text_rect.center = pos
        font.render_to(surface, text_rect, text, color, size = 50)
    def _renderRobot(self, robot : Turtle, canvas):
        color = (35,255,35) if robot.battery > robot.lowBattery else (255,35,35)
        pygame.draw.rect(
            canvas,
            color,
            pygame.Rect(
                ((robot.location[0]+0.8) * self.pixSize ,((robot.location[1]+1-(robot.battery/100)) * self.pixSize)),
                (self.pixSize*0.2, self.pixSize*robot.battery/100),
            ),
        )
        # Now we draw the agent
        pygame.draw.circle(
            canvas,
            (0, 0, 255),
            (robot.location + 0.5) * self.pixSize,
            self.pixSize / 3,
        )
        self._drawTextCentered(canvas, str(robot.type), robot.location, (0,0,0))

    def _renderTarget(self, target : WorkStation, canvas):
        pygame.draw.rect(
            canvas,
            (255, 0, 0),
            pygame.Rect(
                ((target.location[0]) * self.pixSize ,(target.location[1]) * self.pixSize),
                (self.pixSize, self.pixSize),
            ),
        )
        self._drawTextCentered(canvas, str(target.type), target.location, (0,0,0))

    def _renderChargingStation(self, chargingStation : ChargingStation, canvas):
        pygame.draw.rect(
            canvas,
            (30, 230, 30),
            pygame.Rect(
                ((chargingStation.location[0]) * self.pixSize ,(chargingStation.location[1]) * self.pixSize),
                (self.pixSize, self.pixSize),
            ),
        )
        
        self._drawTextCentered(canvas, "C", chargingStation.location, (0,0,0))
    
    
    def _render_frame(self):
        if self.window is None and self.render_mode == "human":
            pygame.init()
            pygame.display.init()
            self.window = pygame.display.set_mode((self.window_size, self.window_size))
        if self.clock is None and self.render_mode == "human":
            self.clock = pygame.time.Clock()

        canvas = pygame.Surface((self.window_size, self.window_size))
        canvas.fill((255, 255, 255))
        # First we draw the target
        for targets in self.targets:
            self._renderTarget(targets, canvas)
        for chargingStation in self.chargingStations:
            self._renderChargingStation(chargingStation, canvas)
        for turtle in self.turtles:
            self._renderRobot(turtle, canvas)

        # Finally, add some gridlines
        for x in range(self.size + 1):
            pygame.draw.line(
                canvas,
                0,
                (0, self.pixSize * x),
                (self.window_size, self.pixSize * x),
                width=3,
            )
            pygame.draw.line(
                canvas,
                0,
                (self.pixSize * x, 0),
                (self.pixSize * x, self.window_size),
                width=3,
            )

        if self.render_mode == "human":
            # The following line copies our drawings from `canvas` to the visible window
            self.window.blit(canvas, canvas.get_rect())
            pygame.event.pump()
            pygame.display.update()

            # We need to ensure that human-rendering occurs at the predefined framerate.
            # The following line will automatically add a delay to keep the framerate stable.
            self.clock.tick(self.metadata["render_fps"])
        else:  # rgb_array
            return np.transpose(
                np.array(pygame.surfarray.pixels3d(canvas)), axes=(1, 0, 2)
            )

    def close(self):
        if self.window is not None:
            pygame.display.quit()
            pygame.quit()
