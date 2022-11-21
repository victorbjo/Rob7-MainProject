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
        self.turtle0 = turtle(1, self.size)
        self.turtle1 = turtle(2, self.size)
        self.target0 = workStation(1, self.size)
        self.chargingStation = ChargingStation(self.size)
        # Observations are dictionaries with the agent's and the target's location.
        # Each location is encoded as an element of {0, ..., `size`}^2, i.e. MultiDiscrete([size, size]).
        #"agent": spaces.Box(low=np.array([0, 0, 0, 1]), high=np.array([size-1, size-1, 100, 5]), dtype=int), 
        self.observation_space = spaces.Dict(
            {
                "agent": spaces.Box(low=np.array([0, 0, 0, 1]), high=np.array([size-1, size-1, 100, 5]), dtype=int), 
                "agent1": spaces.Box(low=np.array([0, 0, 0, 1]), high=np.array([size-1, size-1, 100, 5]), dtype=int), 
                "target": spaces.Box(low=np.array([0, 0, 0,]), high=np.array([size-1, size-1, 5]), dtype=int), #DStructure [0]and[1] is xy pos [2] is the type of "lego" bricks needed 
                "charging_station": spaces.Box(0, size - 1, shape=(2,), dtype=int),
            }
        )

        #We have 4 actions, corresponding to "right", "up", "left", "down", "right"
        actionSpaceArray = [4]
        #self.action_space = spaces.MultiDiscrete(actionSpaceArray)
        self.action_space = spaces.Discrete(4)
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
        return {"agent": self.turtle0.getState(), "agent1": self.turtle1.getState(),
        "target": self.target0.getState(), "charging_station": self.chargingStation.location}

    def _get_info(self):
        return {
            "distance": np.linalg.norm(
                self.turtle0.location[0] - self.target0.location[0]
            )
        }

    def reset(self):
        # We need the following line to seed self.np_random
        #super().reset()

        # Choose the agent's location uniformly at random
        # self._agent_location = [random.randrange(1,50)*10,random.randrange(1,50)*10]
        self.turtle0.reset()
        self.turtle1.reset()
        self.target0.reset()
        self.chargingStation.reset()
        # We will sample the target's location randomly until it does not coincide with the agent's location
        self.target0.location = self.turtle0.location
        while manhattenDist(self.turtle0.location, self.target0.location) < 2 :
            self.target0.getNewLoc()
        while manhattenDist(self.chargingStation.location, self.target0.location) < 2 or manhattenDist(self.chargingStation.location, self.turtle0.location) < 1:
            self.chargingStation.reset()
        observation = self._get_obs()
        info = self._get_info()

        if self.render_mode == "human":
            pass
            #self._render_frame()
        return observation

    def step(self, action):
        #action = action[0]
        # Map the action (element of {0,1,2,3}) to the direction we walk in
        oldDist = manhattenDist(self.turtle0.location, self.target0.location)
        oldLoc = self.turtle0.location
        self.turtle0.move(action)
        self.turtle1.move(action)
        # We use `np.clip` to make sure we don't leave the grid
        newDist = manhattenDist(self.turtle0.location, self.target0.location)
        # An episode is done iff the agent has reached the target
        terminated = np.array_equal(self.turtle0.location, self.target0.location)
        # reward = 100 if terminated else -1  # Binary sparse rewards
        highest_distance = (self.size -1) * np.sqrt(2) # np.power(self.size -1 ,2)
        distance_intensity_factor = 3 # should be odd because we use power for intensity after nomalizing around 0
        #reward = -0.1 * np.power(manhattenDist(self.turtle0.location, self._target_location),distance_intensity_factor)
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

    def _renderRobot(self, robot : turtle, canvas, pix_square_size):
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

    def _renderTarget(self, target : workStation, canvas, pix_square_size):
        pygame.draw.rect(
            canvas,
            (255, 0, 0),
            pygame.Rect(
                ((self.target0.location[0]) * pix_square_size ,(self.target0.location[1]) * pix_square_size),
                (pix_square_size, pix_square_size),
            ),
        )
    def _renderChargingStation(self, chargingStation : ChargingStation, canvas, pix_square_size):
        pygame.draw.rect(
            canvas,
            (30, 230, 30),
            pygame.Rect(
                ((self.chargingStation.location[0]) * pix_square_size ,(self.chargingStation.location[1]) * pix_square_size),
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

        
        self._renderTarget(self.target0,canvas,pix_square_size)
        self._renderChargingStation(self.chargingStation,canvas,pix_square_size)
        
        self._renderRobot(self.turtle0, canvas, pix_square_size)
        self._renderRobot(self.turtle1, canvas, pix_square_size)
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
