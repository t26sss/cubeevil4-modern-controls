#!/usr/bin/env python3
"""Touch look zone with "Modern controls": a swipe turns the camera by the way the finger moved, and the camera
stops when the finger stops (no longer a stick held at the finger's distance from where it went down).
Only the touch look zone, only the sideways turn (the pitch stays as it was); controllers and the C stick of the
touch layout are as before. Small anchored edits, safe to run twice. Run from the repo root, after
apply_modern_controls.py."""
import re, sys
D = "port/android-decomp/app/src/main/java/com/ast/re4decomp/"
failed = []

def sub1(s, pat, fn, what, path):
    new, n = re.subn(pat, fn, s, count=1, flags=re.M)
    if n == 0:
        failed.append(f"{path}: {what}")
        return s
    print("ok:", path, "-", what)
    return new

def process(path, marker, edits):
    s = open(path, encoding="utf-8").read()
    if marker in s:
        print("already done, skipped:", path)
        return
    for pat, fn, what in edits:
        s = sub1(s, pat, fn, what, path)
    open(path, "w", encoding="utf-8").write(s)

process(D + "CoreInput.java", "touchLookPulse", [
    # the flag, the pending turn and the two methods, before touchStick
    (r"^(\s*)(/\*\* A stick of the touch controls \(the C stick or the control stick\).*)$",
     lambda m: m.group(1) + "/** \"Modern controls\" is on (the menu): the touch look zone turns the camera by swipes (touchLookPulse). */\n"
     + m.group(1) + "static volatile boolean modernLook;\n"
     + m.group(1) + "private static final float LOOK_PULSE_GAIN = 30f;  // C stick units (one frame at the full stick each) per share of the shorter side\n"
     + m.group(1) + "private final Object pulseLock = new Object();\n"
     + m.group(1) + "private float lookPending;\n\n"
     + m.group(1) + "/** The touch look zone's finger moved sideways by dx (shares of the shorter side): a turn of the camera, given out frame by frame. */\n"
     + m.group(1) + "public void touchLookPulse(float dx) {\n"
     + m.group(1) + "  synchronized (pulseLock) {\n"
     + m.group(1) + "    lookPending = clamp(lookPending + dx * LOOK_PULSE_GAIN, -60f, 60f);\n"
     + m.group(1) + "  }\n"
     + m.group(1) + "}\n\n"
     + m.group(1) + "/** What of the pending turn goes into this frame's C stick: at most the full stick. */\n"
     + m.group(1) + "private float takeLookPulse() {\n"
     + m.group(1) + "  synchronized (pulseLock) {\n"
     + m.group(1) + "    float out = clamp(lookPending, -1f, 1f);\n"
     + m.group(1) + "    lookPending -= out;\n"
     + m.group(1) + "    if (Math.abs(lookPending) < 0.001f) lookPending = 0;\n"
     + m.group(1) + "    return out;\n"
     + m.group(1) + "  }\n"
     + m.group(1) + "}\n\n" + m.group(1) + m.group(2), "pulse state and methods"),
    # the frame's pad: add it to the C stick of the touch controls
    (r"^(\s*buttons \|= \(touch \? d\.buttons : d\.buttons & ~GC_B\) \| d\.hats;\n\s*float mainX = d\.lx, mainY = d\.ly, cX = d\.rx, cY = d\.ry;)$",
     lambda m: m.group(1) + "\n      float pulse = touch ? takeLookPulse() : 0f;  // \"Modern controls\": the look zone's swipes\n      if (touch && !touchAiming) cX += pulse;", "pad"),
])

process(D + "CoreTouch.java", "touchLookPulse", [
    (r"^(\s*)lookX \+= dx;$",
     lambda m: m.group(1) + "if (CoreInput.modernLook) {\n" + m.group(1) + "  input.touchLookPulse(dx);  // \"Modern controls\": a swipe turns the camera, it does not hold a stick\n"
     + m.group(1) + "} else {\n" + m.group(1) + "  lookX += dx;\n" + m.group(1) + "}", "look"),
])

process(D + "CoreActivity.java", "CoreInput.modernLook", [
    (r"^(\s*)(CoreBridge\.setModernControls\(getSharedPreferences\(INPUT_PREFS, MODE_PRIVATE\)\.getBoolean\(MODERN_CONTROLS, false\)\);)$",
     lambda m: m.group(1) + m.group(2) + "\n" + m.group(1) + "CoreInput.modernLook = getSharedPreferences(INPUT_PREFS, MODE_PRIVATE).getBoolean(MODERN_CONTROLS, false);", "at start"),
])

process(D + "CoreMenu.java", "CoreInput.modernLook", [
    (r"(CoreBridge\.setModernControls\(on\);)", lambda m: m.group(1) + " CoreInput.modernLook = on;", "switch"),
])

if failed:
    print("\nMISSING ANCHORS:\n  " + "\n  ".join(failed))
    sys.exit(1)
