# whiskerADB

`pp` is a small adb wrapper for an Android phone that a person also uses. Every input command first checks that your app is in front and stops if it is not.

```sh
export PATH="$PWD/bin:$PATH"
export PP_PKG=com.example.app # the app id (required)
pp open                       # bring the app forward
pp tap "Save"                 # tap a node by its text or description
pp wait "Done" 10             # wait up to 10 s until a text shows
pp go "Settings" "Account"    # tap, then wait
pp type 'any text, & symbols' # type through the clipboard: exact text
pp key enter|back|del
pp texts                      # the visible texts, one per line
pp shot                       # screenshot, prints the path
pp audit                      # targets under 48 dp and controls without a label: no image, no model
pp compare a.png b.png        # print the screen regions that differ
pp init                       # add a short pp block to AGENTS.md and CLAUDE.md in this folder
pp states                     # light, dark and 200% text in one image; the settings come back after
```

- `audit` reads the uiautomator tree. It costs no image.
- `compare` and `states` need python3 with PIL.
- `states` changes the dark mode and font scale of the whole phone for about 10 s. It restores both on exit. Run it only when you are not using the phone.
- `type` uses the clipboard through `termux-clipboard-set` (Termux:API). Without it, `pp` falls back to `adb shell input text`, which can drop characters.
- `tap` checks only the app in front. A floating chat bubble of another app (Android bubbles) lies over it and takes a tap at its spot. Move the bubble, or tap by coordinates away from it.
- Tap a text field itself, not its hint text, before `type`: a tap on the hint can leave the field without focus.
- Set `PP_OUT` for the screenshot folder.

Needs `adb`, `python3` and a connected phone.
