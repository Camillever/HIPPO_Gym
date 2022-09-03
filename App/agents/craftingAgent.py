from typing import Optional
from crafting import MineCraftingEnv
from crafting.render.render import get_human_action
from crafting.task import RewardShaping, TaskObtainItem

from App.agents import Agent


class CraftingAgent(Agent):
    """
    Use this class as a convenient place to store agent state.
    """

    def start(self, config: dict) -> None:
        """Starts the Agent's environment.
        Args:
            config: trial config.
        """
        game = config.get("game")
        if game == "minecrafting":
            self.env = MineCraftingEnv(max_step=100)
            item_task = self.env.world.item_from_name[config.get("task_item_name")]
            task = TaskObtainItem(
                self.env.world,
                item_task,
                reward_shaping=RewardShaping.NONE,
            )
            self.env.add_task(task)

    def handle_events(self, events) -> Optional[int]:
        action = get_human_action(
            self.env,
            additional_events=events,
            can_be_none=True,
            **self.env.render_variables
        )
        if action:
            action = self.env.action(*action)
        return action

    def step(self, action: int):
        """
        Takes a game step.
        Caller:
            - Trial.take_step()
        Inputs:
            - env (Type: OpenAI gym Environment)
            - action (Type: int corresponding to action in env.action_space)
        Returns:
            - envState (Type: dict containing all information to be recorded for future use)
              change contents of dict as desired, but return must be type dict.
        """
        observation, reward, done, info = self.env.step(action)
        envState = {
            "observation": observation,
            "reward": reward,
            "done": done,
            "info": info,
        }
        return envState

    def render(self):
        """
        Gets render from gym.
        Caller:
            - Trial.get_render()
        Inputs:
            - env (Type: OpenAI gym Environment)
        Returns:
            - return from env.render('rgb_array') (Type: npArray)
              must return the unchanged rgb_array
        """
        return self.env.render("rgb_array")

    def reset(self):
        """
        Resets the environment to start new episode.
        Caller:
            - Trial.reset()
        Inputs:
            - env (Type: OpenAI gym Environment)
        Returns:
            No Return
        """
        self.env.reset()

    def close(self):
        """
        Closes the environment at the end of the trial.
        Caller:
            - Trial.close()
        Inputs:
            - env (Type: OpenAI gym Environment)
        Returns:
            No Return
        """
        self.env.close()
