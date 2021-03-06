import gym

# import torchcraft_py.torchcraft as tc
import torchcraft.Constants as tcc
import torchcraft as tc


class StarCraftEnv(gym.Env):
    def __init__(self, server_ip, server_port, speed, frame_skip, self_play,
                 max_episode_steps):
        self.ip = server_ip
        self.port = server_port
        self.client = tc.Client()
        self.client.connect(server_ip, server_port)
        self.state = self.client.init(micro_battles=True)
        self.speed = speed
        self.frame_skip = frame_skip
        self.self_play = self_play
        self.max_episode_steps = max_episode_steps
        self.step_limit = 300
        self.step_rate = 10

        self.episodes = 0
        self.episode_wins = 0
        self.episode_steps = 0

        self.action_space = self._action_space()
        self.observation_space = self._observation_space()

        self.state = None
        self.obs = None
        self.obs_pre = None

        self.advanced_termination = True

    def __del__(self):
        self.client.close()

    def step(self, action):
        self.episode_steps += 1
        # print(self._make_commands(action))
        self.client.send(self._make_commands(action))
        #self.client.receive()
        self.state = self.client.recv()
        self.obs = self._make_observation()
        reward = self._compute_reward()
        done = self._check_done()
        info = self._get_info()

        self.obs_pre = self.obs
        # print(self.state.game_ended,self.state.battle_just_ended)
        return self.obs, reward, done, info

    def reset(self):
        #utils.print_progress(self.episodes, self.episode_wins)

        if (not self.self_play and self.episode_steps == self.step_limit) or self.advanced_termination:
            # self.client.send([proto.concat_cmd(proto.commands['restart'])])
            self.client.send([[tcc.restart]])
            #self.client.send([[tcc.set_map, 'Map/BroodWar/micro/2dragoons_5marines.scm',0],[tcc.restart]])
            self.state = self.client.recv()
            while not bool(self.state.game_ended):
                self.client.send([])
                self.state = self.client.recv()

        self.step_limit = min(self.step_limit+self.step_rate,self.max_episode_steps)


        self.episodes += 1
        self.episode_steps = 0

        self.client.close()
        self.client.connect(self.ip, self.port)
        state = self.client.init(micro_battles=True)
        # setup = [proto.concat_cmd(proto.commands['set_speed'], self.speed),
        #          proto.concat_cmd(proto.commands['set_gui'], 1),
        #          proto.concat_cmd(proto.commands['set_frameskip'],
        #                           self.frame_skip),
        #          proto.concat_cmd(proto.commands['set_cmd_optim'], 1)]
        setup = [
            [tcc.set_speed, self.speed],
            [tcc.set_gui, 1],
            [tcc.set_frameskip, self.frame_skip],
            [tcc.set_cmd_optim, 1]
            ]

        self.client.send(setup)
        self.state = self.client.recv()
        #/print(len(self.state.units[1]), len(self.state.units[0]))
        self.reset_data()

        # skip the init state, there is no unit at the beginning of
        # self.client.send(self._make_commands(None))
        # self.state = self.client.recv()
        # print(len(self.state.units[1]), len(self.state.units[0]))

        self.obs = self._make_observation()
        self.obs_pre = self.obs
        return self.obs

    def reset_data(self):
        """Reset the state data"""
        pass

    def _action_space(self):
        """Returns a space object"""
        raise NotImplementedError

    def _observation_space(self):
        """Returns a space object"""
        raise NotImplementedError

    def _make_commands(self, action):
        """Returns a game command list based on the action"""
        raise NotImplementedError

    def _make_observation(self):
        """Returns a observation object based on the game state"""
        raise NotImplementedError

    def _compute_reward(self):
        """Returns a computed scalar value based on the game state"""
        raise NotImplementedError

    def _check_done(self):
        """Returns true if the episode was ended"""
        return bool(self.state.game_ended) or self.state.battle_just_ended

    def _get_info(self):
        """Returns a dictionary contains debug info"""
        return {}

    def render(self, mode='human', close=False):
        pass
    def close(self):
        self.client.close()

    # def skip_init(self):
