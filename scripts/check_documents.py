"""Validate requirement IDs, local links, exported artifacts and measured evidence."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT/'docs'


def main():
    sources = [DOCS/'requirements/Vehicle_Parking_System_SRS.md',
               DOCS/'SAD/Vehicle_Parking_System_SAD.md',
               DOCS/'testing/Vehicle_Parking_System_Test_Plan.md']
    for path in sources:
        for suffix in ['.docx', '.pdf']:
            assert path.with_suffix(suffix).stat().st_size > 10000, path
    srs = sources[0].read_text(encoding='utf-8')
    assert set(re.findall(r'^#### (FR-\d+)$', srs, re.M)) == {f'FR-{n:02d}' for n in range(1, 31)}
    assert len(re.findall(r'^SO-\d+', srs, re.M)) >= 2
    assert srs.count('Release acceptance:') == 30
    plan = sources[2].read_text(encoding='utf-8')
    assert '### 5.1 Security Validation' in plan
    catalogue = (DOCS/'testing/TEST_CASES.md').read_text(encoding='utf-8')
    cases = set(re.findall(r'^## (TC-[A-Z]+-\d+)$', catalogue, re.M))
    assert len(cases) >= 10
    rtm = (DOCS/'requirements/traceability_matrix.md').read_text(encoding='utf-8')
    assert set(re.findall(r'TC-[A-Z]+-\d+', rtm)) <= cases
    current = sources + [ROOT/'README.md', ROOT/'frontend/README.md', DOCS/'README.md',
                         DOCS/'requirements/traceability_matrix.md', DOCS/'testing/FINAL_VERIFICATION_REPORT.md',
                         DOCS/'meeting-notes/DELIVERY_REGISTER.md']
    for path in current:
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            if '://' not in target and not target.startswith('#'):
                assert (path.parent/target.split('#')[0]).resolve().exists(), (path, target)
    for path in (DOCS/'diagrams').glob('*.puml'):
        for suffix in ['.svg', '.png']:
            assert path.with_suffix(suffix).stat().st_size > 1000, path
        assert 'Syntax Error' not in path.with_suffix('.svg').read_text(encoding='utf-8')
    assert sum('autonumber' in p.read_text(encoding='utf-8') for p in (DOCS/'diagrams').glob('*.puml')) >= 2
    performance = json.loads((DOCS/'testing/reports/performance.json').read_text(encoding='utf-8'))
    assert performance['all_measured_targets_passed']
    regression = json.loads((DOCS/'testing/reports/regression.json').read_text(encoding='utf-8'))
    assert regression['backend']['executed'] == len(regression['backend']['cases'])
    assert regression['backend']['failed'] == regression['backend']['skipped'] == 0
    print(f'Validated 30 FRs, {len(cases)} canonical test families, local links, document exports and measured evidence.')


if __name__ == '__main__':
    main()
