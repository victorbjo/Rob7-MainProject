import gym
from gym import spaces
import pygame
import numpy as np
import random

class GridWorldEnv(gym.Env):
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 4}

    def __init__(self, render_mode='human', size = 6):
        self.size = size  # The size of the square grid
        self.window_size = 512  # The size of the PyGame window

        # Observations are dictionaries with the agent's and the target's location.
        # Each location is encoded as an element of {0, ..., `size`}^2, i.e. MultiDiscrete([size, size]).
        self.observation_space = spaces.Dict(
            {
                "agent": spaces.Box(0, size - 1, shape=(2,), dtype=int),
                "target": spaces.Box(0, size - 1, shape=(2,), dtype=int),
            }
        )

        # We have 4 actions, corresponding to "right", "up", "left", "down", "right"
        self.action_space = spaces.Discrete(4)

        """
        The following dictionary maps abstract actions from `self.action_space` to 
        the direction we will walk in if that action is taken.
        I.e. 0 corresponds to "right", 1 to "up" etc.
        """
        self._action_to_direction = {
            0: np.array([1, 0]),
            1: np.array([0, 1]),
            2: np.array([-1, 0]),
            3: np.array([0, -1]),
         }
        """ 8 directions action space""" 
        # self._action_to_direction = {
        #     0: np.array([1, 0]),
        #     1: np.array([1, 1]),
        #     2: np.array([0, 1]),
        #     3: np.array([-1, 1]),
        #     4: np.array([-1, 0]),
        #     5: np.array([-1, -1]),
        #     6: np.array([0, -1]),
        #     7: np.array([1, -1]),
        # }


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
        return {"agent": self._agent_location, "target": self._target_location}

    def _get_info(self):
        return {
            "distance": np.linalg.norm(
                self._agent_location[0] - self._target_location[0]
            )
        }

    def reset(self):
        # We need the following line to seed self.np_random
        #super().reset()

        # Choose the agent's location uniformly at random
        # self._agent_location = [random.randrange(1,50)*10,random.randrange(1,50)*10]
        self._agent_location = [random.randrange(0,self.size),random.randrange(0,self.size)]

        # We will sample the target's location randomly until it does not coincide with the agent's location
        self._target_location = self._agent_location
        while np.array_equal(self._target_location, self._agent_location):
            self._target_location = [random.randrange(0,self.size),random.randrange(0,self.size)]

        observation = self._get_obs()
        info = self._get_info()

        if self.render_mode == "human":
            pass
            #self._render_frame()

        return observation

    def step(self, action):
        # Map the action (element of {0,1,2,3}) to the direction we walk in
        direction = self._action_to_direction[action]
        # We use `np.clip` to make sure we don't leave the grid
        self._agent_location = np.clip(
            self._agent_location + direction, 0, self.size - 1
        )
        # An episode is done iff the agent has reached the target
        terminated = np.array_equal(self._agent_location, self._target_location)
        # reward = 100 if terminated else -1  # Binary sparse rewards
        highest_distance = (self.size -1) * np.sqrt(2) # np.power(self.size -1 ,2)
        distance_intensity_factor = 3 # should be odd because we use power for intensity after nomalizing around 0
        reward = -1 * np.power(np.linalg.norm(self._agent_location - self._target_location),distance_intensity_factor)
        if reward == 0:
            reward = 20
        # reward = np.power((highest_distance*(0.6) - np.linalg.norm(self._agent_location - self._target_location)),distance_intensity_factor)
        # reward = (highest_distance*(0.1) - np.linalg.norm(self._agent_location - self._target_location))*distance_intensity_factor
        observation = self._get_obs()
        info = self._get_info()

        if self.render_mode == "human":
            pass
            #self._render_frame()

        return observation, reward, terminated, info

    def render(self, mode):
        if self.render_mode == "rgb_array":
            return self._render_frame()
        return self._render_frame()

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
        # Now we draw the agent
        pygame.draw.circle(
            canvas,
            (0, 0, 255),
            (self._agent_location + 0.5) * pix_square_size,
            pix_square_size / 3,
        )

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
