"""Build the nonlethal garage prototype from the user's local game resources."""
import argparse
import copy
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

from inspect_scene import walk

ROOT = Path(__file__).resolve().parents[1]
SCENE = Path('ep1/quest/main_quests/q304/scenes/q304_05_garage.scene')
SOURCE_SHA256 = '84d98c42f3fac9ade1437d9472e6541f37077775ae1907f67c87f6a5c611bf97'
NAME = 'cassel_twins_survive'
CUSTOM = Path('cassel_twins_survive/localization/en-us')


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def validate(document):
    objects = list(walk(document))
    handles = [o['HandleId'] for o in objects if 'HandleId' in o]
    assert len(handles) == len(set(handles)), 'Duplicate handle definitions'
    dangling = {o['HandleRefId'] for o in objects if 'HandleRefId' in o} - set(handles) - {'-1'}
    assert not dangling, f'Dangling handles: {dangling}'
    root = document['Data']['RootChunk']
    if root['$type'] != 'scnSceneResource':
        return
    nodes = [x['Data'] for x in root['sceneGraph']['Data']['graph']]
    ids = {n['nodeId']['id'] for n in nodes}
    assert len(ids) == len(nodes)
    for node in nodes:
        for sock in node.get('outputSockets', []):
            assert all(d['nodeId']['id'] in ids for d in sock['destinations'])
    line_ids = {x['itemId']['id'] for x in root['screenplayStore']['lines']}
    for obj in objects:
        if obj.get('$type') == 'scnDialogLineEvent':
            assert obj['screenplayLineId']['id'] in line_ids


def patch(document, dialogue):
    document = copy.deepcopy(document)
    root = document['Data']['RootChunk']
    nodes = {x['Data']['nodeId']['id']: x['Data'] for x in root['sceneGraph']['Data']['graph']}
    report = {'removed_events': [], 'redirected_workspots': [], 'dialogue': [], 'version': '0.1.0-prototype'}

    # The first segments stun and extract the twins. The continuation segments
    # contain the executions. Reuse the final floor/standing workspots instead.
    for section_id, final_spots in (
        (2393, {513: 4007, 1: 4011, 257: 2856, 1025: 4045}),
        (2935, {513: 4009, 1: 4038, 257: 2951, 1281: 4055}),
    ):
        section = nodes[section_id]
        kept = []
        for handle in section['events']:
            event = handle['Data']
            kind = event['$type']
            values = [o['$value'] for o in walk(event) if isinstance(o.get('$value'), str)]
            continuation = kind == 'scnPlaySkAnimEvent' and event['startTime'] >= 10099 and any('synced__killing_netrunners' in v for v in values)
            lethal_fx = kind == 'scneventsVFXEvent' and any(v in ('blood_hit_big', 'muzzle_flash_lights_tpp', 'muzzle_flash_tpp') for v in values)
            lethal_audio = kind == 'scnAudioEvent' and any('shoot_netrunner' in v or 'headshot' in v or 'unequip_pistol' in v for v in values)
            gun_prop = any(o.get('$type') == 'scnPropId' and o.get('id') in (7, 8, 9) for o in walk(event))
            if continuation or lethal_fx or lethal_audio or gun_prop:
                report['removed_events'].append({'section': section_id, 'event': event['id']['id'], 'type': kind})
                continue
            # Keep socket signals and their exact timing: other quest branches
            # consume them. Removed animation scaling handles are no longer needed.
            if kind == 'scneventsSocket':
                event['scalingData'] = None
            if kind == 'scnPlaySkAnimEvent' and any('synced__killing_netrunners' in v for v in values):
                performer = event['performer']['id']
                blend = event.get('poseBlendOutWorkspot', {}).get('Data')
                if performer in final_spots and blend:
                    old = blend['workspotId']['id']
                    new = final_spots[performer]
                    blend['workspotId']['id'] = new
                    # The end-of-animation socket must select the same workspot.
                    for socket in section['outputSockets']:
                        for destination in socket['destinations']:
                            if destination['nodeId']['id'] == old:
                                destination['nodeId']['id'] = new
                    report['redirected_workspots'].append([section_id, performer, old, new])
            kept.append(handle)
        section['events'] = kept

    # Keep the nodes and connections for save compatibility, changing only their
    # visual operations. Keep the actors' existing clean appearances.
    for obj in walk(root):
        if obj.get('$type') == 'questVariantState' and obj.get('name', {}).get('$value') in ('scene_blood1', 'scene_blood2'):
            obj['show'] = 0
        if obj.get('$type') in ('questCharacterManagerVisuals_ChangeEntityAppearance', 'questCharacterManagerVisuals_PrefetchEntityAppearance'):
            obj['appearanceEntries'] = [entry for entry in obj['appearanceEntries'] if entry['appearanceName']['$value'] not in ('theo__q304__kidnap_blood', 'bella__q304__kidnap_blood')]
        if obj.get('$type') == 'questEntityManagerToggleComponent_NodeTypeParams' and obj.get('componentName', {}).get('$value') == 'L_MuzzleFlash':
            obj['enable'] = 0
    for prop in root['props']:
        if prop['propId']['id'] in (7, 8, 9):
            prop['spawnDespawnParams']['isEnabled'] = 0

    subtitles = []
    changed = {int(k): v for k, v in dialogue['lines'].items()}
    for line in root['screenplayStore']['lines']:
        item = line['itemId']['id']
        if item not in changed:
            continue
        # New, stable IDs prevent the old execution VO playing over new subtitles.
        new_id = str(16002026000000000000 + item)
        old_id = line['locstringId']['ruid']
        line['locstringId']['ruid'] = new_id
        for key in ('femaleLipsyncAnimationName', 'maleLipsyncAnimationName'):
            line[key]['$value'] = 'None'
        subtitles.append({'$type': 'localizationPersistenceSubtitleEntry', 'femaleVariant': changed[item], 'maleVariant': '', 'stringId': new_id})
        report['dialogue'].append({'item': item, 'old_id': old_id, 'new_id': new_id, 'text': changed[item]})
    option_text = {int(k): v for k, v in dialogue['options'].items()}
    option_ids = {o['locstringId']['ruid']: option_text[o['itemId']['id']] for o in root['screenplayStore']['options'] if o['itemId']['id'] in option_text}
    for descriptor in root['locStore']['vdEntries']:
        text = option_ids.get(descriptor['locstringId']['ruid'])
        if text and descriptor['localeId'] in ('en_us', 'db_db'):
            payload = root['locStore']['vpEntries'][descriptor['vpeIndex']]
            assert payload['variantId'] == descriptor['variantId']
            payload['content'] = text
    validate(document)
    return document, subtitles, report


def resource(template, data):
    doc = copy.deepcopy(template)
    doc['Data']['RootChunk']['root']['Data'] = data
    return doc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, default=Path('E:/Games/Cyberpunk 2077'))
    parser.add_argument('--cli', type=Path, default=ROOT / '.tools/wolvenkit/WolvenKit.CLI.exe')
    args = parser.parse_args()
    original = ROOT / 'work/original'
    cli = str(args.cli.resolve())

    def run(*argv):
        subprocess.run([cli, *map(str, argv)], check=True)

    if not (original / SCENE).exists():
        run('unbundle', args.game / 'archive/pc/ep1/ep1_2_gamedata.archive', '-o', original, '-w', str(SCENE).replace('/', '\\'))
    actual = hashlib.sha256((original / SCENE).read_bytes()).hexdigest()
    if actual != SOURCE_SHA256:
        raise RuntimeError(f'Unsupported garage scene SHA256: {actual}')
    scene_json = original / (str(SCENE) + '.json')
    if not scene_json.exists():
        run('convert', 'serialize', original / SCENE)
    subtitle_path = Path('ep1/localization/en-us/subtitles/quest/q304/q304_05_garage.json')
    template_path = original / (str(subtitle_path) + '.json')
    if not template_path.exists():
        run('unbundle', args.game / 'archive/pc/ep1/lang_en_text.archive', '-o', original, '-w', '*q304_05_garage.json')
        run('convert', 'serialize', original / subtitle_path)
    doc, subtitles, report = patch(read(scene_json), read(ROOT / 'src/dialogue.json'))
    template = read(template_path)
    subdoc = resource(template, {'$type': 'localizationPersistenceSubtitleEntries', 'entries': subtitles})
    submap = resource(template, {'$type': 'localizationPersistenceSubtitleMap', 'entries': [{
        '$type': 'localizationPersistenceSubtitleMapEntry',
        'subtitleFile': {'DepotPath': {'$type': 'ResourcePath', '$storage': 'string', '$value': str(CUSTOM / 'subtitles.json').replace('/', '\\')}, 'Flags': 'Soft'},
        'subtitleGroup': {'$type': 'CName', '$storage': 'string', '$value': 'quest'}}]})
    raw = ROOT / 'work/build/raw'
    cooked = ROOT / 'work/build' / NAME
    for path, data in [(SCENE, doc), (CUSTOM / 'subtitles.json', subdoc), (CUSTOM / 'subtitles_map.json', submap)]:
        source = raw / (str(path) + '.json')
        write(source, data)
        output = cooked / path.parent
        output.mkdir(parents=True, exist_ok=True)
        run('convert', 'deserialize', source, '-o', output)
        target = cooked / path
        if not target.is_file() or target.read_bytes()[:4] != b'CR2W':
            raise RuntimeError(f'Missing or invalid compiled resource: {target}')
    dist = ROOT / 'dist'
    package = dist / 'package/archive/pc/mod'
    package.mkdir(parents=True, exist_ok=True)
    run('pack', cooked, '-o', package)
    archive = package / f'{NAME}.archive'
    if not archive.is_file():
        raise RuntimeError('WolvenKit produced no archive')
    (package / f'{NAME}.archive.xl').write_text('localization:\n  subtitles:\n    en-us:\n      - cassel_twins_survive\\localization\\en-us\\subtitles_map.json\n', encoding='utf-8')
    report['source_sha256'] = actual
    report['archive_sha256'] = hashlib.sha256(archive.read_bytes()).hexdigest()
    report['runtime_verified'] = False
    write(dist / 'build-report.json', report)
    with zipfile.ZipFile(dist / 'cassel-twins-survive-0.1.0-prototype.zip', 'w', zipfile.ZIP_DEFLATED) as bundle:
        for file in sorted((dist / 'package').rglob('*')):
            if file.is_file():
                bundle.write(file, file.relative_to(dist / 'package'))
    zip_path = dist / 'cassel-twins-survive-0.1.0-prototype.zip'
    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    write(dist / 'recipe.json', {
        'schemaVersion': 1, 'component': 'local/cassel-twins-survive',
        'version': '0.1.0-prototype', 'revision': '1', 'artifact': 'sha256:' + digest,
        'game': {'id': 'cyberpunk2077', 'version': '2.31', 'dlc': ['phantom-liberty']},
        'dependencies': {'ArchiveXL': {'source': {'type': 'nexus', 'game': 'cyberpunk2077', 'modId': 4198, 'fileId': 159683}}},
        'mappings': [{'from': 'archive', 'to': 'archive', 'class': 'mo2-overlay'}]})
    write(dist / 'modlist.json', {
        'schemaVersion': 1, 'name': 'Cassel Twins Survive - Prototype',
        'game': {'id': 'cyberpunk2077', 'version': '2.31', 'dlc': ['phantom-liberty']},
        'dependencies': {'Cassel Twins Survive': {'source': {'type': 'local-archive', 'path': './' + zip_path.name}, 'recipe': './recipe.json'}}})
    print(f'Built {archive}. Gameplay validation pending.')


if __name__ == '__main__':
    main()
