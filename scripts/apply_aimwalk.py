#!/usr/bin/env python3
"""The switch "Walk while aiming" (its own menu row, separate from "Modern controls", bit 5 of the aim bits): while aiming, the move stick goes to the game as the C stick
(which the core reads as the walk, patch 0990) and the aim comes from the other source: the controller's right
stick, or the touch C stick (and the look zone's swipes). Small anchored edits, safe to run twice. Run from the
repo root, after apply_touchlook.py. Controllers mapped by the app's own mapping page and keyboards are not covered."""
import re, sys
P = "port/android-decomp/app/src/main/java/com/ast/re4decomp/CoreInput.java"
failed = []

def sub1(s, pat, fn, what):
    new, n = re.subn(pat, fn, s, count=1, flags=re.M)
    if n == 0:
        failed.append(f"{P}: {what}")
        return s
    print("ok:", P, "-", what)
    return new

s = open(P, encoding="utf-8").read()
if "walk while aiming" in s:
    print("already done, skipped:", P)
else:
    # the controller: the move stick walks, the right stick aims
    s = sub1(s, r"^(\s*)(cX = cY = 0;)$",
             lambda m: m.group(1) + m.group(2) + "\n" + m.group(1) + "if (aimWalk) {  // walk while aiming: the move stick goes in the C stick\n"
             + m.group(1) + "  cX = d.lx;\n" + m.group(1) + "  cY = d.ly;\n" + m.group(1) + "}", "controller")
    # the touch controls: the C stick aims, the move stick walks
    s = sub1(s, r"^(\s*)if \(touchAiming && touch && touchAim == AIM_LOOK\) \{",
             lambda m: m.group(1) + "if (touchAiming && touch && aimWalk) {\n"
             + m.group(1) + "  // walk while aiming: the move stick walks (the C stick of the game), the touch C stick aims\n"
             + m.group(1) + "  cX = mainX;\n" + m.group(1) + "  cY = mainY;\n"
             + m.group(1) + "  mainX = d.cStickX;\n" + m.group(1) + "  mainY = d.cStickY;\n"
             + m.group(1) + "} else if (touchAiming && touch && touchAim == AIM_LOOK) {", "touch")
    open(P, "w", encoding="utf-8").write(s)

# --- the flag in CoreInput (next to modernLook, from apply_touchlook.py)
s = open(P, encoding="utf-8").read()
if "static volatile boolean aimWalk" not in s:
    s = sub1(s, r"^(\s*)(static volatile boolean modernLook;)$",
             lambda m: m.group(1) + m.group(2) + "\n" + m.group(1) + "/** \"Walk while aiming\" is on (the menu): see the aiming branches below. */\n" + m.group(1) + "static volatile boolean aimWalk;", "aimWalk flag")
    open(P, "w", encoding="utf-8").write(s)

APP = "port/android-decomp/app/src/main/"
import os

def process(path, marker, edits, tail=""):
    t = open(path, encoding="utf-8").read()
    if marker in t:
        print("already done, skipped:", path)
        return
    for pat, fn, what in edits:
        new, n = re.subn(pat, fn, t, count=1, flags=re.M)
        if n == 0:
            failed.append(f"{path}: {what}")
        else:
            print("ok:", path, "-", what)
            t = new
    open(path, "w", encoding="utf-8").write(t + tail)

# runtime flag, from bit 5 (32) of the aim bits
process("port/whole/runtime/aim_options.cpp", "gAimWalk", [
    (r"^(std::atomic<bool> gModern\(false\);.*)$",
     lambda m: m.group(1) + "\nstd::atomic<bool> gAimWalk(false);   // the app's \"Walk while aiming\" (patch 0990)", "flag"),
    (r"^(\s*gModern\.store\(\(bits & 16\) != 0\);.*)$",
     lambda m: m.group(1) + "\n    gAimWalk.store((bits & 32) != 0);  // bit 5 \"Walk while aiming\" (patch 0990)", "bit 5"),
    (r"^(// Patch 0990 \(player\.cpp\): the app's \"Modern controls\"\.)$",
     lambda m: "// Patch 0990 (player.cpp): the app's \"Walk while aiming\".\nint re4_modern_aimwalk(void)\n{\n    return gAimWalk.load(std::memory_order_relaxed) ? 1 : 0;\n}\n\n" + m.group(1), "getter"),
])

# JNI + the aim bit
process(APP + "cpp/core_mode.cpp", "optAimWalk", [
    (r"^(std::atomic<int> optModern\{0\};.*)$",
     lambda m: m.group(1) + "\nstd::atomic<int> optAimWalk{0};  // the menu's \"Walk while aiming\" (bit 5 of the aim bits, patch 0990)", "optAimWalk"),
    (r"(\| \(optModern\.load\(\) \? 16 : 0\))", lambda m: m.group(1) + " | (optAimWalk.load() ? 32 : 0)", "aim bit"),
], tail='''
// "Walk while aiming" (the menu, Controls): while the aim key is held the move stick walks (patch 0990), sent with the
// aim settings (bit 5).
extern "C" JNIEXPORT void JNICALL Java_com_ast_re4decomp_CoreBridge_setAimWalk(JNIEnv *, jclass, jboolean on) {
  const int want = on == JNI_TRUE ? 1 : 0;
  if (optAimWalk.exchange(want) != want) LOG("walk while aiming: %s", want ? "on" : "off");
}
''')

process(APP + "java/com/ast/re4decomp/CoreBridge.java", "setAimWalk", [
    (r"^(\s*public static native void setModernControls\(boolean on\);)",
     lambda m: m.group(1) + "\n\n  /** \"Walk while aiming\": the move stick walks while the aim key is held (patch 0990). */\n  public static native void setAimWalk(boolean on);", "native"),
])

process(APP + "java/com/ast/re4decomp/CoreActivity.java", "AIM_WALK", [
    (r"(MODERN_CONTROLS = \"modernControls\")", lambda m: m.group(1) + ",\n      AIM_WALK = \"aimWalk\"", "pref key"),
    (r"^(\s*)(CoreInput\.modernLook = getSharedPreferences\(INPUT_PREFS, MODE_PRIVATE\)\.getBoolean\(MODERN_CONTROLS, false\);)$",
     lambda m: m.group(1) + m.group(2) + "\n" + m.group(1) + "CoreBridge.setAimWalk(getSharedPreferences(INPUT_PREFS, MODE_PRIVATE).getBoolean(AIM_WALK, false));\n"
     + m.group(1) + "CoreInput.aimWalk = getSharedPreferences(INPUT_PREFS, MODE_PRIVATE).getBoolean(AIM_WALK, false);", "send at start"),
])

process(APP + "java/com/ast/re4decomp/CoreMenu.java", "ingame_aim_walk", [
    (r"^(\s*)toggle\(fourth, R\.string\.ingame_modern_controls[^\n]*\n[^\n]*CoreBridge\.setModernControls\(on\)[^\n]*\n\s*\}\);",
     lambda m: m.group(0) + "\n" + m.group(1) + "toggle(fourth, R.string.ingame_aim_walk, input.getBoolean(CoreActivity.AIM_WALK, false), on -> {\n" + m.group(1) +
     "  input.edit().putBoolean(CoreActivity.AIM_WALK, on).apply(); CoreBridge.setAimWalk(on); CoreInput.aimWalk = on;\n" + m.group(1) + "});", "toggle"),
    (r"(help\(R\.string\.ingame_modern_controls_help\);)", lambda m: m.group(1) + " help(R.string.ingame_aim_walk_help);", "help"),
])

# the two strings
extra_xml = APP + "res/values/strings_modern.xml"
if os.path.exists(extra_xml):
    x = open(extra_xml, encoding="utf-8").read()
    if "ingame_aim_walk" not in x:
        x = x.replace("</resources>", '''    <string name="ingame_aim_walk">Walk while aiming</string>
    <string name="ingame_aim_walk_help">Walk while aiming: while you hold the aim key, the move stick walks Leon (legs walk, the body bobs a little) and you aim with the right stick or the touch C stick.</string>
</resources>''')
        open(extra_xml, "w", encoding="utf-8").write(x)
        print("ok:", extra_xml, "- strings")
else:
    import glob
    have = any('name="ingame_aim_walk"' in open(f, encoding="utf-8", errors="ignore").read() for f in glob.glob(APP + "res/values/*.xml"))
    if not have:
        failed.append(extra_xml + ": strings_modern.xml is missing")


if failed:
    print("\nMISSING ANCHORS:\n  " + "\n  ".join(failed))
    sys.exit(1)
