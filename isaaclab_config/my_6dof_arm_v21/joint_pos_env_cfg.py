import math
from isaaclab.utils import configclass
from isaaclab.assets import ArticulationCfg, AssetBaseCfg
import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.utils.assets import ISAAC_NUCLEUS_DIR
import isaaclab.envs.mdp as env_mdp

import isaaclab_tasks.manager_based.manipulation.reach.mdp as mdp
from isaaclab_tasks.manager_based.manipulation.reach.reach_env_cfg import ReachEnvCfg, ReachSceneCfg

# =============================================================================
# V21: ORIENTATION FIX
# =============================================================================
# V20 SORUNU: orientation_error 1.5+ rad'a ulaştı (robot 87° yanlış duruyor!)
# Neden: fine_grained (w=30) >> orientation (w=12). Agent pozisyona odaklandı.
# tanh(1.5/0.5) ≈ 0.995 → orientation reward ≈ 0 → agent oryantasyonu terk etti.
#
# V21 DÜZELTMELERİ:
#   1. fine_grained weight:   30 → 15  (pozisyon baskısını azalt)
#   2. orientation weight:    12 → 25  (oryantasyonu zorla)
#   3. orientation std:      0.5 → 0.4 (daha sert gradient, büyük hatalara cevap ver)
#
# Yeni ödül dengesi (tanh tabanlı, std=0.4):
#   error=0.0 rad → reward = 25.0 (max)
#   error=0.4 rad → reward = 25 × 0.46 = 11.5
#   error=1.0 rad → reward = 25 × 0.09 = 2.2
#   error=1.5 rad → reward = 25 × 0.02 = 0.5 (kritik bölgede bile ceza gibi)
#
# Bu değerlerle fine_grained (max ~15) artık orientation (max ~25)'ten küçük.
# =============================================================================

CUSTOM_ROBOT_CFG_v21 = ArticulationCfg(
    spawn=sim_utils.UsdFileCfg(
        usd_path="C:/Users/WWWW/Desktop/6dof-gripper-camera-main/robot_export/tek_joint.usd",
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            disable_gravity=False,
            max_depenetration_velocity=5.0,
        ),
    ),
    init_state=ArticulationCfg.InitialStateCfg(
        pos=(0.0, 0.0, 0.0),
        joint_pos={
            "Revolute_20": 0.0, "Revolute_21": -1.0, "Revolute_22": 1.0,
            "Revolute_23": 0.0, "Revolute_24": 0.0,
            "gripper_base_joint": 0.0, "left_finger_joint": 0.0, "right_finger_joint": 0.0,
        },
    ),
    actuators={
        "arm": ImplicitActuatorCfg(
            joint_names_expr=["Revolute_.*", "gripper_base_joint"],
            effort_limit_sim=400.0,
            stiffness=500.0,   # V20 ile aynı
            damping=100.0,     # V20 ile aynı
        ),
        "gripper": ImplicitActuatorCfg(
            joint_names_expr=[".*_finger_joint"],
            stiffness=500.0,
            damping=100.0,
        ),
    },
)


@configclass
class My6dofReachSceneCfg_v21(ReachSceneCfg):
    table = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/Table",
        spawn=sim_utils.UsdFileCfg(
            usd_path=f"{ISAAC_NUCLEUS_DIR}/Props/Mounts/SeattleLabTable/table_instanceable.usd",
            scale=(3.0, 3.0, 1.0),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(0.0, 0.0, 0.0), rot=(0.70711, 0.0, 0.0, 0.70711)),
    )
    robot = CUSTOM_ROBOT_CFG_v21.replace(prim_path="{ENV_REGEX_NS}/Robot")


@configclass
class My6dofReachEnvCfg_v21(ReachEnvCfg):
    def __post_init__(self):
        super().__post_init__()

        self.episode_length_s = 20.0
        self.scene = My6dofReachSceneCfg_v21(num_envs=self.scene.num_envs, env_spacing=self.scene.env_spacing)

        # Body link
        self.rewards.end_effector_position_tracking.params["asset_cfg"].body_names = ["gripper_base_link"]
        self.rewards.end_effector_position_tracking_fine_grained.params["asset_cfg"].body_names = ["gripper_base_link"]
        self.rewards.end_effector_orientation_tracking.params["asset_cfg"].body_names = ["gripper_base_link"]

        # -----------------------------------------------------------------
        # POZİSYON ödülleri - fine_grained ağırlığı DÜŞÜRÜLDÜ (30 → 15)
        # -----------------------------------------------------------------
        self.rewards.end_effector_position_tracking.weight = 25.0
        self.rewards.end_effector_position_tracking.func = mdp.position_command_error_tanh
        self.rewards.end_effector_position_tracking.params["std"] = 0.5

        self.rewards.end_effector_position_tracking_fine_grained.weight = 15.0   # V20: 30 → V21: 15
        self.rewards.end_effector_position_tracking_fine_grained.params["std"] = 0.05

        # -----------------------------------------------------------------
        # ORYANTASYONcdot ödülü - ARTTIRILDI (12 → 25) + std daraltıldı (0.5 → 0.4)
        #
        # V20'de 1.5+ rad hatada orientaion reward ≈ 0 oluyordu (tanh doyuma ulaştı)
        # V21'de:
        #   std=0.4 → daha agresif gradient (1 rad hatada gradient ~3x daha büyük)
        #   weight=25 → fine_grained'den yüksek, oryantasyon öncelikli
        # -----------------------------------------------------------------
        self.rewards.end_effector_orientation_tracking.weight = 25.0             # V20: 12 → V21: 25
        self.rewards.end_effector_orientation_tracking.func = mdp.orientation_command_error_tanh
        self.rewards.end_effector_orientation_tracking.params["std"] = 0.4       # V20: 0.5 → V21: 0.4

        # -----------------------------------------------------------------
        # HAREKET cezaları - V20 ile aynı
        # -----------------------------------------------------------------
        self.rewards.action_rate.weight = -0.03
        self.rewards.joint_vel.weight = -0.005

        # Eylem ölçeği - V20 ile aynı
        self.actions.arm_action = mdp.JointPositionActionCfg(
            asset_name="robot",
            joint_names=["Revolute_.*", "gripper_base_joint"],
            scale=0.5,
            use_default_offset=True,
        )

        # Komutlar - V20 ile aynı
        self.commands.ee_pose.body_name = "gripper_base_link"
        self.commands.ee_pose.ranges.pos_x = (0.4, 1.1)
        self.commands.ee_pose.ranges.pos_y = (-0.6, 0.6)
        self.commands.ee_pose.ranges.pos_z = (0.1, 0.7)
        self.commands.ee_pose.ranges.roll  = (0.0, 0.0)
        self.commands.ee_pose.ranges.pitch = (math.pi, math.pi)
        self.commands.ee_pose.ranges.yaw   = (0.0, 0.0)


@configclass
class My6dofReachEnvCfg_v21_PLAY(My6dofReachEnvCfg_v21):
    def __post_init__(self):
        super().__post_init__()
        self.scene.num_envs = 32
        self.observations.policy.enable_corruption = False
