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

The Hyper3 static audit confirms Joyose is not thermal-only: it has boot and network capability plus scheduler, game/performance, thermal and memory policy signals. It uses a shared system UID, so UID-wide network blocking is rejected because it could affect unrelated system services.

Further component analysis found two process domains and mixed remote/local responsibilities in the default process. Component disabling is therefore also rejected. The implemented boundary attaches ingress/egress drop programs only to existing cgroup v2 leaves whose process inventory is exclusively Joyose; it never moves tasks or changes CPU controller membership. FD-scoped BPF links auto-detach on normal exit or process death. Missing, shared or unsupported cgroups fail SAFE, while Lineage without Joyose is a no-op.

`825cc986c121` passed Project contract and DAC module validation, including host and Android arm64 compilation, deterministic packaging and the independent module-content gate. This is source/artifact evidence only; cgroup exclusivity, blocked traffic and retained local behavior remain post-optimization device gates.

## CPU ownership core

### Problem

Vendor input boost, Joyose, Power HAL and later DAC scenes can overlap; releasing one request must not clear another owner's boost.

### Current implementation and evidence

The kernel retains WALT, SchedTune, uclamp, schedutil, scheduler boost, CPU boost and core_ctl. Static Hyper3 policy files confirm multiple existing cgroup/task-profile owners, so DAC cannot safely overwrite those groups before runtime ownership evidence.

### Proposed change and benefit

Add a no-write `BoostArbiter` with per-owner deadlines, maximum effective uclamp floor and a higher-priority thermal cap. Keep the CPU backend disabled while the arbiter and parser contracts are built.

### Risk, compatibility and rollback

The arbiter currently owns no kernel resource and contains no CPU masks, frequencies or package policy. Removing the optional module removes the userspace policy layer; all five devices retain vendor behavior.

### Test plan

Exercise overlapping acquire/release, expiry, thermal cap and invalid bounds in the native self-test, then require host and Android arm64 Actions plus module-content validation.
