import gym_examples
import gym
import pygame
from stable_baselines3.common.env_checker import check_env
from stable_baselines3 import PPO
env = gym.make('gym_examples/GridWorld-v0')
#env.render_mode=None
#obs = env.reset()
#env.render(mode = "human")
#env.render_mode="human"
#check_env(env)


model = PPO("MultiInputPolicy", env)

model.learn(total_timesteps=10, reset_num_timesteps=False, tb_log_name="PPO")
episodes = 5

for ep in range(episodes):
    obs = env.reset()
    done = False
    while not done:
        action = model.predict(obs)
        obs, rewards, done, info = env.step(1)
        print(action)
        done = True