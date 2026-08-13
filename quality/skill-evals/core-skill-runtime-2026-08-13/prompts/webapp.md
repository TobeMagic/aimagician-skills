You are testing the web app in the current directory. Prove that the Increment button changes the visible count from 0 to 2 after two clicks.

Constraints:
- Start a loopback server for `index.html` and stop it before finishing.
- Create one re-runnable Playwright probe under `/tmp`, not in the fixture.
- The probe must use semantic selectors, assert desktop and mobile behavior, and fail on page console errors.
- Run the probe and report URL, command, result, console/network findings, and probe path.
