# ========================================================
#  Preprocessing for EstNLTK's TimexTagger
#   Assures that the text will be tokenized in a way
#   expected by TimexTagger
#
#  Requirements
#     Python 3.7+
#     EstNLTK v1.7.0+
# ========================================================

import regex as re

from estnltk import Text

# Import TimexTagger's adapted tokenization (requires EstNLTK v1.7.0+)
from estnltk.taggers.standard.timexes.timex_tagger_preprocessing import make_adapted_cp_tagger
from estnltk.taggers.standard.timexes.timex_tagger_preprocessing import make_adapted_sentence_tokenizer

adjusted_compound_token_tagger = make_adapted_cp_tagger()
adjusted_sentenze_tokenizer = make_adapted_sentence_tokenizer()

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
    text_obj.tag_layer('words')
    adjusted_sentenze_tokenizer.tag( text_obj )
    return text_obj

