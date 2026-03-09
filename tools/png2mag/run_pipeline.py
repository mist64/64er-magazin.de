#!/usr/bin/env python3
"""Run the full block-level OCR pipeline for an article.

Usage:
    python3 tools/png2mag/run_pipeline.py <issue_dir> <start_page> <end_page> [--step N]

Example:
    python3 tools/png2mag/run_pipeline.py issues/8604 053 057
    python3 tools/png2mag/run_pipeline.py issues/8604 053 053 --step 4

Steps:
    1  Block detection + extraction (extract_blocks.py)
    2  Classification agent (needs LLM — prints prompt)
    3  Apply classification (apply_classify.py)
    4  Sub-agent OCR correction (needs LLM — prints prompts)
    5  Concatenation (concat_blocks.py)
    6  Join agent (needs LLM — prints prompt)
    7  Final assembly (assemble_article.py)

Without --step, runs all steps. Agent steps (2, 4, 6) print prompts and
pause for confirmation. Use --step N to resume from step N.
"""

import glob
import json
import os
import re
import shutil
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def page_range(start, end):
    """Generate zero-padded page numbers."""
    return [f'{p:03d}' for p in range(int(start), int(end) + 1)]


def blocks_dir(issue_dir, page):
    return os.path.join(issue_dir, 'tmp', f'p{page}_blocks')


def page_png(issue_dir, page):
    """Find the 600 DPI cropped PNG for a page."""
    png_dir = os.path.join(issue_dir, 'png')
    candidates = [
        os.path.join(png_dir, f'{page}_600_cropped.png'),
        os.path.join(png_dir, f'{page}_600.png'),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    # Try glob
    matches = glob.glob(os.path.join(png_dir, f'{page}_*.png'))
    if matches:
        return matches[0]
    return None


def run_script(args):
    """Run a Python script and stream output."""
    result = subprocess.run(
        [sys.executable] + args,
        capture_output=False,
    )
    if result.returncode != 0:
        print(f'ERROR: {" ".join(args)} failed with code {result.returncode}')
        sys.exit(1)


def read_prompt(name):
    """Read a prompt template file."""
    path = os.path.join(SCRIPT_DIR, name)
    with open(path) as f:
        return f.read()


def read_body_blocks(bdir):
    """Read body_blocks.txt."""
    path = os.path.join(bdir, 'body_blocks.txt')
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [line.strip() for line in f if line.strip()]


# ── Steps ─────────────────────────────────────────────────────────

def step1_extract(issue_dir, pages):
    """Step 1: Block detection + extraction."""
    print('\n' + '=' * 60)
    print('STEP 1: Block detection + extraction')
    print('=' * 60)
    for page in pages:
        png = page_png(issue_dir, page)
        if not png:
            print(f'ERROR: No PNG found for page {page}')
            sys.exit(1)
        bdir = blocks_dir(issue_dir, page)
        os.makedirs(bdir, exist_ok=True)
        print(f'\n--- Page {page} ---')
        run_script([
            os.path.join(SCRIPT_DIR, 'extract_blocks.py'),
            png, bdir,
        ])


def step2_classify(issue_dir, pages):
    """Step 2: Classification agent — returns manifest for LLM."""
    print('\n' + '=' * 60)
    print('STEP 2: Classification agent (needs LLM)')
    print('=' * 60)
    manifest = []
    for page in pages:
        bdir = blocks_dir(issue_dir, page)
        manifest.append({
            'page': page,
            'layout_txt': os.path.join(bdir, 'layout.txt'),
            'overview_png': os.path.join(bdir, 'overview.png'),
            'classify_txt': os.path.join(bdir, 'classify.txt'),
        })
    # Write manifest
    manifest_path = os.path.join(issue_dir, 'tmp', 'classify_manifest.json')
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f'Manifest: {manifest_path}')
    print(f'Pages: {", ".join(pages)}')
    print('>>> Run classification agents, then continue with --step 3')
    return manifest


def step3_apply(issue_dir, pages):
    """Step 3: Apply classification."""
    print('\n' + '=' * 60)
    print('STEP 3: Apply classification')
    print('=' * 60)
    for page in pages:
        bdir = blocks_dir(issue_dir, page)
        run_script([
            os.path.join(SCRIPT_DIR, 'apply_classify.py'),
            bdir, page,
        ])


def step4_block_agents(issue_dir, pages):
    """Step 4: Sub-agent OCR correction — returns manifest for LLM."""
    print('\n' + '=' * 60)
    print('STEP 4: Sub-agent OCR correction (needs LLM)')
    print('=' * 60)
    manifest = []
    for page in pages:
        bdir = blocks_dir(issue_dir, page)
        body = read_body_blocks(bdir)
        for bnum in body:
            txt = os.path.join(bdir, f'block_{bnum}.txt')
            html = os.path.join(bdir, f'block_{bnum}.html')
            png = os.path.join(bdir, f'block_{bnum}.png')
            # Copy txt -> html for agent to edit
            shutil.copy2(txt, html)
            manifest.append({
                'page': page,
                'block': bnum,
                'block_png': png,
                'block_html': html,
            })
    manifest_path = os.path.join(issue_dir, 'tmp', 'block_agent_manifest.json')
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f'Manifest: {manifest_path}')
    print(f'Blocks: {len(manifest)} across {len(pages)} page(s)')
    print('>>> Run block agents, then continue with --step 5')
    return manifest


def step5_concat(issue_dir, pages):
    """Step 5: Concatenation."""
    print('\n' + '=' * 60)
    print('STEP 5: Concatenation')
    print('=' * 60)
    bdirs = [blocks_dir(issue_dir, p) for p in pages]
    run_script([
        os.path.join(SCRIPT_DIR, 'concat_blocks.py'),
    ] + bdirs)


def step6_join(issue_dir, pages):
    """Step 6: Join agent — returns manifest for LLM."""
    print('\n' + '=' * 60)
    print('STEP 6: Join agent (needs LLM)')
    print('=' * 60)
    draft = os.path.join(issue_dir, 'tmp', 'article_draft.html')
    page_pngs = []
    overview_pngs = []
    for page in pages:
        png = page_png(issue_dir, page)
        if png:
            page_pngs.append(png)
        ov = os.path.join(blocks_dir(issue_dir, page), 'overview.png')
        if os.path.exists(ov):
            overview_pngs.append(ov)
    manifest = {
        'draft_html': draft,
        'page_pngs': page_pngs,
        'overview_pngs': overview_pngs,
        'start_page': pages[0],
    }
    manifest_path = os.path.join(issue_dir, 'tmp', 'join_manifest.json')
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f'Manifest: {manifest_path}')
    print(f'Draft: {draft}')
    print(f'Page PNGs: {", ".join(page_pngs)}')
    print('>>> Run join agent, then continue with --step 7')
    return manifest


def step7_assemble(issue_dir, start_page, end_page):
    """Step 7: Final assembly."""
    print('\n' + '=' * 60)
    print('STEP 7: Final assembly')
    print('=' * 60)
    draft = os.path.join(issue_dir, 'tmp', 'article_draft.html')
    run_script([
        os.path.join(SCRIPT_DIR, 'assemble_article.py'),
        draft, issue_dir, start_page, end_page,
    ])


# ── Main ──────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Run block-level OCR pipeline')
    parser.add_argument('issue_dir', help='Issue directory (e.g. issues/8604)')
    parser.add_argument('start_page', help='First page (e.g. 053)')
    parser.add_argument('end_page', help='Last page (e.g. 057)')
    parser.add_argument('--step', type=int, default=None,
                        help='Start from this step (1-7)')
    parser.add_argument('--clean', action='store_true',
                        help='Clean tmp/ block dirs before running')
    args = parser.parse_args()

    pages = page_range(args.start_page, args.end_page)
    start = args.step or 1

    if args.clean:
        for page in pages:
            bdir = blocks_dir(args.issue_dir, page)
            if os.path.exists(bdir):
                shutil.rmtree(bdir)
                print(f'Cleaned {bdir}')
        # Also clean article_draft.html
        draft = os.path.join(args.issue_dir, 'tmp', 'article_draft.html')
        if os.path.exists(draft):
            os.unlink(draft)
            print(f'Cleaned {draft}')

    if start <= 1:
        step1_extract(args.issue_dir, pages)
    if start <= 2:
        step2_classify(args.issue_dir, pages)
        if start < 2 or args.step == 2:
            return  # Pause for agent
    if start <= 3:
        step3_apply(args.issue_dir, pages)
    if start <= 4:
        step4_block_agents(args.issue_dir, pages)
        if start < 4 or args.step == 4:
            return  # Pause for agent
    if start <= 5:
        step5_concat(args.issue_dir, pages)
    if start <= 6:
        step6_join(args.issue_dir, pages)
        if start < 6 or args.step == 6:
            return  # Pause for agent
    if start <= 7:
        step7_assemble(args.issue_dir, args.start_page, args.end_page)

    print('\n' + '=' * 60)
    print('PIPELINE COMPLETE')
    print('=' * 60)


if __name__ == '__main__':
    main()
