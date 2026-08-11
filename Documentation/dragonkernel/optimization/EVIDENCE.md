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

Add a `BoostArbiter` with per-owner deadlines, maximum effective uclamp floor and a higher-priority thermal cap. Add a disabled per-thread uclamp backend that snapshots, verifies and conditionally restores only explicitly transferred thread ownership; do not write existing ROM cgroup policy.

### Risk, compatibility and rollback

The live daemon currently owns no CPU resource and contains no CPU masks, frequencies or package policy. Removing the optional module removes the userspace policy layer; all five devices retain vendor behavior.

### Test plan

Exercise overlapping acquire/release, expiry, thermal cap and invalid bounds in the native self-test, then require host and Android arm64 Actions plus module-content validation. Backend writes remain a post-optimization device gate.

`3ac075e49702` passed Project contract and DAC module validation for the ownership arbiter and module `0.3.0` artifact.

`93b7d887dadb` passed Project contract and DAC module validation for the disabled per-thread uclamp backend and module `0.4.0` artifact.

## Freezer ownership core

### Problem and current implementation

The kernel exposes Binder and cgroup freezer mechanisms, while Android CachedAppOptimizer already owns cached-process lifecycle on supported ROMs. A second independent freezer would race framework visibility, services and Binder state.

### Evidence and proposed change

Kernel source includes `BINDER_FREEZE` and frozen-info ioctls. Add a strict no-write freeze/thaw state machine, read-only Binder capability probe and framework-freezer capture. Prefer the framework owner; keep DAC fallback disabled until complete process eligibility data is available.

### Expected benefit, risk and rollback

The state machine makes rollback and illegal transitions explicit without freezing any process. All five devices retain framework behavior; disabling or removing the module removes the observer.

### Test plan

Exercise the full legal transition chain, rollback-to-active and illegal transition rejection in the native self-test. Require host/Android arm64 Actions and module-content validation; actual freeze/thaw remains a post-optimization device gate.

`e203296ee00e` passed Project contract and DAC module validation for the no-write freezer ownership core and module `0.5.0` artifact.

## Daily, game and thermal policy core

### Problem and current implementation

Fixed frequencies, frame rates, power limits and thermal thresholds conflict across devices, ROM policy owners and ambient conditions. The kernel thermal stack must remain authoritative.

### Proposed change and benefit

Add pure controllers for a caller-supplied daily soft power target, runtime-derived frame deadline and device/ROM-supplied thermal headroom thresholds. Consecutive-sample hysteresis limits oscillation; latency relaxes the daily cap, thermal pressure clears frame rescue, and recovery removes requests incrementally.

### Risk, compatibility and rollback

The controllers emit only normalized decisions. They are not connected to cgroup, cpufreq, KGSL, devfreq or thermal writes, contain no package/process special case and do not alter stock cooling. Removing the optional module removes them.

### Test plan

Exercise over-budget hysteresis and latency override, frame violation/recovery and bottleneck choice, plus immediate thermal tightening and delayed stepwise recovery. Require host and Android arm64 Actions and deterministic module validation before any runtime backend is enabled.

`751c7f2efd34` passed Project contract and DAC module validation for module `0.6.0`; Actions compiled the host and Android arm64 daemon, validated deterministic packaging and produced the module artifact.

## CI supply-chain lock

### Problem and proposed change

Major-version GitHub Action tags are movable and do not bind a final source SHA to immutable CI code. Resolve each reviewed official Action tag to its commit, pin every workflow reference, and make Project contract reject movable or unknown external Actions.

### Risk, compatibility and test plan

Pinned Actions retain their reviewed major versions but require an explicit commit update for future upgrades. Run Project contract, DAC validation and all four five-device kernel matrices because every workflow checkout/upload path changed; retain build and artifact evidence from the pinned workflow SHA.

The manual Release preflight binds a full base/candidate pair, scans only added diff lines for a small set of release-blocking hazards, rejects private/Agent/cache paths and escaping symlinks, and emits affected owner scopes. It deliberately records that full security and conflict reviews remain required.

## Scene selection core

### Problem and proposed change

Independent event handlers can race and apply contradictory policies. Add one pure selector over an atomic event snapshot with explicit safety, thermal, screen, game, camera, interaction, media and power priority.

### Risk, compatibility and test plan

The selector emits only an enum and has no package names or resource backend. Invalid input fails SAFE. Exercise daily, frame rescue, game thermal, thermal emergency and invalid-input priority in host/Android arm64 Actions before connecting real event sources.

The daemon must also fail closed when event-loop descriptors, config watches or timer arming fail, close every descriptor on partial initialization, and rearm telemetry after a validated config reload. Actions compile both host and Android arm64 paths under `-Werror`.

The module daemon takes a nonblocking lock scoped to its state directory, state temporary files reject symlinks, and install directories are root-only. Uninstall resolves `/proc/<pid>/exe` before signalling, so an unrelated process with the same name is not terminated.
