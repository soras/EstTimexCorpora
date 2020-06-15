# ========================================================
#  Preprocessing for EstNLTK's TimexTagger
#   Assures that the text will be tokenized in a way
#   expected by TimexTagger
#
#  Requirements
#     Python 3.5+
#     EstNLTK v1.6.6+
# ========================================================

import regex as re

from estnltk import Text

# Import CompoundTokenTagger with new rules
from estnltk.taggers.text_segmentation.compound_token_tagger import ALL_1ST_LEVEL_PATTERNS
from estnltk.taggers.text_segmentation.compound_token_tagger import CompoundTokenTagger

redefined_number_pat_1 = \
    { 'comment': '*) A generic pattern for detecting long numbers (1 group).',
      'example': '12,456',
      'pattern_type': 'numeric',
      '_group_': 0,
      '_priority_': (2, 1, 5),
      '_regex_pattern_': re.compile(r'''                             
                         \d+           # 1 group of numbers
                         (,\d+|\ *\.)  # + comma-separated numbers or period-ending
                         ''', re.X),
      'normalized': r"lambda m: re.sub(r'[\s]' ,'' , m.group(0))" }

redefined_number_pat_2 = \
   { 'comment': '*) A generic pattern for detecting long numbers (2 groups, point-separated, followed by comma-separated numbers).',
      'example': '67.123,456',
      'pattern_type': 'numeric',
      '_group_': 0,
      '_priority_': (2, 1, 3, 1),
      '_regex_pattern_': re.compile(r'''
                         \d+\.+\d+   # 2 groups of numbers
                         (,\d+)      # + comma-separated numbers
                         ''', re.X),
      'normalized': r"lambda m: re.sub(r'[\s\.]' ,'' , m.group(0))" }

# Create CompoundTokenTagger adjusted for TimexTagger's needs
new_1st_level_patterns = []
for pat in ALL_1ST_LEVEL_PATTERNS:
    if pat['comment'] == '*) Abbreviations of type <uppercase letter> + <numbers>;':
        # Skip this pattern
        continue 
    if pat['comment'] == '*) A generic pattern for detecting long numbers (1 group).':
        new_1st_level_patterns.append( redefined_number_pat_1 )
    elif pat['comment'] == '*) A generic pattern for detecting long numbers (2 groups, point-separated, followed by comma-separated numbers).':
        new_1st_level_patterns.append( redefined_number_pat_2 )
    else:
        new_1st_level_patterns.append( pat )
adjusted_compound_token_tagger = CompoundTokenTagger( patterns_1=new_1st_level_patterns )

# Test 1
test_text = Text('1991. a. jaanuaris, 2001. aasta lõpul või 1. jaanuaril 2001. a.').tag_layer(['tokens'])
adjusted_compound_token_tagger.tag( test_text )
test_text.tag_layer( ['words'] )
assert [t.text for t in test_text.words] == ['1991.', 'a.', 'jaanuaris', ',', '2001.', 'aasta', 'lõpul', 'või', '1.', 'jaanuaril', '2001.', 'a.']

# Test 2
test_text = Text('( 14.11.2001 jõust.01.01.2002 - RT I 2001 , 95 , 587 )').tag_layer(['tokens'])
adjusted_compound_token_tagger.tag( test_text )
test_text.tag_layer( ['words'] )
#print( [(cp.enclosing_text, cp.type) for cp in test_text.compound_tokens] )
assert [t.text for t in test_text.words] == ['(', '14.11.2001', 'jõust', '.', '01.01.2002', '-', 'RT', 'I', '2001', ',', '95', ',', '587', ')']

# Test 3
test_text = Text('24. detsembril kell 18 , 25. detsembril kell 10.30 , 26. ja 31. detsembril kell 17 ja 1. jaanuaril kell.10.30.').tag_layer(['tokens'])
adjusted_compound_token_tagger.tag( test_text )
test_text.tag_layer( ['words'] )
assert [t.text for t in test_text.words] == ['24.', 'detsembril', 'kell', '18', ',', '25.', 'detsembril', 'kell', '10.30', ',', '26.', 'ja', '31.', 'detsembril', 'kell', '17', 'ja', '1.', 'jaanuaril', 'kell', '.', '10.30', '.']

# Test 4
test_text = Text('31.detsembril kell 16 ja 23.30 , 1. jaanuaril kell 13.').tag_layer(['tokens'])
adjusted_compound_token_tagger.tag( test_text )
test_text.tag_layer( ['words'] )
assert [t.text for t in test_text.words] == ['31.', 'detsembril', 'kell', '16', 'ja', '23.30', ',', '1.', 'jaanuaril', 'kell', '13.']


def preprocess_for_timex_tagger( text_obj ):
    """ Adds segmentation layers to text_obj, assuring 
        that the text will be tokenized in a way expected 
        by TimexTagger. """
    text_obj.tag_layer(['tokens'])
    adjusted_compound_token_tagger.tag( text_obj )
    text_obj.tag_layer(['words','sentences'])
    return text_obj

