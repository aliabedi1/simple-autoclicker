# Frontend

Run `npm ci`, then `npm run build` after editing. Commit `dist/` along with source changes, because the Python launcher serves that bundle without a Node.js runtime.

- `npm run lint`: lint React and TypeScript.
- `npm run build`: typecheck and build the production bundle.
- `npx playwright test`: exercise desktop light/dark and narrow-window layouts against the real local server with a fake mouse backend.

The normal app launcher serves the production bundle. `npm run dev` alone shows the frontend but cannot control the mouse: authenticated API actions come from `desktop.py`.
