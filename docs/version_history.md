# Version History — S_Robot_Arm_RL

## V7 — Physics-Focused Stable Baseline
- **Stiffness:** 400, **Damping:** 80 (over-damped, zero vibration)
- **Episode Length:** 25s, **Action Scale:** 0.5
- **Task:** `Isaac-Reach-My6dof-v7`
- **Result:** Stable basic training, orientation not tracked

## V18 — Orientation Reward Added
- Added orientation penalty (-5.0)
- orientation_error stuck at ~0.42 rad

## V19 — Higher Stiffness
- Stiffness: 600, Damping: 160
- Orientation error still stuck at 0.42 rad
- **Problem:** Entropy collapse, learning rate → 0

## V20 — tanh Orientation + Entropy Fix
- New `orientation_command_error_tanh` reward function
- entropy_coef: 0.001 → 0.005
- desired_kl: 0.01 → 0.02
- **Problem:** fine_grained weight (30) >> orientation weight (12)
  → Agent learned to ignore orientation entirely → error reached 1.5+ rad (87°!)

## V21 — ✅ BEST VERSION
- **Fix:** Rebalanced reward weights
  - fine_grained: 30 → **15**
  - orientation: 12 → **25**
  - orientation std: 0.5 → **0.4**
- **Result at iter 5319/6000:**
  - Mean reward: **934**
  - Position error: **0.038m**
  - Orientation error: **0.040 rad (2.3°)**
