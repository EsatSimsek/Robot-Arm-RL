import gymnasium as gym
from . import agents

gym.register(
    id="Isaac-Reach-My6dof-v21",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.joint_pos_env_cfg:My6dofReachEnvCfg_v21",
        "rsl_rl_cfg_entry_point": f"{agents.__name__}:My6dofReachPPORunnerCfg_v21",
    },
)

gym.register(
    id="Isaac-Reach-My6dof-v21-Play",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.joint_pos_env_cfg:My6dofReachEnvCfg_v21_PLAY",
        "rsl_rl_cfg_entry_point": f"{agents.__name__}:My6dofReachPPORunnerCfg_v21",
    },
)
