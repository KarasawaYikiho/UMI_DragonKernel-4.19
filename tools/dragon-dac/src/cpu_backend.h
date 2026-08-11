#pragma once

#include <sys/syscall.h>
#include <unistd.h>

#include <cerrno>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <map>
#include <string>

namespace dragon {

struct SchedAttr {
  uint32_t size = sizeof(SchedAttr);
  uint32_t policy = 0;
  uint64_t flags = 0;
  int32_t nice = 0;
  uint32_t priority = 0;
  uint64_t runtime = 0;
  uint64_t deadline = 0;
  uint64_t period = 0;
  uint32_t util_min = 0;
  uint32_t util_max = 1024;
};

class CpuBackend {
 public:
  ~CpuBackend() {
    std::string ignored;
    restore_all(&ignored);
  }

  static bool valid_bounds(uint32_t util_min, uint32_t util_max) {
    return util_min <= util_max && util_max <= 1024;
  }

  bool supported() const {
    SchedAttr attributes;
    return get(0, &attributes) && attributes.size >= sizeof(SchedAttr);
  }

  bool apply(int tid, uint32_t util_min, uint32_t util_max, std::string* error) {
    if (tid <= 0 || !valid_bounds(util_min, util_max)) {
      *error = "invalid uclamp request";
      return false;
    }
    SchedAttr current;
    if (!get(tid, &current)) {
      *error = "sched_getattr failed: " + std::string(std::strerror(errno));
      return false;
    }
    auto iterator = records_.find(tid);
    const bool inserted = iterator == records_.end();
    if (iterator == records_.end()) {
      iterator = records_.emplace(tid, Record {current, current}).first;
    } else if (!same_clamps(current, iterator->second.applied)) {
      *error = "uclamp ownership changed externally";
      return false;
    }
    SchedAttr next = current;
    next.flags |= kUtilClampMin | kUtilClampMax;
    next.util_min = util_min;
    next.util_max = util_max;
    if (!set(tid, next)) {
      if (inserted) records_.erase(iterator);
      *error = "sched_setattr failed: " + std::string(std::strerror(errno));
      return false;
    }
    iterator->second.applied = next;
    SchedAttr verified;
    if (!get(tid, &verified) || !same_clamps(verified, next)) {
      *error = "uclamp verification failed";
      return false;
    }
    iterator->second.applied = verified;
    return true;
  }

  bool restore_all(std::string* error) {
    bool restored = true;
    std::map<int, Record> remaining;
    for (const auto& [tid, record] : records_) {
      SchedAttr current;
      if (!get(tid, &current)) {
        if (errno != ESRCH) {
          restored = false;
          remaining.emplace(tid, record);
        }
        continue;
      }
      if (!same_clamps(current, record.applied)) {
        restored = false;
        continue;
      }
      SchedAttr original = current;
      original.flags |= kUtilClampMin | kUtilClampMax;
      original.util_min = record.original.util_min;
      original.util_max = record.original.util_max;
      if (!set(tid, original)) {
        restored = false;
        remaining.emplace(tid, record);
      }
    }
    records_.swap(remaining);
    if (!restored) *error = "one or more uclamp owners could not be restored";
    return restored;
  }

  std::size_t owned() const { return records_.size(); }

 private:
  static constexpr uint64_t kUtilClampMin = 0x20;
  static constexpr uint64_t kUtilClampMax = 0x40;

  struct Record {
    SchedAttr original;
    SchedAttr applied;
  };

  static bool same_clamps(const SchedAttr& left, const SchedAttr& right) {
    return left.util_min == right.util_min && left.util_max == right.util_max;
  }

  static bool get(int tid, SchedAttr* attributes) {
    *attributes = SchedAttr {};
    return syscall(__NR_sched_getattr, tid, attributes, sizeof(*attributes), 0) == 0;
  }

  static bool set(int tid, const SchedAttr& attributes) {
    return syscall(__NR_sched_setattr, tid, &attributes, 0) == 0;
  }

  std::map<int, Record> records_;
};

}  // namespace dragon
