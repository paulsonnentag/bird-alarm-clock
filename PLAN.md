# Vogelwecker – plan

An iOS alarm clock that wakes you with a random bird call each day. You guess
which bird is singing, and spaced repetition (as in Anki) gradually teaches you
more birds. The UI is in German.

Screen sketches: `docs/sketches/` (see `overview.png`).

## Decisions so far
- **Platform:** SwiftUI, iOS 26+, using **AlarmKit**. Alarms ring in silent
  mode and Focus, and each alarm can have its own sound.
- **Language:** German UI. Bird names default to German, with English as an option.
- **Screens:** Wecker (time, weekdays, on/off, streak, birds learned; *no*
  "tomorrow's bird" banner) · Ringing (system AlarmKit UI: "Stopp" / "Raten") ·
  Quiz (play the call, 4 photo choices, "Keine Ahnung") · Reveal (photo, name,
  short text, credits, next review) · Meine Vögel (gelernt / am Lernen / noch
  nicht, "Jetzt üben") · Einstellungen · Vögel auswählen.
- **Data:** nothing is bundled except `Vogelwecker/Resources/catalog.json`
  (metadata + URLs). On first launch the app downloads everything and caches
  it, so it then works fully offline:
  - Photos: iNaturalist taxon photos with open (CC) licenses.
  - Calls: xeno-canto, A-quality recordings, preferably songs with no other
    species in the background, 20–75 s long, recorded in or near Germany.
  - Short text: German Wikipedia summary.
- **Catalog:** `tools/build_catalog.py` builds `catalog.json` from about 45
  common Central European birds. It needs `XC_API_KEY` set in the environment.
  **Never commit the key.** The app itself needs no key, because xeno-canto
  download URLs are public.
- **Alarm sounds:** AlarmKit (like notifications) only plays files in the app
  bundle or `Library/Sounds`, and not MP3. Convert each MP3 with AVAudioFile to
  a CAF file (linear PCM, mono, 22 kHz), about 30 s long, normalised, with a
  gentle fade-in, and store it in `Library/Sounds`.
- **Scheduling:** AlarmKit sounds are fixed per alarm. So schedule the next
  ~14 occurrences as one-off alarms, each with its bird chosen in advance.
  Re-plan whenever the app opens or an answer is graded.
- **Choosing birds (SM-2 style):** Each morning, pick the most overdue bird.
  If none is due, introduce a new one (at most one every N days, configurable),
  in catalog order. Right answer: interval 1 → 3 → interval × ease. Wrong:
  interval back to 1 day, ease −0.2. A bird counts as *gelernt* once its
  interval is ≥ 21 days. "Jetzt üben" allows extra practice.
- **"Raten" button:** an AppIntent with `openAppWhenRun` opens the quiz for
  that alarm's bird. If she tapped "Stopp" instead, opening the app later still
  shows the quiz for this morning's unanswered bird.
- **Snooze:** left out of v1, because AlarmKit snooze/countdown needs a Live
  Activity widget extension.
- **Sideloading:** free Apple ID, so the app must be reinstalled from Xcode
  every 7 days. The app reads the expiry date from `embedded.mobileprovision`,
  shows a "Bitte neu installieren" banner 2 days before it expires, and sends a
  notification.
- **Project:** XcodeGen `project.yml` (or a plain Xcode project). Bundle id
  `com.paulsonnentag.vogelwecker`. Choose your Personal Team under Signing.

## Next steps
1. `export XC_API_KEY=...` then `python3 tools/build_catalog.py`. Check that
   every bird has photos and a sensible recording.
2. Build the SwiftUI app as described above, run it in the Simulator, then
   install it on the iPhone.
