# whiskerADB

**Drive an Android app from the command line, on a phone that a person also uses.**

`pp` is a small shell tool on top of `adb`. It taps, types, waits, reads the screen as text and takes screenshots.
Its main rule: **it acts only when your app is in front.** If you open another app, `pp` stops and does nothing.
This protects you. A script cannot tap your messages or your bank app by mistake.

It is made for AI coding agents (Claude Code, Codex, OpenCode and others) that test an app on a real phone. A person can use it as well.

## Why not raw `adb shell input`?

| Problem with raw adb | What `pp` does |
|---|---|
| `input tap 540 1200` needs the pixel position of a button. Positions change with every layout and screen size. | `pp tap "Save"` finds the button by its **text or description** and taps its centre. |
| A tap lands on whatever app is in front. The user switched apps: the tap goes into the wrong app. | Every input command first checks that your app is in front. If not, it exits with code 10. |
| A model needs a screenshot to read the screen. Images cost many tokens. | `pp texts` prints every visible text, one per line. No image is needed. |
| `input text` drops characters and cannot type spaces and symbols well. | `pp type` pastes through the clipboard: the exact text arrives. |
| You do not know whether a screen has loaded. | `pp wait "Done" 10` waits until a text shows. |
| A manual accessibility check takes many screenshots. | `pp audit` finds small touch targets and unlabeled controls from the UI tree. No image. |

## What you need

- A computer (or a phone with a Linux shell) with `adb` and `bash`.
- `python3` (3.8 or newer). The commands `compare` and `states` also need the Python package `Pillow`.
- An Android phone with USB debugging or wireless debugging on, connected to `adb` (check with `adb devices`).
- The app id of the app to test. Example: `com.example.app`. Find it with `adb shell pm list packages | grep name`.

## Install

```sh
git clone https://github.com/spizganed/whiskerADB.git
cd whiskerADB
export PATH="$PWD/bin:$PATH"      # add this line to ~/.bashrc to keep it
export PP_PKG=com.example.app     # your app id: required
```

Check it works. Open your app on the phone, then run:

```sh
pp front && echo "app is in front"
pp texts
```

You should see the texts of the screen.

## A first session

This logs in to an app and checks the result. Each line is one command.

```sh
pp open                          # bring the app to the front
pp wait "Sign in" 10             # wait up to 10 s for the login screen
pp tap "Email"                   # focus the field
pp tap "Install" 3               # the third node with that label (a list of rows with one button each)
pp hold "Message"                # long press (about 800 ms): opens a menu or an action
pp tapxy 540 1200                # a position, on the screen pp uses (never a raw adb input: the id of the second display changes)
pp type 'me@example.com'
pp tap "Password"
pp type 'my secret & symbols'
pp go "Sign in" "Welcome"        # tap Sign in, then wait for Welcome
pp texts                         # read what the screen shows now
pp shot                          # take a screenshot; prints the file path
```

## Commands

| Command | What it does |
|---|---|
| `pp front` | Exit code 0 when the app is in front. Prints nothing. |
| `pp open` | Bring the app to the front. |
| `pp texts` | List the visible texts and descriptions, one per line. |
| `pp tap "label"` | Tap the first node whose text or description equals the label exactly. Exit 2 if no node matches. |
| `pp wait "text" [secs]` | Wait until a text that contains this text shows. Default 20 s. Exit 3 on timeout. |
| `pp go "label" "text" [secs]` | `tap`, then `wait`. The usual way to move between screens. |
| `pp type "text"` | Type into the focused field through the clipboard. |
| `pp key NAME` | Send a key: `enter`, `back`, `del`, `paste`, or an Android key code number. |
| `pp swipe x1 y1 x2 y2` | Swipe between two points. Use it to scroll. |
| `pp scroll down\|up` | Scroll most of one screen in the middle of the screen. |
| `pp find "label" [n]` | Scroll down until the label shows (at most n screens, default 8). Then `pp tap` it. |
| `pp shot [file]` | Screenshot. Wakes the screen first. Prints the file path. |
| `pp audit` | List touch targets under 48 dp and controls with no label. |
| `pp compare a.png b.png` | Print the screen regions that differ between two screenshots. |
| `pp display overlay\|hidden\|locked\|off` | Work on a second display, so the person keeps the phone screen. See below. |
| `pp perf start\|show` | Frame stats of the app since `start`: frames, slow frames, frame times. Also the app's log lines with the tag `Perf`. |
| `pp states [file]` | One image of the screen in light mode, dark mode and 200% text. |
| `pp init` | Add a short `pp` block to `AGENTS.md` and `CLAUDE.md` in the current folder, so an agent knows the tool. |

Exit codes: `0` ok, `2` no matching node, `3` wait timed out, `10` your app is not in front.

### `pp audit`: accessibility without images

It reads the UI tree and prints one line for each problem (`small` or `nolabel`, with the size and the position), then a count. A problem is a clickable element smaller than 48 dp, or a control with no text or description (a screen reader cannot name it). Fix the app, run it again, and the list gets shorter.

### `pp display`: a second screen for the agent

After `pp display overlay` or `pp display hidden`, `open`, `texts`, `tap`, `type`, `key`, `swipe` and `shot` act on the second display. The phone screen stays free. `pp display off` goes back.

- `overlay`: Android's own simulated display. No download. A small preview window floats over the phone screen.
- `hidden`: no window. On Android 14 and newer it is the `locked` display below, so it works with the phone locked too; older Android uses scrcpy-server. `open`, `texts`, `tap`, `swipe` and `shot` work. It has no keyboard, so `pp type` types nothing: send text through the app (for example `pt send`). Tested on Android 17.
- Was: on Android 17 the scrcpy display stopped with the phone locked. Is: `hidden` uses the `locked` display there.
- A locked phone and no second display: input commands stop with exit code 11 and say to run `pp display hidden`. `pp locked` exits 0 when the phone is locked.
- `locked`: no window, and it keeps working while the phone is locked. It is a display of a virtual device, with its own power group: the power button sleeps only the phone screen. It makes a companion association for the adb shell once. No keyboard, as `hidden`. Android 14 and newer. Why and how: `research/LOCKED-DISPLAY.md`.
- Each call is tested on Android 16. `pp states` and `pp audit` still use the phone screen.

### `pp states`: light, dark and large text in one image

It changes the dark mode and the font scale of the **whole phone** for about 10 seconds, takes three screenshots and joins them. Both settings come back when it ends, also after an error. Run it only when you are not using the phone.

### `pp perf`: motion as numbers

`pp perf start` resets the frame stats of the app (`dumpsys gfxinfo`). Do the action. `pp perf show` prints the frame count, the slow frames and the frame times. It also prints the app's log lines with the tag `Perf`, so an app can log its own counts (for example how often a list row redraws). `start` also sets the main log buffer to 8 MB (until the next phone start): some phones keep only 20 s of log. A debug build is slower than a release build: compare a build with a build of the same type.

### `pp compare`: did the screen change?

Take a screenshot before and after a change. `pp compare before.png after.png` prints the regions that differ, on a 24 px grid. An agent can then look at the changed region only.

## Use it with an AI agent

Run `pp init` in your project folder. It adds a short block to `AGENTS.md` and `CLAUDE.md` that lists the commands. The agent then knows how to test the app and to prefer `pp texts` over a screenshot.

A good loop for an agent: build, install, `pp open`, `pp go ...` through the flow, `pp texts` to check, `pp audit` for accessibility, `pp shot` only when it must see the picture.

## Safety

- Every input command (`tap`, `type`, `key`, `swipe`, `shot`, `audit`, `states`) checks the front app first. This is the whole point of the tool.
- `pp` does not work around that check. If it stops, the person is using the phone: wait.
- `pp states` changes phone-wide settings and restores them. Do not run it while someone uses the phone.
- `pp` never rotates the screen.

## Good to know

- **Typing.** `pp type` uses `termux-clipboard-set` (Termux:API) when it exists. Without it, `pp` falls back to `adb shell input text`, which can drop characters. Tap the text field itself, not its hint text, before `type`: a tap on the hint can leave the field without focus.
- **Floating bubbles.** An Android chat bubble of another app lies over your app and takes a tap at its spot. Move the bubble, or tap by coordinates away from it.
- **Several devices.** Set `ANDROID_SERIAL` to the device you want. `pp` passes it to `adb`.
- **Where files go.** Screenshots go to `$PP_OUT`. The default is `$TMPDIR/pp`, or `/tmp/pp`. The screen dump on the phone goes to `$PP_PHONE_DIR`, by default `/sdcard/Download/ADB`, not to the root of the shared storage.
- **Speed.** Each `tap`, `texts` and `wait` poll runs `uiautomator dump`. This takes a moment, so do not poll in a tight loop.
- **Exact labels.** `tap` needs the full text. Run `pp texts` first to see the exact label.
- **Webviews and games.** Nodes with no text and no description cannot be found by label. Use `pp swipe` and `adb shell input tap x y` there.

## Files

```text
bin/pp        the tool: one bash script
lib/find.py   finds a node in the UI tree by label
lib/ui.py     audit, compare and the screenshot sheet
lib/init.py   writes the pp block into AGENTS.md and CLAUDE.md
```

The whole tool is about 230 lines. Read it before you run it.

## Related

- [skills](https://github.com/spizganed/skills): the `audit-ui` skill uses `pp audit` for its cheap checks.

## License

MIT. See [LICENSE](LICENSE).
