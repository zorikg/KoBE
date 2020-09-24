# KoBE
Data and code for [Knowledge Based Machine Translation Evaluation](https://arxiv.org/abs/2009.11027).

This is a temporary location. The code and data will be soon moved to 
[github.com/google-research/google-research](https://github.com/google-research/google-research) repository. A link to
the new location will be posted here.

KoBE is a reference-less machine translation evaluation metric. 
Our approach is based on using entity linking pipelines to ground the entity mentions found in each source sentence 
and candidate translation against a large-scale multilingual knowledge base (Google Knowledge Graph). 
KoBE is then using the matched entity counts as a translation quality signal.

Unfortunately, we are not aware of any open-source multilingual KB and entity linking systems.
Therefore, to make sure our findings are fully reproducible and useful for future work, we release the annotations we
used together with scripts to reproduce our results.
 
**This is not an officially supported Google product.**

## Data
Our dataset contains annotations of the linked entity mentions in [WMT19 metrics track data](http://www.statmt.org/wmt19/results.html).
These entity linking annotations span over 425k sentences in 18 language pairs from 262 different MT systems, 
and contain 1.8 million entity mentions of 28k distinct entities.
The annotations were obtained by running and in-house entity linking system similar to the [Google Cloud Natural 
Language API - Entity Analysis](https://cloud.google.com/natural-language/docs/basics#entity_analysis) that links to
entities from [Google Knowledge Graph Search API](https://developers.google.com/knowledge-graph).

The published data contains a file for each system in each language pair, as well as the annotations for the source 
text and reference translations. Our annotations are in json format and contain all the entities that were detected 
in each sentence. Each entity has an id (from the Knowledge Base), start and end positions in the sentence and the 
text of the mention. 
For example:
```json
{
  "sentence": "In the aftermath of the Lombok earthquake, for instance, foreign nongovernmental organizations were told they were not needed.",
  "entities": [
    {
      "begin": 65,
      "end": 94,
      "id": "/m/0ckys",
      "text": "nongovernmental organizations"
    },
    {
      "begin": 31,
      "end": 41,
      "id": "/m/02r97",
      "text": "earthquake"
    },
    {
      "begin": 24,
      "end": 30,
      "id": "/m/04nd9",
      "text": "Lombok"
    },
    {
      "begin": 81,
      "end": 94,
      "id": "/m/0qb7t",
      "text": "organizations"
    }
  ]
}
```

Additional details and data description can be found in the paper under supplementary material.

## Scripts to reproduce papers results
We also publish the code that calculates KoBE on the annotated dataset to reproduce the results from the paper.
### Prerequisites
* Make sure you have python 3.7.5 or above.
* Make sure you have pandas installed:
```python
pip install pandas
```

### Usage
Clone the directory and then run the "reproduce_paper_results" script.
```python
bash <path to cloned directory root>/KoBE/reproduce_paper_results.sh
```

## bibtex

If you find this useful for your work, please use the following citation:

```
@inproceedings{gekhman2020kobe,
  title={KoBE: Knowledge-Based Machine Translation Evaluation},
  author={Gekhman, Zorik and Aharoni, Roee and Beryozkin, Genady and Freitag, Markus and Macherey, Wolfgang}
  booktitle = "Findings of EMNLP",
  year={2020},
  url={https://arxiv.org/abs/2009.11027},
}
```



