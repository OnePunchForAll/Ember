"""Build an explicit, deterministic Ember source package; never publish it."""
from __future__ import annotations
import argparse
import ast
from fractions import Fraction
import hashlib
import io
import json
from math import gcd
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
import time
import zipfile

RUNTIME = ('ember.py', 'algebra.py', 'algebra_check.py', 'word_series.py',
           'word_check.py', 'campaign.py', 'recurrence.py', 'recurrence_check.py',
           'invariant.py', 'invariant_check.py', 'invariant_map.py', 'obligations.py',
           'recursive.py', 'recursive_check.py', 'source_episode.py', 'apex.py', 'apex_check.py',
           'pyramid.py', 'lexicon.py', 'lexicon_check.py', 'movebench.py', 'agent.py', 'ops_seq.py', 'ops_poly.py',
           'ops_orbit.py', 'ops_egypt.py', 'ops_arith.py', 'ops_word.py', 'ops_matrix.py', 'ops_collatz.py')
EXAMPLES = ('discover_word_boundary.json', 'graph_count.json',
            'polynomial_consequence.json', 'discover_algebra_guards.json',
            'discover_affine_guards.json', 'word_identity.json', 'word_shortcut.json',
            'rational_repair.json', 'campaign_research.json',
            'lemma_source.json', 'lemma_receiving.json', 'discover_recurrence.json',
            'hidden_mode_recurrence.json', 'discover_word_recurrence.json', 'campaign_discovery.json',
            'discover_invariant.json', 'invariant_cancellation.json', 'campaign_invariant.json',
            'nonlinear_invariant.json', 'invariant_reuse_source.json',
            'invariant_reuse_receiving.json', 'campaign_reuse_reentry.json',
            'obligation_source.json', 'obligation_receiving.json',
            'localized_consequence.json', 'localized_cancellation.json', 'campaign_localization.json',
            'guarded_receiving.json', 'campaign_guarded_transfer.json',
            'recursive_reverse_involution.json', 'recursive_qrev.json',
            'recursive_wrong_order.json', 'recursive_add_right_zero.json',
            'campaign_recursive_identity.json', 'source_research_episode.json',
            'orbit_exclusion.json', 'hidden_rank_count.json', 'apex_research.json',
            'word_count.json', 'generating_function.json', 'minimal_recurrence.json', 'orbit_drift.json',
            'orbit_ranking.json', 'eventual_recurrence.json',
            'recursive_lift.json', 'premise_lift_source.json', 'premise_lift_receiving.json',
            'agent_erdos_straus.json', 'agent_unit_fraction_small.json', 'agent_collatz.json', 'agent_decide.json',
            'agent_explore.json', 'agent_choose_lift.json')
FIXED_TIME = (2026, 1, 1, 0, 0, 0)
PRIVATE_PATH = re.compile(rb'(?<![A-Za-z0-9_])[A-Za-z]:[\\/]|/(?:home|Users)/')


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + '\n').encode('utf-8')


def sha(value):
    return hashlib.sha256(value).hexdigest()


def public_credits(raw):
    """Idempotent documentation projection; keep contribution attributions."""
    text = raw.decode('utf-8').replace('\r\n', '\n')
    paragraphs = []
    for paragraph in text.split('\n\n'):
        plain = ' '.join(paragraph.split())
        if plain.startswith('The recovered original TPM message'):
            continue
        paragraph = re.sub(r'Their static\s+source addresses appear in\s+research/NEXT_INTEGRATION_CONTRACT\.md\.\s*',
                           '', paragraph)
        paragraph = re.sub(r', with primary\s+references and its locally derived certificate argument in research/EXTENSION_CONTRACT\.md',
                           '', paragraph)
        paragraph = re.sub(r'Source hashes and reviewed ranges are\s+kept privately in research/discovery_source_pins\.json; the derived argument and\s+primary mathematical background are in research/RECURRENCE_CONTRACT\.md\.\s*',
                           '', paragraph)
        paragraph = re.sub(r'Source attribution and retained corrections are\s+documented privately in research/LOCALIZATION_RESULTS\.md\.\s*',
                           '', paragraph)
        if plain.startswith('The current runtime was authored here'):
            paragraph = ('The current runtime was authored here; it does not import donor programs\n'
                         'or copy their private runtimes. Newly authored code and public documentation\n'
                         'in this package use the MIT License. Adapted recursive example definitions\n'
                         'retain their original MIT attribution in THIRD_PARTY_NOTICES.md. Donor\n'
                         'archives and runtimes are not included. No public hosting\n'
                         'or repository publication is implied by the local package.')
        if paragraph.strip():
            paragraphs.append(paragraph.strip())
    result = ('\n\n'.join(paragraphs) + '\n').encode('utf-8')
    if b'research/' in result:
        raise ValueError('public credits still refer to omitted private research; review projection')
    return result


def collect(root):
    paths = {name: name for name in RUNTIME}
    paths.update({'examples/' + name: 'examples/' + name for name in EXAMPLES})
    paths.update({'LICENSE': 'LICENSE', 'THIRD_PARTY_NOTICES.md': 'THIRD_PARTY_NOTICES.md',
                  'tools/build_public_package.py': 'tools/build_public_package.py',
                  'tools/helper_client.py': 'tools/helper_client.py', 'tools/verdict.py': 'tools/verdict.py',
                  'CAMPAIGNS.md': 'CAMPAIGNS.md'})
    files = {name: (root / source).read_bytes() for name, source in paths.items()}
    readme = root / 'PUBLIC_README.md'
    files['README.md'] = (readme if readme.is_file() else root / 'README.md').read_bytes()
    files['CREDITS.md'] = public_credits((root / 'CREDITS.md').read_bytes())
    for name, raw in files.items():
        if PRIVATE_PATH.search(raw):
            raise ValueError('private absolute filesystem path in public payload: ' + name)
        if name.endswith('.py'):
            ast.parse(raw, filename=name)
    module = ast.parse(files['ember.py'])
    version = next(ast.literal_eval(node.value) for node in module.body
                   if isinstance(node, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == 'VERSION' for t in node.targets))
    manifest = {
        'schema': 'ember.public_source_manifest.v1',
        'version': version,
        'task_api': 'ember.task.v1',
        'license': 'MIT',
        'license_scope': 'Newly authored Ember code and public documentation; adapted MIT example data attributed in THIRD_PARTY_NOTICES.md; donor archives and runtimes excluded.',
        'standing': 'EXPERIMENTAL / SELF_ISOLATED',
        'runtime_source_bytes': sum(len(files[n]) for n in RUNTIME),
        'python_requirement': ('External standard-library Python. Generations through ember-pyramid-15 were tested '
                               'with Python 3.14.6 on Windows; ember-pyramid-16 and -17 were verified with Python 3.11.15 '
                               'on Linux x86_64 only.'),
        'packaging': 'Explicit allowlist; fixed ZIP member metadata and order; no source corpus or instance state.',
        'manifest_self_hash': 'Omitted to avoid circular hashing. The archive hash belongs in a separate receipt.',
        'files': [{'path': n, 'bytes': len(files[n]), 'sha256': sha(files[n])} for n in sorted(files)],
    }
    files['PUBLIC_MANIFEST.json'] = encoded(manifest)
    return files, manifest


def archive_bytes(files):
    output = io.BytesIO()
    # Stored members make archive bytes independent of zlib version.
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_STORED) as zf:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_STORED
            zf.writestr(info, files[name])
    return output.getvalue()


def verify(payload, files, manifest, python, receipt):
    receipt.update({'schema': 'ember.package_verification.v1',
               'version': manifest['version'], 'zip_sha256': sha(payload),
               'zip_bytes': len(payload), 'runtime_source_bytes': manifest['runtime_source_bytes'],
               'python': sys.version, 'platform': platform.platform(),
               'checks': [], 'cli_runs': [], 'limits': [
                   'Same interpreter and host; no second operating system was tested.',
                   'Relocation and Python audit-hook checks are not operating-system isolation.',
                   'No repository, remote or hosted release was created.',
                   'Certificate correctness is covered separately by the component suites.']})
    def check(name, condition):
        receipt['checks'].append({'case': name, 'ok': bool(condition)})
        if not condition:
            raise AssertionError(name)
    check('deterministic_repeated_zip', payload == archive_bytes(files))
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        check('explicit_member_allowlist', zf.namelist() == sorted(files))
        check('member_crc', zf.testzip() is None)
        check('member_bytes_and_metadata', all(zf.read(n) == b and zf.getinfo(n).date_time == FIXED_TIME
                                             for n, b in files.items()))
        listed = {item['path']: item for item in manifest['files']}
        check('manifest_covers_payload_without_self', set(listed) == set(files) - {'PUBLIC_MANIFEST.json'})
        check('manifest_hashes_and_sizes', all(sha(files[n]) == item['sha256'] and len(files[n]) == item['bytes']
                                               for n, item in listed.items()))
    with tempfile.TemporaryDirectory(prefix='ember-package-') as temporary:
        root = Path(temporary) / 'relocated'
        root.mkdir()
        for name, raw in files.items():
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        def cli(label, example, extra=(), expected_code=0):
            args = [python, '-I', '-B', '-X', 'utf8', str(root / 'ember.py'), example, *extra]
            started = time.perf_counter_ns()
            result = subprocess.run(args, cwd=root, capture_output=True, text=True, encoding='utf-8',
                                    timeout=90, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            output = json.loads(result.stdout)
            receipt['cli_runs'].append({'case': label, 'returncode': result.returncode,
                                       'status': output.get('status'), 'elapsed_ns': time.perf_counter_ns() - started,
                                       'stderr': result.stderr})
            check(label + '_exit', result.returncode in expected_code if type(expected_code) is tuple
                  else result.returncode == expected_code)
            check(label + '_stderr', not result.stderr)
            return output
        capabilities = cli('capabilities', '--capabilities')
        check('capabilities_version_and_queries', capabilities.get('api_version') == manifest['task_api']
              and capabilities.get('runtime_version') == manifest['version']
              and 'research_campaign' in capabilities.get('queries', []))
        check('capabilities_proof_policies', capabilities.get('polynomial_proof_policies')
              == ['auto', 'direct', 'lemma_first', 'target_sparse', 'cancellation_sparse', 'obligations', 'localized_first'])
        check('capabilities_recurrence_queries',
              {'discover_recurrence', 'discover_word_recurrence'} <= set(capabilities.get('queries', [])))
        check('capabilities_invariant_interface', 'discover_invariant' in capabilities.get('queries', [])
              and capabilities.get('invariant_policies') == ['full', 'mapped', 'reuse_first'])
        check('capabilities_recursive_interface', 'prove_recursive_identity' in capabilities.get('queries', [])
              and capabilities.get('recursive_identity_policies') == ['direct', 'enumerate', 'residual']
              and capabilities.get('recursive_identity_certificate_kinds') == ['recursive_identity', 'recursive_counterexample'])
        check('capabilities_source_episode_interface', 'source_research_episode' in capabilities.get('queries', [])
              and capabilities.get('source_episode_policies') == ['native_isolated', 'graph_isolated', 'fixed_bridge', 'gap_bridge']
              and capabilities.get('source_episode_formats') == ['pie-problem-v1', 'ember.recursive_claim.v1'])
        check('capabilities_source_episode_bounds', all(capabilities.get('limits', {}).get(key) == value
              for key, value in {'source_records': 8, 'source_record_bytes': 65536, 'source_total_bytes': 524288,
                                 'source_distinct_roots': 4, 'source_seed_entries': 8, 'source_steps_per_call': 64}.items()))
        check('adapted_recursive_data_has_original_notice', b'Proof Invention Engine contributors' in files['THIRD_PARTY_NOTICES.md']
              and b'Permission is hereby granted' in files['THIRD_PARTY_NOTICES.md'])
        recursive_task = json.loads((root / 'examples/recursive_add_right_zero.json').read_bytes())
        for example in ('recursive_add_right_zero.json', 'recursive_reverse_involution.json',
                        'recursive_qrev.json', 'recursive_wrong_order.json'):
            original = json.loads((root / 'examples' / example).read_bytes())
            check('recursive_task_only_' + example,
                  set(original) == {'query', 'domain', 'definitions', 'goal'}
                  and len(original['definitions']) == 9)
        recursive = cli('recursive_direct_original', 'examples/recursive_add_right_zero.json',
                        ['--state', 'recursive-direct.json', '--recursive-policy', 'direct'])
        check('recursive_original_induction_admitted', recursive['status'] == 'CHECKED_RECURSIVE_IDENTITY'
              and recursive['certificate']['kind'] == 'recursive_identity'
              and recursive['certificate']['proof']['rule'] == 'induction'
              and recursive['check']['ok'] is True)
        saved_recursive = (root / 'recursive-direct.json').read_bytes()
        recursive_replay = cli('recursive_final_restart', 'examples/recursive_add_right_zero.json',
                              ['--state', 'recursive-direct.json'])
        check('recursive_final_certificate_freshly_replayed', recursive_replay['status'] == 'CHECKED_RECURSIVE_IDENTITY'
              and recursive_replay.get('reused_after_fresh_check') is True
              and recursive_replay['certificate'] == recursive['certificate'])
        before_zero = (root / 'recursive-direct.json').read_bytes()
        unknown = cli('recursive_zero_work_saved_proof', 'examples/recursive_add_right_zero.json',
                      ['--state', 'recursive-direct.json', '--work', '0'], expected_code=3)
        check('recursive_zero_work_preserves_unreplayed_evidence', unknown['status'] == 'UNKNOWN'
              and not unknown.get('reused_after_fresh_check')
              and (root / 'recursive-direct.json').read_bytes() == before_zero)
        forged_recursive = json.loads(saved_recursive)
        stored = next(row for row in forged_recursive['observations']
                      if row.get('task_id') == recursive['task_id'] and 'certificate' in row)
        stored['certificate']['proof'] = {'rule': 'join', 'left': [], 'right': []}
        (root / 'recursive-forged.json').write_bytes(encoded(forged_recursive))
        repaired = cli('recursive_forged_final_cache', 'examples/recursive_add_right_zero.json',
                       ['--state', 'recursive-forged.json', '--recursive-policy', 'direct'])
        check('recursive_forged_evidence_not_admitted', repaired['status'] == 'CHECKED_RECURSIVE_IDENTITY'
              and not repaired.get('reused_after_fresh_check')
              and repaired['certificate']['proof'] != stored['certificate']['proof'])
        altered = dict(recursive_task, name='unsupported recursive task metadata')
        (root / 'recursive-extra-field.json').write_bytes(encoded(altered))
        refused = cli('recursive_extra_task_field', 'recursive-extra-field.json', expected_code=2)
        check('recursive_task_schema_is_exact', refused['status'] == 'REFUSED')
        bad_steps = cli('recursive_invalid_steps', 'examples/recursive_add_right_zero.json',
                        ['--recursive-steps', '0'], expected_code=2)
        check('recursive_stage_bound_refused', bad_steps['status'] == 'REFUSED')
        false_identity = cli('recursive_original_counterexample', 'examples/recursive_wrong_order.json',
                             ['--state', 'recursive-false.json'])
        check('recursive_original_false_goal_refuted', false_identity['status'] == 'CHECKED_RECURSIVE_COUNTEREXAMPLE'
              and false_identity['certificate']['kind'] == 'recursive_counterexample'
              and false_identity['check']['left_value'] != false_identity['check']['right_value'])
        for label, example, state_name, wanted, replayed in (
                ('recursive_helper_fresh', 'recursive_add_right_zero.json', 'recursive-helper.json', 'CHECKED_RECURSIVE_IDENTITY', False),
                ('recursive_helper_restart', 'recursive_add_right_zero.json', 'recursive-helper.json', 'CHECKED_RECURSIVE_IDENTITY', True),
                ('recursive_helper_counterexample_restart', 'recursive_wrong_order.json', 'recursive-false.json', 'CHECKED_RECURSIVE_COUNTEREXAMPLE', True)):
            began = time.perf_counter_ns()
            process = subprocess.run([python, '-I', '-B', '-X', 'utf8', str(root / 'tools/helper_client.py'),
                'examples/' + example, '--state', state_name, '--recursive-policy', 'direct'],
                cwd=root, capture_output=True, text=True, encoding='utf-8', timeout=90,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            envelope = json.loads(process.stdout)
            receipt['cli_runs'].append({'case': label, 'returncode': process.returncode,
                'status': envelope.get('status'), 'elapsed_ns': time.perf_counter_ns() - began,
                'stderr': process.stderr})
            check(label, process.returncode == 0 and not process.stderr
                  and envelope.get('outcome') == 'closed' and envelope.get('status') == wanted
                  and bool(envelope['result'].get('reused_after_fresh_check')) == replayed)
        direct_campaign = {'query': 'research_campaign', 'problems': [recursive_task],
                           'max_attempts': 1, 'attempt_work': 1_000_000, 'policy': 'fixed'}
        (root / 'recursive-direct-campaign.json').write_bytes(encoded(direct_campaign))
        campaign_result = cli('recursive_direct_campaign', 'recursive-direct-campaign.json',
                              ['--state', 'recursive-campaign-direct.json'])
        check('recursive_campaign_classifies_original_proof', campaign_result['status'] == 'CHECKED_CAMPAIGN'
              and campaign_result['executed_routes'] == ['recursive_direct']
              and campaign_result['problems'][0]['attempts'][0]['result']['status'] == 'CHECKED_RECURSIVE_IDENTITY')
        campaign_replay = cli('recursive_direct_campaign_restart', 'recursive-direct-campaign.json',
                             ['--state', 'recursive-campaign-direct.json'])
        check('recursive_campaign_rechecks_original', campaign_replay['status'] == 'CHECKED_CAMPAIGN'
              and campaign_replay['executed_routes'] == [])
        research_args = ['--state', 'recursive-research.json', '--recursive-steps', '1']
        blocked = cli('recursive_original_root_first_stage', 'examples/recursive_reverse_involution.json',
                      research_args, expected_code=3)
        first_episode_state = (root / 'recursive-research.json').read_bytes()
        first_episode = next(row for row in json.loads(first_episode_state)['observations']
                             if row.get('kind') == 'recursive_episode')
        check('recursive_actual_failed_original_edge_persisted', blocked['status'] == 'UNKNOWN'
              and blocked['recursive']['library_count'] == 0
              and any(node.get('status') == 'BLOCKED' and node.get('residual')
                      for node in first_episode['nodes'].values()))
        resumed = cli('recursive_original_root_second_process', 'examples/recursive_reverse_involution.json',
                      research_args, expected_code=3)
        check('recursive_original_research_restarts_with_proposals', resumed['status'] == 'UNKNOWN'
              and resumed['recursive']['episode_id'] == blocked['recursive']['episode_id']
              and resumed['recursive']['totals']['candidates'] > blocked['recursive']['totals']['candidates']
              and (root / 'recursive-research.json').read_bytes() != first_episode_state)
        completed = cli('recursive_original_root_invented_proof', 'examples/recursive_reverse_involution.json',
                        ['--state', 'recursive-research.json', '--recursive-steps', '64'])
        check('recursive_original_closed_after_checked_invention', completed['status'] == 'CHECKED_RECURSIVE_IDENTITY'
              and len(completed['certificate']['lemmas']) > 0
              and completed['recursive']['totals']['commits'] > 0
              and completed['recursive']['totals']['parent_reentries'] > 0)
        replay = cli('recursive_original_standalone_final_replay', 'examples/recursive_reverse_involution.json',
                     ['--state', 'recursive-research.json'])
        check('recursive_invented_bundle_freshly_replayed', replay['status'] == 'CHECKED_RECURSIVE_IDENTITY'
              and replay.get('reused_after_fresh_check') is True
              and replay['certificate'] == completed['certificate'])
        qrev = cli('recursive_original_qrev_search', 'examples/recursive_qrev.json',
                   ['--state', 'recursive-qrev.json', '--recursive-steps', '64'], expected_code=(0, 3))
        check('recursive_qrev_preserves_observed_outcome', qrev['status'] in ('CHECKED_RECURSIVE_IDENTITY', 'UNKNOWN'))
        receipt['recursive_source_outcomes'] = {
            'reverse_involution': completed['status'], 'qrev': qrev['status'],
            'reverse_lemma_count': len(completed['certificate']['lemmas']),
            'qrev_reason': qrev.get('reason'), 'qrev_progress': qrev.get('recursive')}
        for index in range(16):
            research_campaign = cli('recursive_source_campaign_' + str(index), 'examples/campaign_recursive_identity.json',
                                    ['--state', 'recursive-campaign-research.json'], expected_code=(0, 3))
            check('recursive_source_campaign_status_' + str(index),
                  research_campaign['status'] in ('UNKNOWN', 'CHECKED_CAMPAIGN'))
            if research_campaign['status'] == 'CHECKED_CAMPAIGN':
                break
        check('recursive_source_campaign_completes_checked_original', research_campaign['status'] == 'CHECKED_CAMPAIGN'
              and any(row['result']['status'] == 'CHECKED_RECURSIVE_IDENTITY'
                      and row['result']['certificate']['lemmas']
                      for row in research_campaign['problems'][0]['attempts']))
        replay = cli('recursive_source_campaign_replay', 'examples/campaign_recursive_identity.json',
                     ['--state', 'recursive-campaign-research.json'])
        check('recursive_source_campaign_admission_replayed', replay['status'] == 'CHECKED_CAMPAIGN'
              and replay['executed_routes'] == [])
        # The public source example is built from public task data only. No private
        # bank, source path, supplied proof or controller state is a package input.
        source_task = json.loads((root / 'examples/source_research_episode.json').read_bytes())
        check('source_public_outer_fields', set(source_task) == {'query', 'sources'}
              and source_task['query'] == 'source_research_episode'
              and [s['id'] for s in source_task['sources']] == ['reverse', 'qrev'])
        original_sources = {}
        for source, example in zip(source_task['sources'], ('recursive_reverse_involution.json', 'recursive_qrev.json')):
            check('source_public_record_fields_' + source['id'], set(source) == {'id', 'sha256', 'utf8'}
                  and sha(source['utf8'].encode('utf-8')) == source['sha256'])
            capsule = json.loads(source['utf8'])
            original = json.loads((root / 'examples' / example).read_bytes())
            check('source_public_owned_capsule_' + source['id'], set(capsule) == {'format', 'task', 'claim'}
                  and capsule['format'] == 'ember.recursive_claim.v1' and capsule['claim'] == 'question'
                  and capsule['task'] == original and len(original['definitions']) == 9)
            identity = sha(json.dumps(original, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())
            original_sources[identity] = original
        first_source = cli('source_first_checked_question', 'examples/source_research_episode.json',
            ['--state', 'source-pair.json', '--source-policy', 'fixed_bridge', '--source-steps', '1', '--work', '4000000'], expected_code=3)
        check('source_first_stage_keeps_original_obligations', first_source['status'] == 'UNKNOWN'
              and len(first_source['roots']) == 2
              and sum(row.get('result') is not None for row in first_source['roots']) == 1
              and all(row['task'] == original_sources[row['task_id']] for row in first_source['roots']))
        first_source_state = (root / 'source-pair.json').read_bytes()
        zero_source = cli('source_zero_work_preserved', 'examples/source_research_episode.json',
            ['--state', 'source-pair.json', '--source-policy', 'fixed_bridge', '--work', '0'], expected_code=3)
        check('source_zero_work_does_not_admit_stored_flags', zero_source['status'] == 'UNKNOWN'
              and (root / 'source-pair.json').read_bytes() == first_source_state)
        remaining_source_work = 4000000 - first_source['work'] - zero_source['work']
        check('source_resume_keeps_real_remaining_allowance', remaining_source_work > 0)

        def source_helper(label, extra, expected_code, expected_status, expected_outcome):
            began = time.perf_counter_ns()
            process = subprocess.run([python, '-I', '-B', '-X', 'utf8', str(root / 'tools/helper_client.py'),
                'examples/source_research_episode.json', *extra], cwd=root, capture_output=True, text=True,
                encoding='utf-8', timeout=90, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            envelope = json.loads(process.stdout)
            receipt['cli_runs'].append({'case': label, 'returncode': process.returncode,
                'status': envelope.get('status'), 'elapsed_ns': time.perf_counter_ns() - began, 'stderr': process.stderr})
            check(label, process.returncode == expected_code and not process.stderr
                  and envelope.get('status') == expected_status and envelope.get('outcome') == expected_outcome)
            return envelope

        source_finished = source_helper('source_helper_actual_restart',
            ['--state', 'source-pair.json', '--source-policy', 'fixed_bridge', '--source-steps', '64',
             '--work', str(remaining_source_work)], 0, 'CHECKED_SOURCE_EPISODE', 'closed')['result']
        check('source_restart_checked_both_unchanged_originals', len(source_finished['roots']) == 2
              and all(row['task'] == original_sources[row['task_id']]
                      and row['result']['status'] == 'CHECKED_RECURSIVE_IDENTITY'
                      and row['result']['certificate']['task_id'] == row['task_id'] for row in source_finished['roots'])
              and [row['source_id'] for row in source_finished['sources']] == ['reverse', 'qrev']
              and all(row['assessment'] == 'ANSWERED' for row in source_finished['sources']))
        check('source_restart_installs_checked_seed_prefix', bool(source_finished['source_episode']['bridges'])
              and any(attempt['seed_count'] > 0 for attempt in source_finished['source_episode']['attempts']))
        def source_references(proof):
            if proof['rule'] == 'induction':
                result = set()
                for case in proof['cases'].values():
                    result.update(source_references(case['proof']))
                return result
            return {step['source']['index'] for step in proof['left'] + proof['right']
                    if step['source']['kind'] == 'lemma'}

        used_seed = False
        for row in source_finished['roots']:
            prefix_count = max((attempt['seed_count'] for attempt in source_finished['source_episode']['attempts']
                                if attempt['root_id'] == row['task_id']), default=0)
            certificate = row['result']['certificate']
            used = source_references(certificate['proof']); pending = list(used)
            while pending:
                for index in source_references(certificate['lemmas'][pending.pop()]['proof']):
                    if index not in used:
                        used.add(index); pending.append(index)
            used_seed = used_seed or bool(used & set(range(prefix_count)))
        check('source_final_original_proof_actually_uses_a_checked_seed', used_seed)
        for label, result in (('first', first_source), ('zero', zero_source), ('resumed', source_finished)):
            check('source_disjoint_work_accounting_' + label,
                  result['work_accounts']['common'] + sum(result['work_accounts']['roots'].values()) == result['work'])
        source_replayed = cli('source_fresh_closed_episode_replay', 'examples/source_research_episode.json',
            ['--state', 'source-pair.json', '--source-policy', 'fixed_bridge', '--source-steps', '64'])
        check('source_closed_restart_checks_originals_without_new_actions', source_replayed['status'] == 'CHECKED_SOURCE_EPISODE'
              and source_replayed['source_episode']['actions'] == source_finished['source_episode']['actions']
              and not source_replayed['source_episode']['executed']
              and [r['result']['certificate'] for r in source_replayed['roots']]
                  == [r['result']['certificate'] for r in source_finished['roots']])
        current_source_state = (root / 'source-pair.json').read_bytes()
        source_helper('source_helper_zero_budget_status',
            ['--state', 'source-pair.json', '--source-policy', 'fixed_bridge', '--work', '0'], 3, 'UNKNOWN', 'unknown')
        check('source_helper_zero_preserves_checkpoint', (root / 'source-pair.json').read_bytes() == current_source_state)
        bad_source = json.loads(json.dumps(source_task))
        bad_source['sources'][0]['utf8'] += ' '
        (root / 'source-bad-hash.json').write_bytes(encoded(bad_source))
        refused_source = cli('source_literal_hash_refusal', 'source-bad-hash.json',
            ['--state', 'source-pair.json', '--source-policy', 'fixed_bridge'], expected_code=2)
        check('source_changed_literal_refused_without_state_damage', refused_source['status'] == 'REFUSED'
              and (root / 'source-pair.json').read_bytes() == current_source_state)
        bad_source = json.loads(json.dumps(source_task))
        capsule = json.loads(bad_source['sources'][0]['utf8']); capsule['proof'] = {'claimed': True}
        bad_source['sources'][0]['utf8'] = json.dumps(capsule, sort_keys=True, separators=(',', ':'))
        bad_source['sources'][0]['sha256'] = sha(bad_source['sources'][0]['utf8'].encode())
        (root / 'source-supplied-proof.json').write_bytes(encoded(bad_source))
        refused_source = cli('source_supplied_proof_refusal', 'source-supplied-proof.json', expected_code=2)
        check('source_proof_input_cannot_become_authority', refused_source['status'] == 'REFUSED')
        bad_source_steps = cli('source_zero_steps_refusal', 'examples/source_research_episode.json',
                               ['--source-steps', '0'], expected_code=2)
        check('source_stage_bound_refused', bad_source_steps['status'] == 'REFUSED')
        foreign_source_option = cli('source_options_wrong_query', 'examples/graph_count.json',
                                     ['--source-steps', '1'], expected_code=2)
        check('source_options_stay_in_original_domain', foreign_source_option['status'] == 'REFUSED')
        # Check final receiving bundles where only the checker and original public
        # tasks/certificates exist. Source/controller files are not dependencies.
        standalone = root / 'source-standalone'; standalone.mkdir()
        (standalone / 'recursive_check.py').write_bytes(files['recursive_check.py'])
        packet = [{'task': original_sources[row['task_id']], 'certificate': row['result']['certificate']}
                  for row in source_finished['roots']]
        (standalone / 'evidence.json').write_bytes(encoded(packet))
        standalone_code = r'''import json, pathlib, runpy
root = pathlib.Path.cwd()
checker = runpy.run_path(str(root / 'recursive_check.py'))
class Budget:
    def __init__(self): self.work = 0
    def use(self, n=1):
        self.work += n
        if self.work > 2000000: raise RuntimeError('standalone replay work limit')
answers = [checker['check'](row['task'], row['certificate'], Budget())
           for row in json.loads((root / 'evidence.json').read_text(encoding='utf-8'))]
print(json.dumps(answers))
'''
        began = time.perf_counter_ns()
        standalone_run = subprocess.run([python, '-I', '-B', '-X', 'utf8', '-c', standalone_code],
            cwd=standalone, capture_output=True, text=True, encoding='utf-8', timeout=90,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        receipt['cli_runs'].append({'case': 'source_standalone_original_bundles', 'returncode': standalone_run.returncode,
            'elapsed_ns': time.perf_counter_ns() - began, 'stderr': standalone_run.stderr})
        standalone_checks = json.loads(standalone_run.stdout)
        check('source_final_bundles_replay_without_producer_or_source_context', standalone_run.returncode == 0
              and not standalone_run.stderr and len(standalone_checks) == 2
              and all(row['ok'] and row['kind'] == 'recursive_identity' for row in standalone_checks)
              and {row['task_id'] for row in standalone_checks} == set(original_sources))
        graph = cli('fresh_graph', 'examples/graph_count.json', ['--state', 'graph-state.json'])
        check('original_graph_answer', graph.get('answer') == 2**64)
        polynomial = cli('fresh_polynomial', 'examples/polynomial_consequence.json', ['--state', 'polynomial-state.json'])
        check('polynomial_implication', polynomial['status'] == 'CHECKED_IMPLICATION')
        localized = cli('localized_original_guard', 'examples/localized_cancellation.json',
                        ['--state', 'localized-state.json', '--proof-policy', 'localized_first'])
        check('localized_original_certificate', localized['status'] == 'CHECKED_IMPLICATION'
              and localized['certificate']['kind'] == 'localized_polynomial_combination'
              and localized['certificate']['nonzero_index'] == 0
              and localized['check']['support_checked'] is False)
        m3 = cli('localized_source_converse', 'examples/localized_consequence.json',
                 ['--proof-policy', 'localized_first'])
        check('original_source_converse_found_with_fixed_policy', m3['status'] == 'CHECKED_IMPLICATION'
              and m3['certificate']['kind'] == 'localized_polynomial_combination'
              and m3['certificate']['nonzero_index'] == 1
              and m3['localization']['work'] <= m3['localization']['work_allowance'])
        replay = cli('localized_default_cache_restart', 'examples/localized_cancellation.json',
                     ['--state', 'localized-state.json'])
        check('default_rechecks_new_original_evidence', replay['status'] == 'CHECKED_IMPLICATION'
              and replay.get('reused_after_fresh_check') is True)
        replay = cli('localized_obligations_cache_restart', 'examples/localized_cancellation.json',
                     ['--state', 'localized-state.json', '--proof-policy', 'obligations'])
        check('obligations_cached_localized_kind_is_explicit', replay['status'] == 'CHECKED_IMPLICATION'
              and replay.get('reused_after_fresh_check') is True
              and replay['obligations'].get('original_evidence_replay') is True
              and replay['obligations'].get('final_flat_replay') is False
              and replay['obligations'].get('final_proof_kind') == 'localized_polynomial_combination')
        began = time.perf_counter_ns()
        helper_run = subprocess.run([python, '-I', '-B', '-X', 'utf8', str(root / 'tools/helper_client.py'),
            'examples/localized_cancellation.json', '--state', 'localized-state.json', '--proof-policy', 'localized_first'],
            cwd=root, capture_output=True, text=True, encoding='utf-8', timeout=90,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        envelope = json.loads(helper_run.stdout)
        check('localized_helper_replays_original_proof', helper_run.returncode == 0 and not helper_run.stderr
              and envelope.get('outcome') == 'closed' and envelope.get('status') == 'CHECKED_IMPLICATION'
              and envelope['result'].get('reused_after_fresh_check') is True)
        receipt['cli_runs'].append({'case': 'localized_helper_restart', 'returncode': helper_run.returncode,
            'status': envelope.get('status'), 'elapsed_ns': time.perf_counter_ns() - began})
        forged = json.loads((root / 'localized-state.json').read_bytes())
        localized_row = next(row for row in forged['observations']
                             if row.get('certificate', {}).get('kind') == 'localized_polynomial_combination')
        localized_row['certificate']['multipliers'][0][0][1] = [2, 1]
        (root / 'localized-forged-state.json').write_bytes(encoded(forged))
        recovered = cli('localized_forged_cache', 'examples/localized_cancellation.json',
                        ['--state', 'localized-forged-state.json', '--proof-policy', 'localized_first'])
        check('localized_forgery_rejected_before_rediscovery', recovered['status'] == 'CHECKED_IMPLICATION'
              and not recovered.get('reused_after_fresh_check')
              and recovered['certificate'] == localized['certificate'])
        changed = json.loads((root / 'examples/localized_cancellation.json').read_bytes())
        changed['nonzero'] = ['y']
        (root / 'localized-changed-guard.json').write_bytes(encoded(changed))
        wrong_guard = cli('localized_changed_guard', 'localized-changed-guard.json',
                         ['--state', 'localized-state.json', '--proof-policy', 'localized_first'])
        check('different_guard_not_inherited', wrong_guard['status'] == 'CHECKED_COUNTEREXAMPLE'
              and wrong_guard['certificate']['kind'] == 'rational_counterexample')
        vacuous = {'query': 'polynomial_consequence', 'domain': 'QQ', 'variables': ['x'],
                   'assumptions': [], 'nonzero': ['0'], 'goal': '1', 'multiplier_degree': 0}
        (root / 'localized-vacuous.json').write_bytes(encoded(vacuous))
        empty = cli('localized_vacuous_implication', 'localized-vacuous.json', ['--proof-policy', 'localized_first'])
        check('vacuous_proof_makes_no_support_claim', empty['status'] == 'CHECKED_IMPLICATION'
              and empty['check']['support_checked'] is False and 'support_point' not in empty['certificate'])
        zero = cli('localized_zero_work', 'examples/localized_cancellation.json',
                   ['--proof-policy', 'localized_first', '--work', '0'], expected_code=3)
        check('localized_zero_work_unknown', zero['status'] == 'UNKNOWN')
        localized_campaign = cli('localized_campaign', 'examples/campaign_localization.json',
                                 ['--state', 'localized-campaign-state.json'])
        check('campaign_runs_explicit_original_localization', localized_campaign['status'] == 'CHECKED_CAMPAIGN'
              and localized_campaign['executed_routes'] == ['localized_implication'])
        replay = cli('localized_campaign_restart', 'examples/campaign_localization.json',
                     ['--state', 'localized-campaign-state.json'])
        check('campaign_rechecks_localized_without_new_search', replay['status'] == 'CHECKED_CAMPAIGN'
              and not replay['executed_routes'] and replay.get('replay_work', 0) > 0)
        forged = json.loads((root / 'localized-campaign-state.json').read_bytes())
        campaign_row = next(row for row in forged['observations'] if row.get('kind') == 'research_campaign')
        wrong_route = campaign_row['attempts'][0]['route_id']
        campaign_row['attempts'][0]['result']['status'] = 'CHECKED_COUNTEREXAMPLE'
        (root / 'localized-forged-campaign.json').write_bytes(encoded(forged))
        recovered = cli('localized_campaign_forged_status', 'examples/campaign_localization.json',
                        ['--state', 'localized-forged-campaign.json'])
        check('campaign_wrong_new_kind_status_invalidated', recovered['status'] == 'CHECKED_CAMPAIGN'
              and wrong_route in recovered.get('invalidated_saved_routes', []))
        guarded_seed = cli('guarded_transfer_source', 'examples/localized_cancellation.json',
                           ['--state', 'guarded-instance.json', '--proof-policy', 'localized_first'])
        check('guarded_transfer_source_actually_learned', guarded_seed['status'] == 'CHECKED_IMPLICATION'
              and guarded_seed['certificate']['kind'] == 'localized_polynomial_combination')
        source_only = (root / 'guarded-instance.json').read_bytes()
        unchanged_default = cli('guarded_source_default_policy', 'examples/guarded_receiving.json',
                                ['--state', 'guarded-instance.json'], expected_code=3)
        check('guarded_source_not_implicitly_promoted_into_default', unchanged_default['status'] == 'UNKNOWN'
              and not unchanged_default.get('lemma_reuse', {}).get('used'))
        guarded = cli('guarded_changed_receiving_goal', 'examples/guarded_receiving.json',
                      ['--state', 'guarded-instance.json', '--proof-policy', 'lemma_first'])
        check('guarded_transfer_proves_changed_original', guarded['status'] == 'CHECKED_IMPLICATION'
              and guarded.get('lemma_reuse', {}).get('used') is True
              and guarded['certificate']['kind'] == 'localized_polynomial_combination'
              and guarded['certificate']['nonzero_index'] == 0)
        began = time.perf_counter_ns()
        helper_run = subprocess.run([python, '-I', '-B', '-X', 'utf8', str(root / 'tools/helper_client.py'),
            'examples/guarded_receiving.json', '--state', 'guarded-instance.json', '--proof-policy', 'lemma_first'],
            cwd=root, capture_output=True, text=True, encoding='utf-8', timeout=90,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        envelope = json.loads(helper_run.stdout)
        check('guarded_helper_rechecks_transferred_original', helper_run.returncode == 0 and not helper_run.stderr
              and envelope.get('status') == 'CHECKED_IMPLICATION' and envelope.get('outcome') == 'closed'
              and envelope['result'].get('reused_after_fresh_check') is True)
        receipt['cli_runs'].append({'case': 'guarded_helper_restart', 'returncode': helper_run.returncode,
            'status': envelope.get('status'), 'elapsed_ns': time.perf_counter_ns() - began})
        (root / 'guarded-premises.json').write_bytes(source_only)
        guarded_args = ['--state', 'guarded-premises.json', '--proof-policy', 'obligations', '--obligation-steps', '1']
        pending = cli('guarded_premise_first_step', 'examples/guarded_receiving.json', guarded_args, expected_code=3)
        check('guarded_original_pending_after_flat_child', pending['status'] == 'UNKNOWN'
              and pending['obligations']['executed'][0]['role'] == 'required_premise')
        pending_state = json.loads((root / 'guarded-premises.json').read_bytes())
        resumed = cli('guarded_premise_assembly_restart', 'examples/guarded_receiving.json', guarded_args)
        check('guarded_durable_assembly_rechecks_child', resumed['status'] == 'CHECKED_IMPLICATION'
              and resumed['certificate']['kind'] == 'localized_polynomial_combination'
              and bool(resumed['obligations']['replayed_nodes'])
              and resumed['obligations']['executed'][0]['role'] == 'transfer')
        graph = next(row for row in pending_state['observations'] if row.get('kind') == 'proof_obligations')
        child_id = next(key for key, node in graph['nodes'].items() if node['role'] == 'required_premise'
                        and node.get('result', {}).get('status') == 'CHECKED_IMPLICATION')
        child_certificate = graph['nodes'][child_id]['result']['certificate']
        # This is a valid localized proof of u*v from [u*v-w,w], but the
        # required-premise role only accepts a flat proof for this composition.
        child_certificate.update(kind='localized_polynomial_combination', nonzero_index=0,
                                 multipliers=[[[[1, 0, 0], [1, 1]]], [[[1, 0, 0], [1, 1]]]])
        (root / 'guarded-localized-child.json').write_bytes(encoded(pending_state))
        retried = cli('guarded_saved_localized_child', 'examples/guarded_receiving.json',
            ['--state', 'guarded-localized-child.json', '--proof-policy', 'obligations', '--obligation-steps', '1'], expected_code=3)
        check('guarded_localized_child_invalidated_and_retried_flat', child_id in retried['obligations']['invalidated_nodes']
              and retried['obligations']['executed'][0]['role'] == 'required_premise'
              and retried['obligations']['nodes'][child_id]['result']['certificate']['kind'] == 'polynomial_combination')
        changed = json.loads((root / 'examples/guarded_receiving.json').read_bytes())
        changed['nonzero'] = []
        (root / 'guarded-no-condition.json').write_bytes(encoded(changed))
        refuted = cli('guarded_missing_receiving_condition', 'guarded-no-condition.json',
                      ['--state', 'guarded-instance.json', '--proof-policy', 'lemma_first'])
        check('guarded_source_cannot_authorize_missing_condition', refuted['status'] == 'CHECKED_COUNTEREXAMPLE'
              and refuted['certificate']['kind'] == 'rational_counterexample')
        routes = []
        for index in range(3):
            outcome = cli('guarded_campaign_' + str(index), 'examples/campaign_guarded_transfer.json',
                          ['--state', 'guarded-campaign-state.json'], expected_code=3 if index < 2 else 0)
            routes.extend(outcome['executed_routes'])
        check('guarded_campaign_learns_then_transfers', outcome['status'] == 'CHECKED_CAMPAIGN'
              and routes == ['guarded_lemma_first', 'localized_implication', 'guarded_lemma_first'])
        replay = cli('guarded_campaign_replay', 'examples/campaign_guarded_transfer.json',
                     ['--state', 'guarded-campaign-state.json'])
        check('guarded_campaign_rechecks_complete_original_results', replay['status'] == 'CHECKED_CAMPAIGN'
              and not replay['executed_routes'] and replay['replay_work'] > 0)
        seed = cli('lemma_source', 'examples/lemma_source.json', ['--state', 'lemma-state.json'])
        check('lemma_seed_checked', seed['status'] == 'CHECKED_IMPLICATION')
        receiving = cli('lemma_receiving', 'examples/lemma_receiving.json',
                        ['--state', 'lemma-state.json', '--proof-policy', 'lemma_first'])
        check('lemma_transferred_checked', receiving['status'] == 'CHECKED_IMPLICATION'
              and receiving.get('lemma_reuse', {}).get('used') is True)
        reused = cli('lemma_receiving_restart', 'examples/lemma_receiving.json',
                     ['--state', 'lemma-state.json', '--proof-policy', 'lemma_first'])
        check('lemma_final_proof_rechecked', reused['status'] == 'CHECKED_IMPLICATION'
              and reused.get('reused_after_fresh_check') is True)
        premise_seed = cli('obligation_source', 'examples/obligation_source.json',
                           ['--state', 'premise-state.json', '--proof-policy', 'direct'])
        check('obligation_source_has_unused_equation', premise_seed['status'] == 'CHECKED_IMPLICATION'
              and premise_seed['certificate']['multipliers'][1] == [])
        obligation_args = ['--state', 'premise-state.json', '--proof-policy', 'obligations', '--obligation-steps', '1']
        pending = cli('obligation_first_child', 'examples/obligation_receiving.json', obligation_args, expected_code=3)
        check('one_stage_preserves_unresolved_parent', pending['status'] == 'UNKNOWN'
              and len(pending['obligations']['executed']) == 1
              and pending['obligations']['executed'][0]['role'] == 'required_premise')
        pending_bytes = (root / 'premise-state.json').read_bytes()
        pending_state = json.loads(pending_bytes)
        pending_graph = next(row for row in pending_state['observations'] if row.get('kind') == 'proof_obligations')
        check('source_core_prepared_once_with_exact_duplicate_plans_removed',
              pending['obligations'].get('source_core_preparations') == 1
              and pending['obligations'].get('duplicate_plans') == 3
              and len(pending_graph['plans']) == 3)
        check('incremental_plan_pool_bytes_match_complete_serialization',
              pending['obligations'].get('plan_pool_bytes')
              == len(json.dumps(pending_graph['plans'], sort_keys=True, separators=(',', ':'), allow_nan=False).encode()))
        checked_child_ids = [identity for identity, node in pending_graph['nodes'].items()
                             if node['role'] == 'required_premise' and node.get('result', {}).get('status') == 'CHECKED_IMPLICATION']
        check('saved_child_is_distinct_original_question', len(checked_child_ids) == 1
              and checked_child_ids[0] != pending['task_id'])
        closed_parent = cli('obligation_resume_assembly', 'examples/obligation_receiving.json', obligation_args)
        check('restart_rechecks_child_then_flattens', closed_parent['status'] == 'CHECKED_IMPLICATION'
              and checked_child_ids[0] in closed_parent['obligations']['replayed_nodes']
              and closed_parent['obligations']['executed'][0]['role'] == 'transfer'
              and set(closed_parent['certificate']) == {'kind', 'task_id', 'multipliers'})
        root_only = json.loads((root / 'premise-state.json').read_bytes())
        root_only['observations'] = [row for row in root_only['observations'] if row['task_id'] == closed_parent['task_id']]
        (root / 'premise-root-only.json').write_bytes(encoded(root_only))
        root_replay = cli('obligation_final_without_sources', 'examples/obligation_receiving.json',
                          ['--state', 'premise-root-only.json', '--proof-policy', 'obligations'])
        check('flat_parent_replays_without_library_or_graph', root_replay.get('reused_after_fresh_check') is True
              and root_replay['status'] == 'CHECKED_IMPLICATION')
        forged = json.loads(pending_bytes)
        forged_graph = next(row for row in forged['observations'] if row.get('kind') == 'proof_obligations')
        forged_graph['nodes'][checked_child_ids[0]]['result']['certificate']['multipliers'] = [[], []]
        (root / 'forged-premise.json').write_bytes(encoded(forged))
        rejected_child = cli('obligation_saved_child_forgery', 'examples/obligation_receiving.json',
            ['--state', 'forged-premise.json', '--proof-policy', 'obligations', '--obligation-steps', '1'], expected_code=3)
        check('forged_child_requires_new_original_proof', rejected_child['status'] == 'UNKNOWN'
              and checked_child_ids[0] in rejected_child['obligations']['invalidated_nodes']
              and rejected_child['obligations']['executed'][0]['role'] == 'required_premise')
        forged = json.loads(pending_bytes)
        forged_graph = next(row for row in forged['observations'] if row.get('kind') == 'proof_obligations')
        next(node for node in forged_graph['nodes'].values() if node['role'] == 'transfer')['requires'] = []
        (root / 'forged-dependency.json').write_bytes(encoded(forged))
        bad_graph = cli('obligation_dependency_forgery', 'examples/obligation_receiving.json',
            ['--state', 'forged-dependency.json', '--proof-policy', 'obligations'], expected_code=2)
        check('saved_graph_cannot_erase_required_children', bad_graph['status'] == 'REFUSED')
        referenced = json.loads(pending_bytes)
        next(row for row in referenced['observations'] if row.get('kind') == 'polynomial_consequence')['dependencies'] = ['unproved-reference']
        (root / 'source-reference.json').write_bytes(encoded(referenced))
        refused_source = cli('obligation_source_graph_reference', 'examples/obligation_receiving.json',
            ['--state', 'source-reference.json', '--proof-policy', 'obligations', '--obligation-steps', '1'])
        check('source_reference_cannot_authorize_transfer', refused_source['status'] == 'CHECKED_IMPLICATION'
              and refused_source['obligations'].get('source_core_preparations') == 0
              and refused_source['obligations']['executed'][0]['role'] == 'direct'
              and any('references' in row['reason'] for row in refused_source['obligations']['rejected_plans']))
        (root / 'premise-helper.json').write_bytes(pending_bytes)
        helper_run = subprocess.run([python, '-I', '-B', '-X', 'utf8', str(root / 'tools/helper_client.py'),
            'examples/obligation_receiving.json', '--state', 'premise-helper.json', '--proof-policy', 'obligations',
            '--obligation-steps', '1'], cwd=root, capture_output=True, text=True, encoding='utf-8', timeout=90,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        helper_envelope = json.loads(helper_run.stdout)
        check('obligation_helper_resumes_actual_pending_stage', helper_run.returncode == 0 and not helper_run.stderr
              and helper_envelope.get('outcome') == 'closed'
              and helper_envelope['result']['status'] == 'CHECKED_IMPLICATION'
              and len(helper_envelope['result']['obligations']['executed']) == 1)
        receipt['cli_runs'].append({'case': 'obligation_helper_resume', 'returncode': helper_run.returncode,
                                   'status': helper_envelope.get('status'), 'stderr': helper_run.stderr})
        zero = cli('obligation_zero_work', 'examples/obligation_receiving.json',
                   ['--proof-policy', 'obligations', '--work', '0'], expected_code=3)
        check('obligation_budget_exhaustion_unknown', zero['status'] == 'UNKNOWN')
        bad_steps = cli('obligation_bad_steps', 'examples/obligation_receiving.json',
                       ['--proof-policy', 'obligations', '--obligation-steps', '0'], expected_code=2)
        check('obligation_stage_bound_refused', bad_steps['status'] == 'REFUSED')
        degree_limited = json.loads((root / 'examples/obligation_receiving.json').read_bytes())
        degree_limited['multiplier_degree'] = 0
        (root / 'obligation-degree-zero.json').write_bytes(encoded(degree_limited))
        degree_miss = cli('obligation_receiving_degree_bound', 'obligation-degree-zero.json',
                         ['--state', 'premise-state.json', '--proof-policy', 'obligations', '--obligation-steps', '16'], expected_code=3)
        check('saved_source_cannot_relax_original_degree', degree_miss['status'] == 'UNKNOWN'
              and degree_miss['task_id'] != closed_parent['task_id'])
        false_child_source = {'query': 'polynomial_consequence', 'domain': 'QQ', 'variables': ['a', 'b'],
                              'assumptions': ['a'], 'goal': 'a*b', 'multiplier_degree': 1}
        true_parent = {**false_child_source, 'assumptions': ['b']}
        (root / 'false-child-source.json').write_bytes(encoded(false_child_source))
        (root / 'true-parent.json').write_bytes(encoded(true_parent))
        cli('source_with_unnecessary_parent_premise', 'false-child-source.json', ['--state', 'false-child-state.json'])
        true_result = cli('refuted_child_true_parent', 'true-parent.json',
                         ['--state', 'false-child-state.json', '--proof-policy', 'obligations', '--obligation-steps', '16'])
        check('child_counterexample_never_refutes_true_parent', true_result['status'] == 'CHECKED_IMPLICATION'
              and any(x['role'] == 'required_premise' and x['status'] == 'CHECKED_COUNTEREXAMPLE'
                      for x in true_result['obligations']['executed']))
        # A padded original carrier exceeds the direct search-column bound. The
        # default automatic policy must still produce a valid flat certificate.
        padded_seed = {'query': 'polynomial_consequence', 'domain': 'QQ', 'variables': ['x'],
                       'assumptions': ['x'], 'goal': 'x*x', 'multiplier_degree': 1, 'counterexample_radius': 1}
        padded = {'query': 'polynomial_consequence', 'domain': 'QQ', 'variables': list('abcdef'),
                  'assumptions': list('abcdef') + ['a+b', 'c+d'], 'goal': 'a**4',
                  'multiplier_degree': 3, 'counterexample_radius': 1}
        (root / 'padded-seed.json').write_bytes(encoded(padded_seed))
        (root / 'padded-receiving.json').write_bytes(encoded(padded))
        padded_direct = cli('padded_direct_limit', 'padded-receiving.json',
                            ['--proof-policy', 'direct'], expected_code=3)
        check('padded_direct_unresolved', padded_direct['status'] == 'UNKNOWN')
        cli('padded_seed', 'padded-seed.json', ['--state', 'padded-state.json'])
        padded_auto = cli('padded_automatic_policy', 'padded-receiving.json', ['--state', 'padded-state.json'])
        check('default_auto_settles_original_padded_implication', padded_auto['status'] == 'CHECKED_IMPLICATION')
        recurrence = cli('fresh_recurrence', 'examples/discover_recurrence.json', ['--state', 'recurrence-state.json'])
        check('recurrence_original_fibonacci', recurrence['status'] == 'CHECKED_RECURRENCE'
              and recurrence['certificate']['coefficients'] == [[1, 1], [1, 1]]
              and recurrence['certificate']['initial_terms'] == [[0, 1], [1, 1]])
        recurrence_replay = cli('recurrence_restart', 'examples/discover_recurrence.json',
                                ['--state', 'recurrence-state.json'])
        check('recurrence_fresh_proof_replay', recurrence_replay.get('reused_after_fresh_check') is True)
        hidden = cli('hidden_mode_recurrence', 'examples/hidden_mode_recurrence.json')
        check('scalar_hidden_mode_recurrence', hidden['status'] == 'CHECKED_RECURRENCE'
              and hidden['certificate']['coefficients'] == [[2, 1]])
        word_recurrence = cli('original_word_recurrence', 'examples/discover_word_recurrence.json')
        check('word_recurrence_checked_on_original_patterns', word_recurrence['status'] == 'CHECKED_RECURRENCE')
        invariant = cli('full_invariant', 'examples/discover_invariant.json', ['--state', 'invariant-full-state.json'])
        check('full_invariant_original_law', invariant['status'] == 'CHECKED_INVARIANT'
              and invariant['certificate']['initial_value'] == [25, 1]
              and invariant.get('policy') == 'full' and invariant['check']['initial_checked'])
        mapped = cli('mapped_invariant', 'examples/discover_invariant.json',
                     ['--state', 'invariant-map-state.json', '--invariant-policy', 'mapped'])
        check('mapped_invariant_original_law', mapped['status'] == 'CHECKED_INVARIANT'
              and mapped['certificate']['initial_value'] == [25, 1] and 'dependency_map' in mapped)
        map_state = root / 'invariant-map-state.json'
        forged_map_state = json.loads(map_state.read_text(encoding='utf-8'))
        forged_map_state['observations'][0]['dependency_map'] = {'forged': True, 'accepted': True}
        forged_map_state['observations'][0]['map_status'] = 'FAKE_TRUSTED'
        map_state.write_bytes(encoded(forged_map_state))
        mapped_replay = cli('invariant_corrupt_map_restart', 'examples/discover_invariant.json',
                            ['--state', 'invariant-map-state.json', '--invariant-policy', 'mapped'])
        check('invariant_replay_checks_proof_without_trusting_map', mapped_replay['status'] == 'CHECKED_INVARIANT'
              and mapped_replay.get('reused_after_fresh_check') is True and 'dependency_map' not in mapped_replay)
        preserved = json.loads(map_state.read_text(encoding='utf-8'))
        check('stored_map_explicitly_not_replayed', preserved['observations'][0].get('map_status') == 'STORED_PROPOSAL_NOT_REPLAYED')
        preserved['observations'][0]['certificate']['initial_value'] = [0, 1]
        map_state.write_bytes(encoded(preserved))
        repaired = cli('invariant_forged_certificate', 'examples/discover_invariant.json', ['--state', 'invariant-map-state.json'])
        check('forged_invariant_certificate_replaced_after_check', repaired['status'] == 'CHECKED_INVARIANT'
              and not repaired.get('reused_after_fresh_check') and repaired['certificate']['initial_value'] == [25, 1])
        cancellation = cli('invariant_shared_constant_row', 'examples/invariant_cancellation.json', ['--invariant-policy', 'mapped'])
        check('cross_variable_cancellation_invariant', cancellation['status'] == 'CHECKED_INVARIANT'
              and cancellation['certificate']['initial_value'] == [5, 6])
        nonlinear = cli('nonlinear_cubic_invariant', 'examples/nonlinear_invariant.json')
        check('nonlinear_original_map_conservation', nonlinear['status'] == 'CHECKED_INVARIANT'
              and nonlinear['certificate']['polynomial'] == [[[0, 1], [1, 1]], [[3, 0], [-1, 1]]]
              and nonlinear['certificate']['initial_value'] == [3, 1])
        invariant_unknown = cli('invariant_zero_work', 'examples/discover_invariant.json', ['--work', '0'], expected_code=3)
        check('invariant_exhaustion_unknown', invariant_unknown['status'] == 'UNKNOWN')
        bad_focus = json.loads((root / 'examples/discover_invariant.json').read_text(encoding='utf-8'))
        bad_focus['focus'] = []
        (root / 'invariant-bad-focus.json').write_bytes(encoded(bad_focus))
        invariant_refused = cli('invariant_bad_focus', 'invariant-bad-focus.json', expected_code=2)
        check('invariant_empty_focus_refused', invariant_refused['status'] == 'REFUSED')
        learned = cli('invariant_learn_source', 'examples/invariant_reuse_source.json', ['--state', 'invariant-reuse-state.json'])
        check('invariant_source_generated_checked', learned['status'] == 'CHECKED_INVARIANT'
              and learned['certificate']['initial_value'] == [3, 1])
        source_only = (root / 'invariant-reuse-state.json').read_bytes()
        received = cli('invariant_cross_system_reuse', 'examples/invariant_reuse_receiving.json',
                       ['--state', 'invariant-reuse-state.json', '--invariant-policy', 'reuse_first'])
        check('invariant_receiving_system_checked', received['status'] == 'CHECKED_INVARIANT'
              and received.get('law_reuse', {}).get('used') is True
              and received['certificate']['initial_value'] == [53, 24])
        received_again = cli('invariant_transferred_proof_restart', 'examples/invariant_reuse_receiving.json',
                             ['--state', 'invariant-reuse-state.json', '--invariant-policy', 'reuse_first'])
        check('transferred_proof_rechecked_after_restart', received_again.get('reused_after_fresh_check') is True)
        corrupted = json.loads(source_only)
        corrupted['observations'][0]['certificate']['initial_value'] = [0, 1]
        (root / 'invariant-corrupt-source.json').write_bytes(encoded(corrupted))
        recovered = cli('invariant_source_evidence_forgery', 'examples/invariant_reuse_receiving.json',
                        ['--state', 'invariant-corrupt-source.json', '--invariant-policy', 'reuse_first'])
        check('forged_source_not_used_for_receiving_proof', recovered['status'] == 'CHECKED_INVARIANT'
              and not recovered.get('law_reuse', {}).get('used') and recovered['law_reuse']['source_failures'] == 1
              and recovered['law_reuse']['fallback'] is True)
        changed = json.loads((root / 'examples/invariant_reuse_receiving.json').read_text(encoding='utf-8'))
        changed['transition'] = ['2*u', '3*v']
        (root / 'invariant-changed-dynamics.json').write_bytes(encoded(changed))
        (root / 'invariant-source-only.json').write_bytes(source_only)
        unresolved = cli('invariant_unrelated_dynamics', 'invariant-changed-dynamics.json',
                         ['--state', 'invariant-source-only.json', '--invariant-policy', 'reuse_first'], expected_code=3)
        check('changed_dynamics_does_not_inherit_source_law', unresolved['status'] == 'UNKNOWN'
              and not unresolved['law_reuse']['used'] and unresolved['law_reuse']['target_failures'] > 0)
        word = cli('fresh_word', 'examples/word_identity.json', ['--state', 'word-state.json'])
        check('word_identity', word['status'] == 'CHECKED_WORD_IDENTITY')
        replay = cli('word_restart', 'examples/word_identity.json', ['--state', 'word-state.json'])
        check('word_replayed_after_restart', replay.get('reused_after_fresh_check') is True)
        shortcut = cli('hidden_mode_shortcut', 'examples/word_shortcut.json')
        check('valid_shortcut_identity', shortcut['status'] == 'CHECKED_WORD_IDENTITY')
        bad_shortcut = json.loads((root / 'examples/word_identity.json').read_text(encoding='utf-8'))
        bad_shortcut['formula'] = 'column_shortcut'
        (root / 'incorrect-shortcut.json').write_bytes(encoded(bad_shortcut))
        refutation = cli('word_refutation', 'incorrect-shortcut.json')
        check('wrong_shortcut_refuted', refutation['status'] == 'CHECKED_WORD_COUNTEREXAMPLE')
        rational = cli('rational_repair', 'examples/rational_repair.json')
        check('rational_guard_result', rational['status'] == 'CHECKED_GUARDS' and bool(rational.get('accepted')))
        unknown = cli('exhaustion', 'examples/graph_count.json', ['--work', '0'], expected_code=3)
        check('exhaustion_is_unknown', unknown['status'] == 'UNKNOWN')
        (root / 'bad-task.json').write_text('{"query":"a","query":"b"}', encoding='utf-8')
        refused = cli('duplicate_input', 'bad-task.json', expected_code=2)
        check('duplicate_input_refused', refused['status'] == 'REFUSED')
        for index in range(2):
            args = [python, '-I', '-B', '-X', 'utf8', str(root / 'tools/helper_client.py'),
                    'examples/word_identity.json', '--state', 'helper-state.json']
            began = time.perf_counter_ns()
            helper = subprocess.run(args, cwd=root, capture_output=True, text=True, encoding='utf-8',
                                    timeout=90, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            envelope = json.loads(helper.stdout)
            check('helper_' + str(index) + '_protocol', helper.returncode == 0 and not helper.stderr
                  and envelope.get('api_version') == 'ember.helper.v1' and envelope.get('outcome') == 'closed'
                  and envelope.get('runtime_version') == manifest['version']
                  and envelope.get('result', {}).get('status') == 'CHECKED_WORD_IDENTITY')
            if index:
                check('helper_replays_instance', envelope['result'].get('reused_after_fresh_check') is True)
            receipt['cli_runs'].append({'case': 'helper_' + str(index), 'returncode': helper.returncode,
                                       'status': envelope['status'], 'elapsed_ns': time.perf_counter_ns() - began})
        helper_unknown = subprocess.run([python, '-I', '-B', '-X', 'utf8', str(root / 'tools/helper_client.py'),
                                        'examples/graph_count.json', '--work', '0'], cwd=root,
                                       capture_output=True, text=True, encoding='utf-8', timeout=90,
                                       creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        check('helper_preserves_unknown', helper_unknown.returncode == 3 and not helper_unknown.stderr
              and json.loads(helper_unknown.stdout).get('outcome') == 'unknown')
        for index in range(2):
            began = time.perf_counter_ns()
            run = subprocess.run([python, '-I', '-B', '-X', 'utf8', str(root / 'tools/helper_client.py'),
                                  'examples/discover_invariant.json', '--state', 'invariant-helper-state.json'],
                                 cwd=root, capture_output=True, text=True, encoding='utf-8', timeout=90,
                                 creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            envelope = json.loads(run.stdout)
            check('invariant_helper_' + str(index) + '_protocol', run.returncode == 0 and not run.stderr
                  and envelope.get('status') == 'CHECKED_INVARIANT' and envelope.get('outcome') == 'closed')
            if index:
                check('invariant_helper_rechecks_saved_proof', envelope.get('result', {}).get('reused_after_fresh_check') is True)
            receipt['cli_runs'].append({'case': 'invariant_helper_' + str(index), 'returncode': run.returncode,
                                       'status': envelope.get('status'), 'elapsed_ns': time.perf_counter_ns() - began})
        for index in range(3):
            # The third call receives deliberately forged saved evidence. It must
            # freshly rediscover a valid proof rather than trust the saved flag.
            if index == 2:
                state_path = root / 'recurrence-helper-state.json'
                data = json.loads(state_path.read_text(encoding='utf-8'))
                data['observations'][0]['certificate']['initial_terms'][0][0] += 1
                state_path.write_bytes(encoded(data))
            args = [python, '-I', '-B', '-X', 'utf8', str(root / 'tools/helper_client.py'),
                    'examples/hidden_mode_recurrence.json', '--state', 'recurrence-helper-state.json']
            began = time.perf_counter_ns()
            run = subprocess.run(args, cwd=root, capture_output=True, text=True, encoding='utf-8', timeout=90,
                                 creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            envelope = json.loads(run.stdout)
            check('recurrence_helper_' + str(index) + '_protocol', run.returncode == 0 and not run.stderr
                  and envelope.get('outcome') == 'closed' and envelope.get('status') == 'CHECKED_RECURRENCE')
            result = envelope.get('result', {})
            if index == 1:
                check('recurrence_helper_fresh_restart_check', result.get('reused_after_fresh_check') is True)
            elif index == 2:
                check('recurrence_helper_refuses_forged_saved_proof', not result.get('reused_after_fresh_check')
                      and result['certificate']['initial_terms'] == [[1, 1]])
            receipt['cli_runs'].append({'case': 'recurrence_helper_' + str(index), 'returncode': run.returncode,
                                       'status': envelope.get('status'), 'elapsed_ns': time.perf_counter_ns() - began})
        recurrence_campaign = {
            'query': 'research_campaign', 'max_attempts': 1, 'attempt_work': 1_000_000, 'policy': 'fixed',
            'problems': [json.loads((root / 'examples/hidden_mode_recurrence.json').read_text(encoding='utf-8')),
                         json.loads((root / 'examples/discover_word_recurrence.json').read_text(encoding='utf-8'))]}
        (root / 'recurrence-campaign.json').write_bytes(encoded(recurrence_campaign))
        first = cli('recurrence_campaign_partial', 'recurrence-campaign.json',
                    ['--state', 'recurrence-campaign-state.json'], expected_code=3)
        check('recurrence_campaign_checkpoint', first['status'] == 'UNKNOWN' and first.get('saved_attempt_count') == 1)
        resumed = cli('recurrence_campaign_resume', 'recurrence-campaign.json',
                      ['--state', 'recurrence-campaign-state.json'])
        check('recurrence_campaign_completes', resumed['status'] == 'CHECKED_CAMPAIGN'
              and resumed.get('saved_attempt_count') == 2 and resumed.get('replay_work', 0) > 0)
        replayed = cli('recurrence_campaign_proof_replay', 'recurrence-campaign.json',
                       ['--state', 'recurrence-campaign-state.json'])
        check('recurrence_campaign_rechecks_without_search', replayed['status'] == 'CHECKED_CAMPAIGN'
              and not replayed.get('executed_routes') and replayed.get('replay_work', 0) > 0)
        generated_first = cli('generated_question_original', 'examples/campaign_discovery.json',
                              ['--state', 'generated-question-state.json'], expected_code=3)
        check('generated_question_finite_answer_first', generated_first['status'] == 'UNKNOWN'
              and generated_first['problems'][0]['attempts'][0]['result']['answer'] == 144)
        generated_next = cli('generated_question_restart', 'examples/campaign_discovery.json',
                             ['--state', 'generated-question-state.json'])
        attempts = generated_next['problems'][0]['attempts']
        check('generated_recurrence_is_new_checked_question', generated_next['status'] == 'CHECKED_CAMPAIGN'
              and [a['role'] for a in attempts] == ['original', 'generalization']
              and attempts[-1]['result']['status'] == 'CHECKED_RECURRENCE')
        generated_replay = cli('generated_question_replay', 'examples/campaign_discovery.json',
                               ['--state', 'generated-question-state.json'])
        check('generated_question_replayed_proofs', generated_replay['status'] == 'CHECKED_CAMPAIGN'
              and not generated_replay.get('executed_routes') and generated_replay.get('replay_work', 0) > 0)
        invariant_calls = [cli('invariant_degree_campaign_' + str(index), 'examples/campaign_invariant.json',
                               ['--state', 'invariant-campaign-state.json'], expected_code=3) for index in range(4)]
        degree_rows = invariant_calls[2]['problems'][0]['attempts']
        check('invariant_campaign_original_stays_unknown', all(result['status'] == 'UNKNOWN' for result in invariant_calls)
              and all(row['role'] == 'original' and row['result']['status'] == 'UNKNOWN' for row in degree_rows[:2]))
        check('invariant_campaign_checked_quadratic_is_distinct', len(degree_rows) == 3
              and degree_rows[2]['role'] == 'expansion' and degree_rows[2]['task']['max_degree'] == 2
              and degree_rows[2]['result']['status'] == 'CHECKED_INVARIANT')
        check('invariant_campaign_replays_expansion_without_higher_search',
              not invariant_calls[3]['executed_routes'] and invariant_calls[3]['saved_attempt_count'] == 3
              and invariant_calls[3]['replay_work'] > 0)
        reentry_first = cli('campaign_learns_later_source', 'examples/campaign_reuse_reentry.json',
                            ['--state', 'reuse-reentry-state.json', '--work', '200000'], expected_code=3)
        check('bounded_campaign_learns_before_parent_retry', len(reentry_first['executed_routes']) == 4
              and any(a['result']['status'] == 'CHECKED_INVARIANT' for a in reentry_first['problems'][1]['attempts']))
        reentered = cli('campaign_reenters_original_question', 'examples/campaign_reuse_reentry.json',
                        ['--state', 'reuse-reentry-state.json', '--work', '200000'])
        parent_proof = next(a for a in reentered['problems'][0]['attempts'] if a['result']['status'] == 'CHECKED_INVARIANT')
        check('new_knowledge_reopens_exact_original', reentered['status'] == 'CHECKED_CAMPAIGN'
              and reentered['executed_routes'] == ['invariant_reuse_first']
              and len(reentered['invalidated_proposal_context_routes']) == 1
              and parent_proof['role'] == 'original' and parent_proof['result']['law_reuse']['used'] is True)
        checkpoint = json.loads((root / 'reuse-reentry-state.json').read_text(encoding='utf-8'))
        campaign_record = next(o for o in checkpoint['observations'] if o.get('kind') == 'research_campaign')
        check('superseded_unresolved_attempt_retained', any(a['result']['status'] == 'UNKNOWN'
              for a in campaign_record.get('superseded_attempts', [])))
        reentry_replay = cli('campaign_reentered_proof_replay', 'examples/campaign_reuse_reentry.json',
                             ['--state', 'reuse-reentry-state.json', '--work', '200000'])
        check('reentered_campaign_freshly_rechecked', reentry_replay['status'] == 'CHECKED_CAMPAIGN'
              and not reentry_replay['executed_routes'] and reentry_replay['replay_work'] > 0)
        # A one-step public campaign must checkpoint and make progress on restart.
        campaign_task = json.loads((root / 'examples/campaign_research.json').read_text(encoding='utf-8'))
        campaign_task['max_attempts'] = 1
        (root / 'short-campaign.json').write_bytes(encoded(campaign_task))
        attempts = []
        campaign = None
        for index in range(24):
            # UNKNOWN is a normal partial campaign result; inspect it explicitly.
            args = [python, '-I', '-B', '-X', 'utf8', str(root / 'ember.py'), 'short-campaign.json',
                    '--state', 'campaign-state.json', '--work', '10000000']
            began = time.perf_counter_ns()
            run = subprocess.run(args, cwd=root, capture_output=True, text=True, encoding='utf-8', timeout=90,
                                 creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            campaign = json.loads(run.stdout)
            expected = 3 if campaign['status'] == 'UNKNOWN' else 0
            check('campaign_call_' + str(index) + '_exit', run.returncode == expected and not run.stderr)
            attempts.append(campaign.get('saved_attempt_count', 0))
            receipt['cli_runs'].append({'case': 'campaign_' + str(index), 'returncode': run.returncode,
                                       'status': campaign['status'], 'elapsed_ns': time.perf_counter_ns() - began,
                                       'saved_attempt_count': attempts[-1]})
            if campaign['status'] != 'UNKNOWN':
                break
        check('campaign_completed_checked_outcomes', campaign['status'] == 'CHECKED_CAMPAIGN')
        check('campaign_restarts_progress', len(attempts) > 1 and all(b > a for a, b in zip(attempts, attempts[1:])))
        final = cli('campaign_evidence_restart', 'short-campaign.json', ['--state', 'campaign-state.json'])
        check('campaign_restart_rechecks', final.get('replay_work', 0) > 0 and not final.get('executed_routes'))
        # The apex layer, its synthesized routes and the audited reasoning pyramid.
        check('capabilities_apex_interface', {'apex_research', 'prove_orbit_exclusion'} <= set(capabilities.get('queries', []))
              and capabilities.get('layers') == ['direct', 'apex']
              and capabilities.get('apex', {}).get('faces') == ['N', 'W', 'S', 'E']
              and capabilities.get('apex', {}).get('synthesized_routes')
                  == ['law_instance', 'recursive_seeded', 'recursive_lifted_counterexample', 'word_count_direct',
                      'word_count_law', 'generating_function', 'recurrence_minimality', 'reduced_generating_function',
                      'orbit_prefix', 'orbit_transfer', 'orbit_invariant', 'orbit_drift', 'orbit_ranking']
              and {'count_word_avoiders', 'discover_generating_function', 'certify_minimal_recurrence',
                   'certify_eventual_recurrence'} <= set(capabilities.get('queries', []))
              and capabilities.get('limits', {}).get('orbit_steps') == 1024)
        pyramid = cli('pyramid_map', '--pyramid')
        nodes = {row['node']: row for row in pyramid['lattice']}
        check('pyramid_audit_binds_catalog_to_source', pyramid['status'] == 'PYRAMID' and pyramid['audit']['ok'] is True
              and not pyramid['audit']['problems'] and pyramid['audit']['modules'] == len(RUNTIME) - 1
              and pyramid['audit']['trace_labels'] > 0 and len(pyramid['base']) == pyramid['audit']['moves'])
        check('pyramid_fifteen_nodes_with_realized_apex', [row['level'] for row in pyramid['lattice']]
              == [1] * 4 + [2] * 6 + [3] * 4 + [4] and nodes['NWSE']['realized'] and bool(pyramid['apex'])
              and all(nodes[face]['realized'] for face in 'NWSE'))
        tampered = root / 'pyramid-tamper'; tampered.mkdir()
        for name in RUNTIME:
            (tampered / name).write_bytes(files[name])
        (tampered / 'apex.py').write_bytes(files['apex.py'].replace(
            b"operation='refute_reachability_by_repeated_state'", b"operation='unlisted_refutation'"))
        began = time.perf_counter_ns()
        tamper_run = subprocess.run([python, '-I', '-B', '-X', 'utf8', str(tampered / 'ember.py'), '--pyramid'],
                                    cwd=tampered, capture_output=True, text=True, encoding='utf-8', timeout=90,
                                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        tamper_report = json.loads(tamper_run.stdout)
        receipt['cli_runs'].append({'case': 'pyramid_tampered_label', 'returncode': tamper_run.returncode,
                                   'status': tamper_report.get('status'), 'elapsed_ns': time.perf_counter_ns() - began})
        check('pyramid_audit_detects_uncatalogued_label', tamper_run.returncode == 2 and not tamper_run.stderr
              and tamper_report['audit']['ok'] is False
              and any('unlisted_refutation' in problem for problem in tamper_report['audit']['problems']))
        orbit_task = json.loads((root / 'examples/orbit_exclusion.json').read_bytes())
        orbit = cli('orbit_invariant_separation', 'examples/orbit_exclusion.json', ['--state', 'orbit-state.json'])
        check('orbit_excluded_by_checked_separating_invariant', orbit['status'] == 'CHECKED_ORBIT_EXCLUSION'
              and orbit['face'] == 'N' and orbit['certificate']['kind'] == 'invariant_separation'
              and orbit['certificate']['invariant']['polynomial'] == [[[0, 1], [1, 1]], [[3, 0], [-1, 1]]]
              and orbit['certificate']['invariant']['initial_value'] == [3, 1]
              and orbit['certificate']['target_value'] == [2, 1]
              and [row['face'] for row in orbit['faces_tried']] == ['S', 'E', 'N'])
        orbit_replay = cli('orbit_restart', 'examples/orbit_exclusion.json', ['--state', 'orbit-state.json'])
        check('orbit_certificate_freshly_replayed', orbit_replay.get('reused_after_fresh_check') is True
              and orbit_replay['certificate'] == orbit['certificate'])
        forged_orbit = json.loads((root / 'orbit-state.json').read_bytes())
        saved_orbit = next(row for row in forged_orbit['observations'] if row.get('kind') == 'prove_orbit_exclusion')
        saved_orbit['certificate']['invariant']['polynomial'] = [[[0, 1], [1, 1]]]
        saved_orbit['certificate']['target_value'] = [10, 1]
        (root / 'orbit-forged.json').write_bytes(encoded(forged_orbit))
        repaired_orbit = cli('orbit_forged_separation', 'examples/orbit_exclusion.json', ['--state', 'orbit-forged.json'])
        check('orbit_nonconserved_separation_not_admitted', repaired_orbit['status'] == 'CHECKED_ORBIT_EXCLUSION'
              and not repaired_orbit.get('reused_after_fresh_check')
              and repaired_orbit['certificate'] == orbit['certificate'])
        reaching = dict(orbit_task, target=[[2, 1], [11, 1]])
        (root / 'orbit-reaches.json').write_bytes(encoded(reaching))
        reached = cli('orbit_reaching_witness', 'orbit-reaches.json')
        check('orbit_reachable_target_gets_exact_witness', reached['status'] == 'CHECKED_ORBIT_REACHES'
              and reached['certificate'] == {'kind': 'orbit_witness', 'task_id': reached['task_id'], 'index': 2})
        turn = {'query': 'prove_orbit_exclusion', 'domain': 'QQ', 'variables': ['x', 'y'], 'transition': ['y', '-x'],
                'initial': [[3, 1], [4, 1]], 'target': [[5, 1], [0, 1]], 'max_degree': 2, 'max_steps': 8}
        (root / 'orbit-turn.json').write_bytes(encoded(turn))
        periodic = cli('orbit_periodic_refutation', 'orbit-turn.json')
        check('orbit_repeated_state_excludes_invariant_blind_target', periodic['status'] == 'CHECKED_ORBIT_EXCLUSION'
              and periodic['certificate'] == {'kind': 'periodic_orbit', 'task_id': periodic['task_id'], 'start': 0, 'period': 4})
        (root / 'orbit-blind.json').write_bytes(encoded(dict(turn, max_steps=3)))
        blind = cli('orbit_short_prefix_same_invariant_value', 'orbit-blind.json', expected_code=3)
        check('orbit_unknown_does_not_claim_reachability', blind['status'] == 'UNKNOWN'
              and [row['status'] for row in blind['faces_tried']] == ['UNKNOWN'] * 5
              and 'separates' in blind['faces_tried'][2]['reason']
              and blind['faces_tried'][4]['route'] == 'orbit_ranking')
        check('orbit_zero_work_unknown', cli('orbit_zero_work', 'examples/orbit_exclusion.json', ['--work', '0'],
                                             expected_code=3)['status'] == 'UNKNOWN')
        (root / 'orbit-extra.json').write_bytes(encoded(dict(orbit_task, proof='trusted')))
        check('orbit_supplied_proof_field_refused', cli('orbit_extra_field', 'orbit-extra.json',
                                                       expected_code=2)['status'] == 'REFUSED')
        (root / 'orbit-steps.json').write_bytes(encoded(dict(orbit_task, max_steps=1025)))
        check('orbit_step_bound_refused', cli('orbit_step_bound', 'orbit-steps.json', expected_code=2)['status'] == 'REFUSED')
        rank_task = json.loads((root / 'examples/hidden_rank_count.json').read_bytes())
        rank_direct = cli('hidden_rank_default_direct', 'examples/hidden_rank_count.json', expected_code=3)
        check('hidden_rank_exact_iteration_exceeds_default_work', rank_direct['status'] == 'UNKNOWN')
        rank_exact = cli('hidden_rank_large_work_direct', 'examples/hidden_rank_count.json', ['--work', '20000000'])
        rank_apex = cli('hidden_rank_apex_layer', 'examples/hidden_rank_count.json',
                        ['--layer', 'apex', '--state', 'rank-state.json'])
        law = next(row for row in rank_apex['problems'][0]['attempts'] if row['strategy'] == 'law_instance')
        check('apex_law_instance_matches_exact_iteration', rank_apex['status'] == 'CHECKED_CAMPAIGN'
              and rank_exact['status'] == 'EXACT_DIRECT' and law['result']['status'] == 'CHECKED_EXACT'
              and law['result']['answer'] == rank_exact['answer'] and law['face'] == 'N'
              and law['result']['certificate']['kind'] == 'law_instance')
        check('apex_defers_exact_iteration_beyond_allocation', rank_apex['scheduling_decisions'][0]['selected'] == 'law_instance'
              and rank_apex['scheduling_decisions'][0]['deferred'] == ['auto', 'direct', 'quotient'])
        rank_replay = cli('hidden_rank_apex_restart', 'examples/hidden_rank_count.json',
                          ['--layer', 'apex', '--state', 'rank-state.json'])
        check('apex_law_instance_replayed_without_search', rank_replay['status'] == 'CHECKED_CAMPAIGN'
              and not rank_replay['executed_routes'] and rank_replay['replay_work'] > 0)
        forged_rank = json.loads((root / 'rank-state.json').read_bytes())
        rank_record = next(row for row in forged_rank['observations'] if row.get('kind') == 'apex_research')
        forged_law = next(row for row in rank_record['attempts']
                          if row['result'].get('certificate', {}).get('kind') == 'law_instance')
        forged_law['result']['answer'] += 1
        (root / 'rank-forged.json').write_bytes(encoded(forged_rank))
        rank_repaired = cli('hidden_rank_forged_answer', 'examples/hidden_rank_count.json',
                            ['--layer', 'apex', '--state', 'rank-forged.json'])
        check('apex_forged_law_answer_invalidated_and_recomputed', rank_repaired['status'] == 'CHECKED_CAMPAIGN'
              and forged_law['route_id'] in rank_repaired['invalidated_saved_routes']
              and 'law_instance' in rank_repaired['executed_routes'])
        apex_first = cli('apex_research_example', 'examples/apex_research.json', ['--state', 'apex-state.json'])
        rows = [{row['strategy']: row for row in problem['attempts']} for problem in apex_first['problems']]
        check('apex_example_settles_every_original_across_four_faces', apex_first['status'] == 'CHECKED_CAMPAIGN'
              and rows[0]['invariant_full']['result']['status'] == 'CHECKED_INVARIANT'
              and rows[1]['orbit_prefix']['result']['status'] == 'UNKNOWN'
              and rows[1]['orbit_transfer']['result']['status'] == 'CHECKED_ORBIT_EXCLUSION'
              and rows[1]['orbit_transfer']['face'] == 'E'
              and rows[2]['orbit_prefix']['result']['certificate']['kind'] == 'periodic_orbit'
              and rows[3]['original_implication']['result']['status'] == 'CHECKED_COUNTEREXAMPLE'
              and rows[3]['assumption_slices']['result']['status'] == 'CHECKED_GUARDS'
              and rows[3]['assumption_slices']['face'] == 'W'
              and rows[4]['law_instance']['result']['status'] == 'CHECKED_EXACT' and rows[4]['law_instance']['face'] == 'N'
              and {face for counts in apex_first['face_attempts'] for face, n in counts.items() if n} == {'N', 'W', 'S', 'E'})
        transferred = rows[1]['orbit_transfer']['result']['certificate']
        check('apex_transferred_law_is_the_receiving_systems_checked_law', transferred['kind'] == 'invariant_separation'
              and transferred['invariant']['polynomial'] == [[[0, 1], [1, 1]], [[3, 0], [-1, 1]]]
              and transferred['invariant']['initial_value'] == [3, 1] and transferred['target_value'] == [2, 1])
        apex_replay = cli('apex_research_restart', 'examples/apex_research.json', ['--state', 'apex-state.json'])
        check('apex_restart_rechecks_every_saved_outcome', apex_replay['status'] == 'CHECKED_CAMPAIGN'
              and not apex_replay['executed_routes'] and apex_replay['replay_work'] > 0)
        forged_apex = json.loads((root / 'apex-state.json').read_bytes())
        apex_record = next(row for row in forged_apex['observations'] if row.get('kind') == 'apex_research')
        wrong_orbit = next(row for row in apex_record['attempts']
                           if row['result'].get('certificate', {}).get('kind') == 'periodic_orbit')
        wrong_orbit['result']['status'] = 'CHECKED_ORBIT_REACHES'
        (root / 'apex-forged.json').write_bytes(encoded(forged_apex))
        apex_repaired = cli('apex_forged_orbit_status', 'examples/apex_research.json', ['--state', 'apex-forged.json'])
        check('apex_forged_orbit_status_invalidated', apex_repaired['status'] == 'CHECKED_CAMPAIGN'
              and wrong_orbit['route_id'] in apex_repaired['invalidated_saved_routes'])
        standalone_apex = root / 'apex-standalone'; standalone_apex.mkdir()
        for name in ('apex_check.py', 'recurrence_check.py', 'invariant_check.py', 'algebra_check.py'):
            (standalone_apex / name).write_bytes(files[name])
        packet = [{'task': rank_task, 'certificate': law['result']['certificate']},
                  {'task': orbit_task, 'certificate': orbit['certificate']},
                  {'task': turn, 'certificate': periodic['certificate']},
                  {'task': reaching, 'certificate': reached['certificate']}]
        drift = cli('orbit_drift_exclusion', 'examples/orbit_drift.json')
        check('orbit_drift_decides_an_invariant_free_orbit', drift['status'] == 'CHECKED_ORBIT_EXCLUSION'
              and drift['route'] == 'orbit_drift' and drift['certificate']['kind'] == 'drift_separation'
              and drift['certificate']['index'] == 40
              and [row['status'] for row in drift['faces_tried']] == ['UNKNOWN'] * 3 + ['CHECKED_ORBIT_EXCLUSION'])
        drift_task = json.loads((root / 'examples/orbit_drift.json').read_bytes())
        drift_reach = dict(drift_task, target=[[5, 1], [32, 1]])
        (root / 'drift-reach.json').write_bytes(encoded(drift_reach))
        reach_prefix = cli('orbit_drift_reachable_prefix', 'drift-reach.json')
        drift_reach_certificate = {'kind': 'drift_separation', 'task_id': reach_prefix['task_id'],
                                   'clocked': drift['certificate']['clocked'], 'index': 5}
        (root / 'drift-negative.json').write_bytes(encoded(dict(drift_task, target=[[-3, 1], [7, 1]])))
        negative = cli('orbit_drift_negative_index', 'drift-negative.json')
        check('orbit_drift_negative_index_excludes', negative['status'] == 'CHECKED_ORBIT_EXCLUSION'
              and negative['certificate']['kind'] == 'drift_separation' and 'index' not in negative['certificate'])
        packet.append({'task': drift_task, 'certificate': drift['certificate']})
        packet.append({'task': drift_reach, 'certificate': drift_reach_certificate})
        (standalone_apex / 'evidence.json').write_bytes(encoded(packet))
        apex_standalone_code = standalone_code.replace("'recursive_check.py'", "'apex_check.py'")
        began = time.perf_counter_ns()
        apex_standalone = subprocess.run([python, '-I', '-B', '-X', 'utf8', '-c', apex_standalone_code],
            cwd=standalone_apex, capture_output=True, text=True, encoding='utf-8', timeout=90,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        receipt['cli_runs'].append({'case': 'apex_standalone_certificates', 'returncode': apex_standalone.returncode,
            'elapsed_ns': time.perf_counter_ns() - began, 'stderr': apex_standalone.stderr})
        apex_checks = json.loads(apex_standalone.stdout)
        check('apex_certificates_replay_with_only_checkers', apex_standalone.returncode == 0 and not apex_standalone.stderr
              and [row['ok'] for row in apex_checks] == [True] * 6
              and apex_checks[0]['answer'] == rank_exact['answer']
              and [row.get('outcome') for row in apex_checks[1:]] == ['EXCLUDED', 'EXCLUDED', 'REACHES', 'EXCLUDED',
                                                                        'REACHES']
              and apex_checks[5]['kind'] == 'drift_separation')
        for label, extra, wanted in (('apex_helper_orbit', [], 'CHECKED_ORBIT_EXCLUSION'),
                                     ('apex_helper_layer', ['--layer', 'apex'], 'CHECKED_CAMPAIGN')):
            began = time.perf_counter_ns()
            process = subprocess.run([python, '-I', '-B', '-X', 'utf8', str(root / 'tools/helper_client.py'),
                'examples/orbit_exclusion.json', *extra], cwd=root, capture_output=True, text=True, encoding='utf-8',
                timeout=90, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            envelope = json.loads(process.stdout)
            receipt['cli_runs'].append({'case': label, 'returncode': process.returncode, 'status': envelope.get('status'),
                                       'elapsed_ns': time.perf_counter_ns() - began, 'stderr': process.stderr})
            check(label, process.returncode == 0 and not process.stderr and envelope.get('outcome') == 'closed'
                  and envelope.get('status') == wanted)
        involution = json.loads((root / 'examples/recursive_reverse_involution.json').read_bytes())
        accumulator = json.loads((root / 'examples/recursive_qrev.json').read_bytes())
        (root / 'apex-recursive-pair.json').write_bytes(encoded({'query': 'apex_research', 'problems': [involution, accumulator]}))
        pair = cli('apex_recursive_memory_transfer', 'apex-recursive-pair.json', ['--state', 'apex-recursive.json'])
        pair_rows = [{row['strategy']: row for row in problem['attempts']} for problem in pair['problems']]
        check('apex_recursive_proof_seeds_same_definition_question', pair['status'] == 'CHECKED_CAMPAIGN'
              and pair_rows[0]['recursive_residual']['result']['status'] == 'CHECKED_RECURSIVE_IDENTITY'
              and pair_rows[0]['recursive_seeded']['result']['status'] == 'UNKNOWN'
              and pair_rows[1]['recursive_seeded']['face'] == 'E'
              and pair_rows[1]['recursive_seeded']['result']['status'] == 'CHECKED_RECURSIVE_IDENTITY')
        pair_replay = cli('apex_recursive_memory_restart', 'apex-recursive-pair.json', ['--state', 'apex-recursive.json'])
        check('apex_recursive_transfer_replayed_on_original', pair_replay['status'] == 'CHECKED_CAMPAIGN'
              and not pair_replay['executed_routes'] and pair_replay['replay_work'] > 0)
        # Generation 16: the seven syntheses proposed by the pyramid, each against an independent computation.
        def avoiders(patterns, length):
            keep = max(len(w) for w in patterns) - 1; counts = {'': 1}
            for _ in range(length):
                following = {}
                for tail, count in counts.items():
                    for letter in '01':
                        word = tail + letter
                        if any(word.endswith(w) for w in patterns): continue
                        following[word[-keep:]] = following.get(word[-keep:], 0) + count
                counts = following
            return sum(counts.values())
        word_patterns = ['0110', '111']
        word_law = cli('word_count_law', 'examples/word_count.json', ['--state', 'word-state.json'])
        check('word_count_law_matches_independent_count', word_law['status'] == 'CHECKED_EXACT'
              and word_law['route'] == 'word_count_law' and word_law['face'] == 'N'
              and word_law['certificate']['kind'] == 'word_count_law'
              and word_law['answer'] == avoiders(word_patterns, 5000))
        word_again = cli('word_count_law_restart', 'examples/word_count.json', ['--state', 'word-state.json'])
        check('word_count_law_replayed', word_again.get('reused_after_fresh_check') is True
              and word_again['answer'] == word_law['answer'])
        forged_words = json.loads((root / 'word-state.json').read_bytes())
        next(row for row in forged_words['observations'] if row.get('kind') == 'count_word_avoiders')['answer'] += 1
        (root / 'word-forged.json').write_bytes(encoded(forged_words))
        word_repaired = cli('word_count_forged_answer', 'examples/word_count.json', ['--state', 'word-forged.json'])
        check('word_count_forged_answer_not_reused', not word_repaired.get('reused_after_fresh_check')
              and word_repaired['answer'] == word_law['answer'])
        (root / 'word-short.json').write_bytes(encoded({'query': 'count_word_avoiders', 'patterns': word_patterns,
                                                        'length': 12}))
        word_short = cli('word_count_short_direct', 'word-short.json')
        check('word_count_short_length_iterates_first', word_short['status'] == 'EXACT_DIRECT'
              and word_short['route'] == 'word_count_direct' and word_short['answer'] == avoiders(word_patterns, 12))

        def series(numerator, denominator, count):
            P = [Fraction(a, b) for a, b in numerator]; Q = [Fraction(a, b) for a, b in denominator]; out = []
            for k in range(count):
                value = (P[k] if k < len(P) else 0) - sum(Q[j] * out[k - j] for j in range(1, min(k, len(Q) - 1) + 1))
                out.append(value / Q[0])
            return out
        series_result = cli('generating_function', 'examples/generating_function.json', ['--state', 'series-state.json'])
        check('generating_function_expands_to_independent_counts',
              series_result['status'] == 'CHECKED_GENERATING_FUNCTION'
              and series_result['certificate']['kind'] == 'rational_generating_function'
              and series(series_result['numerator'], series_result['denominator'], 40)
                  == [avoiders(word_patterns, h) for h in range(40)])
        forged_series = json.loads((root / 'series-state.json').read_bytes())
        saved_series = next(row for row in forged_series['observations']
                            if row.get('kind') == 'discover_generating_function')
        saved_series['certificate']['numerator'][0] = [2, 1]
        (root / 'series-forged.json').write_bytes(encoded(forged_series))
        series_repaired = cli('generating_function_forged', 'examples/generating_function.json',
                              ['--state', 'series-forged.json'])
        check('generating_function_forged_numerator_not_reused', not series_repaired.get('reused_after_fresh_check')
              and series_repaired['numerator'] == series_result['numerator'])
        minimal = cli('minimal_recurrence', 'examples/minimal_recurrence.json')
        terms = [2 * 2 ** h + 3 ** h for h in range(3)]
        check('minimal_recurrence_below_carrier_dimension', minimal['status'] == 'CHECKED_MINIMAL_RECURRENCE'
              and minimal['check']['order'] == 2 and minimal['face'] == 'W'
              and [Fraction(*c) for c in minimal['certificate']['recurrence']['coefficients']] == [-6, 5]
              and terms[1] * terms[1] != terms[0] * terms[2])
        word_minimal = dict(json.loads((root / 'examples/generating_function.json').read_bytes()),
                            query='certify_minimal_recurrence')
        (root / 'word-minimal.json').write_bytes(encoded(word_minimal))
        word_order = cli('minimal_word_recurrence', 'word-minimal.json')
        word_terms = [avoiders(word_patterns, h) for h in range(12)]

        def singular(order):
            rows = [[Fraction(word_terms[i + j]) for j in range(order)] for i in range(order)]
            for k in range(order):
                pivot = next((i for i in range(k, order) if rows[i][k]), None)
                if pivot is None: return True
                rows[k], rows[pivot] = rows[pivot], rows[k]
                for i in range(k + 1, order):
                    factor = rows[i][k] / rows[k][k]
                    rows[i] = [a - factor * b for a, b in zip(rows[i], rows[k])]
            return False
        check('minimal_word_recurrence_hankel_independently_nonsingular',
              word_order['status'] == 'CHECKED_MINIMAL_RECURRENCE' and word_order['check']['order'] == 6
              and not singular(6))
        lift_task = json.loads((root / 'examples/recursive_lift.json').read_bytes())
        lift = cli('apex_recursive_refutation_lift', 'examples/recursive_lift.json', ['--state', 'lift-state.json'])
        lift_rows = [{row['strategy']: row for row in problem['attempts']} for problem in lift['problems']]
        (root / 'lift-general.json').write_bytes(encoded(lift_task['problems'][1]))
        general_alone = cli('recursive_generalization_alone', 'lift-general.json', ['--recursive-steps', '8'],
                            expected_code=3)
        lifted_point = lift_rows[1].get('recursive_lifted_counterexample', {}).get('result', {}).get('certificate', {})
        check('apex_lifts_instance_refutation_beyond_bounded_tests', lift['status'] == 'CHECKED_CAMPAIGN'
              and lift_rows[0]['recursive_direct']['result']['status'] == 'CHECKED_RECURSIVE_COUNTEREXAMPLE'
              and lift_rows[1]['recursive_lifted_counterexample']['face'] == 'E'
              and lifted_point.get('point') == {'x': ['succ', ['succ', ['succ', ['zero']]]], 'y': ['zero']}
              and general_alone['status'] == 'UNKNOWN')
        lift_replay = cli('apex_recursive_lift_restart', 'examples/recursive_lift.json', ['--state', 'lift-state.json'])
        check('apex_lifted_refutation_replayed', lift_replay['status'] == 'CHECKED_CAMPAIGN'
              and not lift_replay['executed_routes'])
        cli('premise_lift_source', 'examples/premise_lift_source.json', ['--state', 'premise-lift.json'])
        premise_args = ['--state', 'premise-lift.json', '--proof-policy', 'obligations']
        premise_lift = cli('premise_lift_receiving', 'examples/premise_lift_receiving.json', premise_args)
        check('obligation_premise_refutation_lifts_to_parent', premise_lift['status'] == 'CHECKED_COUNTEREXAMPLE'
              and premise_lift.get('proof_method') == 'lifted_premise_counterexample'
              and [e['role'] for e in premise_lift['obligations']['executed']]
                  == ['required_premise', 'lifted_parent_refutation']
              and premise_lift['certificate']['point'] == [[1, 1], [0, 1]])
        premise_again = cli('premise_lift_restart', 'examples/premise_lift_receiving.json', premise_args)
        check('obligation_lifted_parent_replayed', premise_again['status'] == 'CHECKED_COUNTEREXAMPLE'
              and not premise_again['obligations']['executed'])
        level_state = json.loads((root / 'apex-state.json').read_bytes())
        level_rows = [row for row in level_state['observations'] if row.get('kind') == 'polynomial_consequence'
                      and row['task']['variables'][-1] == 'level']
        standalone_level = root / 'level-standalone'; standalone_level.mkdir()
        (standalone_level / 'algebra_check.py').write_bytes(files['algebra_check.py'])
        (standalone_level / 'evidence.json').write_bytes(encoded([{'task': row['task'], 'certificate': row['certificate']}
                                                                  for row in level_rows]))
        level_run = subprocess.run([python, '-I', '-B', '-X', 'utf8', '-c',
                                    standalone_code.replace("'recursive_check.py'", "'algebra_check.py'")],
                                   cwd=standalone_level, capture_output=True, text=True, encoding='utf-8', timeout=90,
                                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        level_checks = json.loads(level_run.stdout) if level_run.returncode == 0 else []
        receipt['cli_runs'].append({'case': 'level_set_lemmas_standalone', 'returncode': level_run.returncode,
                                   'stderr': level_run.stderr})
        check('apex_invariants_stored_as_checked_level_set_lemmas', len(level_rows) >= 1 and not level_run.stderr
              and len(level_checks) == len(level_rows) and all(row['ok'] for row in level_checks))
        began = time.perf_counter_ns()
        process = subprocess.run([python, '-I', '-B', '-X', 'utf8', str(root / 'tools/helper_client.py'),
            'examples/generating_function.json'], cwd=root, capture_output=True, text=True, encoding='utf-8',
            timeout=90, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        envelope = json.loads(process.stdout)
        receipt['cli_runs'].append({'case': 'apex_helper_series', 'returncode': process.returncode,
                                   'status': envelope.get('status'), 'elapsed_ns': time.perf_counter_ns() - began})
        check('apex_helper_series_closed', process.returncode == 0 and envelope.get('outcome') == 'closed'
              and envelope.get('status') == 'CHECKED_GENERATING_FUNCTION')
        # The last two pyramid proposals: ranking exclusion and reduced generating functions.
        ranking = cli('orbit_ranking_exclusion', 'examples/orbit_ranking.json', ['--state', 'ranking-state.json'])
        ranking_task = json.loads((root / 'examples/orbit_ranking.json').read_bytes())
        orbit_states = [(Fraction(0), Fraction(2))]
        for _ in range(10):
            x, y = orbit_states[-1]; orbit_states.append((x + y * y + 1, y * y))
        sample = [(Fraction(a, b), Fraction(c, d)) for a, b, c, d in
                  ((3, 1, -7, 2), (-5, 3, 11, 4), (13, 7, 0, 1), (-2, 9, -1, 5), (8, 11, 17, 3), (0, 1, 1, 1))]
        check('orbit_ranking_decides_where_other_faces_fail', ranking['status'] == 'CHECKED_ORBIT_EXCLUSION'
              and ranking['route'] == 'orbit_ranking' and ranking['face'] == 'N'
              and ranking['certificate']['kind'] == 'ranking_separation'
              and ranking['certificate']['ranking'] == [[[1, 0], [1, 1]]] and ranking['certificate']['prefix'] == 10
              and [row['status'] for row in ranking['faces_tried']] == ['UNKNOWN'] * 4 + ['CHECKED_ORBIT_EXCLUSION']
              and all((x + y * y + 1) - x == 1 + y * y for x, y in sample)
              and (Fraction(10), Fraction(3)) not in orbit_states
              and all(b[0] > a[0] for a, b in zip(orbit_states, orbit_states[1:])))
        (root / 'ranking-negative.json').write_bytes(encoded(dict(ranking_task, target=[[-3, 1], [7, 1]])))
        ranking_negative = cli('orbit_ranking_negative_gap', 'ranking-negative.json')
        check('orbit_ranking_negative_gap_excludes_without_iteration',
              ranking_negative['status'] == 'CHECKED_ORBIT_EXCLUSION' and ranking_negative['route'] == 'orbit_ranking'
              and ranking_negative['certificate']['prefix'] == 0)
        forged_ranking = json.loads((root / 'ranking-state.json').read_bytes())
        next(row for row in forged_ranking['observations']
             if row.get('kind') == 'prove_orbit_exclusion')['certificate']['floor'] = [2, 1]
        (root / 'ranking-forged.json').write_bytes(encoded(forged_ranking))
        ranking_repaired = cli('orbit_ranking_forged_floor', 'examples/orbit_ranking.json', ['--state', 'ranking-forged.json'])
        check('orbit_ranking_forged_floor_not_reused', not ranking_repaired.get('reused_after_fresh_check')
              and ranking_repaired['certificate'] == ranking['certificate'])
        eventual = cli('eventual_recurrence', 'examples/eventual_recurrence.json', ['--state', 'eventual-state.json'])
        carrier_terms = []; row = [1, 0]
        for _ in range(40):
            carrier_terms.append(row[0] * 5 + row[1]); row = [0, row[0] + 2 * row[1]]
        check('eventual_recurrence_below_all_index_order', eventual['status'] == 'CHECKED_EVENTUAL_RECURRENCE'
              and eventual['face'] == 'W' and eventual['check']['order'] == 1 and eventual['check']['start'] == 2
              and eventual['check']['all_index_order'] == 2 and eventual['check']['coefficients'] == [[2, 1]]
              and carrier_terms[:4] == [5, 1, 2, 4] and carrier_terms[1] != 2 * carrier_terms[0]
              and all(carrier_terms[h] == 2 * carrier_terms[h - 1] for h in range(2, 40)))
        (root / 'eventual-words.json').write_bytes(encoded({'query': 'certify_eventual_recurrence', 'patterns': word_patterns}))
        eventual_words = cli('eventual_word_recurrence', 'eventual-words.json')
        counts = [avoiders(word_patterns, h) for h in range(60)]
        check('eventual_word_recurrence_is_fibonacci_from_six', eventual_words['status'] == 'CHECKED_EVENTUAL_RECURRENCE'
              and eventual_words['check']['order'] == 2 and eventual_words['check']['start'] == 6
              and eventual_words['check']['all_index_order'] == 6
              and eventual_words['check']['coefficients'] == [[1, 1], [1, 1]]
              and all(counts[h] == counts[h - 1] + counts[h - 2] for h in range(6, 60))
              and counts[5] != counts[4] + counts[3])
        forged_eventual = json.loads((root / 'eventual-state.json').read_bytes())
        next(row for row in forged_eventual['observations']
             if row.get('kind') == 'certify_eventual_recurrence')['certificate']['bezout'][0] = [[3, 1]]
        (root / 'eventual-forged.json').write_bytes(encoded(forged_eventual))
        eventual_repaired = cli('eventual_recurrence_forged_bezout', 'examples/eventual_recurrence.json',
                                ['--state', 'eventual-forged.json'])
        check('eventual_recurrence_forged_bezout_not_reused', not eventual_repaired.get('reused_after_fresh_check')
              and eventual_repaired['certificate'] == eventual['certificate'])
        diagonal = dict(json.loads((root / 'examples/minimal_recurrence.json').read_bytes()),
                        query='certify_eventual_recurrence')
        (root / 'eventual-diagonal.json').write_bytes(encoded(diagonal))
        reduced = cli('eventual_recurrence_diagonal', 'eventual-diagonal.json')['certificate']
        # (x-5)(x^2-5x+6): an order-3 all-index law of 2*2**h+3**h whose P/Q shares the factor 1-5x.
        widened = dict(reduced, common=[[1, 1], [-5, 1]],
                       recurrence=dict(reduced['recurrence'], order=3, coefficients=[[30, 1], [-31, 1], [10, 1]],
                                       initial_terms=[[3, 1], [7, 1], [17, 1]]))
        reaching_ranking = dict(ranking_task, target=[[5, 1], [4, 1]])
        standalone_series = root / 'apex-standalone-series'; standalone_series.mkdir()
        for name in ('apex_check.py', 'recurrence_check.py', 'invariant_check.py', 'algebra_check.py'):
            (standalone_series / name).write_bytes(files[name])
        (root / 'ranking-reach.json').write_bytes(encoded(reaching_ranking))
        reached_by_prefix = cli('orbit_ranking_reachable_target', 'ranking-reach.json')
        (standalone_series / 'evidence.json').write_bytes(encoded([
            {'task': ranking_task, 'certificate': ranking['certificate']},
            {'task': reaching_ranking, 'certificate': dict(ranking['certificate'], prefix=5,
                                                           task_id=reached_by_prefix['task_id'])},
            {'task': diagonal, 'certificate': widened}]))
        began = time.perf_counter_ns()
        series_standalone = subprocess.run([python, '-I', '-B', '-X', 'utf8', '-c', apex_standalone_code],
            cwd=standalone_series, capture_output=True, text=True, encoding='utf-8', timeout=90,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        receipt['cli_runs'].append({'case': 'apex_standalone_ranking_and_reduction',
            'returncode': series_standalone.returncode, 'elapsed_ns': time.perf_counter_ns() - began,
            'stderr': series_standalone.stderr})
        series_checks = json.loads(series_standalone.stdout)
        check('ranking_and_reduced_fraction_replay_with_only_checkers', series_standalone.returncode == 0
              and not series_standalone.stderr and [row['ok'] for row in series_checks] == [True] * 3
              and [row.get('outcome') for row in series_checks[:2]] == ['EXCLUDED', 'REACHES']
              and series_checks[1]['index'] == 1 and reached_by_prefix['status'] == 'CHECKED_ORBIT_REACHES'
              and (series_checks[2]['order'], series_checks[2]['all_index_order']) == (2, 3))
        # The typed language, its move bench and the autonomous agent.
        check('capabilities_agent_interface', 'autonomous_research' in capabilities.get('queries', [])
              and capabilities.get('agent', {}).get('problem_types')
                  == ['unit_fraction_cover', 'descent_cover', 'decide', 'explore']
              and 'language' in capabilities)
        bench = cli('move_bench', '--move-bench')
        check('move_bench_every_operator_observed', bench['status'] == 'MOVE_BENCH' and bench['ok'] is True
              and bench['operators'] >= 150 and bench['passed'] == bench['operators']
              and all(row['observed'] == row['dirs'] and row['fixtures'] >= 1 for row in bench['rows']))
        check('pyramid_language_at_least_100_per_direction', all(pyramid['face_counts'][d] >= 100 for d in 'NWSE')
              and pyramid['language']['operators'] == bench['operators']
              and sum(1 for row in pyramid['base'] if row['layer'] == 'lexicon') == bench['operators'])
        tampered_ops = root / 'ops-tamper'; tampered_ops.mkdir()
        for name in RUNTIME:
            (tampered_ops / name).write_bytes(files[name])
        (tampered_ops / 'ops_egypt.py').write_bytes(files['ops_egypt.py'].replace(
            b"@op('egypt_zero_class', 'SE'", b"@op('egypt_zero_class', 'NSE'"))
        began = time.perf_counter_ns()
        tamper_bench = subprocess.run([python, '-I', '-B', '-X', 'utf8', str(tampered_ops / 'ember.py'), '--move-bench'],
                                      cwd=tampered_ops, capture_output=True, text=True, encoding='utf-8', timeout=120,
                                      creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        tamper_rows = {row['name']: row for row in json.loads(tamper_bench.stdout)['rows']}
        receipt['cli_runs'].append({'case': 'move_bench_tampered_directions', 'returncode': tamper_bench.returncode,
                                   'elapsed_ns': time.perf_counter_ns() - began})
        check('move_bench_rejects_unobserved_declared_direction', tamper_bench.returncode == 2 and not tamper_bench.stderr
              and tamper_rows['egypt_zero_class']['ok'] is False and tamper_rows['egypt_zero_class']['observed'] == 'SE')
        small = cli('agent_unit_fraction_small', 'examples/agent_unit_fraction_small.json',
                    ['--state', 'agent-small.json', '--work', '400000000'], expected_code=3)
        levels = {row['modulus']: row for row in small['goal']['levels']}
        squares = lambda M: sorted({x * x % M for x in range(M) if __import__('math').gcd(x, M) == 1})
        check('agent_small_cover_leaves_exactly_the_square_classes', small['status'] == 'UNKNOWN'
              and levels[24]['uncovered_coprime'] == squares(24) and levels[120]['uncovered_coprime'] == squares(120)
              and levels[24]['uncovered'] == 1 and levels[120]['uncovered'] == 2
              and levels[24]['square_pattern'] == {'status': 'checked'}
              and levels[120]['square_pattern'] == {'status': 'checked'}
              and {row['kind'] for row in small['results']} >= {'cover', 'pattern', 'density', 'finite'}
              and any(row['kind'] == 'finite' and row['lo'] == 2 and row['hi'] == 2000 for row in small['results'])
              and len(small['invented_moves']) >= 1)
        again = cli('agent_unit_fraction_resume', 'examples/agent_unit_fraction_small.json',
                    ['--state', 'agent-small.json', '--work', '400000000'], expected_code=3)
        check('agent_resume_rechecks_saved_objects', again['replayed_objects'] > 0 and again['invalidated_objects'] == 0
              and again['moves_executed'] < small['moves_executed']
              and [row['covered'] for row in again['goal']['levels']] == [row['covered'] for row in small['goal']['levels']])
        forged_agent = json.loads((root / 'agent-small.json').read_bytes())
        agent_record = next(row for row in forged_agent['observations'] if row.get('kind') == 'autonomous_research')
        saved_cover = next(row for row in agent_record['objects'] if row['kind'] == 'cover')
        saved_family = saved_cover['data']['entries'][0]['family']
        if 'x' in saved_family: saved_family['x'][0] = ['num', 1, 1]
        elif 's' in saved_family: saved_cover['data']['shapes'][saved_family['s']][0] = [[1, 1]]
        else: saved_family['p'][1] += 1
        (root / 'agent-forged.json').write_bytes(encoded(forged_agent))
        forged_run = cli('agent_forged_cover', 'examples/agent_unit_fraction_small.json',
                         ['--state', 'agent-forged.json', '--work', '400000000'], expected_code=3)
        check('agent_forged_saved_cover_refused', forged_run['invalidated_objects'] >= 1
              and [row['covered'] for row in forged_run['goal']['levels']] == [row['covered'] for row in small['goal']['levels']])
        standalone_lexicon = root / 'lexicon-standalone'; standalone_lexicon.mkdir()
        for name in ('lexicon_check.py', 'recurrence_check.py'):
            (standalone_lexicon / name).write_bytes(files[name])
        saved_objects = [row for row in json.loads((root / 'agent-small.json').read_bytes())['observations']
                         if row.get('kind') == 'autonomous_research'][0]['objects']
        def by_digest(kind):
            return {hashlib.sha256(json.dumps(row['data'], sort_keys=True, separators=(',', ':')).encode()).hexdigest():
                    row['data'] for row in saved_objects if row['kind'] == kind}
        saved_covers = by_digest('cover')

        def with_cover(data):
            if 'cover_ref' in data:
                data = dict({k: v for k, v in data.items() if k != 'cover_ref'}, cover=saved_covers[data['cover_ref']])
            return data
        # A saved range may itself name its cover; the theorem names the range by the digest of its full form.
        saved_ranges = {hashlib.sha256(json.dumps(with_cover(row['data']), sort_keys=True, separators=(',', ':')).encode())
                        .hexdigest(): with_cover(row['data']) for row in saved_objects if row['kind'] == 'finite'}

        def expand(row):
            # Compact claims name their cover or range by digest; expanding a reference is plumbing, the checker decides.
            data = with_cover(row['data'])
            if 'finite_ref' in data:
                data = dict({k: v for k, v in data.items() if k != 'finite_ref'}, finite=saved_ranges[data['finite_ref']])
            return dict(kind=row['kind'], data=data)
        expanded_objects = [expand(row) for row in saved_objects if row['kind'] not in ('template', 'cover_tree')]
        (standalone_lexicon / 'evidence.json').write_bytes(encoded(expanded_objects))
        lexicon_code = r'''import json, pathlib, runpy
root = pathlib.Path.cwd()
checker = runpy.run_path(str(root / 'lexicon_check.py'))
class Budget:
    def __init__(self): self.work = 0
    def use(self, n=1):
        self.work += n
        if self.work > 50000000: raise RuntimeError('standalone replay work limit')
print(json.dumps([checker['check'](row['kind'], row['data'], Budget())['kind']
                  for row in json.loads((root / 'evidence.json').read_text(encoding='utf-8'))]))
'''
        began = time.perf_counter_ns()
        lexicon_run = subprocess.run([python, '-I', '-B', '-X', 'utf8', '-c', lexicon_code], cwd=standalone_lexicon,
                                     capture_output=True, text=True, encoding='utf-8', timeout=120,
                                     creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        receipt['cli_runs'].append({'case': 'agent_objects_standalone', 'returncode': lexicon_run.returncode,
                                   'elapsed_ns': time.perf_counter_ns() - began, 'stderr': lexicon_run.stderr})
        replayed_kinds = json.loads(lexicon_run.stdout) if lexicon_run.returncode == 0 else []
        check('agent_saved_evidence_replays_with_checker_only', lexicon_run.returncode == 0 and not lexicon_run.stderr
              and {'cover', 'finite', 'pattern', 'theorem'} <= set(replayed_kinds)
              and bool({'nofamily', 'obstruction'} & set(replayed_kinds)))
        collatz = cli('agent_collatz', 'examples/agent_collatz.json', ['--work', '2000000000'], expected_code=3)

        def open_classes(k):
            count = 0
            for r in range(2 ** k):
                n, odd, contracted = r, 0, False
                for i in range(1, k + 1):
                    if n % 2: odd += 1; n = (3 * n + 1) // 2
                    else: n //= 2
                    if 3 ** odd < 2 ** i: contracted = True; break
                count += not contracted
            return count
        check('agent_collatz_open_classes_match_independent_count',
              [row['open'] for row in collatz['goal']['levels']] == [open_classes(k) for k in range(1, 11)]
              and any(row['kind'] == 'cfinite' and row['hi'] == 20000 for row in collatz['results'])
              and any(row['kind'] == 'dcover' and row['modulus'] == 1024 and row['covered'] == 1024 - open_classes(10)
                      for row in collatz['results']))
        decided = cli('agent_decide_false_law', 'examples/agent_decide.json')
        check('agent_decides_false_claim_by_checked_refutation', decided['status'] == 'CHECKED_RESEARCH'
              and decided['goal'] == {'claim_status': 'refuted', 'claim_kind': 'law'} and decided['refutations'] == 1)
        explored = cli('agent_explore_words', 'examples/agent_explore.json')
        check('agent_explore_finds_checked_law_gf_period', explored['status'] == 'CHECKED_RESEARCH'
              and set(explored['goal']['found'][0]['checked_kinds']) >= {'law', 'gf', 'period'})
        # The campaign loop: her own refinement choice, certified walls, mined failures, the independent
        # three-valued verdict, and strategies carried to the related problem she offers.
        lifted = cli('agent_choose_lift', 'examples/agent_choose_lift.json', ['--state', 'lift-state.json'], expected_code=3)
        lift_levels = {row['modulus']: row for row in lifted['goal']['levels']}
        squares_120 = sorted({x * x % 120 for x in range(120) if gcd(x, 120) == 1})
        check('agent_chooses_refinement_prime_and_certifies_walls', sorted(lift_levels) == [24, 120]
              and lift_levels[120]['chosen_by'] == 'agent' and lift_levels[120]['uncovered_coprime'] == squares_120 == [1, 49]
              and (lift_levels[120]['certified_walls'] == 2 or lift_levels[120]['obstruction']['status'] == 'checked')
              and lift_levels[120]['signature_pattern'] == {'status': 'checked', 'primes': []}
              and lift_levels[120]['local_images'] == {'3': [1], '5': [1, 4], '8': [1]})
        theorem = next((row for row in lifted['results'] if row['kind'] == 'theorem' and row['modulus'] == 120), {})
        check('agent_states_reduction_theorem', theorem.get('open_residues') == len(squares_120) == 2
              and theorem.get('open_coprime') == 2 and theorem.get('lo') == 2 and theorem.get('range_hi') == 2000)
        example = lifted['failures']['examples'][0]
        check('agent_reports_mined_failures', lifted['failures']['profile']['nonresidue_signatures'] == {'square': 2}
              and ('egypt_classical_family' in example['moves'] and 'classical miss' in example['residuals']
                   or example['settled_by'] == 'obstruction lemma'))
        verdict_path = str(root / 'tools' / 'verdict.py')

        def verdict_run(label, state):
            began = time.perf_counter_ns()
            run = subprocess.run([python, '-I', '-B', '-X', 'utf8', verdict_path, state], cwd=root, capture_output=True,
                                 text=True, encoding='utf-8', timeout=300, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            receipt['cli_runs'].append({'case': label, 'returncode': run.returncode, 'elapsed_ns': time.perf_counter_ns() - began,
                                       'stderr': run.stderr})
            return run.returncode, json.loads(run.stdout)
        code, verdict = verdict_run('verdict_agent_state', 'lift-state.json')
        check('verdict_verifies_every_saved_claim', code == 0 and verdict['bit'] == 'verified' and verdict['self_test']['ok']
              and verdict['counts']['VERIFIED'] >= 9 and not verdict['counts']['REFUTED'] and not verdict['counts']['UNRESOLVED']
              and verdict['walls']['total'] == verdict['walls']['verified']
              and (verdict['walls']['total'] > 0 or any(row['kind'] == 'obstruction' and row['verdict'] == 'VERIFIED'
                                                        for row in verdict['claims']))
              and {row['kind'] for row in verdict['claims']} >= {'cover', 'finite', 'pattern', 'density', 'theorem'})
        forged_lift = json.loads((root / 'lift-state.json').read_bytes())
        lift_record = next(row for row in forged_lift['observations'] if row.get('kind') == 'autonomous_research')
        forged_cover = next(row for row in lift_record['objects'] if row['kind'] == 'cover')['data']
        forged_family = forged_cover['entries'][0]['family']
        if 'x' in forged_family: forged_family['x'][1] = ['num', 7, 1]
        elif 's' in forged_family: forged_cover['shapes'][forged_family['s']][1] = [[7, 1]]
        else: forged_family['p'][1] += 1
        # A forged wall, or the lemma claimed for 5/n, where Type II (1,1,1) reaches the square class 4 mod 5.
        forged_walls = next((row for row in lift_record['objects'] if row['kind'] == 'nofamily'), None)
        if forged_walls: forged_walls['data']['rs'] = sorted(set(forged_walls['data']['rs']) | {11})
        else: next(row for row in lift_record['objects'] if row['kind'] == 'obstruction' and row['data']['m'] % 5 == 0
                   )['data']['a'] = 5
        (root / 'lift-forged.json').write_bytes(encoded(forged_lift))
        code, forged_verdict = verdict_run('verdict_forged_state', 'lift-forged.json')
        check('verdict_refutes_forged_claims', code == 3 and forged_verdict['bit'] == 'no, keep thinking'
              and forged_verdict['counts']['REFUTED'] >= 2
              and any(row['kind'] in ('nofamily', 'obstruction') and row['verdict'] == 'REFUTED'
                      for row in forged_verdict['claims']))
        resumed = cli('agent_choose_lift_resume', 'examples/agent_choose_lift.json', ['--state', 'lift-state.json'],
                      expected_code=3)
        resumed_levels = {row['modulus']: row for row in resumed['goal']['levels']}
        check('agent_resume_keeps_her_refinement_tree', sorted(resumed_levels) == [24, 120]
              and resumed_levels[120]['chosen_by'] == 'agent' and resumed_levels[120]['uncovered_coprime'] == [1, 49]
              and resumed['replayed_objects'] > 0 and resumed['invalidated_objects'] == 0
              and resumed['moves_executed'] < lifted['moves_executed'])
        related = dict(json.loads((root / 'examples/agent_choose_lift.json').read_bytes()), problem=lifted['related_problems'][0])
        (root / 'lift-related.json').write_bytes(encoded(related))
        carried = cli('agent_related_problem', 'lift-related.json', ['--state', 'lift-state.json'], expected_code=3)
        check('strategy_library_carries_to_related_problem', lifted['related_problems'][0]['a'] == 5
              and carried['problem']['a'] == 5 and carried['strategy_library']['reports_loaded'] > 0
              and carried['strategy_library']['entries'] >= lifted['strategy_library']['entries'])
        # Instruments from Campaigns 1 and 2: sieved covers, the per-class theorem chain, the pruned wall search and
        # the retirement policy, each checked against an independent computation.
        sieve_code = r"""import json, pathlib, runpy, sys
from math import gcd
root = pathlib.Path.cwd()
ember = runpy.run_path(str(root / 'ember.py'))
L = ember['local_module']('lexicon'); C = ember['local_module']('lexicon_check')
sys.path.insert(0, str(root / 'tools')); import verdict as V
registry, fixtures = L.load_ops()
rt = L.Runtime(C, ember['Budget'](10 ** 10))
E = registry['egypt_cover_assemble']['fn'].__globals__
fams = E['_classical_families'](rt, 9240, [r for r in range(1, 9240, 7) if gcd(r, 9240) == 1][:160])
plain = E['assemble'](fams, 4, 3, 9240); sieved = dict(plain, chain=[840, 9240])
class B:
    work = 0
    def use(self, n=1): self.work += n
b1, b2 = B(), B()
same = (C.check_cover(plain, b1)['covered'] == C.check_cover(sieved, b2)['covered']
        and C.unreached(plain, B()) == C.unreached(sieved, B()) == sorted(V.open_set(sieved)) == sorted(V.open_set(plain)))
good = dict(a=4, m=4, r=3, k0=0, x=[V.poly_node([V.F(1), V.F(1)]), V.poly_node([V.F(6), V.F(14), V.F(8)]),
                                    V.poly_node([V.F(6), V.F(14), V.F(8)])])
mixed = V.theorem_case(good, 0); mixed['finite']['cover']['entries'].append(dict(family=dict(good, k0=3)))
mixed['finite']['cover']['bound'] = 15
def admits(data):
    try: return C.check_theorem(data, B())['ok']
    except C.Invalid: return False
def admits_kind(kind, data):
    try: return C.check(kind, data, B())['ok']
    except C.Invalid: return False
theorem = (admits(mixed) and V.verdict('theorem', mixed)[0] == 'VERIFIED' and not admits(V.theorem_case(good, 5))
           and V.verdict('theorem', V.theorem_case(good, 5))[0] == 'REFUTED')
def unpruned(a, m, r, bound):
    found = []
    for D in C._divisors(m):
        if D % a: continue
        uv = D // a; e = (-r) % D or D
        found += [('II', u, uv // u, (u + uv // u) // e) for u in C._divisors(uv) if u <= uv // u and (u + uv // u) % e == 0]
    return found + [('I', u, v, w) for u in range(1, bound + 1) for v in range(u, bound + 1) for w in range(1, bound + 1)
                    if ((u + v) * m) % (a * u * v * w) == 0 and ((u + v) * r + w) % (a * u * v * w) == 0]
walls = all(C.classical_parameters(a, m, r, 30, B()) == unpruned(a, m, r, 30)
            for a, m in ((4, 840), (4, 9240), (5, 27720)) for r in (1, 11, 121, 2521 % m, 421))
A = ember['local_module']('agent'); goal = A.CoverGoal(dict(a=4, terms=3, min=2, modulus=24, lifts=[5], verify_to=100), L)
square = 'unit_fraction_cover:eclass:coprime:square'
retire = (goal.retirable(square, 'egypt_ansatz_extend') and not goal.retirable(square, 'egypt_classical_family')
          and not goal.retirable(square, 'egypt_classical_exclusion') and not goal.retirable('unit_fraction_cover:esq', 'x')
          and goal.retire_scope(dict(kind='eclass', data=dict(m=840, r=1))) == 840
          and goal.retire_scope(dict(kind='esq', data=dict(modulus=840))) is None)
complete = (C.classical_parameters(4, 1580040, 32881, 0, B())[:1] == [('I', 38, 297, 1)]
            and V.classical_hit(4, 1580040, 32881, 0) == ('I', 38, 297, 1)
            and C.classical_parameters(4, 1580040, 32881, 120, B()) == []
            and not C.classical_parameters(4, 1580040, 1, 0, B()) and V.classical_hit(4, 1580040, 1, 0) is None)
lemma = dict(a=4, terms=3, m=1580040, rule='classical_reach_nonsquare')
counter = dict(a=5, terms=3, m=840, rule='classical_reach_nonsquare')
def refutes(claim, witness):
    try: return C.check_refutation(dict(claim=dict(kind='obstruction', data=claim), witness=witness), B())['ok']
    except C.Invalid: return False
obstruction = (C.check_obstruction(lemma, B())['ok'] and V.verdict('obstruction', lemma)[0] == 'VERIFIED'
               and admits_kind('obstruction', counter) is False and V.verdict('obstruction', counter)[0] == 'REFUTED'
               and refutes(counter, dict(modulus=5, residue=4, params=['II', 1, 1, 1]))
               and not refutes(counter, dict(modulus=5, residue=3, params=['II', 1, 1, 2])))
# The state bound trims records whose claims a run carried over before the run's own evidence.
import os, tempfile, types
host = types.SimpleNamespace(canonical=ember['canonical'], STATE_LIMIT=ember['STATE_LIMIT'])
p4 = dict(type='unit_fraction_cover', a=4, terms=3); p5 = dict(p4, a=5)
def record(tid, problem, n):
    return dict(task_id=tid, kind='autonomous_research', problem=problem, tried=['t' * 40] * 200, rederivable=[], log=[],
                samples=[], objects=[dict(kind='template', data=dict(i=i, pad='x' * 400)) for i in range(n)])
def saved(carried):
    state = dict(observations=[record('old', dict(p4, extra_lifts=1), 2200)]); new = record('new', dict(p4, extra_lifts=3), 400)
    path = os.path.join(tempfile.mkdtemp(), 'state.json')
    A.save(host, state, path, new, dict(task_id=A.LIBRARY_ID, kind='strategy_library', entries=[]), carried)
    return state, new, os.path.getsize(path)
s1, n1, z1 = saved({'old'}); s2, n2, z2 = saved(set())
old1 = next(o for o in s1['observations'] if o['task_id'] == 'old')
bound = (n1['dropped_objects'] == 0 and len(n1['objects']) == 400 and 0 < len(old1['objects']) < 2200
         and old1['tried'] == [] and z1 <= host.STATE_LIMIT and n2['dropped_objects'] > 0 and z2 <= host.STATE_LIMIT)
# Her library's legacy contexts (no numerator in the name) are read as this numerator only for a one-numerator state.
lib = [dict(context='unit_fraction_cover:eclass:coprime:square', strategy='egypt_ansatz_extend', successes=0, failures=100,
            seconds=1.0),
       dict(context='unit_fraction_cover:a4:eclass:coprime:square', strategy='egypt_family_fit', successes=0, failures=70,
            seconds=1.0),
       dict(context='unit_fraction_cover:a4:eclass:coprime:square', strategy='egypt_divisor_ansatz', successes=3,
            failures=90, seconds=1.0)]
goal4 = A.CoverGoal(dict(a=4, terms=3, min=2, modulus=24, lifts=[5], verify_to=100), L)
one = dict(observations=[dict(kind='autonomous_research', task_id='x', problem=dict(p4))])
two = dict(observations=one['observations'] + [dict(kind='autonomous_research', task_id='y', problem=dict(p5))])
sq = 'unit_fraction_cover:a4:eclass:coprime:square'
first, second = A.experience_priors(goal4, lib, one, p4), A.experience_priors(goal4, lib, two, p4)
priors = (first == {(sq, 'egypt_ansatz_extend'), (sq, 'egypt_family_fit')} and (sq, 'egypt_family_fit') in second
          and (sq, 'egypt_ansatz_extend') not in second)
# A checked lemma at a multiple of m implies exactly the walls on coprime square classes modulo m.
goal120 = A.CoverGoal(dict(a=4, terms=3, min=2, modulus=120, lifts=[], verify_to=100), L)
rt2 = L.Runtime(C, ember['Budget'](10 ** 9)); goal120.init(rt2)
rt2.check(rt2.propose('obstruction', dict(a=4, terms=3, m=120, rule='classical_reach_nonsquare'))); goal120.update(rt2)
implied = (goal120.implied_wall(dict(a=4, terms=3, m=120, r=49)) and goal120.implied_wall(dict(a=4, terms=3, m=24, r=1))
           and not goal120.implied_wall(dict(a=4, terms=3, m=120, r=7))
           and not goal120.implied_wall(dict(a=4, terms=3, m=240, r=49))
           and not goal120.implied_wall(dict(a=5, terms=3, m=120, r=49)))
# Her refinement prime is chosen on exact counts: the count equals a direct search over every coprime lift.
def direct(a, M, p, xs):
    return sum(1 for x in xs for j in range(p) if gcd(x + M * j, M * p) == 1
               and E['classical_search'](a, M * p, x + M * j, 0, B()))
cases = [(a, M, [x for x in xs if gcd(x, M) == 1 and not E['classical_search'](a, M, x, 0, B())])
         for a, M, xs in ((4, 840, [1, 121, 169, 289, 361, 529]), (5, 840, list(range(1, 840, 11))), (4, 24, [1]))]
lift = all(len(xs) >= 1 for a, M, xs in cases) and all(E['lift_reach'](a, M, p, xs, B()) == direct(a, M, p, xs)
                                                     for a, M, xs in cases for p in (2, 3, 5, 7, 11, 13, 17))
# The compact proof format: identities written once in n, families named by class, threshold and identity.
pairs = [(s_, c_) for s_ in E['EXTENDED_S'] for c_ in E['EXTENDED_C']]
found = [E['ansatz'](4, 840, r_, pairs, B(), limit=1) for r_ in (11, 13, 17, 19, 23, 29, 31, 37, 41, 43)]
written = [row[0][0] for row in found if row]
written += [dict(f, m=f['m'] * 7, r=f['r'] + f['m'] * j, x=[[[c.numerator, c.denominator] for c in L.ptrim(L.at_class(
    L.in_n([V.F(n_, d_) for n_, d_ in e], f['m'], f['r']), f['m'] * 7, f['r'] + f['m'] * j))] for e in f['x']])
            for f in written[:2] for j in (1, 2)]  # the same identities restated on subclasses
compact = E['assemble']([dict(data=f) for f in written], 4, 3, 840 * 7)
full = dict({k: v for k, v in compact.items() if k != 'shapes'},
            entries=[dict(family=L.unshape(e['family'], compact.get('shapes'))) for e in compact['entries']])
forged = json.loads(json.dumps(compact)); forged['shapes'][0][0] = [[1, 1]]
compact_ok = (len(written) >= 8 and 'shapes' in compact and len(compact['shapes']) < len(compact['entries'])
              and C.check_cover(compact, B())['covered'] == C.check_cover(full, B())['covered']
              and V.verdict('cover', compact)[0] == 'VERIFIED' and len(json.dumps(compact)) < len(json.dumps(full))
              and not admits_kind('cover', forged) and V.verdict('cover', forged)[0] == 'REFUTED')
batches = A.family_batches(L, 4, 3, written)
back = [row['data'] for row in A.CoverGoal(dict(a=4, terms=3, min=2, modulus=840, lifts=[], verify_to=100), L).expand(batches)]
members = list(V.claims_of(dict(observations=[dict(kind='autonomous_research', task_id='t', objects=batches)])))
batch_ok = (all(admits_kind('ufam', b['data']) for b in batches) and back == written
            and len(members) == len(written) and all(V.verdict(k_, d_)[0] == 'VERIFIED' for _, k_, d_ in members))
print(json.dumps(dict(sieve=same, work=[b1.work, b2.work], theorem=theorem, walls=walls, retire=retire, complete=complete,
                      obstruction=obstruction, bound=bound, priors=priors, implied=implied, lift=lift,
                      compact=compact_ok, batch=batch_ok)))
"""
        began = time.perf_counter_ns()
        sieve_run = subprocess.run([python, '-I', '-B', '-X', 'utf8', '-c', sieve_code], cwd=root, capture_output=True,
                                   text=True, encoding='utf-8', timeout=300,
                                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        receipt['cli_runs'].append({'case': 'campaign_instruments_standalone', 'returncode': sieve_run.returncode,
                                   'elapsed_ns': time.perf_counter_ns() - began, 'stderr': sieve_run.stderr})
        sieve_result = json.loads(sieve_run.stdout) if sieve_run.returncode == 0 else {}
        receipt['sieve_work'] = sieve_result.get('work')
        check('sieved_cover_matches_enumeration_and_verdict', sieve_result.get('sieve') is True)
        check('theorem_chain_is_checked_class_by_class', sieve_result.get('theorem') is True)
        check('pruned_wall_search_matches_unpruned_search', sieve_result.get('walls') is True)
        check('retirement_spares_the_classical_generator_and_walls', sieve_result.get('retire') is True)
        check('complete_classical_enumeration_reaches_past_the_old_bound', sieve_result.get('complete') is True)
        check('classical_obstruction_proved_for_4_and_refuted_for_5', sieve_result.get('obstruction') is True)
        check('state_bound_trims_carried_records_before_new_evidence', sieve_result.get('bound') is True)
        check('library_priors_read_legacy_contexts_for_one_numerator', sieve_result.get('priors') is True)
        check('lemma_implies_only_square_class_walls', sieve_result.get('implied') is True)
        check('prime_choice_counts_lifts_exactly', sieve_result.get('lift') is True)
        check('compact_cover_equals_written_cover_and_refuses_a_forged_identity', sieve_result.get('compact') is True)
        check('family_batch_round_trip_and_independent_verdict', sieve_result.get('batch') is True)
        # Regression checks for defects found while cataloguing generation 15.
        shared_args = ['--state', 'shared-source-recursive.json']
        cli('shared_state_source_first', 'examples/source_research_episode.json',
            shared_args + ['--source-steps', '2', '--work', '4000000'], expected_code=3)
        cli('shared_state_standalone_recursive', 'examples/recursive_reverse_involution.json',
            shared_args + ['--recursive-steps', '1'], expected_code=3)
        shared_again = cli('shared_state_source_resumes', 'examples/source_research_episode.json',
                           shared_args + ['--source-steps', '64', '--work', '4000000'])
        check('source_episode_follows_validated_outside_native_progress',
              shared_again['status'] == 'CHECKED_SOURCE_EPISODE'
              and any(a.get('native_refreshes') for a in shared_again['source_episode']['attempts']))
        textbook = cli('recursive_residual_textbook_lemmas', 'examples/recursive_reverse_involution.json',
                       ['--recursive-steps', '64'])
        def show_term(term):
            if isinstance(term, dict):
                return term['v']
            return term[0] + ('(' + ','.join(show_term(a) for a in term[1:]) + ')' if len(term) > 1 else '')
        lemma_text = [show_term(l['goal']['lhs']) + '=' + show_term(l['goal']['rhs']) for l in textbook['certificate']['lemmas']]
        check('recursive_cursor_restarts_for_new_residual', textbook['status'] == 'CHECKED_RECURSIVE_IDENTITY'
              and 'append(append(v0,v1),v2)=append(v0,append(v1,v2))' in lemma_text
              and not any('append(nil,' in text for text in lemma_text))
        stage_code = r"""import json, pathlib, runpy
root = pathlib.Path.cwd()
ember = runpy.run_path(str(root / 'ember.py'))
engine = ember['local_module']('recursive'); checker = ember['local_module']('recursive_check')
original = engine.check_bundle; calls = []
def refuse_once(*args, **kwargs):
    calls.append(1)
    if len(calls) == 1:
        raise checker.Invalid('forced refusal of one produced proof')
    return original(*args, **kwargs)
engine.check_bundle = refuse_once
task = json.loads((root / 'examples/recursive_reverse_involution.json').read_text())
result = ember['solve'](task, 'stage-refusal-state.json', 10000000, recursive_steps=64)
state = json.loads((root / 'stage-refusal-state.json').read_text())
nodes = [n for o in state['observations'] if o.get('kind') == 'recursive_episode' for n in o['nodes'].values()]
print(json.dumps({'status': result['status'], 'calls': len(calls),
                  'closed': sum(n.get('reason', '').startswith('checker refused produced proof') for n in nodes)}))
"""
        began = time.perf_counter_ns()
        stage_run = subprocess.run([python, '-I', '-B', '-X', 'utf8', '-c', stage_code], cwd=root, capture_output=True,
                                   text=True, encoding='utf-8', timeout=90,
                                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        receipt['cli_runs'].append({'case': 'recursive_stage_checker_refusal', 'returncode': stage_run.returncode,
                                   'elapsed_ns': time.perf_counter_ns() - began, 'stderr': stage_run.stderr})
        stage_result = json.loads(stage_run.stdout)
        check('recursive_stage_checker_refusal_keeps_progress', stage_run.returncode == 0 and not stage_run.stderr
              and stage_result['status'] in ('CHECKED_RECURSIVE_IDENTITY', 'UNKNOWN') and stage_result['calls'] >= 2
              and stage_result['closed'] == 1)
        flat_seed = cli('flat_certificate_seed', 'examples/polynomial_consequence.json', ['--state', 'flat-fields.json'])
        flat_state = json.loads((root / 'flat-fields.json').read_bytes())
        next(row for row in flat_state['observations'] if row.get('certificate', {}).get('kind') == 'polynomial_combination')['certificate']['trusted'] = True
        (root / 'flat-fields-forged.json').write_bytes(encoded(flat_state))
        flat_replay = cli('flat_certificate_extra_field', 'examples/polynomial_consequence.json', ['--state', 'flat-fields-forged.json'])
        check('flat_certificate_extra_field_not_admitted', flat_seed['status'] == 'CHECKED_IMPLICATION'
              and flat_replay['status'] == 'CHECKED_IMPLICATION' and not flat_replay.get('reused_after_fresh_check')
              and 'trusted' not in flat_replay['certificate'])
        refusing = {'query': 'research_campaign', 'max_attempts': 8, 'problems': [
            {'query': 'transition_count', 'matrix': [[1, 1], [1, 0]], 'initial': [1, 0], 'terminal': [0, 1], 'horizon': 10},
            {'query': 'word_avoidance_identity', 'patterns': ['00', '10'], 'formula': 'column_shortcut', 'check_through': 8}]}
        (root / 'campaign-refusing-route.json').write_bytes(encoded(refusing))
        contained = cli('campaign_refusing_route', 'campaign-refusing-route.json', expected_code=3)
        check('campaign_refused_route_stays_local', contained['status'] == 'UNKNOWN'
              and contained['problems'][0]['attempts'][0]['result']['answer'] == 55
              and contained['problems'][1]['attempts'][0]['result']['reason'].startswith('route refused'))
        big = {'query': 'transition_count', 'matrix': [[1000000, 1000000], [1000000, 1000000]],
               'initial': [1, 0], 'terminal': [1, 1], 'horizon': 700}
        (root / 'big-answer.json').write_bytes(encoded(big))
        big_result = cli('exact_answer_beyond_default_digit_limit', 'big-answer.json')
        check('large_exact_answer_serialized', big_result['status'] == 'CHECKED_EXACT'
              and big_result['answer'] == 2 ** 700 * 10 ** 4200)
        # Child audit hook permits only relocated files and the installed interpreter
        # tree after startup. It refuses new socket use and external source reads.
        audit = r'''import os, pathlib, runpy, sys
root = pathlib.Path.cwd().resolve()
allowed = (root, pathlib.Path(sys.base_prefix).resolve(), pathlib.Path(sys.executable).resolve().parent)
def gate(event, args):
    if event.startswith('socket.'):
        raise RuntimeError('network operation refused by relocation audit')
    if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
        target = pathlib.Path(os.fsdecode(args[0])).resolve()
        if not any(target == p or p in target.parents for p in allowed):
            raise RuntimeError('external file refused by relocation audit')
sys.addaudithook(gate)
sys.argv = ['ember.py', 'examples/word_identity.json', '--state', 'audited-state.json']
runpy.run_path(str(root / 'ember.py'), run_name='__main__')
'''
        audited = subprocess.run([python, '-I', '-B', '-X', 'utf8', '-c', audit], cwd=root,
                                 capture_output=True, text=True, encoding='utf-8', timeout=90,
                                 creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        check('audited_relocated_word_cli', audited.returncode == 0 and not audited.stderr
              and json.loads(audited.stdout)['status'] == 'CHECKED_WORD_IDENTITY')
        recurrence_audit = audit.replace('examples/word_identity.json', 'examples/discover_word_recurrence.json')
        audited_recurrence = subprocess.run([python, '-I', '-B', '-X', 'utf8', '-c', recurrence_audit], cwd=root,
                                            capture_output=True, text=True, encoding='utf-8', timeout=90,
                                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        check('audited_relocated_original_recurrence_cli', audited_recurrence.returncode == 0 and not audited_recurrence.stderr
              and json.loads(audited_recurrence.stdout)['status'] == 'CHECKED_RECURRENCE')
        invariant_audit = audit.replace('examples/word_identity.json', 'examples/nonlinear_invariant.json')
        audited_invariant = subprocess.run([python, '-I', '-B', '-X', 'utf8', '-c', invariant_audit], cwd=root,
                                           capture_output=True, text=True, encoding='utf-8', timeout=90,
                                           creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        check('audited_relocated_original_invariant_cli', audited_invariant.returncode == 0 and not audited_invariant.stderr
              and json.loads(audited_invariant.stdout)['status'] == 'CHECKED_INVARIANT')
        recursive_audit = audit.replace("'examples/word_identity.json', '--state', 'audited-state.json'",
            "'examples/recursive_reverse_involution.json', '--state', 'audited-recursive-state.json', '--recursive-steps', '64'")
        for index in range(2):
            audited_recursive = subprocess.run([python, '-I', '-B', '-X', 'utf8', '-c', recursive_audit], cwd=root,
                capture_output=True, text=True, encoding='utf-8', timeout=90,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            original_result = json.loads(audited_recursive.stdout)
            check('audited_relocated_original_recursive_' + str(index), audited_recursive.returncode == 0
                  and not audited_recursive.stderr and original_result['status'] == 'CHECKED_RECURSIVE_IDENTITY'
                  and len(original_result['certificate']['lemmas']) > 0
                  and bool(original_result.get('reused_after_fresh_check')) == bool(index))
        source_audit = audit.replace("'examples/word_identity.json', '--state', 'audited-state.json'",
            "'examples/source_research_episode.json', '--state', 'audited-source-state.json', '--source-policy', 'fixed_bridge', '--source-steps', '64'")
        for index in range(2):
            began = time.perf_counter_ns()
            audited_source = subprocess.run([python, '-I', '-B', '-X', 'utf8', '-c', source_audit],
                cwd=root, capture_output=True, text=True, encoding='utf-8', timeout=90,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            source_result = json.loads(audited_source.stdout)
            receipt['cli_runs'].append({'case': 'audited_relocated_source_episode_' + str(index),
                'returncode': audited_source.returncode, 'status': source_result.get('status'),
                'elapsed_ns': time.perf_counter_ns() - began, 'stderr': audited_source.stderr})
            check('audited_relocated_source_episode_' + str(index), audited_source.returncode == 0
                  and not audited_source.stderr and source_result['status'] == 'CHECKED_SOURCE_EPISODE'
                  and len(source_result['roots']) == 2 and bool(source_result['source_episode']['bridges'])
                  and all(row['task'] == original_sources[row['task_id']]
                          and row['result']['status'] == 'CHECKED_RECURSIVE_IDENTITY' for row in source_result['roots']))
            if index:
                check('audited_source_restart_replays_without_new_invention', not source_result['source_episode']['executed'])
        localization_audit = audit.replace("'examples/word_identity.json', '--state', 'audited-state.json'",
            "'examples/localized_consequence.json', '--state', 'audited-localization-state.json', '--proof-policy', 'localized_first'")
        audited_localization = subprocess.run([python, '-I', '-B', '-X', 'utf8', '-c', localization_audit], cwd=root,
            capture_output=True, text=True, encoding='utf-8', timeout=90,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        check('audited_relocated_original_localized_cli', audited_localization.returncode == 0 and not audited_localization.stderr
              and json.loads(audited_localization.stdout)['status'] == 'CHECKED_IMPLICATION')
        guarded_seed_audit = localization_audit.replace('examples/localized_consequence.json', 'examples/localized_cancellation.json')
        guarded_seed_run = subprocess.run([python, '-I', '-B', '-X', 'utf8', '-c', guarded_seed_audit], cwd=root,
            capture_output=True, text=True, encoding='utf-8', timeout=90,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        check('audited_guarded_source_learning', guarded_seed_run.returncode == 0 and not guarded_seed_run.stderr
              and json.loads(guarded_seed_run.stdout)['status'] == 'CHECKED_IMPLICATION')
        guarded_receiving_audit = localization_audit.replace('examples/localized_consequence.json', 'examples/guarded_receiving.json').replace("'localized_first'", "'lemma_first'")
        guarded_receiving_run = subprocess.run([python, '-I', '-B', '-X', 'utf8', '-c', guarded_receiving_audit], cwd=root,
            capture_output=True, text=True, encoding='utf-8', timeout=90,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        audited_transfer = json.loads(guarded_receiving_run.stdout)
        check('audited_guarded_receiving_transfer', guarded_receiving_run.returncode == 0 and not guarded_receiving_run.stderr
              and audited_transfer['status'] == 'CHECKED_IMPLICATION' and audited_transfer['lemma_reuse']['used'] is True)
        obligation_seed_audit = audit.replace('examples/word_identity.json', 'examples/obligation_source.json')
        seed_audit_run = subprocess.run([python, '-I', '-B', '-X', 'utf8', '-c', obligation_seed_audit], cwd=root,
            capture_output=True, text=True, encoding='utf-8', timeout=90,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        check('audited_relocated_obligation_seed', seed_audit_run.returncode == 0 and not seed_audit_run.stderr
              and json.loads(seed_audit_run.stdout)['status'] == 'CHECKED_IMPLICATION')
        obligation_audit = audit.replace("'examples/word_identity.json', '--state', 'audited-state.json'",
            "'examples/obligation_receiving.json', '--state', 'audited-state.json', '--proof-policy', 'obligations', '--obligation-steps', '1'")
        for stage, expected_code in ((1, 3), (2, 0)):
            audited_stage = subprocess.run([python, '-I', '-B', '-X', 'utf8', '-c', obligation_audit], cwd=root,
                capture_output=True, text=True, encoding='utf-8', timeout=90,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            audit_result = json.loads(audited_stage.stdout)
            check('audited_relocated_obligation_stage_' + str(stage), audited_stage.returncode == expected_code
                  and not audited_stage.stderr
                  and audit_result['status'] == ('UNKNOWN' if stage == 1 else 'CHECKED_IMPLICATION'))
        apex_audit = audit.replace("'examples/word_identity.json', '--state', 'audited-state.json'",
            "'examples/apex_research.json', '--state', 'audited-apex-state.json'")
        audited_apex = subprocess.run([python, '-I', '-B', '-X', 'utf8', '-c', apex_audit], cwd=root,
            capture_output=True, text=True, encoding='utf-8', timeout=90,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        check('audited_relocated_apex_research', audited_apex.returncode == 0 and not audited_apex.stderr
              and json.loads(audited_apex.stdout)['status'] == 'CHECKED_CAMPAIGN')
        # Rebuilding from only public members must not need the development README,
        # private provenance files or an original checkout.
        rebuilt = Path(temporary) / 'rebuilt.zip'
        rebuilding = subprocess.run([python, '-I', '-B', '-X', 'utf8',
                                    str(root / 'tools/build_public_package.py'), '--output', str(rebuilt)],
                                   cwd=root, capture_output=True, text=True, encoding='utf-8', timeout=90,
                                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        check('public_tree_rebuild_exit', rebuilding.returncode == 0 and not rebuilding.stderr)
        check('public_tree_rebuild_identical', rebuilt.read_bytes() == payload)
    receipt['passed'] = len(receipt['checks'])
    receipt['failed'] = 0
    receipt['status'] = 'PASS'
    return receipt


def save_receipt(path, receipt):
    if path is None:
        return
    history = []
    if path.is_file():
        previous = json.loads(path.read_text(encoding='utf-8'))
        history = previous.get('previous_attempts', [])
        history.append({k: previous[k] for k in ('status', 'zip_sha256', 'passed', 'failed', 'error', 'checks')
                        if k in previous})
    receipt['previous_attempts'] = history
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded(receipt))


def main():
    if hasattr(sys, 'set_int_max_str_digits'):
        sys.set_int_max_str_digits(100_000)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--verify', action='store_true')
    parser.add_argument('--receipt', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output or root / 'dist/ember.zip'
    files, manifest = collect(root)
    payload = archive_bytes(files)
    receipt = {} if args.verify else None
    if args.verify:
        try:
            verify(payload, files, manifest, sys.executable, receipt)
            unchanged = collect(root)[0] == files
            receipt['checks'].append({'case': 'public_source_unchanged_during_verification', 'ok': unchanged})
            if not unchanged:
                raise RuntimeError('public source changed during verification; freeze and rebuild')
            receipt['passed'] = len(receipt['checks'])
        except Exception as exc:
            receipt.update(status='FAIL', error=type(exc).__name__ + ': ' + str(exc),
                           passed=sum(c['ok'] for c in receipt.get('checks', [])), failed=1)
            save_receipt(args.receipt, receipt)
            raise
    # Do not publish a partially verified package if verification fails.
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(payload)
    (root / 'PUBLIC_MANIFEST.json').write_bytes(files['PUBLIC_MANIFEST.json'])
    if receipt is not None:
        save_receipt(args.receipt, receipt)
    print(json.dumps({'status': 'VERIFIED' if receipt else 'BUILT_NOT_VERIFIED',
                      'version': manifest['version'], 'zip_bytes': len(payload), 'zip_sha256': sha(payload),
                      'members': len(files), 'checks_passed': receipt['passed'] if receipt else None}))


if __name__ == '__main__':
    main()
