from isaaclab.utils import configclass
from isaaclab_rl.rsl_rl import RslRlOnPolicyRunnerCfg, RslRlPpoActorCriticCfg, RslRlPpoAlgorithmCfg

# V21: Orientation Fix — same PPO params as V20 (entropy_coef=0.005 worked well)

@configclass
class My6dofReachPPORunnerCfg_v21(RslRlOnPolicyRunnerCfg):
    num_steps_per_env = 24
    max_iterations = 6000
    save_interval = 50
    experiment_name = "my6dof_reach_v21_orientation_fix"
    empirical_normalization = True
    policy = RslRlPpoActorCriticCfg(
        init_noise_std=1.0,
        actor_hidden_dims=[400, 200, 100],
        critic_hidden_dims=[400, 200, 100],
        activation="elu",
    )
    algorithm = RslRlPpoAlgorithmCfg(
        value_loss_coef=1.0,
        use_clipped_value_loss=True,
        clip_param=0.2,
        entropy_coef=0.005,   # V20 ile aynı (collapse önlendi, koru)
        learning_rate=1e-3,
        num_learning_epochs=5,
        num_mini_batches=4,
        schedule="adaptive",
        gamma=0.99,
        lam=0.95,
        desired_kl=0.02,      # V20 ile aynı
        max_grad_norm=1.0,
    )
