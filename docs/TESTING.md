# Local validation, 2026-10-02

## Saves

The three user-created manual saves were copied from `C:/Users/d/Saved Games/CD Projekt Red/Cyberpunk 2077` to ignored `work/test-saves-20261002/`. All nine copied files were SHA-256 verified against the originals; hashes are in `work/save-backup-hashes.json`.

| Save | Metadata checkpoint | Use |
| --- | --- | --- |
| ManualSave-46 | `q304_car_found`, objective `04_open_the_car` | Replay the modified sequence |
| ManualSave-47 | `q304_ambush_done`, objective `08_talk_to_reed` | Original post-execution reference |
| ManualSave-48 | `q304_ambush_done`, objective `08b_put_on_outfit` | Original post-code-download reference |

All three saves are game version 2310 / patch 2.31, male V. Female V is covered structurally but has not been observed in-game.

## Build checks

- Source binary SHA-256: `84d98c42f3fac9ade1437d9472e6541f37077775ae1907f67c87f6a5c611bf97`.
- Five integration tests pass against extracted resources.
- Both execution sections, 2393 and 2935, retain their first four synchronized animation segments and lose the later execution segments.
- Every timeline socket signal and its time survives; only the workspot destinations at the ends of those first segments change.
- Existing code-download, journal, disguise, entry/exit and save checkpoint logic is preserved.
- Rewritten spoken lines use new unsigned localization IDs and matching subtitle entries, without mapped original VO.
- Archive contains exactly three resources: the patched scene, new subtitle entries and new subtitle map.
- Scene binary JSON roundtrip passed node/handle validation before the final appearance-operation adjustment. Repeat roundtrip validation of the final artifact is recorded in `work/final-validation.json` when complete.

## MO2 Modlists flow

Test instance: `E:/Modding/mo2modlist/test-install/MO2`.

Test game: `C:/Users/d/Documents/MO2-Modlists-Test-Game`.

1. Resolved `dist/modlist.json` to a three-package lock: this mod, ArchiveXL 1.27.3, and RED4ext 1.30.0.
2. Installed from cache with `--offline` into `Cassel Twins Survive - Test`.
3. Verified 34 managed files with zero differences.
4. Exported all three components, skipping none, to `dist/reexport.json`.
5. Resolved and installed that export with `--offline` into `Cassel Twins Survive - Reimport`.
6. Verified 34 managed files with zero differences again.

The test instance's previous Overwrite directory conflicted with import. It was moved intact to `work/mo2-overwrite-before-test-20261002/` and a new empty Overwrite directory created. This is a reversible test-instance change; preserve that backup. The main `E:/Modding/Cyberpunk2077` instance was not modified.

The test game has physical framework files from earlier test profiles. Its startup also loads Codeware, TweakXL and ITP components. This run therefore does not prove operation in a completely clean game with only the three locked packages.

## Runtime status

Launched the test profile through MO2 on 2026-10-02. RED4ext reports ArchiveXL loaded. ArchiveXL reports `cassel_twins_survive.archive.xl` loaded and `cassel_twins_survive/localization/en-us/subtitles_map.json` merged successfully.

Computer-use capture encountered a minimized game window and a `FrameArrived timed out` error; the bounded retry did not recover capture. User was asked to foreground the game and load ManualSave-46. No visual scene result is claimed.

## Remaining gameplay checks

- Replay from ManualSave-46; confirm tasers work, no guns/shots/blood appear, and both twins settle on the floor without bad transitions.
- Ask Reed about the twins; confirm the new question and reassurance subtitle appear and no contradictory VO plays.
- Test the other first response and optional conversations with Alex.
- Download Aurore's codes and optional Blind_n_Dead file, activate the imprint, change outfit and drive to the stadium.
- Confirm the next mission proceeds, save/reload works, and replay with female V.
- Inspect actual NPC life state if the scene presents any sign that death is triggered outside the inspected scene.

This is an experimental quest patch, not a completed gameplay acceptance result.

## User playtest and 0.1.1 follow-up

The user replayed 0.1.0 on 2026-10-02 and reported no shootings, successful code download, and reaching the point after putting on the netrunner suit. The old "You killed them" choice remained, Reed did not give the new reassurance, and the twins had no small unconscious movements. Movement was explicitly optional.

Inspected a contact sheet extracted from the user's Game Bar recording `Cyberpunk 2077 (C) 2020 by CD Projekt RED 2026-10-02 13-06-33.mp4`. It shows the taser sequence, twins on the floor, the no-objection response ("OK, first step's behind us" / "Targets neutralized"), code transfer, and suit objective. This supports the reported bounded success, not all branches or final mission completion.

The first build only changed embedded choice text, but the original external `q304_05_garage.json` subtitle resource also contains the choice's localization ID. Version 0.1.1 assigns each rewritten option a fresh ID, with matching entries in both the custom subtitle resource and the embedded store. Regression coverage includes option pairs that share an original ID.

Reed's original no-objection line (screenplay item 1793, section 520) now also gives the reassurance, lasting 6.5 seconds. The objection branch already contains it in item 1281. Seven integration tests and final binary JSON roundtrip pass. Rewritten speech remains subtitle-only.

The 0.1.1 manifest resolved to three packages. An offline fresh resolution lacked dependency metadata; normal resolution supplied it. The locked artifact can be installed offline. The attempted update-plan snapshot stopped because the test game is running; the user was asked to exit before deployment. Built files are in `dist/0.1.1-prototype/`.

Optional unconscious motion is deferred. The inspected scene uses dedicated cinematic floor workspots; replacing them needs an alignment check against V's existing jack-in animation. The working floor placement and execution removal are unchanged in 0.1.1.
