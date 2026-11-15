# CubeEvil4 – Modern controls (mod overlay)

A small overlay for [CubeEvil4-Android](https://github.com/Andiweli/CubeEvil4-Android) (the Resident Evil 4 Android port):

Two separate switches (menu → Controls, both off by default, each works without the other):

- **Modern controls**: the left stick moves Leon the way it points, as the camera sees it; the right stick / look zone turns the
  camera (a swipe turns it by the swipe, it does not keep turning).
- **Walk while aiming**: while the aim key is held the move stick walks and the right stick / touch C-stick aims; Leon's legs walk
  (the game's own walk motion + IK on the legs only), the body bobs and sways with the steps, the arms move with the body and the
  laser follows the gun.

This repository contains **only the mod** (patches and scripts). The workflow downloads the upstream project on every run, applies
the mod and builds the APK, so there is no fork to keep in sync. No game files are included or needed here: you still import
your own discs in the app as usual.

## Build it
1. Fork this repository (or use it as a template).
2. *Actions → Build modded APK → Run workflow.* Choose the upstream branch or tag (default: `master`).
3. Download the APK from the run's *Artifacts*.

Optional, to keep the same signature on every build (so updates install over each other): add the repository secrets
`KEYSTORE_B64` (your keystore file, base64), `STORE_PASS`, `KEY_ALIAS`, `KEY_PASS`. **Never publish your keystore.**
Without them a throw-away key is created and the old app has to be uninstalled before installing a new build.

## When upstream changes
The workflow also runs every Monday. If it fails, upstream changed something the mod hooks into:
- the step *Apply the mod…* names the anchor it could not find (`scripts/apply_*.py`), or
- *Build game core* reports `patch failed: 0990-modern-controls.patch` (the game source around the patch changed).

Run the workflow with an older upstream tag (`upstream_ref`) to keep building meanwhile, and fix the script/patch.

## How it works
`scripts/apply_*.py` make small, anchored edits to the upstream app files (JNI, menu, input). They are safe to run twice.
`port/whole/patches/0990-modern-controls.patch` is picked up by upstream's own patch mechanism and changes the game code
(`player.cpp`, `cam_qfps.cpp`, `pl_class.cpp`).

## Known issues
- Walking sideways or backwards while aiming uses the forward walk animation for the legs.
- Only English menu text.
- Diagnostic files (`leon_bones.txt`, `aim_walk_trace*.txt`) are written to the app's files folder once per run.

## Credits and licence
Upstream: Andiweli/CubeEvil4-Android and the decompilation work it builds on. The patch files contain lines of upstream source:
follow upstream's licence and terms when you publish. Add your own `LICENSE` file for the mod's own code.
