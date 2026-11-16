# THE SYSTEM

A career-progression interface in the style of a hunter "System": daily quests, penalties, weekly boss dungeons, a three-floor tower campaign, a skill tree, and real trackers (DSA log, mistake queue, projects, mocks, job pipeline) on top of a live 3D hub.

Everything is one file: `index.html`. No build step, no account, no server-side anything.

## Run it

**Recommended — needed for LeetCode verification:**

```bash
python serve.py
```

Then open `http://localhost:8123`. `serve.py` uses only the Python standard library, listens only on your own computer, serves `index.html`, and relays one read-only request to LeetCode's public profile data (LeetCode blocks web pages from calling it directly).

**Without the helper:** double-click `index.html`. Everything works except LeetCode sync; Codeforces and GitHub checks still work.

Progress saved under `file://` and under `http://localhost:8123` are separate — pick one and stick with it, or move between them with Export / Import in Settings.

**First load needs internet** (Three.js, GSAP and fonts come from CDNs). After that it runs offline for the session, and the browser cache usually covers later visits. If the CDNs are unreachable the app still works — you get a static backdrop instead of the 3D hub.

## How the game maps to the plan

| In the app | What it really is |
|---|---|
| Daily Quest | Weekday ≈2.5 h: 1 medium + 1 weakest-pattern problem, 1 h build/learn, 30 min review. Weekend ≈5.5 h: contest/mock, 3 h project, 1 h design, weekly review. Minutes scale with the hours you set. |
| Ticking a DSA quest | Opens the problem log — the quest is completed *by logging the problem*. |
| Penalty Zone | Miss a day → streak reset, −XP, −Energy, and a penalty quest next day. A Streak Freeze (boss loot, max 2) absorbs one miss. |
| Mistake Quests | Problems logged as "needed hint" or "failed" resurface after 1, 3, 7, 14 days. |
| Weekly Dungeons | Four bosses per week: contest, mock interview, shipped milestone, design write-up. |
| Tower | Three floors (months 1–2, 3–4, 5–6). Floor-boss HP is measured from your real logs, not checkboxes. |
| Shadow Army | One soldier per mastered skill, shipped milestone and defeated boss. |
| Readiness score | 0–100, computed only from what you have logged. It is deliberately harsh early on. |

## Verification (anti-cheat)

Your accounts are set in `CONFIG.accounts` and editable in Settings (LeetCode `Baldanaresh`, Codeforces `Naresh_304`). With verification on **Strict** (the default):

| Claim | Evidence required |
|---|---|
| DSA quest / problem solved | A new accepted submission on LeetCode or Codeforces. Sync (`R`, the ⟳ button, or automatically every 10 min) imports it with difficulty, pattern and failed-attempt count. |
| Mistake Quest "clean" re-solve | A fresh accepted re-submission of that problem since it came due. |
| Project milestone | A new commit in the project's public GitHub repo, made after the milestone was created and after the previous verified milestone. |
| Contest boss, strikes 1–2 | Contest participation this week found on Codeforces (with solve count) or LeetCode. |
| Old "clean" solves | Every 3 days one is randomly audited. Fail the re-solve and half its XP is clawed back. |

Problems logged by hand still work, but earn half XP, do not tick quests, and do not count toward readiness, weekly targets or floor bosses until a matching accepted submission is synced.

Limits worth knowing:

- Only submissions made **after you start** earn anything; older history is ignored.
- LeetCode exposes roughly your last 20–40 submissions, so sync at least every few days.
- A submission counts on the day you sync it for XP, but only ticks a quest if it was submitted that same day — sync before midnight.
- It proves a submission was accepted on your account, not that you solved it unaided. The audits are the defence against that.
- Build/learn, review, design study and mock interviews cannot be checked and stay self-reported.
- GitHub allows 60 unauthenticated checks per hour; private repos cannot be verified.

Turn it off in Settings → Verification if you ever need to.

## Phone: install it and get daily push reminders

The folder is ready to be hosted free on GitHub. Once pushed, three things happen on GitHub's side with your laptop off:

- **GitHub Pages** serves the app at an HTTPS address your phone can open and install.
- **A scheduled job** (`.github/workflows/system.yml`) refreshes `data/leetcode.json` about every 30 minutes, so the app can verify LeetCode solves without `serve.py`.
- **The same job sends push notifications** through the free ntfy app at 08:00, 19:00 and 22:00 India time: the morning brief, an evening check ("1/2 problems submitted so far"), and a last call.

### One-time setup

1. **Create the repo.** On github.com create a new **public** repository, e.g. `the-system`. Do not add a README or licence.
2. **Push this folder** (replace `YOUR_USER`):

   ```bash
   git init
   git add .
   git commit -m "THE SYSTEM"
   git branch -M main
   git remote add origin https://github.com/YOUR_USER/the-system.git
   git push -u origin main
   ```

   The branch must be called `main`. If the push is rejected because of the workflow file, your access token needs the `workflow` scope.
3. **Turn on Pages.** Repo → Settings → Pages → Source: *Deploy from a branch* → `main` / `/ (root)` → Save. After a minute the app is live at `https://YOUR_USER.github.io/the-system/`.
4. **Install ntfy on your phone** (Play Store / App Store, no account needed). Tap **+**, subscribe to a topic with a long, hard-to-guess name such as `system-` followed by 16 random characters. Anyone who knows the name can read it, so treat it like a password.
5. **Give the job that topic.** Repo → Settings → Secrets and variables → Actions → *New repository secret* → name `NTFY_TOPIC`, value = your topic name.
6. **Test it.** Repo → Actions → *System sync and reminders* → *Run workflow* → choose `evening` → Run. Your phone should buzz within a minute. If Actions asks you to enable workflows first, do that.
7. **Install the app.** Open the Pages address on your phone. Android Chrome: menu → *Add to Home screen* / *Install app*. iPhone Safari: Share → *Add to Home Screen*. It then opens full-screen and works offline.

### Things to know

- **Each device has its own save.** Use the phone as your main device, or move progress with Settings → Export / Import.
- **Phone sync is not instant.** LeetCode solves appear after the job's next run (up to ~30 min, sometimes later — GitHub starts scheduled jobs 5–30 min late). Codeforces and GitHub checks are instant everywhere. On the laptop, `python serve.py` is still instant.
- **Reminders only know about coding submissions.** They cannot see whether you ticked build/learn or review in the app.
- **Change the times** by editing the `cron` lines in `.github/workflows/system.yml` (they are in UTC; India = UTC + 5:30). Change usernames or timezone in the `env` block of the same file.
- **Updating the app:** edit, commit, push. Phones pick up the new version on next open (bump `CACHE` in `sw.js` if you add files).
- **Public repo:** the code, your two usernames and the cached list of your recent LeetCode submissions are visible to anyone — the same information your public profiles already show. Your progress save is not in the repo.
- **If GitHub pauses the schedule:** scheduled workflows are disabled after 60 days without repository activity. GitHub emails you; re-enable it from the Actions tab.
- **If the job logs `LeetCode fetch failed`:** LeetCode is refusing GitHub's servers. Reminders still send, but phone-side LeetCode verification will not update; the laptop helper is unaffected.

## Shortcuts

`R` sync accounts · `1`–`9` switch view · `N` log a problem · `F` start/pause focus timer · `M` mute · `S` settings · `?` help · `Esc` close / skip cinematic

## Customize

All balance numbers are in the `CONFIG` object at the very top of the `<script>` in `index.html`:

- `CONFIG.xp` — XP per problem (easy 15 / medium 30 / hard 60), quest, milestone (150), mock (100), boss, etc.
- `CONFIG.level` — level curve: `base * growth^(level-1)`, growth 1.15 = +15% per level.
- `CONFIG.ranks` — each rank needs total XP **and** a best streak.
- `CONFIG.penalty`, `CONFIG.energy`, `CONFIG.freeze`, `CONFIG.difficulty` — how much a missed day hurts.
- `CONFIG.srsDays` — mistake resurfacing schedule.
- `CONFIG.weekly` — weekly targets (10–12 problems, 5–10 outreach messages from month 3).
- `CONFIG.salary`, `CONFIG.readiness`, `CONFIG.pomodoro`, `CONFIG.hours`, `CONFIG.quality`.
- `CONFIG.accounts`, `CONFIG.verify` — linked IDs, manual-entry XP multiplier, sync interval, audit frequency and clawback, Codeforces rating → difficulty.

Content lives just below it as plain arrays: `SKILLS` (tree nodes and prerequisites), `WEEKLY_BOSSES`, `FLOORS` (campaign conditions), `ACHIEVEMENTS`, `SEED_COMPANIES`, `PATTERNS`. Quest wording is in `genQuests()`.

Console helpers for tuning: `SYS.shiftDays(1)` simulates tomorrow (resets on reload), `SYS.xp(500)` grants XP, `SYS.readiness()` prints the score breakdown.

## Backup

Settings → **Export backup** downloads a JSON file. **Import backup** restores it. Clearing browser data deletes your progress, so export occasionally. **Reset** wipes everything on this device.

## Performance

Graphics quality defaults to Auto: if the frame rate stays under ~38 fps it steps down (fewer particles, lower resolution, then no post-processing). You can force High / Medium / Low in Settings. Reduced motion follows your OS setting or can be forced.

## Upgrading to Vite + React Three Fiber (optional)

The file is already split into numbered sections that map onto modules:

1. `npm create vite@latest the-system -- --template react` then `npm i three @react-three/fiber @react-three/drei @react-three/postprocessing gsap zustand`.
2. Sections 1–5 (`CONFIG`, static data, utilities, state, progression logic) are framework-free — move them into `src/game/*.js` unchanged and wrap `state` in a zustand store with the `persist` middleware (same storage key keeps existing saves).
3. Section 10 (`World`) becomes `<Canvas>` components: each `mat(...)` shader turns into a `shaderMaterial` from drei, the army into `<Instances>`, and the composer into `<EffectComposer><Bloom/><ChromaticAberration/><Noise/><Vignette/></EffectComposer>`.
4. Sections 6–9 (views) become React components; the `ACT` map becomes store actions.
5. Sections 11–13 (sound, cinematics, onboarding) can be reused almost as-is behind hooks.
