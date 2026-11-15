#!/usr/bin/env python3
"""Adds the "Modern controls" switch to the CURRENT files of the repo with small anchored edits (no file is
replaced as a whole). Safe to run twice: a file that already has the change is left alone. Run from the repo root."""
import glob, os, re, sys

APP = "port/android-decomp/app/src/main/"
failed = []

def sub1(s, pat, fn, what, path):
    new, n = re.subn(pat, fn, s, count=1, flags=re.M)
    if n == 0:
        failed.append(f"{path}: {what}")
        return s
    print("ok:", path, "-", what)
    return new

def process(path, marker, edits, tail=""):
    s = open(path, encoding="utf-8").read()
    if marker in s:
        print("already done, skipped:", path)
        return
    for pat, fn, what in edits:
        s = sub1(s, pat, fn, what, path)
    open(path, "w", encoding="utf-8").write(s + tail)

# 1. an earlier copy of this patch under another number would apply the same change twice: keep only 0990
for f in glob.glob("port/whole/patches/*.patch"):
    if os.path.basename(f) != "0990-modern-controls.patch" and "re4ModernPrepare" in open(f, encoding="utf-8", errors="ignore").read():
        os.remove(f)
        print("removed duplicate patch:", f)

# 2. runtime flag
process("port/whole/runtime/aim_options.cpp", "gModern", [
    (r"^(std::atomic<bool> gFar\(false\);.*)$",
     lambda m: m.group(1) + "\nstd::atomic<bool> gModern(false);   // the app's \"Modern controls\" (patch 0990)", "flag"),
    (r"^(\s*const bool far = \(bits & 8\) != 0;.*)$",
     lambda m: m.group(1) + "\n    gModern.store((bits & 16) != 0);  // bit 4 \"Modern controls\" (patch 0990)", "bit 4"),
    (r"^(int re4_far_camera\(void\))",
     lambda m: "// Patch 0990 (player.cpp): the app's \"Modern controls\".\nint re4_modern_controls(void)\n{\n    return gModern.load(std::memory_order_relaxed) ? 1 : 0;\n}\n\n" + m.group(1), "getter"),
])

# 3. JNI + aim bit
process(APP + "cpp/core_mode.cpp", "optModern", [
    (r"^(std::atomic<int> optFarCamera\{0\};.*)$",
     lambda m: "std::atomic<int> optModern{0};  // the menu's \"Modern controls\" (bit 4 of the aim bits, patch 0990)\n" + m.group(1), "optModern"),
    (r"(const int aim = optAim\.load\(\))", lambda m: m.group(1) + " | (optModern.load() ? 16 : 0)", "aim bit"),
], tail='''
// "Modern controls" (the menu, Controls): the left stick moves Leon the way it points, as the camera sees it
// (patch 0990), sent with the aim settings (bit 4).
extern "C" JNIEXPORT void JNICALL Java_com_ast_re4decomp_CoreBridge_setModernControls(JNIEnv *, jclass, jboolean on) {
  const int want = on == JNI_TRUE ? 1 : 0;
  if (optModern.exchange(want) != want) LOG("modern controls: %s", want ? "on" : "off");
}
''')

process(APP + "java/com/ast/re4decomp/CoreBridge.java", "setModernControls", [
    (r"^(\s*public static native void setFarCamera\(boolean on\);)",
     lambda m: m.group(1) + "\n\n  /** \"Modern controls\": the left stick moves Leon the way it points, as the camera sees it (patch 0990). */\n  public static native void setModernControls(boolean on);", "native"),
])

process(APP + "java/com/ast/re4decomp/CoreActivity.java", "MODERN_CONTROLS", [
    (r"(FAR_CAMERA = \"farCamera\")", lambda m: m.group(1) + ",\n      MODERN_CONTROLS = \"modernControls\"", "pref key"),
    (r"^(\s*)(CoreBridge\.setFarCamera\(.*\);)$",
     lambda m: m.group(1) + m.group(2) + "\n" + m.group(1) + "CoreBridge.setModernControls(getSharedPreferences(INPUT_PREFS, MODE_PRIVATE).getBoolean(MODERN_CONTROLS, false));", "send at start"),
])

process(APP + "java/com/ast/re4decomp/CoreMenu.java", "ingame_modern_controls", [
    (r"^(\s*)(toggle\(third, R\.string\.ingame_always_run,.*)$",
     lambda m: m.group(1) + m.group(2) + "\n" + m.group(1) + "MenuLayout.Buttons fourth = buttonsRow(body);\n" + m.group(1) +
     "toggle(fourth, R.string.ingame_modern_controls, input.getBoolean(CoreActivity.MODERN_CONTROLS, false), on -> {\n" + m.group(1) +
     "  input.edit().putBoolean(CoreActivity.MODERN_CONTROLS, on).apply(); CoreBridge.setModernControls(on);\n" + m.group(1) + "});", "toggle row"),
    (r"(help\(R\.string\.ingame_always_run_help\);)", lambda m: m.group(1) + " help(R.string.ingame_modern_controls_help);", "help"),
])

# 4. the two strings: not twice (a resource defined in two files stops the build)
extra = APP + "res/values/strings_modern.xml"
for f in glob.glob(APP + "res/values/*.xml"):
    if f != extra and 'name="ingame_modern_controls"' in open(f, encoding="utf-8", errors="ignore").read():
        if os.path.exists(extra):
            os.remove(extra)
            print("strings already in", f, "- removed strings_modern.xml")
        break

if failed:
    print("\nMISSING ANCHORS:\n  " + "\n  ".join(failed))
    sys.exit(1)
