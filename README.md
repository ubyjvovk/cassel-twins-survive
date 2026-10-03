# Cassel Twins Survive

A Cyberpunk 2077: Phantom Liberty quest mod in development.

In **I've Seen That Face Before**, Reed and Alex incapacitate Aurore and Aymeric instead of executing them. The twins stay unconscious on the garage floor. V and Alex still obtain the access codes and assume their identities for Firestarter.

## Status

**0.1.2 installed in the test profile.** The user tested the first prototype through the suit objective: no shootings and Aurore's code download succeeded. The current build adds generic male audio for Reed's reassurance and deploys the choice-ID and timing fixes. This version needs an in-game replay.

The archive removes the continuation animations containing the shootings, gun props, shot audio, blood effects and bloody appearance changes. It retains the initial taser sequence and hands actors over to the existing floor/standing workspots. Those animation transitions may still need refinement after visual testing.

Rewritten dialogue is English. Reed's reassurance now has a 4.8-second Microsoft Mark recording; other rewritten lines remain subtitle-only. It uses new localization IDs so the original execution dialogue does not play. Reed's response on either first-choice path is: "Leave them be. We'll be done by the time they come to their senses." The no-objection path gives this subtitle 6.5 seconds. Edited choices have new IDs supplied through both the embedded scene store and the global subtitle map; changing only embedded text was insufficient in the first live test. Enable dialogue subtitles for testing.

Eight local-resource integration checks pass. The 0.1.2 packed scene and voice map pass roundtrip checks, and vgmstream decodes the packaged WEM format to the expected sample count. Both versions were packed and their scenes re-exported with valid graph/handle references. For 0.1.0, the MO2 Modlists workflow resolved the required ArchiveXL/RED4ext dependencies, installed offline, exported, and reimported offline. Both profiles verified 34 managed files with zero differences. The game startup log confirms ArchiveXL loaded that mod's configuration and merged its subtitle map. Full mission completion remains unverified.

The installed game's `ep1_2_gamedata.archive` contains the garage scene at `ep1/quest/main_quests/q304/scenes/q304_05_garage.scene`. Its synchronized execution animations, post-execution workspots, dialogue and code-download interactions need coordinated changes. Replacing a quest flag alone cannot deliver the intended scene.

WolvenKit Console 9.0.1 is available locally in `.tools/wolvenkit/`. Extracted game resources and JSON exports live under ignored `work/original/`; they must not be committed or published.

## Completion criteria

- Neither twin is executed, including scene fast-forward and both V variants.
- Both twins remain unconscious on the floor, with no execution or blood effects.
- Identity scan, access codes and optional Voodoo Treasure information remain obtainable.
- Dialogue and objectives describe incapacitation instead of death.
- Firestarter starts and both major story branches remain reachable.
- The built archive installs through a local-source MO2 Modlists manifest, reproduces offline and exports/reimports successfully.
- Gameplay is checked from a save before the hijack. Archive compilation and loading logs alone are insufficient.

## Tools

Run `tools/inspect_scene.py <exported.scene.json>` to list scene graph nodes, embedded quest operations and referenced animations. This reads the WolvenKit JSON without modifying it.

Build with Python 3.10+ and WolvenKit Console 9.0.1:

```powershell
python tools/build.py --game 'E:/Games/Cyberpunk 2077' --cli '.tools/wolvenkit/WolvenKit.CLI.exe'
python -m unittest discover -s tests -v
```

The builder accepts only the inspected 2.31 garage scene's SHA-256. It extracts resources if needed, applies the source patch, checks graph references, compiles, packs, and generates a local-source package definition in `dist/0.1.2-prototype/`. Game resources and generated archives remain untracked.

Outputs in that version directory: `cassel-twins-survive-0.1.2-prototype.zip`, `package.json` and `build-report.json`. The original 0.1.0 artifacts remain in `dist/`. ArchiveXL is required; its pinned recipe dependency allows MO2 Modlists to resolve RED4ext transitively.

This prototype replaces `q304_05_garage.scene` and conflicts with other mods replacing that same scene. New spoken text and edited choice text are English-only. Load a save before opening the twins' car; post-execution saves cannot validate the replacement sequence or undo their saved scene state.

See `docs/TESTING.md` for the local saves, installation evidence and remaining checks.

Documentation: [WolvenKit quest editor](https://wiki.redmodding.org/wolvenkit/wolvenkit-app/editor/quest-editor), [JSON conversion](https://wiki.redmodding.org/wolvenkit/wolvenkit-app/usage/import-export/import-export-as-json).

## Development installs

MO2 Modlists installs a hash-locked package snapshot. Editing this repository does not update an installed profile. Rebuild the archive and ZIP, then run the reviewed `add --replace` update using the generated package.json against the test profile with the game closed. Refresh the open MO2 window afterwards. The game cannot load the Python builder or authoring JSON directly.

## One package definition

`package.json` is the mod definition, dependency declaration, download source,
and declarative installation recipe. It requires MO2 Modlists 0.10 or newer.
Import this URL:

`https://raw.githubusercontent.com/ubyjvovk/cassel-twins-survive/main/package.json`

The top-level `name`, `version`, `dependencies`, `scripts`, and `repository` follow
npm conventions. MO2-specific metadata lives under `mo2`. The mod depends on
`archivexl: ^1.27.3`; available ArchiveXL and RED4ext versions and their download
sources are embedded in `mo2.packages`, using the same package format. No executable
install script is needed: `mo2.install` copies the archive folder.

The mod ZIP remains the existing 0.1.2 release asset. This schema migration changes
installation metadata, not gameplay. The older two-file definition is preserved
in the `v0.1.2-prototype` Git tag for older MO2 Modlists releases.

A local build writes `dist/<version>/package.json` with a local ZIP source.
`python tools/prepare_manifest.py` updates the repository definition to point to
the corresponding GitHub release. Publish that exact ZIP before sharing the URL.
