"""Prepare the repository manifest for the current, already built release ZIP."""
import hashlib

from build import ROOT, VERSION, read, write


def main():
    dist = ROOT / 'dist' / VERSION
    archive = dist / f'cassel-twins-survive-{VERSION}.zip'
    integrity = 'sha256:' + hashlib.sha256(archive.read_bytes()).hexdigest()
    package = read(ROOT / 'package.json')
    previous = package['mo2']
    if (any(s.get('tag') == 'v' + VERSION for s in previous.get('sources', []))
            and previous.get('integrity') != integrity):
        raise RuntimeError('This version already pins different release bytes. Bump package.json version and build a new release.')
    package['version'] = VERSION
    package['mo2']['sources'] = [{'type': 'github-release', 'repository': 'ubyjvovk/cassel-twins-survive',
                                'tag': 'v' + VERSION, 'asset': archive.name}]
    package['mo2']['integrity'] = integrity
    write(ROOT / 'package.json', package)
    print(f'Prepared package.json for v{VERSION}: {integrity}')


if __name__ == '__main__':
    main()
