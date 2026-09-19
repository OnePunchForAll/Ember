"""Build an explicit, deterministic Ember source package; never publish it."""
from __future__ import annotations
import argparse
import ast
import hashlib
import io
import json
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
           'recursive.py', 'recursive_check.py')
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
            'campaign_recursive_identity.json')
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
                  'tools/helper_client.py': 'tools/helper_client.py'})
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
        'python_requirement': 'External standard-library Python; tested with Python 3.14.6 on Windows only.',
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
