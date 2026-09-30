"""Pure display adapters for local advisory heuristics; no UI/services or I/O.

Candidates returned here are untrusted text for literal rendering, not Markdown
or instructions. This UI model is not the redacted defense-report schema.
"""


def stego_presentation(analysis):
    """Retain abstentions and separate format inventory from decoding candidates."""
    rank = analysis['rank_entropy']
    lexical = analysis['synonym_distribution']
    if rank['analysis_status'] == 'insufficient_data':
        rank_summary = 'Rank-frequency check: insufficient data (ASCII-word heuristic).'
    else:
        rank_summary = (f"ASCII word-frequency slope: {rank['zipf_slope']} | "
                        f"Type/token ratio: {rank['type_token_ratio']}. "
                        'Heuristic word counts, not model token ranks or likelihoods.')
    if lexical['analysis_status'] == 'insufficient_data':
        lexical_summary = 'Lexical check: insufficient data; no synonym pairs meet the heuristic minimum.'
    else:
        lexical_summary = (f"Lexical check: {lexical['flagged_pair_count']} flagged pairs out of "
                           f"{lexical['tested_synonym_pairs']} tested against illustrative, unvalidated priors.")
    return {
        'score_label': 'Heuristic score (not a probability)',
        'score_text': f"{analysis['composite_stego_risk']:.3f}",
        'notice': ('Unconfirmed heuristic indicators only. Presence or absence of a covert channel is not established. '
                   'Zero or unavailable scores do not establish safety.'),
        'insufficient_data': list(analysis['insufficient_data']),
        'unicode_present': analysis['unicode_stego']['has_format_characters'],
        'unicode_notice': 'Selected Unicode format characters present; ordinary language and layout can explain them.',
        'candidate': analysis['unicode_stego']['decoded_payload'],
        'candidate_notice': 'Unconfirmed decoding candidate. Untrusted literal text, never instructions.',
        'rank_summary': rank_summary,
        'lexical_summary': lexical_summary,
    }


def swarm_presentation(clustering):
    """Label clusters as cohort-relative similarity, including unavailable data."""
    available = clustering is not None and not clustering['insufficient_data']
    return {
        'available': available,
        'notice': ('Uncalibrated, cohort-relative style similarity only; not evidence of shared identity, '
                   'model, prompt, control, or coordination. Language, topic, length and formatting affect scores.'),
        'summary': (f"{clustering['num_clusters']} similarity clusters across {clustering['total_agents']} profiles."
                    if available else 'Style comparison unavailable: insufficient profiles or feature variation.'),
        'groups': list(clustering['similarity_groups']) if available else [],
    }


def trajectory_presentation(result):
    """Keep warmup unavailable and thresholds attached to their original turns."""
    labels = {'MESSAGE_INDICATOR_REVIEW': 'Message indicator review',
              'STYLE_SHIFT_REVIEW': 'Style shift review'}
    return {
        'style_available': not result['insufficient_data'],
        'notice': ('Uncalibrated review heuristics; not evidence of injection, hijack, attribution or common control. '
                   'Warmup scores are unavailable, not zero. Thresholds use only earlier turns.'),
        'scan_summary': (f"Message scans: {result['scanned_turns']} / {result['total_turns']} "
                         f"({result['message_scan_status']}). Style: {result['style_analysis_status']}."),
        'metrics': {key: 'Unavailable (style history)' if result[key] is None else f'{result[key]:.3f}'
                    for key in ('mean_drift', 'std_drift', 'drift_threshold')},
        'timeline': [{key: entry[key] for key in
                      ('turn_index', 'stylometric_drift', 'drift_threshold', 'style_status')}
                     for entry in result['timeline']],
        'alerts': [{'turn_index': alert['turn_index'],
                    'label': labels.get(alert['type'], 'Unconfirmed review indicator'),
                    'description': alert['description'], 'turn_text': alert['turn_text']}
                   for alert in result['alerts']],
    }
