# ===========================================================
#  Evaluates EstNLTK v1.7 TimexTagger on the corpora
#
#  Requirements
#     Python 3.7+
#     EstNLTK v1.7.0+
# ===========================================================

import os, os.path, re
from sys import argv

from datetime import datetime
from collections import OrderedDict
from collections import defaultdict

from estnltk.taggers import TimexTagger
from estnltk_core.converters import json_to_text

from estnltk.taggers import DiffTagger
from estnltk_core import Layer

from estnltk.taggers.system.diff_tagger import iterate_diff_conflicts
from estnltk.taggers.system.diff_tagger import iterate_modified
from estnltk.taggers.system.diff_tagger import iterate_missing
from estnltk.taggers.system.diff_tagger import iterate_extra
from estnltk_core.layer_operations import flatten

from preprocessing import preprocess_for_timex_tagger

# Location where to search for test corpora
input_search_dir = '..'

# Collected input/test corpora
input_dirs = []

# Gather potential input directories
for res_name in sorted(os.listdir(input_search_dir)):
    fpath = os.path.join(input_search_dir, res_name)
    if os.path.isdir(fpath) and fpath.endswith('_v1_6_json'):
        input_dirs.append( fpath )
        print(' Detected potential test corpus: {}'.format(fpath))

# Parse potential input directories from sys.argv
if len(argv) >= 2:
    for arg in argv[1:]:
        if os.path.isdir(arg):
            input_dirs.append( arg )
            print(' Detected potential test corpus: {}'.format(arg))

basic_eval_attributes = ("type", "value", "mod", "quant", "freq")

timex_diff_tagger = DiffTagger(layer_a='gold_timexes',
                               layer_b='auto_timexes',
                               output_layer='timexes_diff_layer',
                               output_attributes=('span_status',)+basic_eval_attributes+("begin_point", "end_point", "part_of_interval"),
                               span_status_attribute='span_status')



def reduce_timex_layer( timexes_layer, new_layer_name, reduce_ordered_dict=True ):
    '''Reduces a timexes layer so that it can be compared via DiffTagger.
       Basically, removes attributes that have variable values and which exact
       matching is of lesser importance ("tid", "anchor_time_id", and "begin_point", 
       "end_point" and "part_of_interval" initiations with strings).'''
    new_layer = Layer(name=new_layer_name, \
                      attributes=('type', 'value', 'mod', 'quant', 'freq', 'begin_point', 'end_point', 'part_of_interval'), \
                      text_object=text_obj,\
                      ambiguous=False)
    for tmx_span in timexes_layer:
        assert len(tmx_span.annotations) == 1
        loc = ( tmx_span.start, tmx_span.end )
        annotations = {}
        for attr in new_layer.attributes:
            value = tmx_span.annotations[0][attr]
            if attr in ['begin_point', 'end_point', 'part_of_interval']:
                if value is not None and isinstance(value, str):
                    # If there is a string value (e.g. '??'), remove it
                    annotations[attr] = None
                else:
                    if reduce_ordered_dict and isinstance(value, OrderedDict):
                        value = OrderedDict( [(k,value[k]) for k in ['type', 'value', 'mod', 'quant', 'freq'] if k in value] )
                    annotations[attr] = value
            else:
                annotations[attr] = value
        new_layer.add_annotation( loc, **annotations )
    return new_layer



def find_timexes_with_full_span_match( gold_layer, auto_layer ):
    '''Finds all pairs of full span matches between gold and auto 
       timexes. 
       Returns a list of pairs: (gold_timex_span, auto_timex_span).
    '''
    pairs = []
    used_auto = set()
    for gid, gold_tmx_span in enumerate( gold_layer ):
        for aid, auto_tmx_span in enumerate( auto_layer ):
            if gold_tmx_span.start == auto_tmx_span.start and \
               gold_tmx_span.end   == auto_tmx_span.end:
                if aid in used_auto:
                    raise Exception('(!) Auto timex {!r} has already been matched a gold one.'.format())
                pairs.append( (gold_tmx_span, auto_tmx_span) )
                used_auto.add( aid )
    return pairs



def aggregate_differences( diff_layer, diffs_dict, full_span_matches, create_and_return_log=True ):
    ''' Finds statistics about matching annotations (both on 
        TIMEX extent and TIMEX attributes), and accumulates 
        these statistics into the diffs_dict. 
        If required, constructs a log output, reporting common, 
        missing and redundant annotations, and returns as a 
        list of log lines (strings).
    ''' 
    assert isinstance(diffs_dict, defaultdict)
    #
    #  1) TIMEX extent
    #
    unchanged_spans  = diff_layer.meta['unchanged_spans']
    modified_spans   = diff_layer.meta['modified_spans']
    missing_spans    = diff_layer.meta['missing_spans']
    extra_spans      = diff_layer.meta['extra_spans']
    # Strict alignment
    gold_spans = unchanged_spans + modified_spans + missing_spans
    auto_spans = unchanged_spans + modified_spans + extra_spans
    diffs_dict['gold_spans'] += gold_spans
    diffs_dict['auto_spans'] += auto_spans
    diffs_dict['unchanged_spans'] += unchanged_spans
    diffs_dict['modified_spans']  += modified_spans
    diffs_dict['missing_spans']   += missing_spans
    diffs_dict['extra_spans']     += extra_spans
    diffs_dict['documents'] += 1
    # Relaxed alignment: for each conflict, find one best match,
    # and remove from missing/extra countings
    map_gold_to_auto = {}
    map_auto_to_gold = {}
    map_gold_to_auto_score = defaultdict(int)
    for gold, auto in iterate_diff_conflicts(diff_layer, 'span_status'):
        # calculate match score
        score = 0
        for attr in ['type', 'value']:
            if gold.annotations[0][attr] == auto.annotations[0][attr]:
                score += 2
        for attr in ['mod', 'quant', 'freq', 'begin_point', 'end_point', 'part_of_interval']:
            if gold.annotations[0][attr] == auto.annotations[0][attr]:
                score += 1
        gold_key = (gold.start, gold.end)
        auto_key = (auto.start, auto.end)
        if map_gold_to_auto_score[gold_key] < score and \
           auto_key not in map_auto_to_gold:
            # Update records
            assert gold.annotations[0]['span_status'] == 'missing'
            assert auto.annotations[0]['span_status'] == 'extra'
            # Release old auto key
            if gold_key in map_gold_to_auto:
                if len(map_gold_to_auto[gold_key]) == 2:
                    [_, old_auto] = map_gold_to_auto[gold_key]
                    old_auto_key = (old_auto.start, old_auto.end)
                    del map_auto_to_gold[old_auto_key]
            # Add new keys
            map_gold_to_auto[gold_key] = [gold, auto]
            map_auto_to_gold[auto_key] = [gold, auto]
            map_gold_to_auto_score[gold_key] = score
    assert len( map_gold_to_auto.keys() ) == len( map_auto_to_gold.keys() )
    missing_spans -= len( map_gold_to_auto.keys() )
    extra_spans -= len( map_gold_to_auto.keys() )
    assert missing_spans >= 0
    assert extra_spans >= 0
    diffs_dict['missing_spans_lenient'] += missing_spans
    diffs_dict['extra_spans_lenient'] += extra_spans
    gold_spans = unchanged_spans + modified_spans + missing_spans
    auto_spans = unchanged_spans + modified_spans + extra_spans
    diffs_dict['gold_spans_lenient'] += gold_spans
    diffs_dict['auto_spans_lenient'] += auto_spans
    #
    #  2) TIMEX attributes 
    #
    unchanged_annotations = diff_layer.meta['unchanged_annotations']
    extra_annotations   = diff_layer.meta['extra_annotations']
    missing_annotations = diff_layer.meta['missing_annotations']
    #
    # unchanged_annotations + missing_annotations = number_of_annotations_in_old_layer
    # unchanged_annotations + extra_annotations   = number_of_annotations_in_new_layer
    # 
    diffs_dict['total_gold_annotations'] += unchanged_annotations + missing_annotations
    diffs_dict['total_auto_annotations'] += unchanged_annotations + extra_annotations
    for attr in basic_eval_attributes:
        diffs_dict['matching_'+str(attr)] += unchanged_annotations
        diffs_dict['total_'+str(attr)]    += unchanged_annotations
    for diff_span in iterate_modified( diff_layer, 'span_status' ):
        for attr in basic_eval_attributes:
            values = []
            for annotation in diff_span.annotations:
                values.append( annotation[attr] )
            if len(set(values)) == 1:
                diffs_dict['matching_'+str(attr)] += 1
                diffs_dict['total_'+str(attr)] += 1
            else:
                diffs_dict['total_'+str(attr)] += 1
    #
    # Collect statistics for precision and recall
    # Find retrieved & relevant attributes
    #
    # 1) from full matches
    for (gold_span, auto_span) in full_span_matches:
        assert len(gold_span.annotations) == 1
        assert len(auto_span.annotations) == 1
        gold_key = (gold_span.start, gold_span.end)
        auto_key = (auto_span.start, auto_span.end)
        assert gold_key not in map_gold_to_auto.keys()
        assert auto_key not in map_auto_to_gold.keys()
        gold_annotation = gold_span.annotations[0]
        auto_annotation = auto_span.annotations[0]
        for attr in basic_eval_attributes:
            if gold_annotation[attr] is not None:
                diffs_dict['total_relevant_'+str(attr)] += 1
            if auto_annotation[attr] is not None:
                diffs_dict['total_retrieved_'+str(attr)] += 1
            if gold_annotation[attr] is not None and \
               auto_annotation[attr] is not None and \
               gold_annotation[attr] == auto_annotation[attr]:
                diffs_dict['total_pr_matching_'+str(attr)] += 1
    # 2) from partial matches
    for gold_key in sorted(map_gold_to_auto.keys()):
        [gold_span, auto_span] = map_gold_to_auto[gold_key]
        assert len(gold_span.annotations) == 1
        assert len(auto_span.annotations) == 1
        gold_annotation = gold_span.annotations[0]
        auto_annotation = auto_span.annotations[0]
        for attr in basic_eval_attributes:
            if gold_annotation[attr] is not None:
                diffs_dict['total_relevant_'+str(attr)] += 1
            if auto_annotation[attr] is not None:
                diffs_dict['total_retrieved_'+str(attr)] += 1
            if gold_annotation[attr] is not None and \
               auto_annotation[attr] is not None and \
               gold_annotation[attr] == auto_annotation[attr]:
                diffs_dict['total_pr_matching_'+str(attr)] += 1
    # Create log ( report common, missing and redundant annotations )
    if create_and_return_log:
        log_str = ['COMMON:']
        # full match
        for (gold_span, auto_span) in full_span_matches:
            gold_ann = gold_span.annotations[0]
            auto_ann = auto_span.annotations[0]
            gold_str = '<{}:{}> ({}:{}) : {!r}'.format(gold_ann.start, gold_ann.end, gold_ann['type'], gold_ann['value'], gold_ann.text)
            auto_str = '<{}:{}> ({}:{}) : {!r}'.format(auto_ann.start, auto_ann.end, auto_ann['type'], auto_ann['value'], auto_ann.text)
            attribs_mismatch = []
            for attr in basic_eval_attributes + ('begin_point', 'end_point', 'part_of_interval'):
                if gold_ann[attr] != auto_ann[attr]:
                    attribs_mismatch.append( attr )
            if not attribs_mismatch:
                log_str.append(' (+) ' + gold_str)
                log_str.append('     ' + auto_str)
            else:
                log_str.append(' (-) ' + gold_str + '  mismatching {}'.format(attribs_mismatch))
                log_str.append('     ' + auto_str)
        # partial match
        for gold_key in sorted(map_gold_to_auto.keys()):
            [gold_span, auto_span] = map_gold_to_auto[gold_key]
            gold_ann = gold_span.annotations[0]
            auto_ann = auto_span.annotations[0]
            gold_str = '<{}:{}> ({}:{}) : {!r}'.format(gold_ann.start, gold_ann.end, gold_ann['type'], gold_ann['value'], gold_ann.text)
            auto_str = '<{}:{}> ({}:{}) : {!r}'.format(auto_ann.start, auto_ann.end, auto_ann['type'], auto_ann['value'], auto_ann.text)
            attribs_mismatch = []
            for attr in basic_eval_attributes + ('begin_point', 'end_point', 'part_of_interval'):
                if gold_ann[attr] != auto_ann[attr]:
                    attribs_mismatch.append( attr )
            if not attribs_mismatch:
                log_str.append(' (±) ' + gold_str + '  mismatching extent')
                log_str.append('     ' + auto_str)
            else:
                log_str.append(' (-) ' + gold_str + '  mismatching {}'.format(attribs_mismatch))
                log_str.append('     ' + auto_str)
        missing_count = 0
        for diff_span in iterate_missing(diff_layer, 'span_status'):
            assert len(diff_span.annotations) == 1
            gold_ann = diff_span.annotations[0]
            gold_key = (gold_ann.start, gold_ann.end)
            if gold_key in map_gold_to_auto.keys():
                continue
            if missing_count == 0:
                log_str.append('MISSING:')
            missing_count += 1
            gold_str = '<{}:{}> ({}:{}) : {!r}'.format(gold_ann.start, gold_ann.end, gold_ann['type'], gold_ann['value'], gold_ann.text)
            log_str.append('(--) ' + gold_str + ' ')
        extra_count = 0
        for diff_span in iterate_extra(diff_layer, 'span_status'):
            assert len(diff_span.annotations) == 1
            auto_ann = diff_span.annotations[0]
            auto_key = (auto_ann.start, auto_ann.end)
            if auto_key in map_auto_to_gold.keys():
                continue
            if extra_count == 0:
                log_str.append('REDUNDANT:')
            extra_count += 1
            auto_str = '<{}:{}> ({}:{}) : {!r}'.format(auto_ann.start, auto_ann.end, auto_ann['type'], auto_ann['value'], auto_ann.text)
            log_str.append('(--) ' + auto_str + ' ')
        return log_str
    return None



def calculate_results( diffs_dict, print_out=True, return_log=False, report_attr_accuracy=False ):
    ''' Uses statistics from diffs_dict and calculates
        recall, precision and f1-score on TIMEX extent
        (both relaxed and strict) and on basic TIMEX
        attributes (type, value, mod, etc.).
        If required, then prints evaluation results out.
        If required, then returns evaluation table as a 
        list of strings.
    ''' 
    #
    #  unchanged_spans + modified_spans + missing_spans = length_of_old_layer
    #  unchanged_spans + modified_spans + extra_spans = length_of_new_layer
    #  ==> 
    #   rec = (unchanged_spans + modified_spans) / length_of_old_layer
    #  prec = (unchanged_spans + modified_spans) / length_of_new_layer
    #
    log_str = ['']
    if diffs_dict['documents'] > 1:
        log_str.append(' Documents evaluated: '+str(diffs_dict['documents']) ) 
    log_str.append(' Auto annotations:  '+str(diffs_dict['total_auto_annotations']) ) 
    log_str.append(' Gold annotations:  '+str(diffs_dict['total_gold_annotations']) ) 
    log_str.append('')
    #  Relaxed:
    rec  = (diffs_dict['unchanged_spans']+diffs_dict['modified_spans']) / diffs_dict['gold_spans_lenient'] if diffs_dict['gold_spans_lenient'] > 0 else 0
    prec = (diffs_dict['unchanged_spans']+diffs_dict['modified_spans']) / diffs_dict['auto_spans_lenient'] if diffs_dict['auto_spans_lenient'] > 0 else 0
    f1   = 2*(rec*prec) / (rec+prec) if rec+prec > 0 else 0.0
    log_str.append('     TIMEX extent(relaxed)   rec: {:.3f}     prec: {:.3f}     f1: {:.3f} '.format(rec, prec, f1)) 
    #  Strict:
    rec  = (diffs_dict['unchanged_spans']+diffs_dict['modified_spans']) / diffs_dict['gold_spans'] if diffs_dict['gold_spans'] > 0 else 0
    prec = (diffs_dict['unchanged_spans']+diffs_dict['modified_spans']) / diffs_dict['auto_spans'] if diffs_dict['auto_spans'] > 0 else 0
    f1   = 2*(rec*prec) / (rec+prec) if rec+prec > 0 else 0.0
    log_str.append('     TIMEX extent(strict)    rec: {:.3f}     prec: {:.3f}     f1: {:.3f} '.format(rec, prec, f1)) 
    log_str.append('')
    for attr in basic_eval_attributes:
        # Precision and recall
        total_retrieved   = diffs_dict['total_retrieved_'+str(attr)]
        total_relevant    = diffs_dict['total_relevant_'+str(attr)]
        total_pr_matching = diffs_dict['total_pr_matching_'+str(attr)]
        rec  = total_pr_matching / total_relevant if total_relevant > 0 else 0
        prec = total_pr_matching / total_retrieved if total_retrieved > 0 else 0
        f1   = 2*(rec*prec) / (rec+prec) if rec+prec > 0 else 0.0
        if report_attr_accuracy:
            # Accuracy
            matching = diffs_dict['matching_'+str(attr)]
            total    = diffs_dict['total_'+str(attr)]
            accuracy = matching/total if total > 0 else 0.0
            log_str.append('     TIMEX {:8}          rec: {:.3f}     prec: {:.3f}     f1: {:.3f}     acc:  {:.3f} '.format( attr, rec, prec, f1, accuracy ))
        else:
            log_str.append('     TIMEX {:8}          rec: {:.3f}     prec: {:.3f}     f1: {:.3f}'.format( attr, rec, prec, f1 ))
    log_str.append('')
    if print_out:
        print( '\n'.join(log_str) )
    if return_log:
        return log_str
    else:
        return None



def initialize_log_file():
    '''Initializes an empty log file with the current moment (datetime.now()).'''
    cur_date = ('{}'.format( datetime.now()))
    cur_date = cur_date.replace(' ', 'T')
    cur_date = cur_date.replace(':', '_')
    cur_date = re.sub('\.[0-9]+$', '', cur_date)
    log_file_name = 'test_json_log_'+cur_date+'.txt'
    with open( log_file_name, 'w', encoding='utf-8') as out_f:
        pass
    return log_file_name


def write_out_log( title_str, log_str, log_file_path ):
    '''Outputs given log_str (a list of strings) into the given 
       logfile (log_file_path). '''
    with open( log_file_path, 'a', encoding='utf-8') as out_f:
        if title_str and len(title_str) > 0:
            out_f.write(('='*50)+'\n')
            out_f.write(('  '*5)+title_str+'\n' )
            out_f.write(('='*50)+'\n')
        if log_str and len(log_str) > 0:
            for line in log_str:
                out_f.write( line+'\n' )
            out_f.write('\n')


if len(input_dirs) > 0:
    # Test on input corpora
    timex_tagger = TimexTagger()
    global_start = datetime.now()
    log_file_name = initialize_log_file()
    for test_dir in sorted(input_dirs):
        start = datetime.now()
        test_docs = []
        for fname in sorted(os.listdir(test_dir)):
            if fname.endswith('.json'):
                test_docs.append((fname, os.path.join(test_dir,fname)))
        if test_docs:
            print( '',test_dir ,'contains',len(test_docs),'json files for evaluation.')
            write_out_log( test_dir, None, log_file_name )
            corpus_diffs_dict = defaultdict(int)
            subcorpus_diffs_dict = defaultdict(int)
            last_subcorpus = None
            for (fname, fpath) in test_docs:
                text_obj = json_to_text( file=fpath )
                subcorpus = text_obj.meta['_subcorpus'] if '_subcorpus' in text_obj.meta else None
                if 'morph_analysis' not in text_obj.layers or \
                   'sentences' not in text_obj.layers or \
                   'words' not in text_obj.layers:
                    print('  Loading and pre-annotating',fname,'...')
                    preprocess_for_timex_tagger( text_obj )
                    text_obj.tag_layer(['morph_analysis'])
                else:
                    print('  Loading',fname,'...')
                print('  Annotating',fname,'...')
                timex_tagger.tag( text_obj )
                new_auto_timexes = reduce_timex_layer(text_obj['timexes'], 'auto_timexes')
                new_gold_timexes = reduce_timex_layer(text_obj['gold_timexes'], 'gold_timexes')
                # Find differences
                diff_layer = timex_diff_tagger.make_layer( text_obj, layers={'gold_timexes': new_gold_timexes, 'auto_timexes': new_auto_timexes} )
                full_span_matches = find_timexes_with_full_span_match( new_gold_timexes, new_auto_timexes )
                # corpus diffs
                aggregate_differences( diff_layer, corpus_diffs_dict, full_span_matches, create_and_return_log=False )
                # subcorpus diffs
                if subcorpus:
                    # last subcorpus stats
                    if last_subcorpus is not None and last_subcorpus != subcorpus:
                        sub_results_log_str = calculate_results( subcorpus_diffs_dict, print_out=False, return_log=True )
                        sub_results_log_str[0] = " Subcorpus {!r} results".format(last_subcorpus)
                        write_out_log( None, sub_results_log_str, log_file_name )
                        subcorpus_diffs_dict = defaultdict(int)
                    aggregate_differences( diff_layer, subcorpus_diffs_dict, full_span_matches, create_and_return_log=False )
                # doc diffs
                doc_diffs_dict = defaultdict(int)
                log_str = aggregate_differences( diff_layer, doc_diffs_dict, full_span_matches, create_and_return_log=True )
                # Write out results
                # doc diffs
                write_out_log( fname, log_str, log_file_name )
                # doc stats
                results_log_str = calculate_results( doc_diffs_dict, print_out=False, return_log=True )
                write_out_log( None, results_log_str, log_file_name )
                
                # Remember last subcorpus
                last_subcorpus = subcorpus
            # last subcorpus stats
            if last_subcorpus is not None:
                sub_results_log_str = calculate_results( subcorpus_diffs_dict, print_out=False, return_log=True )
                sub_results_log_str[0] = " Subcorpus {!r} results".format(last_subcorpus)
                write_out_log( None, sub_results_log_str, log_file_name )
            results_log_str = calculate_results( corpus_diffs_dict, print_out=True, return_log=True )
            results_log_str[0] = " Corpus {!r} results".format(test_dir)
            write_out_log( None, results_log_str, log_file_name )
            print(' Corpus processing time: {}'.format(datetime.now()-start))
        else:
            print( '(!)',test_dir ,'contains no json files for evaluation.')
        #break
    timex_tagger.close() # Terminate Java process
    print(' Total processing time:  {}'.format(datetime.now()-global_start))
else:
    print('(!) No potential test corpora detected. Please use convert_*.py scripts to automatically '+\
          'create the corpora or provide corpus locations via command line arguments.')
