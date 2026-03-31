# S_Robot_Arm_RL

Custom 6-DOF Robot Arm — Reinforcement Learning Training with [IsaacLab](https://isaac-sim.github.io/IsaacLab/)

> **Best result (V21):** Position error ~3.8cm | Orientation error ~2.3° | Mean reward ~934

> **Tested with:** Isaac Sim 4.5 + IsaacLab (commit: `main` branch, early 2026)

---

## 🎬 Demo

![V21 Demo](media/v21_demo.gif)

*V21 trained policy — 32 parallel environments, ~2.3° orientation error, ~3.8cm position error*

---

## 📁 Repository Structure

```
S_Robot_Arm_RL/
├── robot_description/
│   ├── s_robot_arm_6dof.usd             # ✅ USD used in RL training (references robot_assembly/)
│   ├── robot_assembly/                  # ✅ Required by s_robot_arm_6dof.usd (relative path)
│   │   ├── robot_assembly.usd
│   │   ├── sonn.usd
│   │   └── configuration/
│   │       ├── robot_assembly_base.usd  # 4.6MB — geometry fully embedded, no external deps
│   │       ├── robot_assembly_physics.usd
│   │       ├── robot_assembly_robot.usd
│   │       └── robot_assembly_sensor.usd
│   ├── robot_assembly.urdf              # Full robot URDF
│   ├── robot_assembly_single_joint.urdf
│   ├── meshes/                          # STL mesh files
│   ├── final_controllers.yaml           # ROS2 controller config
│   └── unified_controllers.yaml
│
├── isaaclab_config/
│   ├── reach_env_cfg.py                 # Base environment config (from IsaacLab)
│   └── my_6dof_arm_v21/                 # ✅ Training configuration
│       ├── __init__.py                  # Gym environment registration
│       ├── joint_pos_env_cfg.py         # Environment config
│       └── agents/
│           ├── __init__.py
│           └── rsl_rl_ppo_cfg.py        # PPO algorithm config
│
├── mdp/
│   └── rewards.py                       # Custom reward functions
│
└── docs/
    └── version_history.md
```

---

## 🤖 Robot Specifications

| Property | Value |
|----------|-------|
| DOF | 6 + gripper |
| USD File | `robot_description/s_robot_arm_6dof.usd` |
| Stiffness | 500 |
| Damping | 100 |
| Workspace | 0.4–1.1m, ±60° cone |

---

## ⚙️ Requirements

- **NVIDIA Isaac Sim 4.x**
- **IsaacLab** — [Install Guide](https://isaac-sim.github.io/IsaacLab/main/source/setup/installation/index.html)
- GPU with CUDA support

---

## 🚀 Installation & Setup

### 1. Install IsaacLab

```bash
git clone https://github.com/isaac-sim/IsaacLab.git
cd IsaacLab

# Windows
.\isaaclab.bat --install
```

### 2. Copy the config folder

Copy `isaaclab_config/my_6dof_arm_v21/` into IsaacLab:

```
IsaacLab/source/isaaclab_tasks/isaaclab_tasks/manager_based/manipulation/reach/config/my_6dof_arm_v21/
```

### 3. Replace the reward file

**Copy and replace** (not append) `mdp/rewards.py` from this repo to:
```
IsaacLab/source/isaaclab_tasks/isaaclab_tasks/manager_based/manipulation/reach/mdp/rewards.py
```

This file contains all original IsaacLab reward functions **plus** the custom `orientation_command_error_tanh`. No other changes needed — the `mdp/__init__.py` already exports everything via `from .rewards import *`.

> ℹ️ You do **NOT** need to add any import to `config/__init__.py`. IsaacLab's `import_packages()` auto-discovers all config subpackages.

> ℹ️ `isaaclab_config/reach_env_cfg.py` in this repo is for **reference only** — it already exists in IsaacLab, do NOT copy it.

### 4. Update the USD path

In `isaaclab_config/my_6dof_arm_v21/joint_pos_env_cfg.py`, find the line starting with `usd_path=` and update it to your local path:

```python
usd_path="C:/YOUR_PATH/S_Robot_Arm_RL/robot_description/s_robot_arm_6dof.usd",
```


---

## 🏋️ Training

```powershell
cd <IsaacLab_root>

# Start training (headless recommended)
.\isaaclab.bat -p scripts\reinforcement_learning\rsl_rl\train.py `
  --task Isaac-Reach-My6dof-v21 `
  --num_envs 4096 `
  --headless

# Resume from checkpoint
.\isaaclab.bat -p scripts\reinforcement_learning\rsl_rl\train.py `
  --task Isaac-Reach-My6dof-v21 `
  --num_envs 4096 `
  --headless `
  --resume
```

### Key metrics to monitor

| Metric | Target |
|--------|--------|
| `orientation_error` | < 0.05 rad |
| `position_error` | < 0.05 m |
| `Mean reward` | > 900 |
| `Mean entropy loss` | > 7.0 |

---

## 🎮 Playback

```powershell
.\isaaclab.bat -p scripts\reinforcement_learning\rsl_rl\play.py `
  --task Isaac-Reach-My6dof-v21-Play `
  --num_envs 32
```

---

## 🔧 Key Parameters — V21

**PPO** (`agents/rsl_rl_ppo_cfg.py`):
```python
entropy_coef = 0.005   # Prevents entropy collapse
desired_kl   = 0.02
```

### 🏅 Reward Structure & Weights (`joint_pos_env_cfg.py`)

Rewards are carefully shaped to optimize the agent's learning behavior. In the V21 version, a balance between position and orientation is established, ensuring the robot not only reaches the target but also maintains the exact desired angle.

| Reward Name / Function | Weight | Parameter (std) | Purpose & Effect |
| :--- | :---: | :---: | :--- |
| **`end_effector_position_tracking`**<br>`position_command_error_tanh` | **25.0** | `0.5` | Provides **general (coarse) position tracking** to guide the end-effector toward the target. With `std=0.5`, the robot is gradually pulled toward the target even from a distance. |
| **`end_effector_position_tracking_fine_grained`** | **15.0** | `0.05` | Provides **highly precise position tracking** that takes over when close to the target. Due to `std=0.05`, it grants high rewards only at millimeter distances, locking the robot directly to the center. In V21, its weight is reduced from 30 to 15 to prevent the agent from collapsing the orientation in favor of proximity greed. |
| **`end_effector_orientation_tracking`**<br>`orientation_command_error_tanh` | **25.0** | `0.4` | A **custom orientation reward** written specifically for `S_Robot_Arm_RL`. A `std=0.4` value creates an aggressive gradient. If the robot is at a bad angle (`>1.5 rad`), it receives near-zero points. As it aligns correctly, the reward scales up exponentially via a **tanh** function. Setting this weight to 25 makes it the primary driving factor forcing the robot to fix its angle. |
| **`action_rate`** | **-0.03** | `-` | Penalizes sudden changes (jerks) between consecutive actions. Prevents robot jittering and ensures a smooth, realistic control signal. |
| **`joint_vel`** | **-0.005** | `-` | Penalizes excessively high joint velocities. Prevents simulation instability and ensures safer, controlled movements. |

**Physics**:
```python
stiffness = 500.0
damping   = 100.0
```

---

## 📄 Custom Reward Functions (`mdp/rewards.py`)

To fill the gaps in the standard IsaacLab architecture, a **positive reward function** (`orientation_command_error_tanh`) was written. Rather than merely penalizing orientation errors, this explicitly encourages correct orientation:

```python
def orientation_command_error_tanh(env, std, command_name, asset_cfg):
    # reward = 1 - tanh(error / std)
```

For `std=0.4`, this formulation yields:
* Error `0.0 rad` (perfect align) → **Reward = 1.0** *(maximum)*
* Error `0.4 rad` → **Reward ≈ 0.46** *(moderate)*
* Error `1.0 rad` → **Reward ≈ 0.07** *(very low)*
* Error `1.5 rad` → **Reward ≈ 0.02** *(near zero)*

This logic ensures the robot is heavily reinforced at every step as long as it maintains the correct angle. For further math and implementation details, refer to `mdp/rewards.py`.

---

## 🏆 Final Results (V21, ~6000 iterations)

| Metric | Value |
|--------|-------|
| Mean reward | **934** |
| Position error | **0.038m** |
| Orientation error | **0.040 rad (2.3°)** |
| Training time | ~2 hours (RTX GPU) |

---

## 📝 License

MIT License — ITU Industrial Robotics Team
