#!/usr/bin/env python3
"""The bone list of Leon (patch 0990, re4ModernDumpBones): the runtime functions that write leon_bones.txt into the
app's files folder. Small anchored edits, safe to run twice. Run from the repo root, after apply_modern_controls.py."""
import re, sys
P = "port/whole/runtime/aim_options.cpp"
s = open(P, encoding="utf-8").read()
if "re4_modern_bone_begin" in s:
    print("already done, skipped:", P)
    sys.exit(0)
FUNCS = '''// Patch 0990 (player.cpp re4ModernDumpBones): the list of Leon's parts, to find the ones of his legs.
// leon_bones.txt in the app's own files folder (Android/data/<package>/files).
static FILE* gBones = nullptr;

void re4_modern_bone_begin(int n)
{
    static const char* paths[] = {
        "/storage/emulated/0/Android/data/com.ast.cubeevil4/files/leon_bones.txt",
        "/sdcard/Android/data/com.ast.cubeevil4/files/leon_bones.txt",
        "/data/user/0/com.ast.cubeevil4/files/leon_bones.txt",
        "/data/data/com.ast.cubeevil4/files/leon_bones.txt",
    };
    gBones = nullptr;
    for (const char* path : paths) {
        gBones = fopen(path, "w");
        if (gBones) {
            re4_log("bones: writing %s", path);
            break;
        }
    }
    if (!gBones) {
        re4_log("bones: no file could be opened");
        return;
    }
    fprintf(gBones, "Leon: %d parts\\n# index parent(255=model) restX restY restZ worldX worldY worldZ (mm; world relative to Leon)\\n", n);
}

void re4_modern_bone(int index, int parent, float cx, float cy, float cz, float wx, float wy, float wz)
{
    if (gBones) {
        fprintf(gBones, "%d %d %.0f %.0f %.0f %.0f %.0f %.0f\\n", index, parent, cx, cy, cz, wx, wy, wz);
    }
}

// Patch 0990 (player.cpp re4ModernLegs): one line of numbers a frame while Leon walks aiming (the first 300 lines),
// aim_walk_trace.txt in the app's files folder, written once a run.
void re4_modern_trace(const float* v, int n)
{
    static FILE* f = nullptr;
    static int lines = 0;
    static const char* paths[] = {
        "/storage/emulated/0/Android/data/com.ast.cubeevil4/files/aim_walk_trace.txt",
        "/sdcard/Android/data/com.ast.cubeevil4/files/aim_walk_trace.txt",
        "/data/user/0/com.ast.cubeevil4/files/aim_walk_trace.txt",
    };
    if (lines >= 300) {
        return;
    }
    if (!f) {
        for (const char* path : paths) {
            f = fopen(path, "w");
            if (f) {
                break;
            }
        }
        if (!f) {
            lines = 300;
            return;
        }
        fprintf(f, "# mag joyX joyY joyDpad subX subY m3r wepPitch fwork0 | pelvisAim xyz | pelvisWalk xyz | leg17walk xyz | leg17final xyz | leg17pos xyz | legStep seqSpeed seqFrame seqNum | plAngY plAngX\\n");
    }
    for (int i = 0; i < n; i++) {
        fprintf(f, "%.3f ", v[i]);
    }
    fprintf(f, "\\n");
    fflush(f);
    lines++;
}

// Patch 0990 (player.cpp re4ModernLegs): the second trace, aim_walk_trace2.txt (the first 120 lines).
void re4_modern_trace2(const float* v, int n)
{
    static FILE* f = nullptr;
    static int lines = 0;
    static const char* paths[] = {
        "/storage/emulated/0/Android/data/com.ast.cubeevil4/files/aim_walk_trace2.txt",
        "/sdcard/Android/data/com.ast.cubeevil4/files/aim_walk_trace2.txt",
        "/data/user/0/com.ast.cubeevil4/files/aim_walk_trace2.txt",
    };
    if (lines >= 120) {
        return;
    }
    if (!f) {
        for (const char* path : paths) {
            f = fopen(path, "w");
            if (f) {
                break;
            }
        }
        if (!f) {
            lines = 120;
            return;
        }
        fprintf(f, "# per part 17..25: ang before xyz, ang after the walk motion xyz; then part 5 (before, after), part 2 (before, after)\\n");
    }
    for (int i = 0; i < n; i++) {
        fprintf(f, "%.3f ", v[i]);
    }
    fprintf(f, "\\n");
    fflush(f);
    lines++;
}

void re4_modern_bone_end(void)
{
    if (gBones) {
        fclose(gBones);
        gBones = nullptr;
        re4_log("bones: written");
    }
}

'''
new, n = re.subn(r"^(// Patch 0990 \(player\.cpp\): the app's \"Modern controls\"\.)$", lambda m: FUNCS + m.group(1), s, count=1, flags=re.M)
if n == 0:
    print("MISSING ANCHOR: getter comment of re4_modern_controls"); sys.exit(1)
new, n = re.subn(r"^(#include <cstdlib>)$", lambda m: "#include <cstdio>\n" + m.group(1), new, count=1, flags=re.M)
if n == 0:
    print("MISSING ANCHOR: #include <cstdlib>"); sys.exit(1)
open(P, "w", encoding="utf-8").write(new)
print("ok:", P)
