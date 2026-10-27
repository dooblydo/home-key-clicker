# Home Key Clicker

A small Linux desktop app that sends the **Home** key to selected windows on a timer. It can run one timer for one window or separate timers for multiple windows. Timer intervals can be fixed or randomized.

## Features

- Select one window or two or more windows to control.
- Run an independent countdown for each selected window.
- Set a fixed interval in minutes, use the 1, 5, 10, or 30 minute presets, or choose a random interval.
- Use the built in random ranges (4–6 or 5–9 minutes) or enter a custom random range.
- Stop all timers at any time.

When a timer expires, the app focuses its assigned window, waits briefly for focus to settle, and sends Home. The timers use the same selected interval or random range, with independent countdowns.

## Requirements

- Linux running an X11 desktop session
- Python 3 with Tkinter
- `xdotool`

On Ubuntu or Debian based systems, install the dependencies with:

```sh
sudo apt install python3-tk xdotool
```

## Run

```sh
python3 home_key_clicker.py
```

Choose **Single window** or **Multiple windows**, click **Choose windows…**, and select the target window or windows. In multiple mode, hold Ctrl or Shift while selecting. Choose an interval and click **Start**.

The app needs an X11 session because it uses `xdotool` to activate windows and send key presses. It may not work in a Wayland session.

## AppImage

On x86_64 Linux, build an AppImage with:

```sh
./build-appimage.sh
```

The script builds a bundled Python app and includes `xdotool` plus its non-glibc libraries. The resulting file is `build/appimage/dist/HomeKeyClicker-x86_64.AppImage`. It still requires an X11 session.

GitHub Actions can build the AppImage manually from the Actions tab. Pushing a version tag such as `v1.0.0` also creates a GitHub release with the AppImage attached.
