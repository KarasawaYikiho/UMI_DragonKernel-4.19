# Optimization evidence

## Phase 0 and DAC skeleton

### Problem

The kernel had mechanisms but no complete ownership map, Joyose cloud-control boundary, runtime capture contract, DAC userspace layer or synchronized module artifact.

### Current implementation

WALT/SchedTune/uclamp/schedutil/boost/core_ctl/KGSL/devfreq/freezer/QTI thermal are present. Only the Xiaomi `thermal_message` kernel mailbox had been removed.

### Evidence

Current-tree Kconfig, source creation points, DTS owners, build scripts and public CI contracts were inspected at `08f410eb5242`. Runtime values remain intentionally unknown.

### Proposed change

Add the Phase 0 audit, read-only adb capture, event-driven native DAC skeleton, safe module template, deterministic packager and a pinned CI-only Android toolchain.

### Expected benefit

Later CPU/freezer/game/thermal work can use one policy owner, fail safe, avoid guessed paths and ship userspace functions independently of kernel variants.

### Risk

The skeleton is not a performance policy. Joyose block mode is rejected until ROM evidence identifies safe interception points.

### Compatibility

Kernel variants remain Original, Magisk, KernelSU and SukiSU. BBG remains common. The module uses the shared Magisk-module format without a ROOT-manager API dependency.

### Rollback

Remove the optional module. Phase 1 owns no kernel resource and defaults to disabled dry-run.

### Test plan

Project contract, Python/module self-tests, YAML and shell syntax, CI host self-test, pinned NDK arm64 build, ELF dependency check, deterministic ZIP comparison, then post-optimization device validation.

The first module CI run rejected an unchecked `timerfd` read under `-Werror`. The follow-up handles short/error reads by entering SAFE and recording the failure; no policy write is attempted.

The next run passed host and Android arm64 builds, then exposed a validation working-directory error. The checksum is intentionally portable and names only the ZIP basename, so CI now verifies it from the artifact directory.

`8df152184620` passed Project contract and DAC module validation. The downloaded module artifact passed its portable checksum, fixed inventory and modes, AArch64 ELF, no-external-libc++ and safe-default checks. Six fast Original device builds for the unchanged kernel snapshot also completed successfully.

The Hyper3 static audit confirms Joyose is not thermal-only: it has boot and network capability plus scheduler, game/performance, thermal and memory policy signals. It uses a shared system UID, so UID-wide network blocking is rejected because it could affect unrelated system services. Cloud isolation remains observe-only until the internal remote-delivery/local-policy boundary is isolated without disabling required local behavior.
