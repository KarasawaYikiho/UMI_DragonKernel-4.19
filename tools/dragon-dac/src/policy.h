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
