#include <sys/epoll.h>
#include <sys/inotify.h>
#include <sys/signalfd.h>
#include <sys/stat.h>
#include <sys/timerfd.h>
#include <unistd.h>

#include <fcntl.h>

#include <cerrno>
#include <cstdint>
#include <csignal>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <map>
#include <sstream>
#include <string>
#include <vector>

namespace {

constexpr int kMaxEvents = 4;

struct Config {
  bool enabled = false;
  bool freezer = false;
  bool game = false;
  bool ddr = false;
  bool dry_run = true;
  int telemetry_interval_s = 5;
  std::string mode = "auto";
  std::string cloud_control = "observe";
};

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

std::string parent_path(const std::string& path) {
  const auto separator = path.find_last_of('/');
  return separator == std::string::npos ? "." : path.substr(0, separator);
}

std::map<std::string, bool> probe_backends() {
  return {
      {"schedtune", path_exists("/dev/stune")},
      {"cgroup", path_exists("/sys/fs/cgroup")},
      {"kgsl", path_exists("/sys/class/kgsl/kgsl-3d0")},
      {"devfreq", path_exists("/sys/class/devfreq")},
      {"thermal", path_exists("/sys/class/thermal")},
      {"cpu_boost", path_exists("/sys/devices/system/cpu/cpu_boost")},
  };
}

bool atomic_write(const std::string& path, const std::string& data) {
  const std::string temporary = path + ".tmp";
  const int file = open(temporary.c_str(), O_CREAT | O_TRUNC | O_WRONLY | O_CLOEXEC, 0600);
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

std::string status_json(const std::string& scene, const Config& config,
                        const std::string& error,
                        const std::map<std::string, bool>& backends) {
  std::ostringstream output;
  output << "{\n  \"schema\": 1,\n  \"scene\": \"" << scene << "\",\n"
         << "  \"enabled\": " << (config.enabled ? "true" : "false") << ",\n"
         << "  \"dry_run\": " << (config.dry_run ? "true" : "false") << ",\n"
         << "  \"cloud_control\": \"" << config.cloud_control << "\",\n"
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
  return 0;
}

int run_daemon(const std::string& config_path, const std::string& state_path,
               bool force_dry_run) {
  Config config;
  std::string error;
  bool valid = load_config(config_path, &config, &error);
  if (force_dry_run) config.dry_run = true;
  if (valid && config.cloud_control == "block") {
    valid = false;
    error = "cloud-control block backend is not validated";
  }
  std::string scene = valid && config.enabled && config.mode != "safe" ? "BOOT" : "SAFE";
  const auto backends = probe_backends();
  if (!atomic_write(state_path, status_json(scene, config, error, backends))) {
    std::cerr << "cannot write state: " << std::strerror(errno) << '\n';
    return 1;
  }

  sigset_t signal_mask;
  sigemptyset(&signal_mask);
  sigaddset(&signal_mask, SIGINT);
  sigaddset(&signal_mask, SIGTERM);
  sigaddset(&signal_mask, SIGHUP);
  if (sigprocmask(SIG_BLOCK, &signal_mask, nullptr) != 0) return 1;
  const int signal_fd = signalfd(-1, &signal_mask, SFD_CLOEXEC | SFD_NONBLOCK);
  const int timer_fd = timerfd_create(CLOCK_MONOTONIC, TFD_CLOEXEC | TFD_NONBLOCK);
  const int inotify_fd = inotify_init1(IN_CLOEXEC | IN_NONBLOCK);
  const int epoll_fd = epoll_create1(EPOLL_CLOEXEC);
  if (signal_fd < 0 || timer_fd < 0 || inotify_fd < 0 || epoll_fd < 0) return 1;

  itimerspec timer {};
  timer.it_value.tv_sec = config.telemetry_interval_s;
  timer.it_interval.tv_sec = config.telemetry_interval_s;
  timerfd_settime(timer_fd, 0, &timer, nullptr);
  inotify_add_watch(inotify_fd, parent_path(config_path).c_str(),
                    IN_CLOSE_WRITE | IN_MOVED_TO | IN_CREATE | IN_DELETE);
  for (const int descriptor : {signal_fd, timer_fd, inotify_fd}) {
    epoll_event event {};
    event.events = EPOLLIN;
    event.data.fd = descriptor;
    if (epoll_ctl(epoll_fd, EPOLL_CTL_ADD, descriptor, &event) != 0) return 1;
  }

  bool running = true;
  while (running) {
    epoll_event events[kMaxEvents] {};
    const int count = epoll_wait(epoll_fd, events, kMaxEvents, -1);
    if (count < 0 && errno == EINTR) continue;
    if (count < 0) break;
    for (int index = 0; index < count; ++index) {
      if (events[index].data.fd == signal_fd) {
        signalfd_siginfo info {};
        if (read(signal_fd, &info, sizeof(info)) != static_cast<ssize_t>(sizeof(info))) continue;
        if (info.ssi_signo == SIGHUP) {
          Config next;
          std::string next_error;
          if (load_config(config_path, &next, &next_error)) {
            config = next;
            if (force_dry_run) config.dry_run = true;
            if (config.cloud_control == "block") {
              error = "cloud-control block backend is not validated";
              scene = "SAFE";
            } else {
              error.clear();
              scene = config.enabled && config.mode != "safe" ? "DAILY" : "SAFE";
            }
          } else {
            error = next_error;
            scene = "SAFE";
          }
          atomic_write(state_path, status_json(scene, config, error, backends));
        } else {
          running = false;
        }
      } else if (events[index].data.fd == inotify_fd) {
        char buffer[512];
        while (read(inotify_fd, buffer, sizeof(buffer)) > 0) {}
        Config next;
        std::string next_error;
        if (load_config(config_path, &next, &next_error)) {
          config = next;
          if (force_dry_run) config.dry_run = true;
          if (config.cloud_control == "block") {
            error = "cloud-control block backend is not validated";
            scene = "SAFE";
          } else {
            error.clear();
            scene = config.enabled && config.mode != "safe" ? "DAILY" : "SAFE";
          }
        } else {
          error = next_error;
          scene = "SAFE";
        }
        atomic_write(state_path, status_json(scene, config, error, backends));
      } else if (events[index].data.fd == timer_fd) {
        uint64_t expirations = 0;
        read(timer_fd, &expirations, sizeof(expirations));
      }
    }
  }

  scene = "STOPPED";
  atomic_write(state_path, status_json(scene, config, error, backends));
  close(epoll_fd);
  close(inotify_fd);
  close(timer_fd);
  close(signal_fd);
  return 0;
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
    bool dry_run = false;
    for (int index = 2; index < argc; ++index) {
      const std::string argument = argv[index];
      if (argument == "--config" && index + 1 < argc) config = argv[++index];
      else if (argument == "--state" && index + 1 < argc) state = argv[++index];
      else if (argument == "--dry-run") dry_run = true;
      else {
        std::cerr << "unknown argument: " << argument << '\n';
        return 2;
      }
    }
    return run_daemon(config, state, dry_run);
  }
  std::cerr << "usage: dragon-dac daemon [--config PATH] [--state PATH] [--dry-run] | status [--state PATH] | --self-test\n";
  return 2;
}
