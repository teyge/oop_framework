import sys
import os
# ensure repo root on path when running from tests/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from leveleditor import LevelEditor
import json
le = LevelEditor(start_w=3,start_h=3)
# toggle Hindernis privacy
le.privacy_flags['Hindernis'] = True
j = le.to_json()
print('Hindernis in to_json settings:', 'Hindernis' in j.get('settings', {}))
print('settings[Hindernis]:', j.get('settings', {}).get('Hindernis'))
# Now simulate loading
s = json.dumps(j)
le2 = LevelEditor(start_w=2,start_h=2)
le2.from_json(json.loads(s))
print('le2.privacy_flags[Hindernis]:', le2.privacy_flags.get('Hindernis'))
