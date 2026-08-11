#pragma once

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <map>

namespace dragon {

enum class BoostOwner {
  kTouch,
  kAppLaunch,
  kGameLoading,
  kFrameRescue,
};

enum class FreezeState {
  kActive,
  kBackground,
  kCached,
  kFreezeDelay,
  kEligibilityCheck,
  kBinderPrepare,
  kFreezing,
  kFrozen,
  kThawing,
};

enum class Bottleneck {
  kNone,
  kCpu,
  kGpu,
  kMemory,
  kThermal,
};

enum class ThermalState {
  kNormal,
  kWarm,
  kHot,
  kCritical,
};

enum class Scene {
  kBoot,
  kScreenOff,
  kScreenOnIdle,
  kDaily,
  kInteractive,
  kScroll,
  kAppLaunch,
  kAppSwitch,
  kVideo,
  kAudio,
  kCamera,
  kGameLoading,
  kGame,
  kGameFrameRescue,
  kGameThermal,
  kCharging,
  kBatterySaver,
  kThermalEmergency,
  kSafe,
};

struct SceneInputs {
  bool valid = true;
  bool booting = false;
  bool screen_on = true;
  bool idle = false;
  bool interactive = false;
  bool scrolling = false;
  bool app_launch = false;
  bool app_switch = false;
  bool video = false;
  bool audio = false;
  bool camera = false;
  bool game_loading = false;
  bool game = false;
  bool frame_late = false;
  bool thermal_limited = false;
  bool thermal_emergency = false;
  bool charging = false;
  bool battery_saver = false;
};

class SceneSelector {
 public:
  Scene update(const SceneInputs& input) {
    charging_ = input.charging;
    battery_saver_ = input.battery_saver;
    if (!input.valid) scene_ = Scene::kSafe;
    else if (input.thermal_emergency) scene_ = Scene::kThermalEmergency;
    else if (input.booting) scene_ = Scene::kBoot;
    else if (!input.screen_on) scene_ = Scene::kScreenOff;
    else if (input.game && input.thermal_limited) scene_ = Scene::kGameThermal;
    else if (input.game_loading) scene_ = Scene::kGameLoading;
    else if (input.game && input.frame_late) scene_ = Scene::kGameFrameRescue;
    else if (input.game) scene_ = Scene::kGame;
    else if (input.camera) scene_ = Scene::kCamera;
    else if (input.app_launch) scene_ = Scene::kAppLaunch;
    else if (input.app_switch) scene_ = Scene::kAppSwitch;
    else if (input.scrolling) scene_ = Scene::kScroll;
    else if (input.interactive) scene_ = Scene::kInteractive;
    else if (input.video) scene_ = Scene::kVideo;
    else if (input.audio) scene_ = Scene::kAudio;
    else if (input.battery_saver) scene_ = Scene::kBatterySaver;
    else if (input.charging) scene_ = Scene::kCharging;
    else if (input.idle) scene_ = Scene::kScreenOnIdle;
    else scene_ = Scene::kDaily;
    return scene_;
  }

  Scene scene() const { return scene_; }
  bool charging() const { return charging_; }
  bool battery_saver() const { return battery_saver_; }

 private:
  Scene scene_ = Scene::kBoot;
  bool charging_ = false;
  bool battery_saver_ = false;
};

struct GameDecision {
  Bottleneck bottleneck = Bottleneck::kNone;
  uint32_t rescue = 0;
};

class DailyBudgetController {
 public:
  explicit DailyBudgetController(uint32_t step = 64, uint32_t samples = 3)
      : step_(std::min(step, 1024U)), samples_(std::max(samples, 1U)) {}

  uint32_t update(uint32_t power_mw, uint32_t target_mw, bool latency_ok) {
    if (!latency_ok) {
      over_budget_ = 0;
      allowance_ = std::min(1024U, allowance_ + step_);
    } else if (target_mw != 0 && power_mw > target_mw) {
      if (++over_budget_ >= samples_) {
        allowance_ = allowance_ > step_ ? allowance_ - step_ : 0;
        over_budget_ = 0;
      }
    } else {
      over_budget_ = 0;
    }
    return allowance_;
  }

  uint32_t allowance() const { return allowance_; }

 private:
  uint32_t step_;
  uint32_t samples_;
  uint32_t over_budget_ = 0;
  uint32_t allowance_ = 1024;
};

class GameController {
 public:
  explicit GameController(uint32_t step = 64, uint32_t samples = 3)
      : step_(std::min(step, 1024U)), samples_(std::max(samples, 1U)) {}

  GameDecision update(uint32_t target_frame_us, uint32_t p95_frame_us,
                      uint32_t cpu_pressure, uint32_t gpu_pressure,
                      uint32_t memory_pressure, bool thermal_limited) {
    if (thermal_limited) {
      violations_ = 0;
      recoveries_ = 0;
      rescue_ = 0;
      return {Bottleneck::kThermal, 0};
    }
    if (target_frame_us == 0 || cpu_pressure > 1024 || gpu_pressure > 1024 ||
        memory_pressure > 1024) {
      violations_ = 0;
      recoveries_ = 0;
      rescue_ = 0;
      return {};
    }
    if (static_cast<uint64_t>(p95_frame_us) * 100U >
        static_cast<uint64_t>(target_frame_us) * 105U) {
      if (++violations_ < samples_) return {Bottleneck::kNone, rescue_};
      violations_ = 0;
      recoveries_ = 0;
      rescue_ = std::min(1024U, rescue_ + step_);
      if (gpu_pressure >= cpu_pressure && gpu_pressure >= memory_pressure)
        return {Bottleneck::kGpu, rescue_};
      if (memory_pressure >= cpu_pressure)
        return {Bottleneck::kMemory, rescue_};
      return {Bottleneck::kCpu, rescue_};
    }
    violations_ = 0;
    if (p95_frame_us <= target_frame_us && ++recoveries_ >= samples_) {
      rescue_ = rescue_ > step_ ? rescue_ - step_ : 0;
      recoveries_ = 0;
    }
    return {Bottleneck::kNone, rescue_};
  }

 private:
  uint32_t step_;
  uint32_t samples_;
  uint32_t violations_ = 0;
  uint32_t recoveries_ = 0;
  uint32_t rescue_ = 0;
};

struct ThermalConfig {
  uint32_t warm_enter;
  uint32_t warm_exit;
  uint32_t hot_enter;
  uint32_t hot_exit;
  uint32_t critical_enter;
  uint32_t critical_exit;
  uint32_t warm_cap;
  uint32_t hot_cap;
  uint32_t critical_cap;
  uint64_t recovery_dwell_ms;
};

class ThermalGuard {
 public:
  explicit ThermalGuard(ThermalConfig config)
      : config_(config), valid_(valid(config)) {}

  static bool valid(const ThermalConfig& config) {
    return config.critical_enter < config.hot_enter &&
           config.hot_enter < config.warm_enter &&
           config.warm_exit > config.warm_enter &&
           config.hot_exit > config.hot_enter &&
           config.critical_exit > config.critical_enter &&
           config.critical_cap <= config.hot_cap &&
           config.hot_cap <= config.warm_cap && config.warm_cap <= 1024;
  }

  ThermalState update(uint32_t headroom, uint64_t now_ms) {
    if (!valid_) {
      state_ = ThermalState::kCritical;
      return state_;
    }
    const ThermalState previous = state_;
    ThermalState hotter = state_;
    if (headroom <= config_.critical_enter) hotter = ThermalState::kCritical;
    else if (headroom <= config_.hot_enter && state_ < ThermalState::kHot)
      hotter = ThermalState::kHot;
    else if (headroom <= config_.warm_enter && state_ < ThermalState::kWarm)
      hotter = ThermalState::kWarm;
    if (hotter > state_) {
      state_ = hotter;
      entered_ms_ = now_ms;
      return state_;
    }
    if (now_ms - entered_ms_ < config_.recovery_dwell_ms) return state_;
    if (state_ == ThermalState::kCritical && headroom >= config_.critical_exit)
      state_ = ThermalState::kHot;
    else if (state_ == ThermalState::kHot && headroom >= config_.hot_exit)
      state_ = ThermalState::kWarm;
    else if (state_ == ThermalState::kWarm && headroom >= config_.warm_exit)
      state_ = ThermalState::kNormal;
    if (state_ != previous) entered_ms_ = now_ms;
    return state_;
  }

  uint32_t cap() const {
    if (!valid_) return 0;
    if (state_ == ThermalState::kCritical) return config_.critical_cap;
    if (state_ == ThermalState::kHot) return config_.hot_cap;
    if (state_ == ThermalState::kWarm) return config_.warm_cap;
    return 1024;
  }

 private:
  ThermalConfig config_;
  bool valid_;
  ThermalState state_ = ThermalState::kNormal;
  uint64_t entered_ms_ = 0;
};

class FreezeStateMachine {
 public:
  FreezeState state() const { return state_; }

  bool transition(FreezeState next) {
    const bool allowed =
        (state_ == FreezeState::kActive && next == FreezeState::kBackground) ||
        (state_ == FreezeState::kBackground && next == FreezeState::kCached) ||
        (state_ == FreezeState::kCached && next == FreezeState::kFreezeDelay) ||
        (state_ == FreezeState::kFreezeDelay && next == FreezeState::kEligibilityCheck) ||
        (state_ == FreezeState::kEligibilityCheck && next == FreezeState::kBinderPrepare) ||
        (state_ == FreezeState::kBinderPrepare && next == FreezeState::kFreezing) ||
        (state_ == FreezeState::kFreezing && next == FreezeState::kFrozen) ||
        (state_ == FreezeState::kFrozen && next == FreezeState::kThawing) ||
        (state_ == FreezeState::kThawing && next == FreezeState::kActive) ||
        (state_ != FreezeState::kFrozen && state_ != FreezeState::kThawing &&
         next == FreezeState::kActive);
    if (allowed) state_ = next;
    return allowed;
  }

 private:
  FreezeState state_ = FreezeState::kActive;
};

class BoostArbiter {
 public:
  bool acquire(BoostOwner owner, uint32_t uclamp_min, uint64_t deadline_ns) {
    if (uclamp_min > 1024 || deadline_ns == 0) return false;
    requests_[owner] = {uclamp_min, deadline_ns};
    return true;
  }

  void release(BoostOwner owner) { requests_.erase(owner); }

  void set_thermal_cap(uint32_t cap) { thermal_cap_ = std::min(cap, 1024U); }

  uint32_t effective(uint64_t now_ns) {
    uint32_t floor = 0;
    for (auto iterator = requests_.begin(); iterator != requests_.end();) {
      if (iterator->second.deadline_ns <= now_ns) {
        iterator = requests_.erase(iterator);
      } else {
        floor = std::max(floor, iterator->second.uclamp_min);
        ++iterator;
      }
    }
    return std::min(floor, thermal_cap_);
  }

  std::size_t active() const { return requests_.size(); }

 private:
  struct Request {
    uint32_t uclamp_min;
    uint64_t deadline_ns;
  };

  std::map<BoostOwner, Request> requests_;
  uint32_t thermal_cap_ = 1024;
};

}  // namespace dragon
