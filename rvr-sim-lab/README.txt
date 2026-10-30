RVR Sim Lab: notes for the web developer
========================================

FILES
  rvr-sim-lab.html        The simulator (HTML, CSS and JS inline).
  rvr-sim-lab-guide.html  The how-to guide. Links to rvr-sim-lab.html (and back).
  vendor/                 Self-hosted Blockly 10.4.3 and fonts. Both pages load from here.
Keep all of these together in the same folder.

HOSTING
  Static files only. No server code, database or build step. Upload the whole folder to
  any location on the site, e.g. /rvr-sim-lab/, and link to rvr-sim-lab-guide.html or
  rvr-sim-lab.html from your navigation.

  IMPORTANT: use a separate subdomain if your site has logins or anything private, e.g.
  sim.example.org rather than example.org/rvr-sim-lab/. The simulator runs whatever code
  a student types or pastes, with the same access as any script on that origin. Code
  pasted from elsewhere could read cookies and browser storage for that origin, so it
  must not share one with signed-in pages. A subdomain also keeps 'unsafe-eval' off the
  rest of the site. Make sure any session cookies aren't scoped to the parent domain.

DEPENDENCIES
  Everything is in vendor/, so the pages make no requests to other sites.
    vendor/blockly/   Blockly 10.4.3 (blocks editor, Python generator, sounds, icons).
                      Apache License 2.0, see vendor/blockly/LICENSE.
    vendor/fonts/     Latin subsets of Chakra Petch, Figtree and JetBrains Mono.
                      SIL Open Font License 1.1, see the OFL-*.txt files there.
  If Blockly can't load, the page still works in text-only mode (JavaScript or Python).

CONTENT SECURITY POLICY (only if your site sets a CSP header)
  The simulator runs the student's code in the browser with new Function(), so it needs:
    default-src 'self'
    script-src  'self' 'unsafe-inline' 'unsafe-eval'
    style-src   'self' 'unsafe-inline'
    img-src     'self' data:
    media-src   'self'
  Student code only runs in the student's own browser; nothing is sent to any server.

DATA
  Student programs, mission progress and the measured robot speed are saved in the
  browser's localStorage only (keys starting with "rvrsim:" and "rvrguide:"). No cookies,
  analytics or network calls.
  The two pages share the measured speed, so they must be served from the same origin.

EMBEDDING
  Works as a full page (recommended). To embed in an existing page, use an iframe of at
  least ~1300px wide for the side-by-side layout; narrower widths stack the panels.
