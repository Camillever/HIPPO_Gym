import json, shortuuid, time

from multiprocessing.connection import Connection

from App.agents.my_agent import CraftingAgent
from App.message_handlers.my_handler import PyGameLibrairyHandler
from App.recorders import Recorder
from App.utils import array_to_b64, load_config

class Trial():

    def __init__(self, pipe:Connection):
        self.config = load_config()
        self.pipe = pipe
        self.frameId = 0
        self.humanAction = self.config.get('defaultAction')
        self.episode = 0
        self.done = False
        self.play = self.config.get('defaultStart', False)
        self.record = []
        self.trialId = shortuuid.uuid()
        self.outfile = None
        self.framerate = self.config.get('startingFrameRate', 30)
        self.userId = None
        self.projectId = self.config.get('projectId')
        self.filename = None
        self.path = None

        self.start()
        self.run()

    def start(self):
        '''
        Call the function in the Agent/Environment combo required to start 
        a trial. By default passes the environment name that will be passed
        to gym.make(). 
        By default this expects the openAI Gym Environment object to be
        returned. 
        '''
        self.config['filter_by_utility'] = True
        self.config['task_number'] = 5
        self.config['rank_by_complexity'] = True

        self.agent = CraftingAgent()
        self.message_handler = PyGameLibrairyHandler(
            self,
            filter_by_utility=self.config.get('filter_by_utility'),
            task_number=self.config.get('task_number'),
            rank_by_complexity=self.config.get('rank_by_complexity')
        )
        self.recorder = Recorder(self)
        self.agent.start(self.config.get('game'))

    def run(self):
        '''
        This is the main event controlling function for a Trial. 
        It handles the render-step loop
        '''
        while not self.done:
            message = self.check_message()
            if message:
                self.message_handler.handle_message(message)
                self.recorder.record_message(message)
            if self.play:
                render = self.get_render()
                self.send_render(render)
                self.recorder.record_render(render)
                if self.humanAction is not None:
                    env_state = self.agent.step(self.humanAction)
                    self.recorder.record_step(env_state)
                    self.humanAction = self.config.get('defaultAction')
                    if env_state['done']:
                        self.reset()
            time.sleep(1/self.framerate)

    def reset(self):
        '''
        Resets the OpenAI gym environment to start a new episode.
        By default this function will create a new log file for every
        episode, if the intention is to log only full trials then
        comment the 3 lines below contianing self.outfile and 
        self.create_file.
        '''
        if self.check_trial_done():
            self.end()
        else:
            self.agent.reset()
            self.message_handler.reset()
            self.recorder.reset()
            self.episode += 1

    def check_trial_done(self):
        '''
        Checks if the trial has been completed and can be quit. Add conditions
        as required.
        '''
        return self.episode >= self.config.get('maxEpisodes', 20)

    def end(self):
        '''
        Closes the environment through the agent, closes any remaining outfile
        and sends the 'done' message to the websocket pipe. If logging the 
        whole trial memory in self.record, uncomment the call to self.save_record()
        to write the record to file before closing.
        '''
        self.pipe.send('done')
        self.agent.close()
        self.recorder.close()
        self.play = self.config.get('defaultStart', False)
        self.done = True

    def check_message(self):
        '''
        Checks pipe for messages from websocket, tries to parse message from
        json. Retruns message or error message if unable to parse json.
        Expects some poorly formatted or incomplete messages.
        '''
        if self.pipe.poll():
            message = self.pipe.recv()
            try:
                message = json.loads(message)
            except:
                message = {'error': 'unable to parse message', 'frameId': self.frameId}
            return message
        return None

    def get_render(self) -> dict:
        '''
        Calls the Agent/Environment render function which must return a npArray.
        Translates the npArray into a jpeg image and then base64 encodes the 
        image for transmission in json message.
        '''
        render = self.agent.render()
        frame = array_to_b64(render)
        self.frameId += 1
        return {'frame': frame, 'frameId': self.frameId}

    def send_render(self, render:dict=None):
        '''
        Attempts to send render message to websocket
        '''
        if render is None:
            render = self.get_render()
        try: 
            self.pipe.send(json.dumps(render))
        except:
            raise TypeError("Render Dictionary is not JSON serializable")

    def send_ui(self, ui=None):
        if ui is None:
            defaultUI = ['left','right','up','down','start','pause']
            ui = self.config.get('ui', defaultUI)
        try:
            self.pipe.send(json.dumps({'UI': ui}))
        except:
            raise TypeError("Render Dictionary is not JSON serializable")

    def send_variables(self):
        try:
            self.pipe.send(json.dumps(self.config.get('variables')))
        except:
            return
