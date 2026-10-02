"""Integration checks against locally extracted game resources (not bundled)."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from build import ROOT, SCENE, patch, read, validate
from inspect_scene import walk


class ScenePatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = ROOT / 'work/original' / (str(SCENE) + '.json')
        if not source.exists():
            raise unittest.SkipTest('Extract game resources with tools/build.py first')
        cls.original = read(source)
        cls.patched, cls.subtitles, cls.report = patch(cls.original, read(ROOT / 'src/dialogue.json'))
        cls.root = cls.patched['Data']['RootChunk']

    def test_preserves_quest_flow_and_original(self):
        pristine = read(ROOT / 'work/original' / (str(SCENE) + '.json'))
        self.assertEqual(self.original, pristine)
        for key in ('entryPoints', 'exitPoints', 'notablePoints', 'workspotInstances'):
            self.assertEqual(pristine['Data']['RootChunk'][key], self.root[key])
        # Every socket event survives; progression and the code-download branch
        # must still receive all their original timeline signals.
        def signals(doc):
            return [(o['id'], o['startTime'], o['osockStamp']) for o in walk(doc) if o.get('$type') == 'scneventsSocket']
        self.assertEqual(signals(pristine), signals(self.patched))

    def test_both_gender_sections_keep_tasers_remove_executions(self):
        for node in self.root['sceneGraph']['Data']['graph']:
            n = node['Data']
            if n['nodeId']['id'] not in (2393, 2935):
                continue
            animations = [o for o in walk(n) if o.get('$type') == 'scnPlaySkAnimEvent']
            synchronized = [o for o in animations if any('synced__killing_netrunners' in v.get('$value', '') for v in walk(o) if isinstance(v.get('$value'), str))]
            self.assertEqual(len(synchronized), 4)
            self.assertTrue(all(o['startTime'] < 10099 for o in synchronized))
            values = [o['$value'] for o in walk(n) if isinstance(o.get('$value'), str)]
            self.assertIn('netrunners_taser__idle__01', values)
            self.assertNotIn('blood_hit_big', values)
            self.assertFalse(any('shoot_netrunner' in v or 'headshot' in v for v in values))

    def test_changed_dialogue_has_new_ids_and_subtitles(self):
        old_ids = {l['locstringId']['ruid'] for l in self.original['Data']['RootChunk']['screenplayStore']['lines']}
        new_ids = {s['stringId'] for s in self.subtitles}
        self.assertFalse(old_ids & new_ids)
        dialogue = read(ROOT / 'src/dialogue.json')
        self.assertEqual(len(new_ids), len(dialogue['lines']) + len(dialogue['options']))
        self.assertTrue(any("come to their senses" in s['femaleVariant'] for s in self.subtitles))

    def test_choices_resolve_through_both_localization_routes(self):
        subtitle_text = {s['stringId']: s['femaleVariant'] for s in self.subtitles}
        old_options = {o['itemId']['id']: o['locstringId']['ruid'] for o in self.original['Data']['RootChunk']['screenplayStore']['options']}
        expected = read(ROOT / 'src/dialogue.json')['options']
        for option in self.root['screenplayStore']['options']:
            item = str(option['itemId']['id'])
            if item not in expected:
                continue
            loc_id = option['locstringId']['ruid']
            self.assertNotEqual(loc_id, old_options[int(item)])
            self.assertEqual(subtitle_text[loc_id], expected[item])
            descriptors = [d for d in self.root['locStore']['vdEntries'] if d['locstringId']['ruid'] == loc_id and d['localeId'] == 'en_us']
            self.assertTrue(descriptors)
            for d in descriptors:
                p = self.root['locStore']['vpEntries'][d['vpeIndex']]
                self.assertEqual(p['variantId'], d['variantId'])
                self.assertEqual(p['content'], expected[item])

    def test_reassurance_is_on_both_response_paths(self):
        lines = {l['itemId']['id']: l for l in self.root['screenplayStore']['lines']}
        subtitle_text = {s['stringId']: s['femaleVariant'] for s in self.subtitles}
        for item in (1281, 1793):
            self.assertIn('come to their senses', subtitle_text[lines[item]['locstringId']['ruid']])
        node = next(n['Data'] for n in self.root['sceneGraph']['Data']['graph'] if n['Data']['nodeId']['id'] == 520)
        self.assertGreaterEqual(node['sectionDuration']['stu'], 6000)

    def test_rejects_dangling_handle(self):
        bad = copy.deepcopy(self.patched)
        bad['bad'] = {'HandleRefId': 'missing'}
        with self.assertRaisesRegex(AssertionError, 'Dangling'):
            validate(bad)

    def test_blood_appearance_operations_are_empty(self):
        names = [o['appearanceName']['$value'] for o in walk(self.root) if 'appearanceName' in o and isinstance(o['appearanceName'], dict)]
        self.assertNotIn('theo__q304__kidnap_blood', names)
        self.assertNotIn('bella__q304__kidnap_blood', names)


if __name__ == '__main__':
    unittest.main()
