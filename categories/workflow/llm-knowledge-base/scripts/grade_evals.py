#!/usr/bin/env python3
"""
Grade eval runs against assertions. Correctly handles content_contains checks
by using assertion-name-based search terms, not the human-readable text field.
"""

import json
import os
import re
import sys
from glob import glob


def find_all_md_files(directory):
    """Get relative paths of all markdown files in directory."""
    files = []
    for root, dirs, fnames in os.walk(directory):
        for fname in fnames:
            if fname.endswith('.md'):
                relpath = os.path.relpath(os.path.join(root, fname), directory)
                files.append(os.path.join(directory, relpath))
    return files


def search_md_files(directory, pattern, case_sensitive=False):
    """Search all markdown files for a string or regex pattern."""
    results = []
    for fpath in find_all_md_files(directory):
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            if case_sensitive:
                if pattern in content:
                    results.append(fpath)
            else:
                if pattern.lower() in content.lower():
                    results.append(fpath)
        except:
            pass
    return results


def search_md_files_regex(directory, regex):
    """Search all markdown files using regex."""
    results = []
    for fpath in find_all_md_files(directory):
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            matches = re.findall(regex, content, re.MULTILINE | re.DOTALL)
            if matches:
                results.append({'file': fpath, 'matches': matches[:3]})
        except:
            pass
    return results


def count_in_file(filepath, pattern, case_sensitive=False):
    """Count occurrences of pattern in a file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        if case_sensitive:
            return content.count(pattern)
        return content.lower().count(pattern.lower())
    except:
        return 0


def grade_run(output_dir):
    """Grade a single eval run based on assertion names."""
    md_files = find_all_md_files(output_dir)

    # Map file paths to categories for assertion checking
    article_files = [f for f in md_files if '/articles/' in f.replace('\\', '/')]
    concept_files = [f for f in md_files if '/concepts/' in f.replace('\\', '/')]
    connection_files = [f for f in md_files if '/connections/' in f.replace('\\', '/')]
    report_files = [f for f in md_files if '/reports/' in f.replace('\\', '/')]
    slide_files = [f for f in md_files if '/slides/' in f.replace('\\', '/')]
    index_files = [f for f in md_files if '/index.md' in f.replace('\\', '/')]
    lint_files = [f for f in md_files if 'lint' in f.lower() or 'health' in f.lower()]
    all_md = md_files

    def check(condition):
        return condition, ""

    results = []

    # ---- Assertion: creates-wiki-article ----
    passed = len(article_files) > 0 or len(concept_files) > 0
    evidence = article_files[:1] + concept_files[:1]
    results.append({
        'name': 'creates-wiki-article',
        'text': 'A wiki article about MoE is created under wiki/articles/ or wiki/concepts/',
        'passed': passed,
        'evidence': [os.path.basename(e) for e in evidence[:2]] if evidence else ['No article files found']
    })

    # ---- Assertion: creates-wiki-index ----
    passed = len(index_files) > 0
    results.append({
        'name': 'creates-wiki-index',
        'text': 'A wiki index or table of contents is created (wiki/index.md or equivalent)',
        'passed': passed,
        'evidence': [os.path.basename(f) for f in index_files] if passed else ['No index found']
    })

    # ---- Assertion: uses-wiki-links ----
    found = search_md_files_regex(output_dir, r'\[\[.*?\]\]')
    results.append({
        'name': 'uses-wiki-links',
        'text': 'Articles use [[wiki-link]] syntax for cross-references',
        'passed': len(found) > 0,
        'evidence': [f['matches'][0] for f in found[:2]] if found else ['No wiki-links found']
    })

    # ---- Assertion: has-provenance ----
    found = search_md_files(output_dir, 'moe-2024')
    results.append({
        'name': 'has-provenance',
        'text': 'Wiki article links back to the raw source (moe-2024.md reference exists)',
        'passed': len(found) > 0,
        'evidence': [os.path.basename(f) for f in found[:2]] if found else ['No provenance found']
    })

    # ---- Assertion: structured-frontmatter ----
    found = search_md_files_regex(output_dir, r'^---\s*\ntitle:')
    results.append({
        'name': 'structured-frontmatter',
        'text': 'Wiki article has YAML frontmatter with title and tags',
        'passed': len(found) > 0,
        'evidence': [os.path.basename(f['file']) for f in found[:2]] if found else ['No frontmatter found']
    })

    # ---- Assertion: creates-report ----
    passed = len(report_files) > 0
    results.append({
        'name': 'creates-report',
        'text': 'A markdown report is generated under outputs/reports/',
        'passed': passed,
        'evidence': [os.path.basename(f) for f in report_files] if passed else ['No report files found']
    })

    # ---- Assertion: has-citations ----
    found = search_md_files_regex(output_dir, r'\[\[.*?\]\]')
    if not found:
        # Also check for markdown links to wiki pages
        found = search_md_files_regex(output_dir, r'\[.*?\]\(.*?wiki')
    results.append({
        'name': 'has-citations',
        'text': 'Report cites specific wiki pages or concepts',
        'passed': len(found) > 0,
        'evidence': [os.path.basename(f['file']) for f in found[:2]] if found else ['No citations found']
    })

    # ---- Assertion: creates-outputs-dir ----
    outputs_dir = os.path.join(output_dir, 'outputs')
    reports_dir = os.path.join(output_dir, 'outputs', 'reports')
    has_reports = os.path.isdir(reports_dir)
    # Also check if reports/ is directly in output_dir
    has_reports_direct = os.path.isdir(os.path.join(output_dir, 'reports'))
    passed = has_reports or has_reports_direct or len(report_files) > 0
    results.append({
        'name': 'creates-outputs-dir',
        'text': 'Outputs directory structure follows skill convention',
        'passed': passed,
        'evidence': ['outputs/ directory exists'] if passed else ['No outputs/ directory found']
    })

    # ---- Assertion: adds-connections ----
    passed = len(connection_files) > 0
    results.append({
        'name': 'adds-connections',
        'text': 'New connections or gaps are identified (wiki/connections/ or equivalent)',
        'passed': passed,
        'evidence': [os.path.basename(f) for f in connection_files[:2]] if passed else ['No connections files found']
    })

    # ---- Assertion: synthesized-answer ----
    target_files = report_files if report_files else all_md
    max_len = 0
    for f in target_files:
        try:
            with open(f, 'r') as fh:
                max_len = max(max_len, len(fh.read()))
        except:
            pass
    passed = max_len > 200  # substantial content
    results.append({
        'name': 'synthesized-answer',
        'text': 'Report contains a synthesized answer, not just a list of sources',
        'passed': passed,
        'evidence': [f'Longest file: {max_len} chars'] if passed else ['Files too short']
    })

    # ---- Assertion: creates-marp-file ----
    passed = len(slide_files) > 0
    # Also check for md files with Marp frontmatter
    if not passed:
        found = search_md_files_regex(output_dir, r'marp:\s*true')
        if found:
            passed = True
            slide_files = [f['file'] for f in found]
    results.append({
        'name': 'creates-marp-file',
        'text': 'A Marp slide file is created under outputs/slides/',
        'passed': passed,
        'evidence': [os.path.basename(f) for f in slide_files] if passed else ['No Marp files found']
    })

    # ---- Assertion: has-marp-frontmatter ----
    found = search_md_files_regex(output_dir, r'marp:\s*true')
    results.append({
        'name': 'has-marp-frontmatter',
        'text': 'Slide file has marp: true frontmatter',
        'passed': len(found) > 0,
        'evidence': [os.path.basename(f['file']) for f in found[:1]] if found else ['No marp:true found']
    })

    # ---- Assertion: has-slide-separators ----
    found = search_md_files_regex(output_dir, r'\n---\n')
    results.append({
        'name': 'has-slide-separators',
        'text': "Uses '---' slide separators (Marp format)",
        'passed': len(found) > 0,
        'evidence': [f'{len(f["matches"])} separators in {os.path.basename(f["file"])}' for f in found[:1]] if found else ['No --- separators found']
    })

    # ---- Assertion: has-sufficient-slides ----
    # Count --- separators which indicate slide breaks
    max_separators = 0
    best_file = ''
    for f in all_md:
        count = count_in_file(f, '\n---\n')
        if count > max_separators:
            max_separators = count
            best_file = f
    passed = max_separators >= 4  # at least 5 slides = 4 separators
    results.append({
        'name': 'has-sufficient-slides',
        'text': 'Has at least 5 slides',
        'passed': passed,
        'evidence': [f'{max_separators + 1} slides in {os.path.basename(best_file)}'] if passed else [f'Only {max_separators} separators found']
    })

    # ---- Assertion: covers-transformer-to-moe ----
    has_transformer = len(search_md_files(output_dir, 'transformer')) > 0
    has_moe = len(search_md_files(output_dir, 'mixture of expert')) > 0 or len(search_md_files(output_dir, 'MoE')) > 0
    passed = has_transformer and has_moe
    results.append({
        'name': 'covers-transformer-to-moe',
        'text': 'Covers both Transformer and MoE topics',
        'passed': passed,
        'evidence': [f'Transformer: {"✅" if has_transformer else "❌"}, MoE: {"✅" if has_moe else "❌"}']
    })

    # ---- Assertion: produces-lint-report ----
    passed = len(lint_files) > 0 or len(report_files) > 0
    results.append({
        'name': 'produces-lint-report',
        'text': 'A lint/health check report is produced',
        'passed': passed,
        'evidence': [os.path.basename(f) for f in (lint_files or report_files)[:1]] if passed else ['No lint report found']
    })

    # ---- Assertion: identifies-orphans ----
    found = search_md_files(output_dir, 'orphan')
    if not found:
        found = search_md_files(output_dir, 'isolated')
    if not found:
        found = search_md_files(output_dir, 'unlinked')
    results.append({
        'name': 'identifies-orphans',
        'text': 'Report checks for orphan pages',
        'passed': len(found) > 0,
        'evidence': [os.path.basename(f) for f in found[:1]] if found else ['No orphan check found']
    })

    # ---- Assertion: checks-references ----
    found = search_md_files(output_dir, 'broken')
    if not found:
        found = search_md_files(output_dir, 'backlink')
    if not found:
        found = search_md_files(output_dir, 'reference')
    results.append({
        'name': 'checks-references',
        'text': 'Report checks for broken backlinks or references',
        'passed': len(found) > 0,
        'evidence': [os.path.basename(f) for f in found[:1]] if found else ['No reference check found']
    })

    # ---- Assertion: has-recommendations ----
    found = search_md_files(output_dir, 'recommend')
    if not found:
        found = search_md_files(output_dir, 'suggest')
    if not found:
        found = search_md_files(output_dir, 'action')
    results.append({
        'name': 'has-recommendations',
        'text': 'Report includes actionable recommendations',
        'passed': len(found) > 0,
        'evidence': [os.path.basename(f) for f in found[:1]] if found else ['No recommendations found']
    })

    # ---- Assertion: prioritized-fixes ----
    found = search_md_files(output_dir, 'P0')
    if not found:
        found = search_md_files(output_dir, 'priority')
    if not found:
        found = search_md_files(output_dir, 'categor')
    results.append({
        'name': 'prioritized-fixes',
        'text': 'Report has prioritized or categorized issue list',
        'passed': len(found) > 0,
        'evidence': [os.path.basename(f) for f in found[:1]] if found else ['No prioritization found']
    })

    return results


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else '/Users/user/universal-skills/categories/workflow/llm-knowledge-base/workspace/iteration-1'
    all_results = {}

    for eval_dir in sorted(os.listdir(workspace)):
        eval_path = os.path.join(workspace, eval_dir)
        if not os.path.isdir(eval_path):
            continue

        for variant in ['with_skill', 'without_skill']:
            output_dir = os.path.join(eval_path, variant, 'outputs')
            if not os.path.isdir(output_dir):
                print(f"Skipping {eval_dir}/{variant}: no outputs directory")
                continue

            print(f"\n=== {eval_dir}/{variant} ===")
            results = grade_run(output_dir)

            grading_path = os.path.join(eval_path, variant, 'grading.json')
            with open(grading_path, 'w') as f:
                json.dump({'eval_id': eval_dir.split('-')[1] if '-' in eval_dir else '0', 'results': results}, f, indent=2, ensure_ascii=False)

            passed = sum(1 for r in results if r['passed'])
            total = len(results)
            print(f"  Score: {passed}/{total}")
            for r in results:
                status = "✅" if r['passed'] else "❌"
                evidence = r['evidence'][0] if r['evidence'] else ''
                print(f"  {status} {r['name']}: {evidence[:70]}")


if __name__ == '__main__':
    main()
