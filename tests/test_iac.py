import copy
import unittest
from deploy.genie_space import canonical, digest, render, make_plan, check_plan

BASE = {'version': 2, 'instructions': {'text_instructions': [{'id': 'a'*32, 'content': ['base']}]}, 'benchmarks': {'questions': []}}
ENV = {'title': 'Clase', 'warehouse_id': 'wh', 'description': 'Práctica'}

class IaCTests(unittest.TestCase):
    def test_v0_preserves_configuration(self):
        self.assertEqual(render(BASE, 'base', ENV)['serialized_space'], BASE)

    def test_complete_prompt_replaces_content_preserving_benchmark_and_id(self):
        result = render(BASE, '\nV1', ENV)['serialized_space']
        self.assertEqual(result['benchmarks'], BASE['benchmarks'])
        self.assertEqual(result['instructions']['text_instructions'], [{'id':'a'*32,'content':['\nV1']}])
        self.assertEqual(BASE['instructions']['text_instructions'][0]['content'], ['base'])

    def test_api_content_normalization(self):
        other = copy.deepcopy(BASE)
        other['instructions']['text_instructions'][0]['content'] = ['ba', 'se']
        self.assertEqual(digest(canonical(BASE)), digest(canonical(other)))

    def test_multiple_instruction_containers_rejected(self):
        other = copy.deepcopy(BASE)
        other['instructions']['text_instructions'] *= 2
        with self.assertRaises(ValueError): render(other, 'change', ENV)

    def test_idempotent_plan(self):
        target = render(BASE, '', ENV)
        self.assertFalse(make_plan(target, target, 'id', 'https://dbx')['changed'])

    def test_drift_rejects_plan(self):
        old = render(BASE, '', ENV)
        plan = make_plan(old, render(BASE, 'V1', ENV), 'id', 'https://dbx')
        with self.assertRaises(ValueError): check_plan(plan, render(BASE, 'UI edit', ENV), 'https://dbx')

    def test_wrong_workspace_rejected(self):
        old = render(BASE, '', ENV)
        with self.assertRaises(ValueError): check_plan(make_plan(old, old, 'id', 'https://dbx'), old, 'https://other')

    def test_tampered_desired_rejected(self):
        old = render(BASE, '', ENV)
        p = make_plan(old, old, 'id', 'https://dbx')
        p['desired']['title'] = 'tampered'
        with self.assertRaises(ValueError): check_plan(p, old, 'https://dbx')
