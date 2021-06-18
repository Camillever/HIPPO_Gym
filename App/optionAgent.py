from agent import Agent

from crafting import MineCraftingEnv
from crafting.examples.minecraft.rendering import get_human_action

from pygame.event import Event
from pygame.locals import MOUSEBUTTONDOWN, MOUSEBUTTONUP

class CraftingAgent(Agent):
    '''
    Use this class as a convenient place to store agent state.
    '''

    def start(self, game:str):
        '''
        Starts an OpenAI gym environment.
        Caller:
            - Trial.start()
        Inputs:
            -   game (Type: str corresponding to allowable gym environments)
        Returs:
            - env (Type: OpenAI gym Environment as returned by gym.make())
            Mandatory
        '''
        self.env = MineCraftingEnv()

    def coordinates_to_action(self, coords):
        coords = (int(coords['x']), int(coords['y']))
        events = self.coords_to_pygame_events(coords)
        action = get_human_action(self.env, additional_events=events,
            can_be_none=True, **self.env.render_variables)
        if action:
            action = self.env.action(*action)
        return action

    @staticmethod
    def coords_to_pygame_events(coords):
        return [Event(MOUSEBUTTONDOWN, pos=coords, button=1),
            Event(MOUSEBUTTONUP, pos=coords, button=1)]

    def step(self, action:int):
        '''
        Takes a game step.
        Caller: 
            - Trial.take_step()
        Inputs:
            - env (Type: OpenAI gym Environment)
            - action (Type: int corresponding to action in env.action_space)
        Returns:
            - envState (Type: dict containing all information to be recorded for future use)
              change contents of dict as desired, but return must be type dict.
        '''
        observation, reward, done, info = self.env.step(action)
        envState = {'observation': observation, 'reward': reward, 'done': done, 'info': info}
        return envState

    def render(self):
        '''
        Gets render from gym.
        Caller:
            - Trial.get_render()
        Inputs:
            - env (Type: OpenAI gym Environment)
        Returns:
            - return from env.render('rgb_array') (Type: npArray)
              must return the unchanged rgb_array
        '''
        return self.env.render('rgb_array')
    
    def reset(self):
        '''
        Resets the environment to start new episode.
        Caller: 
            - Trial.reset()
        Inputs:
            - env (Type: OpenAI gym Environment)
        Returns: 
            No Return
        '''
        self.env.reset()
    
    def close(self):
        '''
        Closes the environment at the end of the trial.
        Caller:
            - Trial.close()
        Inputs:
            - env (Type: OpenAI gym Environment)
        Returns:
            No Return
        '''
        self.env.close()
