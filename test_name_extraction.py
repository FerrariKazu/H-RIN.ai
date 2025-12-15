import json
import sys

data = json.load(sys.stdin)
print('Name:', data.get('resume', {}).get('name', 'NOT FOUND'))
print('Persons:', data.get('nlp', {}).get('entities', {}).get('persons', []))
print('Recommended roles count:', len(data.get('ml', {}).get('recommended_roles', [])))
if data.get('ml', {}).get('recommended_roles'):
    first_role = data['ml']['recommended_roles'][0]
    print('First role type:', type(first_role))
    print('First role:', first_role)
