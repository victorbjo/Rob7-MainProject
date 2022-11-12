import gym
from gym import spaces
import pygame
import numpy as np
import random
from .envTools import *
class GridWorldEnv(gym.Env):
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 4}

    def __init__(self, render_mode='human', size = 6):
        self.size = size  # The size of the square grid
        self.window_size = 512  # The size of the PyGame window
        self.turtle0 = turtle(self.size)
        # Observations are dictionaries with the agent's and the target's location.
        # Each location is encoded as an element of {0, ..., `size`}^2, i.e. MultiDiscrete([size, size]).
        self.observation_space = spaces.Dict(
            {
                "agent": spaces.Box(0, size - 1, shape=(3,), dtype=int), 
                "target": spaces.Box(0, size - 1, shape=(2,), dtype=int),
                "charging_station": spaces.Box(0, size - 1, shape=(2,), dtype=int),
            }
        )

        # We have 4 actions, corresponding to "right", "up", "left", "down", "right"
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
        return {"agent": [self.turtle0.location[0],self.turtle0.location[1],self.turtle0.battery], 
        "target": self._target_location, "charging_station": self._charging_station_location}

    def _get_info(self):
        return {
            "distance": np.linalg.norm(
                self.turtle0.location[0] - self._target_location[0]
            )
        }

    def reset(self):
        # We need the following line to seed self.np_random
        #super().reset()

        # Choose the agent's location uniformly at random
        # self._agent_location = [random.randrange(1,50)*10,random.randrange(1,50)*10]
        self.turtle0.reset()
        self._charging_station_location = [random.randrange(0,self.size),random.randrange(0,self.size)]
        # We will sample the target's location randomly until it does not coincide with the agent's location
        self._target_location = self.turtle0.location
        while manhattenDist(self.turtle0.location, self._target_location) < 2 :
            self._target_location = [random.randrange(0,self.size),random.randrange(0,self.size)]
        while manhattenDist(self._charging_station_location, self._target_location) < 2 or manhattenDist(self._charging_station_location, self.turtle0.location) < 1:
            self._charging_station_location = [random.randrange(0,self.size),random.randrange(0,self.size)]
        observation = self._get_obs()
        info = self._get_info()

        if self.render_mode == "human":
            pass
            #self._render_frame()
        return observation

    def step(self, action):
        # Map the action (element of {0,1,2,3}) to the direction we walk in
        oldDist = manhattenDist(self.turtle0.location, self._target_location)
        oldLoc = self.turtle0.location
        self.turtle0.move(action)
        # We use `np.clip` to make sure we don't leave the grid
        newDist = manhattenDist(self.turtle0.location, self._target_location)
        # An episode is done iff the agent has reached the target
        terminated = np.array_equal(self.turtle0.location, self._target_location)
        # reward = 100 if terminated else -1  # Binary sparse rewards
        highest_distance = (self.size -1) * np.sqrt(2) # np.power(self.size -1 ,2)
        distance_intensity_factor = 3 # should be odd because we use power for intensity after nomalizing around 0
        #reward = -0.1 * np.power(manhattenDist(self.turtle0.location, self._target_location),distance_intensity_factor)
        oldBatDist = manhattenDist(oldLoc, self._charging_station_location)
        newBatDist = manhattenDist(self.turtle0.location, self._charging_station_location)
        if newDist < oldDist:
            reward = 2
        elif newDist == oldDist:
            reward = -1
        else:
            reward = -10
        if terminated and self.turtle0.battery > 2:
            reward = 100
        elif terminated and self.turtle0.battery <= 2:
            reward = -6
            terminated = False
        elif terminated:
            reward = 0
        if self.turtle0.battery <= 0:
            reward = -100
            terminated = True
        if self.turtle0.battery < 2:
            if newBatDist < oldBatDist:
                reward = 2
            elif newBatDist == oldBatDist:
                reward = -1
            else:
                reward = -10
        if np.array_equal(self.turtle0.location, self._charging_station_location) and self.turtle0.battery < 2:
            self.turtle0.battery = 5
            reward = 100
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

    def _renderRobot(self,robot : turtle, canvas, pix_square_size):
        color = (35,255,35) if self.turtle0.battery > 2 else (255,35,35)
        pygame.draw.rect(
            canvas,
            color,
            pygame.Rect(
                ((robot.location[0]+0.8) * pix_square_size ,((robot.location[1]+1-(robot.battery/5)) * pix_square_size)),
                (pix_square_size*0.2, pix_square_size*robot.battery/5),
            ),
        )
        # Now we draw the agent
        pygame.draw.circle(
            canvas,
            (0, 0, 255),
            (robot.location + 0.5) * pix_square_size,
            pix_square_size / 3,
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
        pygame.draw.rect(
            canvas,
            (255, 0, 0),
            pygame.Rect(
                ((self._target_location[0]) * pix_square_size ,(self._target_location[1]) * pix_square_size),
                (pix_square_size, pix_square_size),
            ),
        )

        

        pygame.draw.rect(
            canvas,
            (40, 255, 40),
            pygame.Rect(
                ((self._charging_station_location[0]) * pix_square_size ,(self._charging_station_location[1]) * pix_square_size),
                (pix_square_size, pix_square_size),
            ),
        )
        
        self._renderRobot(self.turtle0, canvas, pix_square_size)
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
