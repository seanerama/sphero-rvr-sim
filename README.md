# RVR Sim Lab

A browser-based simulator for practicing Sphero RVR+ coding. Young coders build a program with blocks, see it as JavaScript or Python, test it in a virtual arena, then copy it into Sphero Edu to run on a real robot.

It runs entirely in the browser. There is no account, server or install, and nothing a student writes leaves their device.

## Features

- **Three ways to code:** Blockly blocks, JavaScript and Python, using Sphero Edu command names.
- **Four missions:** Free Roam, Square Dance, Garage Parking and Red Light Stop.
- **Live arena:** a top-down view with walls, color tiles, a trail, sensor readouts and speech bubbles.
- **Match your real robot:** measure your robot once, and the sim, the mission hints and the guide all use its real speed. A color test checks your cards under your own lights.
- **Copy for Sphero Edu:** copies your program, plus a small color helper if it needs one.
- **How-to guide:** an interactive walkthrough for kids and their grown-ups.
- **Private by design:** Blockly and the fonts are self-hosted, with no cookies, analytics or third-party requests. Work is saved in the browser's `localStorage`.

## Try it locally

You need Python 3, or any other static file server.

```sh
git clone https://github.com/seanerama/sphero-rvr-sim.git
cd sphero-rvr-sim
python3 -m http.server 8000 -d rvr-sim-lab
```

Then open:

- Simulator: <http://localhost:8000/rvr-sim-lab.html>
- Guide: <http://localhost:8000/rvr-sim-lab-guide.html>

## Deploying

The site is static files with no build step. Upload everything in `rvr-sim-lab/`, including `vendor/`.

The simulator runs code that students type or paste, so if your site has logins or private pages, host it on a separate subdomain. See [`rvr-sim-lab/README.txt`](rvr-sim-lab/README.txt) for this and for the Content Security Policy it needs.

## Project layout

```text
rvr-sim-lab/
  rvr-sim-lab.html        The simulator (HTML, CSS and JS inline)
  rvr-sim-lab-guide.html  The how-to guide
  README.txt              Hosting notes for web developers
  vendor/                 Self-hosted Blockly and fonts
tests/
  test_sim.py             Browser test suite
```

## Testing

```sh
pip install playwright
playwright install chromium
python3 tests/test_sim.py
```

The suite drives both pages in headless Chromium. It solves the missions in both languages, and it compares the sim's Python output with real CPython.

## Known limits

- **Not yet tested on hardware:** the project hasn't been run on a real RVR+ or in Sphero Edu. Command names were checked against Sphero's programming wiki. The color matching is an untested estimate.
- **The sim is idealized:** the robot starts and stops instantly and drives perfectly straight. Speed calibration matches a 2-second drive, so very short moves may differ on a real robot.
- **Python is a subset:** it covers what beginners use, including functions, lists, tuples, dictionaries, slices and f-strings. Classes, list comprehensions and `try`/`except` give a clear error. Whole-number results print as `5`, not `5.0`.

## License

The project is released under the [MIT License](LICENSE).

Third-party files in `rvr-sim-lab/vendor/` keep their own licenses:

- Blockly: [Apache License 2.0](rvr-sim-lab/vendor/blockly/LICENSE)
- Chakra Petch, Figtree and JetBrains Mono: SIL Open Font License 1.1, in [`vendor/fonts/`](rvr-sim-lab/vendor/fonts)

## Trademarks

RVR Sim Lab is an independent practice tool. It is not made, endorsed or sponsored by Sphero, Inc. Sphero, RVR, RVR+ and Sphero Edu are trademarks of Sphero, Inc.
