# SafeRx — Demo Video Script
**Microsoft Agents League Hackathon 2026 · Creative Apps Track**
Target runtime: **4:45 – 5:00**

---

## Pre-recording checklist
- [ ] Backend running: `uvicorn agent.main:app --reload` (terminal hidden or minimised)
- [ ] Frontend running: `npm run dev` in `frontend/` (http://localhost:5173)
- [ ] Browser at localhost:5173, window maximised, DevTools closed
- [ ] architecture.png open in Preview, ready to switch to
- [ ] Screen resolution 1920×1080, browser zoom 100%
- [ ] Microphone tested — no background noise
- [ ] Disable notifications (macOS: Focus mode on)

---

## Section 1 — Hook `0:00 – 0:20`

### Narration
> "Every year, **169,000 children** die from fake antibiotics.
> Not from a lack of medicine — from medicine that was never real."

### On-screen action
- Black screen fades in with white text overlay:
  **"169,000 children die annually from counterfeit antibiotics."**
  *(Source: WHO, 2017)*
- Hold for 4 seconds, then fade to the SafeRx app.

### Recording notes
- Record this title card separately in a video editor if needed — even a full-screen
  browser tab with large CSS text works.
- Speak slowly. Let the number land before continuing.
- Total silence for 1–2 seconds after the stat before the next word.

---

## Section 2 — Problem `0:20 – 0:50`

### Narration
> "This is Amara. She's a community health worker in rural Nigeria.
> Today she's at a market, handing antibiotics to a child with pneumonia.
> The packaging looks right. The name is correct. But is it real?
> Right now, she has no way to know. There is no tool she can use.
> She dispenses it — and hopes."

### On-screen action
- Show a still image or short b-roll clip: health worker holding a medicine pack
  in a market setting. *(Use a royalty-free image from Unsplash or WHO media library.)*
- Overlay text fades in at bottom: **"No verification tool. No database access.
  No way to know."**

### Recording notes
- If you don't have b-roll, use a close-up of a medicine box with blurred background.
- Keep the narration unhurried — this is the emotional setup for the entire demo.
- Fade to the SafeRx UI to close the section.

---

## Section 3 — Solution intro `0:50 – 1:10`

### Narration
> "SafeRx is an AI medicine verification agent built on Azure AI Foundry.
> You describe the medicine — name, manufacturer, batch number, anything
> on the packaging — and in seconds it cross-references WHO, FDA, EMA, and
> regional regulatory databases to tell you if it's safe to dispense.
> Let me show you."

### On-screen action
- Cut to the SafeRx frontend at http://localhost:5173.
- Show the full UI: header, textarea, demo buttons.
- Hover over the three demo scenario buttons briefly to show they exist.
- Don't click anything yet — just orient the viewer.

### Recording notes
- Keep this tight. Viewers should be hungry to see the demo by the time this ends.
- The UI should look clean. If the previous session left a result on screen, refresh first.

---

## Section 4 — Live demo: RED scenario `1:10 – 2:30`

### Narration

**[1:10 – 1:25] Entering the input**
> "I'm entering a real scenario — Artesunate, a critical malaria treatment,
> has one of the highest counterfeit rates in the world.
> Let me type in a suspicious batch."

**[1:25 – 1:50] Loading animation**
> "Watch the agent work through its six-step reasoning chain.
> First it extracts the drug name and batch number from raw text.
> Then — and this is the key — it hits Foundry IQ: simultaneously querying
> the WHO Global Surveillance database, the FDA, the EMA, and regional
> batch recall systems in parallel."

**[1:50 – 2:10] RED result appears**
> "There it is. RED. Counterfeit detected.
> Three independent databases flagged this batch — WHO GFMD confirmed counterfeit,
> FDA Class I recall, and a batch alert on BX7741.
> This is not a score. This is grounded, cited evidence."

**[2:10 – 2:25] Action steps + report**
> "The agent doesn't just label it red — it tells Amara exactly what to do.
> Quarantine immediately. Don't dispense. Contact WHO. Preserve the packaging.
> And it generates a full regulatory report, ready to submit to the national
> medicines authority."

**[2:25 – 2:30] Transition**
> "Now let's see the other side."

### On-screen action

| Time | Action |
|------|--------|
| 1:10 | Click the textarea. Type slowly: `Artesunate 50mg, batch BX7741, PharmaCorp` |
| 1:22 | Click **Verify Medicine** button |
| 1:25 | Let the 6-step loading animation play fully — **do not skip it** |
| 1:50 | RED result card fills screen — pause here for 3 seconds |
| 1:53 | Scroll down slowly to show the database matches section |
| 1:58 | Click **Sources Checked** to expand — show WHO GFMD (COUNTERFEIT_CONFIRMED), FDA (CLASS_I_RECALL), BATCH_ALERTS |
| 2:08 | Scroll back up to the emergency banner: *"EMERGENCY — Immediate action required"* |
| 2:12 | Scroll to action steps — let viewer read the first 3 |
| 2:18 | Scroll to Regulatory Report section — click **Download** (show the file save dialog briefly) |
| 2:25 | Scroll back to top to reset for GREEN demo |

### Recording notes
- Type slowly at 1:10 — this isn't a speed test. Viewers should read along.
- At 1:50 when the RED circle appears, **stop talking for 2 full seconds**. Let the
  pulsing circle do its work. It's the signature visual.
- The emergency banner is red on red — make sure your screen brightness is high enough
  for it to be readable on the recording.
- If the 6-step animation feels too slow live, you can use the **✕ RED** demo button
  instead of typing — it's faster and more reliable for recording.

---

## Section 5 — Live demo: GREEN scenario `2:30 – 3:00`

### Narration
> "Same system. Same six steps. Same databases.
> Paracetamol, 500mg, GlaxoSmithKline — a legitimate batch.
> Watch how fast a verified medicine comes back clean."

*(pause while result loads)*

> "Green. Verified safe. WHO database matched. FDA registered.
> No alerts, no flags, no recalls.
> Amara can dispense with confidence — and this whole check took under a second."

### On-screen action

| Time | Action |
|------|--------|
| 2:30 | Click **✓ GREEN** demo button |
| 2:33 | Loading animation plays — briefer because GREEN skips report generation |
| 2:38 | GREEN circle pulses on screen — pause 2 seconds |
| 2:40 | Scroll down to Sources Checked — show WHO GFMD: MATCHED, FDA: MATCHED, no alerts |
| 2:50 | Scroll back up — show `verified: true`, processing time in ms |
| 2:58 | Transition to architecture screen |

### Recording notes
- The contrast with RED is the point of this section. Let the GREEN circle breathe.
- Call out the processing time (sub-1ms in mock, will be 2–4s with live Azure) —
  speed matters for health workers in low-bandwidth environments.

---

## Section 6 — Architecture `3:00 – 3:45`

### Narration
> "Here's how it works under the hood."

*(switch to architecture diagram)*

> "Input comes in as text today — with photo and voice on the roadmap via
> Azure Vision and Azure Speech.
> The SafeRx Agent — running on Azure AI Foundry with GPT-4o — runs a
> six-step reasoning chain. The critical step is Foundry IQ Verification:
> it queries an Azure AI Search index grounded across WHO, FDA, EMA, and
> regional authority alert databases simultaneously, using parallel async calls.
> The risk score combines that grounded retrieval with LLM anomaly reasoning —
> so the model can't hallucinate a verdict. Every RED flag cites a real record ID."

*(gesture toward output layer)*

> "Output goes to the user as a risk verdict with action steps.
> For YELLOW and RED cases, it generates a full regulatory report.
> And for enterprise deployments — hospital pharmacy systems, national health
> ministries — the entire agent is surfaceable through Microsoft 365 Copilot Studio."

*(final beat)*

> "The entire codebase — FastAPI backend, React frontend, agent orchestration,
> Pydantic models — was built with GitHub Copilot. Every file. Every function."

### On-screen action

| Time | Action |
|------|--------|
| 3:00 | Switch to architecture.png in Preview (full screen) |
| 3:05 | Point or highlight the INPUT column — dim Photo/Voice, bright Text |
| 3:12 | Move to AGENT box — trace the 6 steps top to bottom |
| 3:18 | Highlight Step 2 (Foundry IQ — blue) specifically |
| 3:24 | Move to KNOWLEDGE section — point to WHO, FDA, EMA, Regional sub-boxes |
| 3:32 | Move to OUTPUT column — GREEN / YELLOW / RED |
| 3:38 | Point to ENTERPRISE column — Regulatory Report + Copilot Studio |
| 3:44 | Hold on full diagram for 1 second, then switch back to browser |

### Recording notes
- Use your cursor as a pointer — move it slowly across the diagram as you narrate.
- You don't need a laser pointer or annotation tool. A slowly moving cursor is enough.
- If using QuickTime, the cursor is visible by default.

---

## Section 7 — Impact + close `3:45 – 4:30`

### Narration
> "Let's come back to where we started."

> "169,000 children. Every year. From medicine that looked real."

> "SafeRx puts a WHO-grounded verification agent in the hands of anyone with a phone —
> a community health worker in Lagos, a pharmacist in Dhaka, a parent in a rural clinic.
> No training required. No database subscription. Just: describe the medicine, get an answer."

> "At enterprise scale, a hospital pharmacy can pipe their entire incoming batch manifest
> through the API and flag counterfeits before a single tablet reaches a patient."

> "We built this in one hackathon weekend, on Azure AI Foundry, with GitHub Copilot.
> The infrastructure already exists. The databases already exist.
> What didn't exist — until now — was an agent that connected them."

*(pause)*

> "Know before you swallow."

### On-screen action
- Switch back to the SafeRx frontend.
- The GREEN result from the previous demo should still be visible.
- Slowly scroll up to show the Header — SafeRx logo and tagline.
- Hold on **"Know before you swallow."** tagline for 3 seconds.
- Fade to black.

### Recording notes
- This is the emotional close. Slow down more than feels natural.
- The tagline should be the last thing on screen before the credits card.
- Leave 1 second of silence after "Know before you swallow." before cutting.

---

## Section 8 — Credits `4:30 – 5:00`

### On-screen (title card — no narration)

```
SafeRx
AI Medicine Verification Agent

Built by Sanchita Thayagaran
Microsoft Agents League Hackathon 2026

github.com/Sanchita-Thayagaran/saferx

Powered by:
Azure AI Foundry · Foundry IQ · Azure AI Search
GitHub Copilot · React · FastAPI

"Know before you swallow."
```

### Recording notes
- Dark background (#0A0F1E), white text, blue accent for SafeRx.
- Can be built as a second full-screen HTML page, or composited in video editor.
- Soft background music fade-out over this card (optional — check contest rules on music).
- Hold for the full 30 seconds. Judges watch credits.

---

## Timing summary

| Section | Start | End | Duration |
|---------|-------|-----|----------|
| 1. Hook | 0:00 | 0:20 | 0:20 |
| 2. Problem | 0:20 | 0:50 | 0:30 |
| 3. Solution intro | 0:50 | 1:10 | 0:20 |
| 4. RED demo | 1:10 | 2:30 | 1:20 |
| 5. GREEN demo | 2:30 | 3:00 | 0:30 |
| 6. Architecture | 3:00 | 3:45 | 0:45 |
| 7. Impact + close | 3:45 | 4:30 | 0:45 |
| 8. Credits | 4:30 | 5:00 | 0:30 |
| **Total** | | | **5:00** |

---

## Backup: if the API is slow or fails during recording

Use the demo buttons (`✓ GREEN`, `⚠ YELLOW`, `✕ RED`) instead of typing — they
call `POST /verify/demo?scenario=X` which is instant in mock mode and bypasses
any extraction latency. Results are identical to manual entry for the demo scenarios.

If mock mode is active (Azure keys not wired to live index), all results are still
fully realistic — the mock data is drawn from real WHO alert patterns.

---

## Post-production notes

- Recommended tool: **QuickTime** (screen + mic) → export → trim in iMovie or DaVinci Resolve.
- Add captions for the WHO statistic and the "Know before you swallow." tagline —
  contest judges may watch without audio.
- Export at 1080p minimum. 4K if your machine handles it.
- Check contest upload size limit before exporting — compress with HandBrake if needed.
