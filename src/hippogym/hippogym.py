import asyncio
from typing import Dict, Optional, Union
from multiprocessing import Process


from hippogym.trial import Trial, TrialConfig, DeterministicTrialConfig
from hippogym.trialsteps.trialstep import TrialStep
from hippogym.log import get_logger
from hippogym.communicator import WebSocketCommunicator, SSLCertificate

from websockets.server import WebSocketServerProtocol

LOGGER = get_logger(__name__)

UserID = str


class HippoGym:
    """Main class for a full HippoGym experiment."""

    def __init__(self, trial_config: Union[TrialConfig, Trial, TrialStep]) -> None:
        """Initialize an HippoGym experiment.

        Args:
            trial_config (TrialConfig | Trial | TrialStep): Configuration to use for Trials.
                If a single Trial or a single TrialStep is given, it will be converted to a
                DeterministicTrialConfig.

        """
        if isinstance(trial_config, TrialStep):
            trial_config = Trial(steps=[trial_config])
        if isinstance(trial_config, Trial):
            trial_config = DeterministicTrialConfig(trial_config)
        self.trial_config = trial_config

        self.trials: Dict[UserID, Process] = {}
        self._trial_seed = 0  # TODO use yield

    def start(
        self,
        host: str = "localhost",
        port: int = 5000,
        ssl_certificate: Optional["SSLCertificate"] = None,
    ):
        asyncio.run(self.start_server(host, port, ssl_certificate))

    async def start_server(
        self,
        host: str,
        port: int,
        ssl_certificate: Optional[SSLCertificate] = None,
    ):
        """Start hippogym server side.

        Args:
            ssl_certificate (Optional[SSLCertificate]): SSL certificate for ssl server.
            host (str): Host for non-ssl server.
            port (int): Port for ssl server, non-ssl server will be on port + 1.
        """
        communicator = WebSocketCommunicator(self, host, port, ssl_certificate)
        await communicator.start()

    async def start_connexion(self, websocket: WebSocketServerProtocol, _path: str):
        """Handle a new websocket connexion.

        Args:
            websocket (WebSocketServerProtocol): Websocket just created.
        """
        try:
            user_message: dict = await websocket.recv()
            user_id = user_message.get("userId")
            LOGGER.info("User connected: %s", user_id)
            self.start_trial(user_id)
        finally:
            self.stop_trial(user_id)

    def start_trial(self, user_id: UserID):
        """Start a trial for the given user.

        Args:
            user_id (UserID): Unique ID for the user.

        Raises:
            ValueError: If user is already in trial.
        """
        trial = self.trial_config.sample(self._trial_seed)
        trial.build()
        new_trial_process = Process(target=trial.run, daemon=True)
        if user_id in self.trials:
            raise ValueError(f"{user_id=} already in trial")
        self.trials[user_id] = new_trial_process
        self._trial_seed += 1
        new_trial_process.start()
        return trial

    def stop_trial(self, user_id: UserID):
        """Stop the trial for the given user.

        Args:
            user_id (UserID): Unique ID of the user.
        """
        trial_process = self.trials.pop(user_id)
        trial_process.kill()
