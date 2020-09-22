# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import math
import os
from collections import defaultdict, Counter
from pathlib import Path
import pandas as pd


def read_all_annotations(annotations_dir_path, all_lps):
    result = defaultdict(defaultdict)
    for lang_pair_str in all_lps:
        print(f"{lang_pair_str} read annotations\n")
        for annotations_filename in os.listdir(os.path.join(annotations_dir_path, lang_pair_str)):
            with open(os.path.join(annotations_dir_path, lang_pair_str, annotations_filename)) as reader:
                annotations = json.load(reader)
            if "-ref." not in annotations_filename and "-src." not in annotations_filename:
                lang_pair_suffix = f".{lang_pair_str}"
                system_name = annotations_filename[len("newstest2019."):-len(lang_pair_suffix)]
            else:
                system_name = 'ref' if "-ref." in annotations_filename else 'src'
            result[lang_pair_str][system_name] = annotations
    return result


def calc_percentage(total, matched):
    return round(float(matched * 100) / total, 2)


def entity_count_penalty(src_count, cnd_count):
    s, c = float(src_count), float(cnd_count)
    return 1.0 if c < 2 * s else math.exp(1 - c / (2 * s))


def match_ids(src_annotations, cnd_annotations):
    counters = Counter()
    for src_annotation, cnd_annotation in zip(src_annotations, cnd_annotations):
        cnd_ids_counter = Counter()
        for cnd_entity in cnd_annotation['entities']:
            counters.update(['cnd_count'])
            cnd_ids_counter.update([cnd_entity['id']])
        for src_entity in src_annotation['entities']:
            counters.update(['src_count'])
            if src_entity['id'] in cnd_ids_counter:
                counters.update(['match_count'])
                cnd_ids_counter.subtract([src_entity['id']])
                if cnd_ids_counter[src_entity['id']] == 0:
                    cnd_ids_counter.pop(src_entity['id'])
    return counters


def get_correlation(full_df, metric_mame, lp):
    lp_df = full_df.loc[full_df['lp'] == lp]
    return round(lp_df['DA'].corr(lp_df[metric_mame]), 3)


def get_correlations(full_df, lps):
    d = {lp: [] for lp in lps}
    d['metric'] = []
    for metric in full_df.columns:
        if metric not in {'lp', 'DA', 'system'}:
            d['metric'].append(metric)
            for lang_pair_str in lps:
                d[lang_pair_str].append(get_correlation(full_df, metric, lang_pair_str))
    df = pd.DataFrame(d, columns=['metric'] + lps).set_index('metric')
    df.index.name = None
    return df


def generate_results_table(submitted_qe_and_bleu_and_us_correl_df, lps):
    df = submitted_qe_and_bleu_and_us_correl_df[lps].drop(['entity_recall_metric']).rename(
        index={'entity_recall_qe': 'KoBE'}).dropna(how='all')
    df.fillna(value='--', inplace=True)
    return df


def calc_scores(all_annotations):
    scores = {'entity_recall_qe': defaultdict(defaultdict), 'entity_recall_metric': defaultdict(defaultdict)}
    for lang_pair, annotations in all_annotations.items():
        print(f"{lang_pair} calc scores\n")
        all_system_names = [key for key in annotations if key not in {'src', 'ref'}]
        for sys_name in all_system_names:
            qe_counters = match_ids(annotations['src']['annotated_sentence'],
                                    annotations[sys_name]['annotated_sentence'])
            metric_counters = match_ids(annotations['ref']['annotated_sentence'],
                                        annotations[sys_name]['annotated_sentence'])
            scores['entity_recall_qe'][lang_pair][sys_name] = calc_percentage(qe_counters['src_count'], qe_counters[
                'match_count']) * entity_count_penalty(qe_counters['src_count'], qe_counters['cnd_count'])
            scores['entity_recall_metric'][lang_pair][sys_name] = calc_percentage(metric_counters['src_count'],
                                                                                  metric_counters[
                                                                                      'match_count']) * entity_count_penalty(
                metric_counters['src_count'], metric_counters['cnd_count'])
    return scores


def get_wmt19_results(base_path, all_lps):
    all_results_df = pd.read_csv(
        open(os.path.join(base_path, 'wmt19_metric_task_results/sys-level_scores_metrics.csv')), sep=',')
    del all_results_df['Unnamed: 0']
    submitted_qe_and_bleu_df = all_results_df[
        ['lp', 'DA', 'system', 'BLEU', 'ibm1-morpheme', 'ibm1-pos4gram', 'LASIM', 'LP', 'UNI', 'UNI+', 'USFD',
         'USFD-TL', 'YiSi-2', 'YiSi-2_srl']].loc[all_results_df['lp'].isin(set(all_lps))]
    return submitted_qe_and_bleu_df


def calc_scores_df(all_annotations):
    scores = calc_scores(all_annotations)
    all_score_names = ['entity_recall_qe', 'entity_recall_metric']
    d = {'lp': [], 'system': [], 'entity_recall_qe': [], 'entity_recall_metric': []}
    for lang_pair in scores[all_score_names[0]].keys():
        for system in scores[all_score_names[0]][lang_pair].keys():
            d['lp'].append(lang_pair)
            d['system'].append(system)
            d['entity_recall_qe'].append(scores['entity_recall_qe'][lang_pair][system])
            d['entity_recall_metric'].append(scores['entity_recall_metric'][lang_pair][system])
    scores_df = pd.DataFrame(d, columns=['lp', 'system', 'entity_recall_qe', 'entity_recall_metric'])
    return scores_df


def merge_scores_with_wmt_scores(scores_df, submitted_qe_and_bleu_df):
    submitted_qe_and_bleu_and_us_df = pd.merge(submitted_qe_and_bleu_df, scores_df, how='outer',
                                               left_on=['lp', 'system'], right_on=['lp', 'system'])
    submitted_qe_and_bleu_and_us_df = submitted_qe_and_bleu_and_us_df[
        (submitted_qe_and_bleu_and_us_df['system'] != 'online-B.0') | (
                submitted_qe_and_bleu_and_us_df['lp'] != 'gu-en')]  # Scores for 'online-B.0' in 'gu-en' are missing
    return submitted_qe_and_bleu_and_us_df


def print_results(submitted_qe_and_bleu_and_us_correl_df, to_en_lps, from_en_lps, no_en_lps):
    to_en_results_table = generate_results_table(submitted_qe_and_bleu_and_us_correl_df, to_en_lps)
    print(f"\n{to_en_results_table.drop(['ibm1-morpheme', 'ibm1-pos4gram'])}")  # No reported ibm1 results in WMT19.

    from_en_results_table = generate_results_table(submitted_qe_and_bleu_and_us_correl_df, from_en_lps)
    print(f"\n{from_en_results_table.drop(['ibm1-morpheme', 'ibm1-pos4gram'])}")  # No reported ibm1 results in WMT19.

    no_en_results_table = generate_results_table(submitted_qe_and_bleu_and_us_correl_df, no_en_lps)
    print(f"\n{no_en_results_table}")

    to_en_metric_results_table = submitted_qe_and_bleu_and_us_correl_df.loc[['BLEU', 'entity_recall_metric']][to_en_lps]
    print(f"\n\n{to_en_metric_results_table.rename(index={'entity_recall_metric': 'KoBE reference based'})}")


def main(base_path):
    print(f"\nreading annotated data from - {base_path}\n")
    to_en_lps = ['de-en', 'fi-en', 'gu-en', 'kk-en', 'lt-en', 'ru-en', 'zh-en']
    from_en_lps = ['en-cs', 'en-de', 'en-fi', 'en-gu', 'en-kk', 'en-lt', 'en-ru', 'en-zh']
    no_en_lps = ['de-cs', 'de-fr', 'fr-de']
    all_lps = to_en_lps + no_en_lps + from_en_lps

    # Read all annotated WMT19 data.
    annotated_data_path = os.path.join(base_path, 'annotations/wmt19-submitted-data/newstest2019')
    all_annotations = read_all_annotations(annotated_data_path, all_lps)

    # Calculate KoBE scores.
    scores_df = calc_scores_df(all_annotations)

    # Read other metrics results from WMT19.
    submitted_qe_and_bleu_df = get_wmt19_results(base_path, all_lps)

    # Merge KoBE results with other metrics results from WMT19 to single table.
    submitted_qe_and_bleu_and_us_df = merge_scores_with_wmt_scores(scores_df, submitted_qe_and_bleu_df)

    # Calculate all metrics correlations with human DA.
    submitted_qe_and_bleu_and_us_correl_df = get_correlations(submitted_qe_and_bleu_and_us_df, all_lps)

    # Print the results as presented in KoBE paper.
    print_results(submitted_qe_and_bleu_and_us_correl_df, to_en_lps, from_en_lps, no_en_lps)


if __name__ == '__main__':
    main(os.path.join(Path(__file__).parents[1], 'data'))
