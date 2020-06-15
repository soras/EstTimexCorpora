# ===========================================================
#  Converts ERY2012_t3-olp-ajav_modified corpus' files to 
#  EstNLTK v1.6 Text objects
#  -- optionally, adds EstNLTK's segmentation and 
#     morphological annotations;
#  -- saves results as json files;
#
#  Requirements
#     Python 3.5+
#     EstNLTK v1.6.6+
# ===========================================================

import os, os.path
from sys import argv

from datetime import datetime
from collections import OrderedDict

from estnltk.converters import text_to_json

from tml_conv_utils import import_t3_olp_ajav_file
from tml_conv_utils import _debug_concise_timex_str

from preprocessing import preprocess_for_timex_tagger

input_dir  = '../ERY2012_t3-olp-ajav_modified/t3-olp-ajav'
output_dir = '../ERY2012_v1_6_json'

# dry run: just process files, but do not write out anything
dry_run = False

# preprocess with EstNLTK v1.6: add segmentation and morphological annotations
preprocess = False

# Parse sys.argv
if len(argv) >= 2:
    for arg in argv[1:]:
        if arg.lower() in ['-p', '--preprocess']:
            preprocess = True
        if arg.lower() in ['-d', '--dry_run', '--dryrun']:
            dry_run = True

# Check for input directory
assert os.path.exists( input_dir) and os.path.isdir( input_dir ), \
       '(!) Unable to find ERY2012_t3-olp-ajav input directory at {!r}'.format( input_dir )

# Create output dir if required
if not dry_run and not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Convert all *.t3-olp-ajav files in the input directory
original_tokens = 0
converted = 0
timex_count = 0
implicit_timex_count = 0
commented = 0
start = datetime.now()
for fname in sorted(os.listdir(input_dir)):
    if not fname.endswith('.t3-olp-ajav'):
        continue
    fpath = os.path.join(input_dir, fname)
    if not preprocess:
        print('  Converting',fname,'...')
    else:
        print('  Converting and preprocessing',fname,'...')
    # Import/convert document
    text_obj = import_t3_olp_ajav_file( fpath, fname )
    if text_obj:
        assert 'document_creation_time' in text_obj.meta
        seen_implicit_timexes = set()
        # Collect statistics
        original_tokens += text_obj.meta['_original_token_count']
        for timex in text_obj.gold_timexes:
            #print( _debug_concise_timex_str( timex ) )
            timex_count += 1
            if isinstance(timex.annotations[0]['begin_point'], OrderedDict):
                seen_implicit_timexes.add( timex.annotations[0]['begin_point']['tid'] )
            if isinstance(timex.annotations[0]['end_point'], OrderedDict):
                seen_implicit_timexes.add( timex.annotations[0]['end_point']['tid'] )
            if isinstance(timex.annotations[0]['part_of_interval'], OrderedDict):
                seen_implicit_timexes.add( timex.annotations[0]['part_of_interval']['tid'] )
            if timex.annotations[0]['comment'] is not None:
                commented += 1
        implicit_timex_count += len( seen_implicit_timexes )
        # Preprocess with EstNLTK (if required)
        if preprocess:
            preprocess_for_timex_tagger( text_obj )
            text_obj.tag_layer(['morph_analysis'])
        #print(text_obj.meta)
        converted += 1
        if not dry_run:
            # Write out results
            new_fname = fname.replace('.t3-olp-ajav', '.json')
            fpath = os.path.join( output_dir, new_fname )
            text_to_json( text_obj, fpath )
    #break

# Output statistics
print()
print(' Total processing time: {}'.format(datetime.now()-start))
print(' Docs converted:        ', converted )
print('    Original tokens:    ', original_tokens)
print('    Explicit  timexes:  ', timex_count )
print('    Implicit  timexes:  ', implicit_timex_count )
print('    Commented timexes:  ', commented )
print()
