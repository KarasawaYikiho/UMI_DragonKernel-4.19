#include <dirent.h>
#include <linux/bpf.h>
#include <linux/filter.h>
#include <sys/epoll.h>
#include <sys/file.h>
#include <sys/inotify.h>
#include <sys/ioctl.h>
#include <sys/signalfd.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/timerfd.h>
#include <unistd.h>

#include <fcntl.h>

#include <cerrno>
#include <cstdint>
#include <csignal>
#include <ctime>
#include <cstdlib>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <initializer_list>
#include <map>
#include <set>
#include <sstream>
#include <string>
#include <vector>

#include "cpu_backend.h"
#include "policy.h"

namespace {

constexpr int kMaxEvents = 4;
constexpr uint64_t kHeartbeatIntervalSeconds = 30;
constexpr uint64_t kAndroidUidRange = 100000;
constexpr uint64_t kAndroidSystemAppId = 1000;

struct Config {
  bool enabled = false;
  bool freezer = false;
  bool game = false;
  bool ddr = false;
  bool cpu = false;
  bool dry_run = true;
  int telemetry_interval_s = 5;
  std::string mode = "auto";
  std::string cloud_control = "block";
};

struct CloudAttachment {
  int ingress_link_fd = -1;
  int egress_link_fd = -1;
};

struct BinderFrozenStatusInfo {
  uint32_t pid;
  uint32_t sync_recv;
  uint32_t async_recv;
};

constexpr unsigned long kBinderGetFrozenInfo =
    _IOWR('b', 15, BinderFrozenStatusInfo);

std::string trim(std::string value) {
  const auto first = value.find_first_not_of(" \t\r\n");
  if (first == std::string::npos) return {};
  const auto last = value.find_last_not_of(" \t\r\n");
  return value.substr(first, last - first + 1);
}

bool parse_bool(const std::string& value, bool* out) {
  if (value == "1" || value == "true") {
    *out = true;
    return true;
  }
  if (value == "0" || value == "false") {
    *out = false;
    return true;
  }
  return false;
}

bool load_config(const std::string& path, Config* config, std::string* error) {
  std::ifstream input(path);
  if (!input) {
    *error = "config unavailable: " + path;
    return false;
  }
  Config candidate;
  std::string line;
  int line_number = 0;
  while (std::getline(input, line)) {
    ++line_number;
    line = trim(line);
    if (line.empty() || line[0] == '#') continue;
    const auto delimiter = line.find('=');
    if (delimiter == std::string::npos) {
      *error = "invalid config line " + std::to_string(line_number);
      return false;
    }
    const std::string key = trim(line.substr(0, delimiter));
    const std::string value = trim(line.substr(delimiter + 1));
    bool* boolean = nullptr;
    if (key == "dac.enabled") boolean = &candidate.enabled;
    else if (key == "dac.cpu.enabled") boolean = &candidate.cpu;
    else if (key == "dac.freezer.enabled") boolean = &candidate.freezer;
    else if (key == "dac.game.enabled") boolean = &candidate.game;
    else if (key == "dac.ddr.enabled") boolean = &candidate.ddr;
    else if (key == "dac.dry_run") boolean = &candidate.dry_run;
    if (boolean) {
      if (!parse_bool(value, boolean)) {
        *error = "invalid boolean for " + key;
        return false;
      }
    } else if (key == "dac.mode") {
      if (value != "auto" && value != "safe") {
        *error = "invalid dac.mode";
        return false;
      }
      candidate.mode = value;
    } else if (key == "dac.cloud_control.remote") {
      if (value != "observe" && value != "block") {
        *error = "invalid cloud control mode";
        return false;
      }
      candidate.cloud_control = value;
    } else if (key == "telemetry.interval_s") {
      try {
        candidate.telemetry_interval_s = std::stoi(value);
      } catch (...) {
        *error = "invalid telemetry interval";
        return false;
      }
      if (candidate.telemetry_interval_s < 1 || candidate.telemetry_interval_s > 60) {
        *error = "telemetry interval outside 1..60";
        return false;
      }
    } else {
      *error = "unknown config key: " + key;
      return false;
    }
  }
  *config = candidate;
  return true;
}

std::string json_escape(const std::string& value) {
  std::string output;
  for (const char character : value) {
    switch (character) {
      case '\\': output += "\\\\"; break;
      case '"': output += "\\\""; break;
      case '\n': output += "\\n"; break;
      case '\r': output += "\\r"; break;
      case '\t': output += "\\t"; break;
      default: output += character;
    }
  }
  return output;
}

bool path_exists(const char* path) {
  struct stat status {};
  return stat(path, &status) == 0;
}

bool binder_freezer_supported() {
  const int descriptor = open("/dev/binder", O_RDWR | O_CLOEXEC);
  if (descriptor < 0) return false;
  BinderFrozenStatusInfo information {static_cast<uint32_t>(getpid()), 0, 0};
  const bool supported = ioctl(descriptor, kBinderGetFrozenInfo, &information) == 0;
  close(descriptor);
  return supported;
}

std::string parent_path(const std::string& path) {
  const auto separator = path.find_last_of('/');
  return separator == std::string::npos ? "." : path.substr(0, separator);
}

bool is_decimal(const char* value) {
  if (!*value) return false;
  for (const char* cursor = value; *cursor; ++cursor) {
    if (*cursor < '0' || *cursor > '9') return false;
  }
  return true;
}

bool is_joyose_name(const std::string& name) {
  constexpr char kPackage[] = "com.xiaomi.joyose";
  return name == kPackage ||
         (name.compare(0, sizeof(kPackage) - 1, kPackage) == 0 &&
          name.size() > sizeof(kPackage) - 1 && name[sizeof(kPackage) - 1] == ':');
}

bool is_joyose_identity(const std::string& name, uint64_t effective_uid) {
  return effective_uid % kAndroidUidRange == kAndroidSystemAppId &&
         is_joyose_name(name);
}

bool read_proc_file_at(int proc_fd, const char* name, std::string* output) {
  const int fd = openat(proc_fd, name, O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
  if (fd < 0) return false;
  char buffer[4096];
  output->clear();
  while (output->size() < 65536) {
    const ssize_t count = read(fd, buffer, sizeof(buffer));
    if (count == 0) break;
    if (count < 0) {
      if (errno == EINTR) continue;
      close(fd);
      output->clear();
      return false;
    }
    output->append(buffer, static_cast<size_t>(count));
  }
  const bool complete = output->size() < 65536;
  close(fd);
  if (!complete) output->clear();
  return complete;
}

bool effective_uid_from_status(const std::string& status, uint64_t* uid) {
  std::istringstream input(status);
  std::string line;
  while (std::getline(input, line)) {
    if (line.compare(0, 4, "Uid:") != 0) continue;
    uint64_t real = 0;
    uint64_t effective = 0;
    uint64_t saved = 0;
    uint64_t filesystem = 0;
    std::istringstream values(line.substr(4));
    if (!(values >> real >> effective >> saved >> filesystem)) return false;
    *uid = effective;
    return true;
  }
  return false;
}

bool is_joyose_pid(int pid) {
  const std::string proc_path = "/proc/" + std::to_string(pid);
  const int proc_fd = open(proc_path.c_str(), O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW);
  if (proc_fd < 0) return false;
  std::string cmdline;
  std::string status;
  const bool readable = read_proc_file_at(proc_fd, "cmdline", &cmdline) &&
                        read_proc_file_at(proc_fd, "status", &status);
  close(proc_fd);
  uint64_t effective_uid = 0;
  if (!readable || !effective_uid_from_status(status, &effective_uid)) return false;
  const auto terminator = cmdline.find('\0');
  if (terminator != std::string::npos) cmdline.resize(terminator);
  return is_joyose_identity(cmdline, effective_uid);
}

std::string unified_cgroup_path(const std::string& content) {
  std::istringstream input(content);
  std::string line;
  while (std::getline(input, line)) {
    if (line.compare(0, 3, "0::") == 0) {
      const std::string path = trim(line.substr(3));
      if (!path.empty() && path[0] == '/' && path.find("..") == std::string::npos) return path;
    }
  }
  return {};
}

bool scan_joyose_cgroups(std::set<std::string>* paths, int* process_count,
                         std::string* error) {
  DIR* directory = opendir("/proc");
  if (!directory) {
    *error = "cannot scan process table";
    return false;
  }
  dirent* entry = nullptr;
  while ((entry = readdir(directory)) != nullptr) {
    if (!is_decimal(entry->d_name)) continue;
    const int pid = std::atoi(entry->d_name);
    if (!is_joyose_pid(pid)) continue;
    ++*process_count;
    std::ifstream input("/proc/" + std::to_string(pid) + "/cgroup");
    std::ostringstream content;
    content << input.rdbuf();
    const std::string path = unified_cgroup_path(content.str());
    if (path.empty()) {
      closedir(directory);
      *error = "Joyose has no isolated cgroup v2 path";
      return false;
    }
    paths->insert(path);
  }
  closedir(directory);
  return true;
}

bool cgroup_is_joyose_only(const std::string& path) {
  std::ifstream input("/sys/fs/cgroup" + path + "/cgroup.procs");
  int pid = 0;
  bool found = false;
  while (input >> pid) {
    found = true;
    if (!is_joyose_pid(pid)) return false;
  }
  return found;
}

int bpf_call(enum bpf_cmd command, union bpf_attr* attributes) {
  return static_cast<int>(syscall(__NR_bpf, command, attributes, sizeof(*attributes)));
}

int load_drop_program(enum bpf_attach_type attach_type, std::string* error) {
  bpf_insn instructions[2] {};
  instructions[0].code = BPF_ALU64 | BPF_MOV | BPF_K;
  instructions[0].dst_reg = BPF_REG_0;
  instructions[0].imm = 0;
  instructions[1].code = BPF_JMP | BPF_EXIT;
  const char license[] = "GPL";
  char verifier_log[4096] {};
  union bpf_attr attributes {};
  attributes.prog_type = BPF_PROG_TYPE_CGROUP_SKB;
  attributes.expected_attach_type = attach_type;
  attributes.insn_cnt = 2;
  attributes.insns = reinterpret_cast<uint64_t>(instructions);
  attributes.license = reinterpret_cast<uint64_t>(license);
  attributes.log_buf = reinterpret_cast<uint64_t>(verifier_log);
  attributes.log_size = sizeof(verifier_log);
  attributes.log_level = 1;
  const int descriptor = bpf_call(BPF_PROG_LOAD, &attributes);
  if (descriptor < 0) *error = "cgroup BPF load failed: " + std::string(std::strerror(errno));
  return descriptor;
}

int create_link(int cgroup_fd, int program_fd, enum bpf_attach_type attach_type,
                std::string* error) {
  union bpf_attr attributes {};
  attributes.link_create.target_fd = cgroup_fd;
  attributes.link_create.prog_fd = program_fd;
  attributes.link_create.attach_type = attach_type;
  const int descriptor = bpf_call(BPF_LINK_CREATE, &attributes);
  if (descriptor < 0) *error = "cgroup BPF link failed: " + std::string(std::strerror(errno));
  return descriptor;
}

class CloudIsolator {
 public:
  ~CloudIsolator() { clear(); }

  bool reconcile(bool block, std::string* status, std::string* error) {
    if (!block) {
      clear();
      *status = "observe";
      return true;
    }
    std::set<std::string> desired;
    int process_count = 0;
    if (!scan_joyose_cgroups(&desired, &process_count, error)) {
      clear();
      *status = "safe";
      return false;
    }
    if (process_count == 0) {
      clear();
      *status = "not-present";
      return true;
    }
    for (const auto& path : desired) {
      if (!cgroup_is_joyose_only(path)) {
        clear();
        *error = "Joyose cgroup is shared or unavailable";
        *status = "safe";
        return false;
      }
    }
    for (auto iterator = attachments_.begin(); iterator != attachments_.end();) {
      if (desired.count(iterator->first) == 0) {
        release(&iterator->second);
        iterator = attachments_.erase(iterator);
      } else {
        ++iterator;
      }
    }
    for (const auto& path : desired) {
      if (attachments_.count(path) != 0) continue;
      CloudAttachment attachment;
      const int cgroup_fd = open(("/sys/fs/cgroup" + path).c_str(),
                                 O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW);
      if (cgroup_fd < 0) *error = "cannot open Joyose cgroup";
      if (cgroup_fd < 0 || !prepare(cgroup_fd, &attachment, error)) {
        if (cgroup_fd >= 0) close(cgroup_fd);
        release(&attachment);
        clear();
        *status = "safe";
        return false;
      }
      close(cgroup_fd);
      if (!cgroup_is_joyose_only(path)) {
        release(&attachment);
        clear();
        *error = "Joyose cgroup membership changed during attach";
        *status = "safe";
        return false;
      }
      attachments_.emplace(path, attachment);
    }
    *status = "blocked";
    error->clear();
    return true;
  }

  void clear() {
    for (auto& [path, attachment] : attachments_) {
      (void)path;
      release(&attachment);
    }
    attachments_.clear();
  }

  size_t count() const { return attachments_.size(); }

 private:
  static bool prepare(int cgroup_fd, CloudAttachment* attachment, std::string* error) {
    int program_fd = load_drop_program(BPF_CGROUP_INET_INGRESS, error);
    if (program_fd < 0) return false;
    attachment->ingress_link_fd = create_link(cgroup_fd, program_fd,
                                              BPF_CGROUP_INET_INGRESS, error);
    close(program_fd);
    if (attachment->ingress_link_fd < 0) return false;
    program_fd = load_drop_program(BPF_CGROUP_INET_EGRESS, error);
    if (program_fd < 0) return false;
    attachment->egress_link_fd = create_link(cgroup_fd, program_fd,
                                             BPF_CGROUP_INET_EGRESS, error);
    close(program_fd);
    if (attachment->egress_link_fd < 0) return false;
    return true;
  }

  static void release(CloudAttachment* attachment) {
    for (const int descriptor : {attachment->egress_link_fd,
                                 attachment->ingress_link_fd}) {
      if (descriptor >= 0) close(descriptor);
    }
    *attachment = CloudAttachment {};
  }

  std::map<std::string, CloudAttachment> attachments_;
};

std::map<std::string, bool> probe_backends() {
  return {
      {"schedtune", path_exists("/dev/stune")},
      {"cgroup", path_exists("/sys/fs/cgroup")},
      {"cgroup_bpf", path_exists("/sys/fs/cgroup/cgroup.controllers")},
      {"binder_freezer", binder_freezer_supported()},
      {"kgsl", path_exists("/sys/class/kgsl/kgsl-3d0")},
      {"devfreq", path_exists("/sys/class/devfreq")},
      {"thermal", path_exists("/sys/class/thermal")},
      {"cpu_boost", path_exists("/sys/devices/system/cpu/cpu_boost")},
  };
}

bool atomic_write(const std::string& path, const std::string& data) {
  const std::string temporary = path + ".tmp";
  const int file = open(temporary.c_str(), O_CREAT | O_TRUNC | O_WRONLY | O_CLOEXEC |
                                           O_NOFOLLOW, 0600);
  if (file < 0) return false;
  const ssize_t written = write(file, data.data(), data.size());
  const bool ok = written == static_cast<ssize_t>(data.size()) && fsync(file) == 0;
  close(file);
  if (!ok || rename(temporary.c_str(), path.c_str()) != 0) {
    unlink(temporary.c_str());
    return false;
  }
  return true;
}

uint64_t boottime_seconds() {
  timespec value {};
  if (clock_gettime(CLOCK_BOOTTIME, &value) != 0 || value.tv_sec < 0) return 0;
  return static_cast<uint64_t>(value.tv_sec);
}

void close_fds(std::initializer_list<int> descriptors) {
  for (const int descriptor : descriptors) {
    if (descriptor >= 0) close(descriptor);
  }
}

bool arm_timer(int descriptor, int interval_s) {
  itimerspec timer {};
  timer.it_value.tv_sec = interval_s;
  timer.it_interval.tv_sec = interval_s;
  return timerfd_settime(descriptor, 0, &timer, nullptr) == 0;
}

std::string status_json(const std::string& scene, const Config& config,
                        const std::string& cloud_status, size_t cloud_cgroups,
                        const std::string& error,
                        const std::map<std::string, bool>& backends) {
  std::ostringstream output;
  output << "{\n  \"schema\": 1,\n  \"scene\": \"" << scene << "\",\n"
         << "  \"enabled\": " << (config.enabled ? "true" : "false") << ",\n"
         << "  \"dry_run\": " << (config.dry_run ? "true" : "false") << ",\n"
         << "  \"cloud_control\": \"" << config.cloud_control << "\",\n"
         << "  \"cloud_status\": \"" << cloud_status << "\",\n"
         << "  \"cloud_cgroups\": " << cloud_cgroups << ",\n"
         << "  \"error\": \"" << json_escape(error) << "\",\n"
         << "  \"owned_resources\": [],\n  \"backends\": {";
  bool first = true;
  for (const auto& [name, supported] : backends) {
    output << (first ? "\n" : ",\n") << "    \"" << name << "\": "
           << (supported ? "true" : "false");
    first = false;
  }
  output << "\n  }\n}\n";
  return output.str();
}

int run_self_test() {
  bool value = false;
  if (!parse_bool("true", &value) || !value) return 1;
  if (!parse_bool("0", &value) || value) return 1;
  if (parse_bool("invalid", &value)) return 1;
  if (json_escape("a\"b\\c\n") != "a\\\"b\\\\c\\n") return 1;
  if (!is_joyose_name("com.xiaomi.joyose") ||
      !is_joyose_name("com.xiaomi.joyose:worker") ||
      is_joyose_name("com.xiaomi.joyose.other")) return 1;
  if (!is_joyose_identity("com.xiaomi.joyose", 1000) ||
      !is_joyose_identity("com.xiaomi.joyose:worker", 101000) ||
      is_joyose_identity("com.xiaomi.joyose", 10000) ||
      is_joyose_identity("com.xiaomi.joyose.other", 1000)) return 1;
  uint64_t parsed_uid = 0;
  if (!effective_uid_from_status("Name:\tjoyose\nUid:\t1000\t1000\t1000\t1000\n",
                                 &parsed_uid) ||
      parsed_uid != 1000 ||
      effective_uid_from_status("Uid:\tbroken\n", &parsed_uid)) return 1;
  if (unified_cgroup_path("2:cpu:/x\n0::/uid_1000/pid_12\n") !=
      "/uid_1000/pid_12") return 1;
  if (!unified_cgroup_path("0::/../unsafe\n").empty()) return 1;
  dragon::BoostArbiter arbiter;
  if (!arbiter.acquire(dragon::BoostOwner::kTouch, 128, 20) ||
      !arbiter.acquire(dragon::BoostOwner::kAppLaunch, 256, 30) ||
      arbiter.effective(10) != 256) return 1;
  arbiter.release(dragon::BoostOwner::kAppLaunch);
  if (arbiter.effective(10) != 128) return 1;
  arbiter.set_thermal_cap(64);
  if (arbiter.effective(10) != 64 || arbiter.effective(20) != 0 ||
      arbiter.active() != 0 || arbiter.acquire(dragon::BoostOwner::kTouch, 1025, 1)) return 1;
  if (!dragon::CpuBackend::valid_bounds(0, 1024) ||
      dragon::CpuBackend::valid_bounds(513, 512) ||
      dragon::CpuBackend::valid_bounds(0, 1025)) return 1;
  dragon::FreezeStateMachine freezer;
  for (const auto state : {dragon::FreezeState::kBackground,
                           dragon::FreezeState::kCached,
                           dragon::FreezeState::kFreezeDelay,
                           dragon::FreezeState::kEligibilityCheck,
                           dragon::FreezeState::kBinderPrepare,
                           dragon::FreezeState::kFreezing,
                           dragon::FreezeState::kFrozen,
                           dragon::FreezeState::kThawing,
                           dragon::FreezeState::kActive}) {
    if (!freezer.transition(state)) return 1;
  }
  if (freezer.transition(dragon::FreezeState::kFrozen)) return 1;
  dragon::DailyBudgetController daily(64, 2);
  if (daily.update(2200, 2000, true) != 1024 ||
      daily.update(2200, 2000, true) != 960 ||
      daily.update(2200, 2000, false) != 1024) return 1;
  dragon::GameController game(64, 2);
  if (game.update(10000, 11000, 900, 700, 500, false).rescue != 0) return 1;
  const auto cpu_rescue = game.update(10000, 11000, 900, 700, 500, false);
  if (cpu_rescue.bottleneck != dragon::Bottleneck::kCpu || cpu_rescue.rescue != 64)
    return 1;
  if (game.update(10000, 9000, 900, 700, 500, false).rescue != 64 ||
      game.update(10000, 9000, 900, 700, 500, false).rescue != 0 ||
      game.update(10000, 11000, 900, 700, 500, true).bottleneck !=
          dragon::Bottleneck::kThermal) return 1;
  dragon::GameController gpu_game(64, 1);
  dragon::GameController memory_game(64, 1);
  if (gpu_game.update(10000, 11000, 500, 900, 700, false).bottleneck !=
          dragon::Bottleneck::kGpu ||
      memory_game.update(10000, 11000, 500, 700, 900, false).bottleneck !=
          dragon::Bottleneck::kMemory ||
      memory_game.update(0, 11000, 500, 700, 900, false).rescue != 0) return 1;
  const dragon::ThermalConfig thermal_config {
      300, 400, 200, 300, 100, 200, 768, 512, 256, 1000};
  if (!dragon::ThermalGuard::valid(thermal_config)) return 1;
  dragon::ThermalGuard thermal(thermal_config);
  if (thermal.update(250, 0) != dragon::ThermalState::kWarm || thermal.cap() != 768 ||
      thermal.update(150, 100) != dragon::ThermalState::kHot || thermal.cap() != 512 ||
      thermal.update(50, 200) != dragon::ThermalState::kCritical ||
      thermal.update(250, 500) != dragon::ThermalState::kCritical ||
      thermal.update(250, 1200) != dragon::ThermalState::kHot) return 1;
  auto invalid_thermal_config = thermal_config;
  invalid_thermal_config.hot_enter = invalid_thermal_config.warm_enter;
  dragon::ThermalGuard invalid_thermal(invalid_thermal_config);
  if (dragon::ThermalGuard::valid(invalid_thermal_config) ||
      invalid_thermal.update(1024, 0) != dragon::ThermalState::kCritical ||
      invalid_thermal.cap() != 0) return 1;
  dragon::SceneSelector scenes;
  dragon::SceneInputs scene_inputs;
  if (scenes.update(scene_inputs) != dragon::Scene::kDaily) return 1;
  scene_inputs.game = true;
  scene_inputs.frame_late = true;
  scene_inputs.battery_saver = true;
  if (scenes.update(scene_inputs) != dragon::Scene::kGameFrameRescue ||
      !scenes.battery_saver()) return 1;
  scene_inputs.thermal_limited = true;
  if (scenes.update(scene_inputs) != dragon::Scene::kGameThermal) return 1;
  scene_inputs.thermal_emergency = true;
  if (scenes.update(scene_inputs) != dragon::Scene::kThermalEmergency) return 1;
  scene_inputs.valid = false;
  if (scenes.update(scene_inputs) != dragon::Scene::kSafe) return 1;
  return 0;
}

int run_daemon(const std::string& config_path, const std::string& state_path,
               const std::string& heartbeat_path, bool force_dry_run) {
  const std::string lock_path = parent_path(state_path) + "/daemon.lock";
  const int lock_fd = open(lock_path.c_str(), O_CREAT | O_RDWR | O_CLOEXEC | O_NOFOLLOW, 0600);
  if (lock_fd < 0 || flock(lock_fd, LOCK_EX | LOCK_NB) != 0) {
    if (lock_fd >= 0) close(lock_fd);
    std::cerr << "another daemon owns the state directory\n";
    return 1;
  }
  Config config;
  std::string error;
  bool valid = load_config(config_path, &config, &error);
  bool config_valid = valid;
  if (force_dry_run) config.dry_run = true;
  sigset_t signal_mask;
  sigemptyset(&signal_mask);
  sigaddset(&signal_mask, SIGINT);
  sigaddset(&signal_mask, SIGTERM);
  sigaddset(&signal_mask, SIGHUP);
  if (sigprocmask(SIG_BLOCK, &signal_mask, nullptr) != 0) {
    close(lock_fd);
    return 1;
  }
  const auto backends = probe_backends();
  CloudIsolator cloud;
  std::string cloud_status = valid ? "pending" : "safe";
  if (valid) valid = cloud.reconcile(config.cloud_control == "block", &cloud_status, &error);
  std::string scene = valid && config.enabled && config.mode != "safe"
                          ? "BOOT"
                          : (valid && cloud_status == "blocked" ? "CLOUD_ONLY" : "SAFE");
  std::string last_state;
  auto publish = [&]() {
    const std::string state = status_json(scene, config, cloud_status, cloud.count(), error, backends);
    if (state == last_state) return true;
    if (!atomic_write(state_path, state)) return false;
    last_state = state;
    return true;
  };
  auto reload = [&]() {
    Config next;
    std::string next_error;
    if (!load_config(config_path, &next, &next_error)) {
      config_valid = false;
      valid = false;
      cloud.clear();
      cloud_status = "safe";
      error = next_error;
      scene = "SAFE";
      return;
    }
    config_valid = true;
    config = next;
    if (force_dry_run) config.dry_run = true;
    valid = cloud.reconcile(config.cloud_control == "block", &cloud_status, &error);
    scene = valid && config.enabled && config.mode != "safe"
                ? "DAILY"
                : (valid && cloud_status == "blocked" ? "CLOUD_ONLY" : "SAFE");
  };
  if (!publish()) {
    std::cerr << "cannot write state: " << std::strerror(errno) << '\n';
    close(lock_fd);
    return 1;
  }
  uint64_t last_heartbeat = boottime_seconds();
  if (!heartbeat_path.empty() &&
      (last_heartbeat == 0 ||
       !atomic_write(heartbeat_path, std::to_string(last_heartbeat) + "\n"))) {
    cloud.clear();
    cloud_status = "safe";
    error = "heartbeat write failed";
    scene = "SAFE";
    publish();
    close(lock_fd);
    return 1;
  }

  const int signal_fd = signalfd(-1, &signal_mask, SFD_CLOEXEC | SFD_NONBLOCK);
  const int timer_fd = timerfd_create(CLOCK_MONOTONIC, TFD_CLOEXEC | TFD_NONBLOCK);
  const int inotify_fd = inotify_init1(IN_CLOEXEC | IN_NONBLOCK);
  const int epoll_fd = epoll_create1(EPOLL_CLOEXEC);
  if (signal_fd < 0 || timer_fd < 0 || inotify_fd < 0 || epoll_fd < 0) {
    close_fds({epoll_fd, inotify_fd, timer_fd, signal_fd, lock_fd});
    return 1;
  }
  const int watch = inotify_add_watch(
      inotify_fd, parent_path(config_path).c_str(),
      IN_CLOSE_WRITE | IN_MOVED_TO | IN_CREATE | IN_DELETE);
  if (!arm_timer(timer_fd, config.telemetry_interval_s) || watch < 0) {
    close_fds({epoll_fd, inotify_fd, timer_fd, signal_fd, lock_fd});
    return 1;
  }
  for (const int descriptor : {signal_fd, timer_fd, inotify_fd}) {
    epoll_event event {};
    event.events = EPOLLIN;
    event.data.fd = descriptor;
    if (epoll_ctl(epoll_fd, EPOLL_CTL_ADD, descriptor, &event) != 0) {
      close_fds({epoll_fd, inotify_fd, timer_fd, signal_fd, lock_fd});
      return 1;
    }
  }

  bool running = true;
  bool failed = false;
  auto fail_closed = [&](const char* message) {
    cloud.clear();
    cloud_status = "safe";
    error = message;
    scene = "SAFE";
    failed = true;
    running = false;
    publish();
  };
  while (running) {
    epoll_event events[kMaxEvents] {};
    const int count = epoll_wait(epoll_fd, events, kMaxEvents, -1);
    if (count < 0 && errno == EINTR) continue;
    if (count < 0) {
      fail_closed("epoll wait failed");
      break;
    }
    for (int index = 0; index < count; ++index) {
      if ((events[index].events & EPOLLIN) == 0 ||
          (events[index].events & (EPOLLERR | EPOLLHUP)) != 0) {
        fail_closed("event source failed");
        break;
      }
      if (events[index].data.fd == signal_fd) {
        signalfd_siginfo info {};
        const ssize_t signal_read = read(signal_fd, &info, sizeof(info));
        if (signal_read < 0 && errno == EAGAIN) continue;
        if (signal_read != static_cast<ssize_t>(sizeof(info))) {
          fail_closed("signalfd read failed");
          break;
        }
        if (info.ssi_signo == SIGHUP) {
          reload();
          if (!arm_timer(timer_fd, config.telemetry_interval_s)) {
            fail_closed("timerfd rearm failed");
          }
          if (running && !publish()) fail_closed("state write failed");
        } else {
          running = false;
        }
      } else if (events[index].data.fd == inotify_fd) {
        char buffer[512];
        ssize_t inotify_read = 0;
        while ((inotify_read = read(inotify_fd, buffer, sizeof(buffer))) > 0) {}
        if (inotify_read < 0 && errno != EAGAIN) {
          fail_closed("inotify read failed");
          break;
        }
        reload();
        if (!arm_timer(timer_fd, config.telemetry_interval_s)) {
          fail_closed("timerfd rearm failed");
        }
        if (running && !publish()) fail_closed("state write failed");
      } else if (events[index].data.fd == timer_fd) {
        uint64_t expirations = 0;
        const ssize_t timer_read = read(timer_fd, &expirations, sizeof(expirations));
        if (timer_read < 0 && errno == EAGAIN) continue;
        if (timer_read != static_cast<ssize_t>(sizeof(expirations))) {
          fail_closed("timerfd read failed");
          break;
        } else if (config_valid) {
          valid = cloud.reconcile(config.cloud_control == "block", &cloud_status, &error);
          scene = valid && config.enabled && config.mode != "safe"
                      ? "DAILY"
                      : (valid && cloud_status == "blocked" ? "CLOUD_ONLY" : "SAFE");
        }
        if (!publish()) {
          fail_closed("state write failed");
        } else if (!heartbeat_path.empty()) {
          const uint64_t now = boottime_seconds();
          if (now == 0 || now < last_heartbeat ||
              (now - last_heartbeat >= kHeartbeatIntervalSeconds &&
               !atomic_write(heartbeat_path, std::to_string(now) + "\n"))) {
            fail_closed("heartbeat write failed");
          } else if (now - last_heartbeat >= kHeartbeatIntervalSeconds) {
            last_heartbeat = now;
          }
        }
      }
      if (!running) break;
    }
  }

  cloud.clear();
  if (!failed) {
    cloud_status = "stopped";
    scene = "STOPPED";
    publish();
  }
  close_fds({epoll_fd, inotify_fd, timer_fd, signal_fd, lock_fd});
  return failed ? 1 : 0;
}

}  // namespace

int main(int argc, char** argv) {
  if (argc == 2 && std::string(argv[1]) == "--self-test") return run_self_test();
  if (argc >= 2 && std::string(argv[1]) == "status") {
    const std::string state = argc == 4 && std::string(argv[2]) == "--state"
                                  ? argv[3]
                                  : "/data/adb/dragon-dac/state.json";
    std::ifstream input(state);
    if (!input) return 1;
    std::cout << input.rdbuf();
    return 0;
  }
  if (argc >= 2 && std::string(argv[1]) == "daemon") {
    std::string config = "/data/adb/dragon-dac/config/dac.conf";
    std::string state = "/data/adb/dragon-dac/state.json";
    std::string heartbeat;
    bool dry_run = false;
    for (int index = 2; index < argc; ++index) {
      const std::string argument = argv[index];
      if (argument == "--config" && index + 1 < argc) config = argv[++index];
      else if (argument == "--state" && index + 1 < argc) state = argv[++index];
      else if (argument == "--heartbeat" && index + 1 < argc) heartbeat = argv[++index];
      else if (argument == "--dry-run") dry_run = true;
      else {
        std::cerr << "unknown argument: " << argument << '\n';
        return 2;
      }
    }
    return run_daemon(config, state, heartbeat, dry_run);
  }
  std::cerr << "usage: dragon-dac daemon [--config PATH] [--state PATH] [--heartbeat PATH] [--dry-run] | status [--state PATH] | --self-test\n";
  return 2;
}
