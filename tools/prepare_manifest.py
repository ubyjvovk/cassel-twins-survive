"""Prepare the repository manifest for the current, already built release ZIP."""
import hashlib

from build import ROOT, VERSION, read, write


def main():
    dist = ROOT / 'dist' / VERSION
    archive = dist / f'cassel-twins-survive-{VERSION}.zip'
    recipe = read(dist / 'recipe.json')
    integrity = 'sha256:' + hashlib.sha256(archive.read_bytes()).hexdigest()
    if recipe['artifact'] != integrity:
        raise RuntimeError('Built ZIP no longer matches its recipe')
    manifest = read(dist / 'modlist.json')
    manifest['dependencies']['Cassel Twins Survive'] = {
        'source': {'type': 'github-release', 'repository': 'ubyjvovk/cassel-twins-survive',
                   'tag': 'v' + VERSION, 'asset': archive.name},
        'recipe': './recipes/cassel-twins-survive.json',
        'integrity': integrity,
    }
    write(ROOT / 'modlist.json', manifest)
    write(ROOT / 'recipes/cassel-twins-survive.json', recipe)
    print(f'Prepared manifest for v{VERSION}: {integrity}')


if __name__ == '__main__':
    main()
