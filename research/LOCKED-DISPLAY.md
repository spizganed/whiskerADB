# A hidden display that works with the phone locked

Research of 2026-11-01 on a Nothing phone with Android 17 (API 37). Result: it works, with a display of a virtual device.

## Why `pp display hidden` stops when the phone locks

- scrcpy-server makes its display with `VIRTUAL_DISPLAY_FLAG_OWN_DISPLAY_GROUP` and `ALWAYS_UNLOCKED`. The flags are set (`dumpsys display`), but the display goes into display group 0, the group of the phone screen.
- The power button sleeps group 0 ("default and adjacent groups", see `cmd power help`). The display sleeps with it: its activity pauses and the screenshot is black.
- Cause, in the Android 17 source (`LogicalDisplayMapper.assignDisplayGroupLocked`, `DisplayGroupAllocator`): with the "separate timeouts" feature on, the group comes from the content mode of the display. A virtual display with no desktop mode gets the primary group (0). This choice overrides `OWN_DISPLAY_GROUP`. Logcat: `Setting new display group 0 for display N ... for reason: 0`.
- No flag set changes this: four flag sets were tried, also without `DEVICE_DISPLAY_GROUP`. All went to group 0.

## What works: a display of a virtual device

- A trusted display of a virtual device (VirtualDeviceManager) without `OWN_DISPLAY_GROUP` goes into the display group of that device: group 1. Power group 1 comes with it.
- The power button sleeps group 0 only. Seen after a real power button press: group 0 asleep (wakefulness 3), the lock screen up (`isKeyguardShowing=true`), group 1 awake, the activity on the display still resumed. `screencap -d`, `input -d N tap` and `uiautomator dump --windows` all worked while the phone was locked.
- The adb shell user can do it: it holds `CREATE_VIRTUAL_DEVICE` and `ASSOCIATE_COMPANION_DEVICES`.

Steps (the test tool is `VD2.java` in this folder):

1. Make a companion association for the shell with a device profile. The positional form is the one that works:
   `adb shell cmd companiondevice associate 0 com.android.shell 02:00:00:4D:45:52 android.app.role.COMPANION_DEVICE_APP_STREAMING`
   With no profile, the virtual device fails: "Unsupported CDM Association device profile null".
2. Read the id: `adb shell cmd companiondevice list 0` (`mId=...`).
3. Build and push the tool: `javac -cp android.jar VD2.java`, `d8 --min-api 34`, push to `/data/local/tmp/vd.dex`.
4. Run it: `CLASSPATH=/data/local/tmp/vd.dex app_process / VD2 <id> 1080 2400 420 1449`. Flags 0x1449: PUBLIC, OWN_CONTENT_ONLY, SUPPORTS_TOUCH, TRUSTED, ALWAYS_UNLOCKED. It prints the display id and keeps the display while it runs.
5. Clean up: kill the process (the device and its display go), then `cmd companiondevice disassociate 0 com.android.shell <MAC>`.

## Open

- Battery: power group 1 stays awake, so the phone does not doze while the display exists. Measure the drain.
- Android 14 to 16: `OWN_DISPLAY_GROUP` may work there as it is (no separate timeouts). Not tested.
- `pp display hidden` still uses scrcpy-server. Next step: a `pp display locked` (or a new hidden mode) with this tool, and a screenshot path (`screencap -d` with the SurfaceFlinger id).
