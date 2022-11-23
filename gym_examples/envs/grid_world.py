import gym
from gym import spaces
import pygame
import numpy as np
import random
from .envTools import *
class GridWorldEnv(gym.Env):
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 4}

    def __init__(self, render_mode='human', size = 7):
        self.size = size  # The size of the square grid
        self.window_size = 512  # The size of the PyGame window
        self.numOfTurtles = 4
        self.numOfTargets = 3
        self.numOfChargingStations = 2
        self.spawnableSpace = []
        self.turtles : list[Turtle] = []
        self.targets : list[WorkStation] = []
        self.chargingStations : list[ChargingStation] = []
        self.observation_space = spaces.Dict({})
        for i in range(self.numOfTurtles):
            self.turtles.append(Turtle(i, self.size))
            self.observation_space["agent" + str(i)] = spaces.Box(low=np.array([0, 0, 0, 1]), high=np.array([size-1, size-1, 100, 5]), dtype=int)
        for i in range(self.numOfTargets):
            self.targets.append(WorkStation(i, self.size))
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

        self.turtle0 = self.turtles[0]
        self.turtle1 = self.turtles[1]
        self.target0 = self.targets[0]
        self.chargingStation = self.chargingStations[0]        
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
                self.turtle0.location[0] - self.target0.location[0]
            )
        }

    def reset(self): 
        a  = self.spawnableSpace.copy()
        for turtle in self.turtles:
            turtle.reset(a)
        for target in self.targets:
            target.reset(a)
        for chargingStation in self.chargingStations:
            chargingStation.reset(a)
        observation = self._get_obs()
        info = self._get_info()

        if self.render_mode == "human":
            pass
            #self._render_frame()
        return observation

    def step(self, action):
        oldDist = manhattenDist(self.turtle0.location, self.target0.location)
        oldLoc = self.turtle0.location
        for idx, turtle in enumerate(self.turtles):
            turtle.move(action[idx])
        newDist = manhattenDist(self.turtle0.location, self.target0.location)
        terminated = np.array_equal(self.turtle0.location, self.target0.location)

        highest_distance = (self.size -1) * np.sqrt(2) 

        oldBatDist = manhattenDist(oldLoc, self.chargingStation.location)
        newBatDist = manhattenDist(self.turtle0.location, self.chargingStation.location)
        if newDist < oldDist:
            reward = 5
        elif newDist == oldDist:
            reward = -3
        else:
            reward = -15
        if terminated and self.turtle0.battery > self.turtle0.lowBattery:
            reward = 50
        elif terminated and self.turtle0.battery <= self.turtle0.lowBattery:
            reward = -25
            terminated = False
        elif terminated:
            reward = 0
        if self.turtle0.battery <= 0:
            reward = -100
            terminated = True
        if self.turtle0.battery < 2:
            if newBatDist < oldBatDist:
                reward = 4
            elif newBatDist == oldBatDist:
                reward = -3
            else:
                reward = -(25 * (2-self.turtle0.battery))
        if np.array_equal(self.turtle0.location, self.chargingStation.location) and self.turtle0.battery < self.turtle0.lowBattery:
            self.turtle0.battery = 100
            reward = 10
        observation = self._get_obs()
        info = self._get_info()

        if self.render_mode == "human":
            pass
            #self._render_frame()
        #print(observation)
        return observation, reward, terminated, info



    def render(self, mode):
        if self.render_mode == "rgb_array":
            return self._render_frame()
        return self._render_frame()

    def _drawTextCentered(self, surface, text, text_size, loc, size, color):
        font = pygame.freetype.SysFont("monospace", 0) 
        x = loc[0]*size
        y = loc[1]*size
        pos = (x, y)
        text_rect = font.get_rect(text, size = 50)
        text_rect.center = pos
        font.render_to(surface, text_rect, text, color, size = 50)

    def _renderRobot(self, robot : Turtle, canvas, pix_square_size):
        color = (35,255,35) if robot.battery > robot.lowBattery else (255,35,35)
        pygame.draw.rect(
            canvas,
            color,
            pygame.Rect(
                ((robot.location[0]+0.8) * pix_square_size ,((robot.location[1]+1-(robot.battery/100)) * pix_square_size)),
                (pix_square_size*0.2, pix_square_size*robot.battery/100),
            ),
        )
        # Now we draw the agent
        pygame.draw.circle(
            canvas,
            (0, 0, 255),
            (robot.location + 0.5) * pix_square_size,
            pix_square_size / 3,
        )

    def _renderTarget(self, target : WorkStation, canvas, pix_square_size):
        pygame.draw.rect(
            canvas,
            (255, 0, 0),
            pygame.Rect(
                ((target.location[0]) * pix_square_size ,(target.location[1]) * pix_square_size),
                (pix_square_size, pix_square_size),
            ),
        )
    def _renderChargingStation(self, chargingStation : ChargingStation, canvas, pix_square_size):
        self._drawTextCentered(canvas, "C", 40, chargingStation.location, pix_square_size, (0,0,0))
        pygame.draw.rect(
            canvas,
            (30, 230, 30),
            pygame.Rect(
                ((chargingStation.location[0]) * pix_square_size ,(chargingStation.location[1]) * pix_square_size),
                (pix_square_size, pix_square_size),
            ),
        )
    def _render_frame(self):
        if self.window is None and self.render_mode == "human":
            pygame.init()
            pygame.display.init()
            self.window = pygame.display.set_mode((self.window_size, self.window_size))
        if self.clock is None and self.render_mode == "human":
            self.clock = pygame.time.Clock()

        canvas = pygame.Surface((self.window_size, self.window_size))
        canvas.fill((255, 255, 255))
        pix_square_size = (
            self.window_size / self.size
        )  # The size of a single grid square in pixels
        # First we draw the target
        for targets in self.targets:
            self._renderTarget(targets, canvas, pix_square_size)
        for chargingStation in self.chargingStations:
            self._renderChargingStation(chargingStation, canvas, pix_square_size)
        for turtle in self.turtles:
            self._renderRobot(turtle, canvas, pix_square_size)

        # Finally, add some gridlines
        for x in range(self.size + 1):
            pygame.draw.line(
                canvas,
                0,
                (0, pix_square_size * x),
                (self.window_size, pix_square_size * x),
                width=3,
            )
            pygame.draw.line(
                canvas,
                0,
                (pix_square_size * x, 0),
                (pix_square_size * x, self.window_size),
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
