from backend.state import init_state, get_merged_catalog
import os
os.environ['PRISM_DATA_ROOT'] = '/Users/zhanghong/Documents/Research/Slitless_spectroscopy/sapphires_data'

init_state()
catalog = get_merged_catalog()
for r in catalog:
    if str(r['ID']) == '420':
        print('Source 420:')
        print('  Columns:', r.colnames)
        for c in r.colnames:
            if 'RA' in c or 'DEC' in c:
                print(f'  {c}: {r[c]}')
        break
