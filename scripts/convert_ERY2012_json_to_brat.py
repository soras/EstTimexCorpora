# ===========================================================
#  Converts ERY2012_t3-olp-ajav_modified corpus' v1.6 json 
#  files to Brat annotation files 
#  ( *.ann  &  *.txt  &  configuration files )
#  
#  More about Brat: https://brat.nlplab.org
#
#  Requirements
#     Python 3.6+
#     EstNLTK v1.6.9+
# ===========================================================

import os, os.path
import re
from sys import argv

from datetime import datetime
from collections import OrderedDict

from estnltk.converters import json_to_text, text_to_json

from tml_conv_utils import _debug_concise_timex_str

input_dir  = '../ERY2012_v1_6_json'
output_dir = '../ERY2012_v1_6_BRAT'

# dry run: just process files, but do not write out anything
dry_run = False

# Parse sys.argv
if len(argv) >= 2:
    for arg in argv[1:]:
        if arg.lower() in ['-d', '--dry_run', '--dryrun']:
            dry_run = True

# Check for input directory
assert os.path.exists( input_dir ) and os.path.isdir( input_dir ), \
       '(!) Unable to find ERY2012_v1_6_json input directory at {!r}'.format( input_dir )

# Create output dir if required
if not dry_run and not os.path.exists(output_dir):
    os.makedirs(output_dir)

def get_timex_tag_str( timex_span ):
    '''Returns a timex tag corresponding to the given timex span.'''
    assert timex_span._layer is not None
    annotation = timex_span.annotations[0]
    out_str = ['<TIMEX']
    out_str.append(' text={!r}'.format(timex_span.text))
    for attr in timex_span._layer.attributes:
        if attr in annotation and annotation[attr] is not None:
            out_str.append(' ')
            out_str.append('{}={!r}'.format(attr,annotation[attr]))
    out_str.append('>')
    return ''.join(out_str)

def create_annotations_file_content( text_obj, timexes_layer='gold_timexes', correct_indexes=True ):
    ''' Creates .ann file content based on timex annotations in given Text object. 
        Brat's standoff annotations format:  https://brat.nlplab.org/standoff.html
    '''
    trigger_annotations = []
    attribute_annotations = []
    annotator_notes = []
    mapping = []
    for t_nr, timex in enumerate( text_obj[timexes_layer] ):
        t_nr += 1
        tmx_start = timex.start
        tmx_end   = timex.end
        if correct_indexes:
            # Problem: it seems that BRAT is counting every newline ('\n') as two 
            # index positions. So, we have to shift indexes by the number of newlines
            newlines1 = text_obj.text[:tmx_start].count('\n')
            tmx_start += newlines1
            newlines2 = text_obj.text[:tmx_end].count('\n')
            tmx_end += newlines2
        trigger = f'T{t_nr}\tTimex {tmx_start} {tmx_end}\t{timex.text}'
        trigger_annotations.append( trigger )
        attribute_nr = len(attribute_annotations)+1
        attribute = f'A{attribute_nr}\ttype T{t_nr} {timex.type}'
        attribute_annotations.append( attribute )
        note_nr = len(annotator_notes)+1
        annotator_note = f'#{note_nr}\tAnnotatorNotes T{t_nr}\tOriginal: {get_timex_tag_str(timex)}'
        annotator_notes.append( annotator_note )
        mapping.append( (f'T{t_nr}', timex.tid ) )
    ann_file_content = ('\n'.join(trigger_annotations)) + '\n' + ('\n'.join(attribute_annotations)) + '\n' + ('\n'.join(annotator_notes))
    return ann_file_content, mapping

def create_annotations_conf_content():
    ''' Creates content for the "annotations.conf" file. 
        Brat's annotations configuration file format: https://brat.nlplab.org/configuration.html#annotation-configuration
        Note: As of brat v1.3, attributes cannot be assigned to relations, so we created a separate TLINK for each relation 
        type.
    '''
    conf_string = '''
[entities]
Timex
Event
Entity

[relations]
Tlink_BEFORE	Arg1:Timex,	Arg2:Event
Tlink_AFTER	Arg1:Timex,	Arg2:Event
Tlink_IS_INCLUDED	Arg1:Timex,	Arg2:Event
Tlink_INCLUDES	Arg1:Timex,	Arg2:Event
Tlink_SIMULTANEOUS	Arg1:Timex,	Arg2:Event
Tlink_VAGUE	Arg1:Timex,	Arg2:Event

Tlink_BEFORE	Arg1:Timex,	Arg2:Entity
Tlink_AFTER	Arg1:Timex,	Arg2:Entity
Tlink_IS_INCLUDED	Arg1:Timex,	Arg2:Entity
Tlink_INCLUDES	Arg1:Timex,	Arg2:Entity
Tlink_SIMULTANEOUS	Arg1:Timex,	Arg2:Entity
Tlink_VAGUE	Arg1:Timex,	Arg2:Entity

has_Argument	Arg1:Event,	Arg2:Event

# The [relations] section is also used to define rules regarding which entities are 
# allowed to overlap in their spans. The following definition instructs that
# "any entity annotation may overlap in any way with any other":
# <OVERLAP>	Arg1:<ENTITY>, Arg2:<ENTITY>, <OVL-TYPE>:<ANY>

[events]

[attributes]
type	Arg:Timex, Value:DATE|TIME|DURATION|SET
class	Arg:Event, Value:OCCURRENCE|REPORTING|PERCEPTION|ASPECTUAL|I_ACTION|I_STATE|STATE|MODAL
class_confidence	Arg:Event, Value:high|neutral|low
duration	Arg:Event, Value:instant|seconds|minutes|hours|days|weeks|months|years|centuries|forever
duration_confidence	Arg:Event, Value:high|neutral|low

#reltype	Arg:Tlink, Value:BEFORE|INCLUDES|IS_INCLUDED|SIMULTANEOUS|AFTER|VAGUE
#reltype_confidence	Arg:Tlink, Value:high|neutral|low

'''
    return re.sub('^\n+', '', conf_string)


# Convert all EstNLTK v1.6 *.json files in the input directory
converted = 0
timex_count = 0
start = datetime.now()
entity_mapping = []
for fname in sorted(os.listdir(input_dir)):
    if not fname.endswith('.json'):
        continue
    fpath = os.path.join(input_dir, fname)
    print('  Converting',fname,'...')
    # Import/convert document
    text_obj = json_to_text( file=fpath )
    if text_obj:
        assert 'document_creation_time' in text_obj.meta
        #assert 'sentences' in text_obj.layers, f'(!) Missing "sentences" layer in the text from file {fname}!'
        assert 'gold_timexes' in text_obj.layers, f'(!) Missing "gold_timexes" layer in the text from file {fname}!'
        # Convert Text's annotations to brat format
        ann_content, mapping = create_annotations_file_content( text_obj, 'gold_timexes' )
        for (brat_id, timex_id) in mapping:
            entity_mapping.append(f'{fname}\t{brat_id} {timex_id}')
            timex_count += 1
        converted += 1
        if not dry_run:
            # Write out results
            # 1) Plain text file
            new_text_fname = fname.replace('.json', '.txt')
            fpath = os.path.join( output_dir, new_text_fname )
            with open(fpath, 'w', encoding='utf-8') as out_f:
                out_f.write( text_obj.text )
            # 2) Annotations file
            new_text_fname = fname.replace('.json', '.ann')
            fpath = os.path.join( output_dir, new_text_fname )
            with open(fpath, 'w', encoding='utf-8') as out_f:
                out_f.write( ann_content )

# Save entity mapping
if not dry_run:
    if entity_mapping:
        fpath = os.path.join( output_dir, 'entity_mapping.conf' )
        with open(fpath, 'w', encoding='utf-8') as out_f:
            for line in entity_mapping:
                out_f.write( line )
                out_f.write( '\n' )
    # Save 'annotation.conf'
    conf_content = create_annotations_conf_content()
    fpath = os.path.join( output_dir, 'annotation.conf' )
    with open(fpath, 'w', encoding='utf-8') as out_f:
        out_f.write( conf_content )
        out_f.write( '\n' )
    
# Output statistics
print()
print(' Total processing time: {}'.format( datetime.now()-start) )
print(' Docs converted:        ', converted )
print('    Explicit  timexes:  ', timex_count )
print()

