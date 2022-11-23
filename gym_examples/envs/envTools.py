import numpy as np
import random
def manhattenDist(robot, goal):
    return abs(robot[0] - goal[0]) + abs(robot[1] - goal[1])
class Turtle():
    def __init__(self, type, size = 6):
        self.size = size
        self.type = type
        self.location = [random.randrange(0,self.size),random.randrange(0,self.size)]
        self.battery = random.randrange(20,60)
        self.lowBattery = 30
        self._action_to_direction = {
            0: np.array([1, 0]),
            1: np.array([0, 1]),
            2: np.array([-1, 0]),
            3: np.array([0, -1]),
            4: np.array([0, 0]),
        }
    def move(self, action):
        direction = self._action_to_direction[action]
        self.location = np.clip(self.location + direction, 0, self.size - 1)
        self.battery -= 1
        if self.battery < 0:
            self.battery = 0
    def reset(self):
        self.location = [random.randrange(0,self.size),random.randrange(0,self.size)]
        self.battery = random.randrange(20,60)
    def getState(self):
        return [self.location[0],self.location[1], self.battery, self.type]
            
class WorkStation():
    def __init__(self, type, size = 6):
        self.size = size
        self.type = type
        self.location = [random.randrange(0,self.size),random.randrange(0,self.size)]
    def reset(self):
        self.getNewLoc()
    def getNewLoc(self):
        self.location = [random.randrange(0,self.size),random.randrange(0,self.size)]
    def getState(self):
        return [self.location[0],self.location[1], self.type]
class ChargingStation(WorkStation):
    def __init__(self, size = 6):
        self.size = size
        self.location = [random.randrange(0,self.size),random.randrange(0,self.size)]
if __name__ == "__main__":
    a = (1,1)
    b = (1,1)
    #print(np.linalg.norm(a - b))
    print(manhattenDist(a,b))