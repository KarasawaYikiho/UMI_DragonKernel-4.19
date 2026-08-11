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
