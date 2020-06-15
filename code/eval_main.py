# Copyright 2020 Google LLC.
# SPDX-License-Identifier: Apache-2.0

from collections import defaultdict, Counter
import pandas as pd
import json, math, os, sys
from pathlib import Path


def calc_percentage(total, matched):
    return round(float(matched * 100) / total, 2)


def read_all_annotations(annotations_dir_path, lang_pairs_strings):
    result = defaultdict()
    for lang_pair_str in lang_pairs_strings:
        print("\n" + lang_pair_str + " read annotations")
        lang_pair_suffix = "." + lang_pair_str
        result[lang_pair_str] = defaultdict()
        for annotations_filename in os.listdir(os.path.join(annotations_dir_path, lang_pair_str)):
            with open(os.path.join(annotations_dir_path, lang_pair_str, annotations_filename)) as reader:
                annotations = json.load(reader)
            if "-ref." not in annotations_filename and "-src." not in annotations_filename:
                system_name = annotations_filename[len("newstest2019."):-len(lang_pair_suffix)]
            else:
                system_name = 'ref' if "-ref." in annotations_filename else 'src'
            result[lang_pair_str][system_name] = annotations
    return result


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


def get_correl(full_df, metric_mame, lp):
    lp_df = full_df.loc[full_df['lp'] == lp]
    return round(lp_df['DA'].corr(lp_df[metric_mame]), 3)


def get_correllations(full_df, lang_pairs_strings):
    d = {lp: [] for lp in lang_pairs_strings}
    d['metric'] = []
    for metric in full_df.columns:
        if metric not in {'lp', 'DA', 'system'}:
            d['metric'].append(metric)
            for lang_pair_str in lang_pairs_strings:
                d[lang_pair_str].append(get_correl(full_df, metric, lang_pair_str))
    correl_df = pd.DataFrame(d, columns=['metric'] + lang_pairs_strings).set_index('metric')
    correl_df.index.name = None
    return correl_df


def genarate_results_table_for_paper(submitted_qe_and_bleu_and_us_df_correl_df_raw, lang_pairs_strings):
    df = submitted_qe_and_bleu_and_us_df_correl_df_raw[lang_pairs_strings].drop(['entity_recall_metric']).rename(
        index={'entity_recall_qe': 'KoBE'}).dropna(how='all')
    df.fillna(value='--', inplace=True)
    return df


def main(base_path):
    lang_pairs_strings = ['de-en', 'fi-en', 'gu-en', 'kk-en', 'lt-en', 'ru-en', 'zh-en', 'en-cs', 'en-de', 'en-fi',
                          'en-gu', 'en-kk', 'en-lt', 'en-ru', 'en-zh', 'de-cs', 'de-fr', 'fr-de']

    all_annotations = read_all_annotations(os.path.join(base_path, 'annotations/wmt19-submitted-data/newstest2019'),
                                           lang_pairs_strings)

    scores = {'entity_recall_qe': defaultdict(dict), 'entity_recall_metric': defaultdict(dict)}
    for lang_pair in all_annotations.keys():
        scores['entity_recall_qe'][lang_pair], scores['entity_recall_metric'][lang_pair] = defaultdict(
            dict), defaultdict(dict)
        print("\n" + str(lang_pair) + " calc scores")
        all_system_names = [key for key in all_annotations[lang_pair] if key not in {'src', 'ref'}]
        for sys_name in all_system_names:
            qe_counters = match_ids(all_annotations[lang_pair]['src']['annotated_sentence'],
                                    all_annotations[lang_pair][sys_name]['annotated_sentence'])
            metric_counters = match_ids(all_annotations[lang_pair]['ref']['annotated_sentence'],
                                        all_annotations[lang_pair][sys_name]['annotated_sentence'])
            scores['entity_recall_qe'][lang_pair][sys_name] = calc_percentage(qe_counters['src_count'], qe_counters[
                'match_count']) * entity_count_penalty(qe_counters['src_count'], qe_counters['cnd_count'])
            scores['entity_recall_metric'][lang_pair][sys_name] = calc_percentage(metric_counters['src_count'],
                                                                                  metric_counters[
                                                                                      'match_count']) * entity_count_penalty(
                metric_counters['src_count'], metric_counters['cnd_count'])

    all_results_df = pd.read_csv(
        open(os.path.join(base_path, 'wmt19_metric_task_results/sys-level_scores_metrics.csv')), sep=',')
    del all_results_df['Unnamed: 0']
    submitted_qe_and_bleu_df = all_results_df[
        ['lp', 'DA', 'system', 'BLEU', 'ibm1-morpheme', 'ibm1-pos4gram', 'LASIM', 'LP', 'UNI', 'UNI+', 'USFD',
         'USFD-TL', 'YiSi-2', 'YiSi-2_srl']].loc[all_results_df['lp'].isin(set(lang_pairs_strings))]

    all_score_names = ['entity_recall_qe', 'entity_recall_metric']
    d = {'lp': [], 'system': [], 'entity_recall_qe': [], 'entity_recall_metric': []}
    for lang_pair in scores[all_score_names[0]].keys():
        for system in scores[all_score_names[0]][lang_pair].keys():
            d['lp'].append(lang_pair)
            d['system'].append(system)
            d['entity_recall_qe'].append(scores['entity_recall_qe'][lang_pair][system])
            d['entity_recall_metric'].append(scores['entity_recall_metric'][lang_pair][system])
    scores_df = pd.DataFrame(d, columns=['lp', 'system', 'entity_recall_qe', 'entity_recall_metric'])

    submitted_qe_and_bleu_and_us_df = pd.merge(submitted_qe_and_bleu_df, scores_df, how='outer',
                                               left_on=['lp', 'system'], right_on=['lp', 'system'])
    submitted_qe_and_bleu_and_us_df = submitted_qe_and_bleu_and_us_df[
        (submitted_qe_and_bleu_and_us_df['system'] != 'online-B.0') | (
                    submitted_qe_and_bleu_and_us_df['lp'] != 'gu-en')]  # Scores for 'online-B.0' in 'gu-en' are missing
    submitted_qe_and_bleu_and_us_df_correl_df_raw = get_correllations(submitted_qe_and_bleu_and_us_df,
                                                                      lang_pairs_strings)

    print(f"\n{genarate_results_table_for_paper(submitted_qe_and_bleu_and_us_df_correl_df_raw, ['de-en', 'fi-en', 'gu-en', 'kk-en', 'lt-en', 'ru-en', 'zh-en']).drop(['ibm1-morpheme', 'ibm1-pos4gram'])}")
    print(f"\n{genarate_results_table_for_paper(submitted_qe_and_bleu_and_us_df_correl_df_raw, ['en-cs', 'en-de', 'en-fi', 'en-gu', 'en-kk', 'en-lt', 'en-ru', 'en-zh']).drop(['ibm1-morpheme', 'ibm1-pos4gram'])}")
    print(f"\n{genarate_results_table_for_paper(submitted_qe_and_bleu_and_us_df_correl_df_raw, ['de-cs', 'de-fr', 'fr-de'])}")
    print(f"\n{submitted_qe_and_bleu_and_us_df_correl_df_raw.loc[['BLEU', 'entity_recall_metric']][['de-en', 'fi-en', 'gu-en', 'kk-en', 'lt-en', 'ru-en', 'zh-en']].rename(index={'entity_recall_metric': 'KoBE reference based'})}")


if __name__ == '__main__':
    main(os.path.join(Path(__file__).parents[1], 'data'))
