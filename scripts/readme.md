## Processing TIMEX corpora with EstNLTK and evaluating TimexTagger

This folder contains scripts for converting TIMEX corpora to EstNLTK's JSON format files, and for evaluating EstNLTK's TimexTagger on the corpus. [EstNLTK](https://github.com/estnltk/estnltk) v1.6.6+ is required for running the scripts. 

Scripts for converting corpora to EstNLTK's JSON format files:

  * `convert_ERY2012_to_v1_6_json.py`
  * `convert_Mthesis2010_to_v1_6_json.py`

    Scripts should run without any arguments. Optionally, flag `-p` can be used to force preprocessing of the corpora (segmentation and morphological analysis layers will be added). By default, scripts write JSON files to folders `../ERY2012_v1_6_json` and `../MT2010tml_v1_6_json`, respectively.

Script for evaluating TimexTagger:

  * `eval_v1_6_timex_tagger.py`

    Provided that the corpora have already been converted to EstNLTK's JSON files, the script should be able to find the converted corpora (from the default location), and perform the evaluation. 

    The script outputs a date-stamped log file, which 1) lists matching, missing and redundant TIMEX annotations for each document, 2) reports precison / recall / F1-score for each document. Additionally, corpus-wise evaluation summaries will be provided;
   

Modules (used by scripts):

  * `tml_conv_utils.py` -- utilities for converting corpus texts to EstNLTK's Text objects;
  * `preprocessing.py` -- preprocessing with segmentation fixes required by TimexTagger;