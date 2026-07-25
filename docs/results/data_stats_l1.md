---
title: "data stats — level 1"
author: "<wtl>"
project: wtl-dllm
tags: [results, data]
---

# Level 1 corpus

```json
[
  {
    "file": "train_l1.jsonl",
    "n": 200000,
    "unique": 9640,
    "unique_ratio": 0.0482,
    "len_min": 5,
    "len_max": 9,
    "digit_dist": {
      "0": 80482,
      "1": 185660,
      "2": 135123,
      "3": 132834,
      "4": 130343,
      "5": 128054,
      "6": 126662,
      "7": 126876,
      "8": 72160,
      "9": 69874
    },
    "carry_rate_in_additions": 0.576
  },
  {
    "file": "eval_l1.jsonl",
    "n": 2000,
    "unique": 1778,
    "unique_ratio": 0.889,
    "len_min": 5,
    "len_max": 9,
    "digit_dist": {
      "0": 859,
      "1": 1833,
      "2": 1359,
      "3": 1334,
      "4": 1354,
      "5": 1274,
      "6": 1235,
      "7": 1206,
      "8": 746,
      "9": 662
    },
    "carry_rate_in_additions": 0.592
  },
  {
    "file": "eval_perturbed_l1.jsonl",
    "n": 2000,
    "unique": 581,
    "unique_ratio": 0.2905,
    "len_min": 5,
    "len_max": 9,
    "digit_dist": {
      "0": 580,
      "1": 1512,
      "2": 652,
      "3": 643,
      "4": 621,
      "5": 567,
      "6": 862,
      "7": 1029,
      "8": 2824,
      "9": 2737
    },
    "carry_rate_in_additions": 1.0
  }
]
```
