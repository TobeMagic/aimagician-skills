# React Browser Setup

Use this module only for standalone browser-native prototypes or motion compositions that need React. Existing repositories keep their current framework, package manager, build system, and pinned dependency policy.

## Setup Contract

- Prefer project-installed React and ReactDOM with a lockfile. Do not silently introduce a second React version or a global package.
- If a standalone no-build artifact must load a CDN, pin exact versions and filenames, record Subresource Integrity hashes and `crossorigin`, provide an offline fallback, and verify the final URLs at implementation time. Never copy a stale version or integrity value from a reference.
- JSX needs an explicit project transform. For durable work, precompile it; browser Babel is acceptable only for a bounded prototype and must not be presented as production setup.
- Keep one root, load React before ReactDOM, and mount only after the target element exists. Surface compile and runtime errors visibly during development.
- Split large compositions by scene, data, and reusable primitive. Shared deterministic time and tokens stay in one small module; individual scenes must not own competing clocks.

## Failure Matrix

| Symptom | Check |
|---|---|
| `React is not defined` | Dependency order, module/global mode, and actual script load. |
| JSX token error | Missing transform or serving raw JSX to a browser that expects JavaScript. |
| Blank root | Mount target, console error, strict-mode side effect, or failed asset import. |
| Duplicate hooks/runtime error | More than one React copy or incompatible React/renderer versions. |
| Capture differs from playback | Wall-clock effects, strict-mode double execution, unseeded state, or an active animation ticker. |

For deterministic motion, use `assets/starter/react-motion-stage.jsx`. The starter assumes React is supplied by the host project; it intentionally does not embed a remote CDN or vendor identity.
