# ========================================================
#  Utilities for converting  *.t3-olp-ajav  and  *.tml 
#  files to EstNLTK v1.6 Text objects
#
#  Requirements
#     Python 3.5+
#     EstNLTK v1.6.6+
# ========================================================

import re
import copy

from collections import OrderedDict

from estnltk import Text
from estnltk.text import Layer

# Pattern for lines with single tags
single_tag_line_pat = re.compile('^(<[^<>]+>)\s*$')

# Pattern for capturing names & values of attributes
tag_attribs_pat = re.compile('([^= ]+)="([^"]+?)"')

def parse_tag_attributes( tag_str ):
    """Extracts names & values of attributes from an XML tag string,
       and returns as a dictionary."""
    assert tag_str.count('"') % 2 == 0, \
        '(!) Uneven number of quotation marks in: '+str(tag_str)
    attribs = {}
    for attr_match in tag_attribs_pat.finditer(tag_str):
        key   = attr_match.group(1)
        value = attr_match.group(2)
        if key in attribs:
           if attribs[key] != value:
               raise Exception(' (!) Unexpected: attribute "'+key+'" appears more than once with conflicting values in: '+tag_str)
        attribs[key] = value
    return attribs


def parse_doc_metadata( ignore_content ):
    """Extracts document metadata from the content of 
       <ignoreeri>-tags."""
    metadata = {}
    ignore_str = ' '.join(ignore_content)
    fields = ignore_str.split('|')
    for field_str in fields:
        field_str = field_str.strip()
        if len(field_str) > 0 and ' ' in field_str:
            field_parts = field_str.split()
            if field_parts[0].endswith(':'):
                key = field_parts[0][:-1]
                value = ' '.join(field_parts[1:])
                if key in metadata and metadata[key] != value:
                    print('Warn! Conflicting metadata for key {!r}: {!r} vs {!r}. Using the last value.'.format(key, metadata[key], value))
                metadata[key] = value
            else:
                raise Exception('(!) Unexpected metadata field: {!r}'.format(field_str))
    return metadata


def get_subcorpus_name( t3_olp_ajav_fname ):
    '''Parses subcorpus name from the file name and returns. 
       This is specific to ERY2012 corpus.'''
    assert '_' in t3_olp_ajav_fname
    corpus_name = t3_olp_ajav_fname.split('_')[0]
    if corpus_name == 'sea':
        corpus_name = 'seadused'
    elif corpus_name == 'rkogu':
        corpus_name = 'riigikogu_stenogrammid'
    return corpus_name


def convert_timex_attributes( timex, remove_start_end=True ):
    """Rewrites TIMEX attribute names and values from the XML format
       (e.g. 'temporalFunction', 'anchorTimeID') to Python's format
       (e.g. 'temporal_function', 'anchor_time_id') and normalizes/
       corrects attribute values where necessary."""
    if 'temporalFunction' in timex:
        timex['temporal_function'] = timex['temporalFunction']
        del timex['temporalFunction']
        if timex['temporal_function'].lower() == 'true':
            timex['temporal_function'] = True
        elif timex['temporal_function'].lower() == 'false':
            timex['temporal_function'] = False
    if 'anchorTimeID' in timex:
        timex['anchor_time_id'] = timex['anchorTimeID']
        del timex['anchorTimeID']
    if 'beginPoint' in timex:
        timex['begin_point'] = timex['beginPoint']
        del timex['beginPoint']
    if 'endPoint' in timex:
        timex['end_point'] = timex['endPoint']
        del timex['endPoint']
    if remove_start_end:
        if '_start' in timex:
            del timex['_start']
        if '_end' in timex:
            del timex['_end']
        if 'text' in timex:
            del timex['text']
    return timex


def convert_timex_to_ordered_dict( timex, remove_start_end=True ):
    """Converts timex from dictionary format to OrderedDict format.
       Also rename TIMEX attribute names with the help of 
       convert_timex_attributes. Returns resulting OrderedDict.
    """
    # 1) Make a copy and convert attribute names
    timex_copy = copy.deepcopy(timex)
    timex_copy = convert_timex_attributes( timex_copy, remove_start_end=remove_start_end )
    # 2) Format as an OrderedDict
    ordered_timex_dict = OrderedDict()
    for attrib in ['tid', 'type', 'value', 'temporal_function', 'mod', 'anchor_time_id', 'quant', \
                   'freq', 'begin_point', 'end_point', 'comment']:
        if attrib in timex_copy:
            ordered_timex_dict[attrib] = timex_copy[attrib]
    return ordered_timex_dict


def get_parent_of_interval( cur_timex, other_timexes ):
    '''Finds out if current timex is part of an interval timex in other_timexes.
       If so, then returns the corresponding interval timex, and the position 
       of the current timex in the interval ('begin_point' or 'end_point').'''
    assert 'tid' in cur_timex
    for other_timex in other_timexes:
        assert 'tid' in other_timex
        if 'beginPoint' in other_timex and other_timex['beginPoint'] == cur_timex['tid']:
            return other_timex, 'begin_point'
        if 'endPoint' in other_timex and other_timex['endPoint'] == cur_timex['tid']:
            return other_timex, 'end_point'
    return None, None


def get_child_timepoints( cur_timex, other_timexes, only_implicit=True ):
    '''Finds out if the current timex is an interval with beginPoint and 
       endPoint. Returns a tuple with corresponding beginPoint and endPoint
       timexes. Otherwise, None values will be in filled in the tuple.'''
    assert 'tid' in cur_timex
    begin_point = None
    end_point   = None
    if 'beginPoint' in cur_timex or 'endPoint' in cur_timex:
        for other_timex in other_timexes:
            assert 'tid' in other_timex
            if other_timex['tid'] == 't0':
                continue
            if 'beginPoint' in cur_timex and cur_timex['beginPoint'] == other_timex['tid']:
                begin_point = other_timex
            if 'endPoint' in cur_timex and cur_timex['endPoint'] == other_timex['tid']:
                end_point = other_timex
    if only_implicit:
        # Discard time points that are not implicit
        if begin_point and ('_start' in begin_point or 'text' in begin_point):
            begin_point = None
        if end_point and ('_start' in end_point or 'text' in end_point):
            end_point = None
    return begin_point, end_point


def is_removable_interval_timex( timex, other_timexes ):
    '''Returns True iff timex has 'beginPoint' and 'endPoint',
       and both of these are referring to explicit timexes in
       text. Main idea: if explicit timepoints exist, then the
       timex itself must be an implicit interval, which can be 
       removed (to avoid duplicates in annotations).'''
    if timex['type'] == 'DURATION':
        beginTimex, endTimex = \
             get_child_timepoints( timex, other_timexes, \
                                   only_implicit=False )
        if beginTimex and '_start' in beginTimex and \
           endTimex and '_start' in endTimex:
            return True
    return False


def locations_overlap( a, b, x, y ):
    '''Detects if text locations [a:b] and [x:y] are overlapping.
       Inspiration from: 
       https://github.com/estnltk/estnltk/blob/version_1.6/estnltk/layer/span_operations.py
    '''
    return (a <= x and y <= b) or (x <= a and b <= y) or \
           (a <= x and x <= b) or (x <= b and b <= y)


def _debug_concise_timex_str( timex_span ):
    '''Returns a string of concise timex annotations.'''
    assert timex_span._layer is not None
    annotation = timex_span.annotations[0]
    out_str = ['{']
    out_str.append('text={!r}'.format(timex_span.text))
    for attr in timex_span._layer.attributes:
        if attr in annotation and annotation[attr] is not None:
            out_str.append(';')
            out_str.append('{}={!r}'.format(attr,annotation[attr]))
    out_str.append('}')
    return ''.join(out_str)


def create_new_text_obj( fname, metadata, cur_text_len, cur_tokens, cur_tok_id, \
                         raw_timexes, timexes_layer_name='gold_timexes' ):
    '''Based on the snapshot of data collected from the file, creates a 
       new EstNLTK v1.6 Text object, and populates with metadata and gold 
       standard timexes layer. Returns the Text object.'''
    # Construct new text object
    text_str = ''.join(cur_tokens)
    assert len(text_str) == cur_text_len
    text_obj = Text( text_str )
    # Add metadata
    text_obj.meta['source_file'] = fname
    assert len(metadata) >= 1
    if len(metadata) > 1:
        print('Warn! Unexpected number of metadata items {!r}. Using only first.'.format(metadata))
    for (k,v) in metadata[0].items():
        text_obj.meta[k] = v
    text_obj.meta['_original_token_count'] = cur_tok_id
    # Add document creation date
    for timex in raw_timexes:
        if 'functionInDocument' in timex and \
            timex['functionInDocument'] == 'CREATION_TIME':
            assert 'value' in timex
            text_obj.meta['document_creation_time'] = timex['value']
            if 'comment' in timex:
                text_obj.meta['dct_comment'] = timex['comment']
            break
    # Add TIMEX-es layer
    timexes_layer = Layer(name=timexes_layer_name, \
                          attributes=('tid', 'type', 'value', 'temporal_function', 'anchor_time_id', \
                                      'mod', 'quant', 'freq', 'begin_point', 'end_point', 'part_of_interval', \
                                      'comment' ), \
                          text_object=text_obj,\
                          ambiguous=False)
    for timex in raw_timexes:
        if '_start' in timex and '_end' in timex:
            # Determine if this TIMEX is part of an interval (without textual content)
            interval_timex, place_in_interval = get_parent_of_interval( timex, raw_timexes )
            if interval_timex:
                if interval_timex.get('type', None) == 'DURATION':
                    # Record interval timex as an implicit timex
                    interval_timex_odict = convert_timex_to_ordered_dict( interval_timex )
                    timex['part_of_interval'] = interval_timex_odict
                else:
                    raise Exception('(!) Unexpected interval_timex {!r} for timex {!r}'.format(interval_timex,timex))
            # Determine if this TIMEX is an implicit interval that has explicit timepoints 
            # in text. If so, skip it to avoid duplicates in annotations
            if is_removable_interval_timex( timex, raw_timexes ):
                continue
            # Determine if this is an explicit interval with one or more implicit time points
            # If so, then attach the implicit time points as OrderedDict-s
            begin_point_tmx, end_point_tmx = get_child_timepoints( timex, raw_timexes, only_implicit=True )
            if begin_point_tmx:
                begin_point_odict = convert_timex_to_ordered_dict( begin_point_tmx )
                timex['beginPoint'] = begin_point_odict
            if end_point_tmx:
                end_point_odict = convert_timex_to_ordered_dict( end_point_tmx )
                timex['endPoint'] = end_point_odict
            # Determine exact position of the timex:
            if 'text' not in timex:
                # Timexes without pre-specified textual position/substring:
                #  _start and _end provide all the information we need
                loc = (timex['_start'], timex['_end'])
                annotations = convert_timex_attributes( copy.deepcopy(timex) )
                for k in annotations.keys():
                    if k not in timexes_layer.attributes:
                        raise Exception('(!) Unexpceted key {!r} in {!r}'.format(k,annotations))
                timexes_layer.add_annotation( loc, **annotations )
            elif 'text' in timex:
                # Timexes with pre-specified textual position/substring:
                #  we need to detect exact indexes of position in text
                loc = (timex['_start'], timex['_end'])
                textual_content = timex['text']
                timex_span = text_obj.text[loc[0]:loc[1]]
                if re.sub('\s+', '', textual_content) == timex_span:
                    # A) strings match if spaces are removed from text, e.g.
                    #    text="31. 12. 1997.a."  vs token="31.12.1997.a."
                    loc = (timex['_start'], timex['_end'])
                    annotations = convert_timex_attributes( copy.deepcopy(timex) )
                    for k in annotations.keys():
                        if k not in timexes_layer.attributes:
                            raise Exception('(!) Unexpceted key {!r} in {!r}'.format(k,annotations))
                    timexes_layer.add_annotation( loc, **annotations )
                elif re.sub('\s+', '', textual_content) == re.sub('\s+', '', timex_span):
                    # B) strings match if spaces are removed from both text and token, e.g.
                    #    text="täna kell 19. 08"  vs token="täna kell 19.08"
                    loc = (timex['_start'], timex['_end'])
                    annotations = convert_timex_attributes( copy.deepcopy(timex) )
                    for k in annotations.keys():
                        if k not in timexes_layer.attributes:
                            raise Exception('(!) Unexpceted key {!r} in {!r}'.format(k,annotations))
                    timexes_layer.add_annotation( loc, **annotations )
                elif textual_content in timex_span:
                    # C) text is a substring of the phrase, e.g.
                    #    text="1899-"  vs  token="1899-1902"
                    i = text_obj.text.find(textual_content, timex['_start'])
                    if i > -1 and i+len(textual_content) <= loc[1]:
                        new_start = i
                        new_end = i + len(textual_content)
                        assert text_obj.text[new_start:new_end]==textual_content
                        loc = (new_start, new_end)
                        annotations = convert_timex_attributes( copy.deepcopy(timex) )
                        for k in annotations.keys():
                            if k not in timexes_layer.attributes:
                                raise Exception('(!) Unexpceted key {!r} in {!r}'.format(k,annotations))
                        timexes_layer.add_annotation( loc, **annotations )
                    else:
                        raise Exception('(!) Unable to detect location of the timex {!r}'.format(timex))
                else:
                    # D) Tricky situation: text only overlaps the phrase.
                    #    So, we must find out its true indexes in text.
                    i = 0
                    candidate_locs = []
                    while (text_obj.text.find(textual_content, i) > -1):
                        i = text_obj.text.find(textual_content, i)
                        j = i + len(textual_content)
                        if locations_overlap( timex['_start'], timex['_end'], i, j ):
                            # if there is an overlap between the token location
                            # and timex location, then we have a candidate
                            if [i,j] not in candidate_locs:
                                candidate_locs.append( [i,j] )
                        i = j
                    if len(candidate_locs) == 0:
                        # Try to search when spaces are removed
                        textual_content = re.sub('\s+', '', textual_content)
                        i = 0
                        while (text_obj.text.find(textual_content, i) > -1):
                            i = text_obj.text.find(textual_content, i)
                            j = i + len(textual_content)
                            if locations_overlap( timex['_start'], timex['_end'], i, j ):
                                # if there is an overlap between the token location
                                # and timex location, then we have a candidate
                                if [i,j] not in candidate_locs:
                                    candidate_locs.append( [i,j] )
                            i = j
                    if len(candidate_locs) == 1:
                        # Exactly one location: all clear!
                        new_start = candidate_locs[0][0]
                        new_end   = candidate_locs[0][1]
                        assert text_obj.text[new_start:new_end]==textual_content
                        loc = (new_start, new_end)
                        annotations = convert_timex_attributes( copy.deepcopy(timex) )
                        for k in annotations.keys():
                            if k not in timexes_layer.attributes:
                                raise Exception('(!) Unexpceted key {!r} in {!r}'.format(k,annotations))
                        timexes_layer.add_annotation( loc, **annotations )
                    elif len(candidate_locs) > 1: 
                        stretch = text_obj.text[candidate_locs[0][0]:candidate_locs[-1][-1]]
                        raise Exception('(!) Multiple possible locations {!r} detected for the timex {!r} in {!r}'.format(candidate_locs,timex, stretch))
                    elif len(candidate_locs) == 0:
                        loc = (timex['_start'], timex['_end'])
                        print( text_obj.text[loc[0]:loc[1]] )
                        raise Exception('(!) Unable to detect location of the timex {!r}'.format(timex))
    text_obj.add_layer( timexes_layer )
    return text_obj


def import_t3_olp_ajav_file( fpath, fname, token_sep = ' ', 
                                           sentence_sep = '\n', 
                                           paragraph_sep = '\n\n', 
                                           timexes_layer_name='gold_timexes',
                                           add_subcorpus_name = True ):
    '''Imports content of given t3_olp_ajav file as an EstNLTK Text object.
       Reconstructs text using token_sep, sentence_sep and paragraph_sep 
       correspondingly as token, sentence and paragraph separators.
       Populates the Text object with metadata and a flat timexes layer,
       naming it 'gold_timexes' by default.
       Returns the Text object.'''
    ignore_part = []
    inside_ignore = False
    prev_was_sent_end = False
    metadata   = []
    cur_tokens = []
    cur_text_len = 0
    cur_tok_id   = 0
    sentence_locs = []
    raw_timexes   = []
    nested_timexes      = []
    nested_timex_starts = []
    with open( fpath, 'r', encoding='utf-8' ) as in_f:
        # Parse t3_olp_ajav file
        for line in in_f:
            line = line.strip()
            single_tag_match = single_tag_line_pat.match(line)
            if single_tag_match:
                tag_str = single_tag_match.group(1)
                tag_attribs = None
                if tag_str.lower().startswith('<timex'):
                    tag_attribs = parse_tag_attributes( tag_str )
                    if tag_str.lower().strip().endswith('/>'):
                        # an empty TIMEX tag (can also be DCT )
                        tag_attribs = parse_tag_attributes( tag_str )
                        assert '_start' not in tag_attribs and '_end' not in tag_attribs
                        raw_timexes.append( tag_attribs )
                    elif not tag_str.lower().strip().endswith('/>'):
                        # TIMEX tag starting a phrase
                        tag_attribs = parse_tag_attributes( tag_str )
                        assert '_start' not in tag_attribs
                        start_pos = cur_text_len
                        if len(cur_tokens) > 0:
                            if not prev_was_sent_end:
                                start_pos += len(token_sep)
                        nested_timexes.append( tag_attribs )
                        nested_timex_starts.append( start_pos )
                if tag_str.lower().startswith('</timex'):
                    # TIMEX tag ending a phrase
                    tag_attribs = nested_timexes.pop()
                    start_pos = nested_timex_starts.pop()
                    assert '_start' not in tag_attribs
                    assert '_end' not in tag_attribs
                    tag_attribs['_start'] = start_pos
                    tag_attribs['_end'] = cur_text_len
                    assert 'tid' in tag_attribs, '(!) Timex missing attrib "tid": {!r}'.format(tag_attribs)
                    assert 'type' in tag_attribs, '(!) Timex missing attrib "type": {!r}'.format(tag_attribs)
                    raw_timexes.append( tag_attribs )
                # document metadata
                if tag_str.lower().startswith('<ignoreeri'):
                    inside_ignore = True
                elif tag_str.lower().startswith('</ignoreeri'):
                    inside_ignore = False
                    cur_metadata = parse_doc_metadata( ignore_part )
                    ignore_part = []
                    if len(metadata) > 0 and len(cur_tokens) > 0:
                        # Previous metadata exists: mark this position
                        # as a paragraph boundary
                        if cur_tokens[-1] == sentence_sep and sentence_sep in paragraph_sep:
                            # Replace sentence separator with paragraph separator
                            cur_tokens[-1] = paragraph_sep
                            cur_text_len += len(paragraph_sep) - len(sentence_sep)
                        else:
                            # Add new paragraph separator
                            cur_tokens.append(paragraph_sep)
                            cur_text_len += len(paragraph_sep)
                    else:
                        # Metadata seen first time: just record it
                        metadata.append( cur_metadata )
                # sentence boundaries
                if tag_str.lower().startswith('<s>'):
                    sentence_locs.append( [cur_text_len] )
                elif tag_str.lower().startswith('</s>'):
                    # add sentence separator str
                    cur_tokens.append(sentence_sep)
                    cur_text_len += len(sentence_sep)
                    assert len(sentence_locs[-1]) == 1
                    sentence_locs[-1].append( cur_text_len )
                    prev_was_sent_end = True
                #print(tag_str,tag_attribs)
            else:
                # Collect content inside ignore (document metadata)
                if inside_ignore:
                    ignore_part.append( line )
                elif '    ' in line:
                    line_analyses = line.split('    ')
                    word_token = line_analyses[0]
                    if len(cur_tokens) > 0 and not prev_was_sent_end:
                        # add token separator str
                        cur_tokens.append(token_sep)
                        cur_text_len += len(token_sep)
                    cur_tokens.append(word_token)
                    cur_tok_id += 1
                    cur_text_len += len(word_token)
                    prev_was_sent_end = False
                else:
                    raise Exception('(!) Unexpected line format {!r}'.format(line))
    # Construct new text object
    if len(cur_tokens) > 0:
        if add_subcorpus_name and len(metadata) == 1:
            subcorpus_name = get_subcorpus_name( fname )
            metadata[0]['_subcorpus'] = subcorpus_name
        return create_new_text_obj( fname, metadata, cur_text_len, cur_tokens, \
                                    cur_tok_id, raw_timexes, timexes_layer_name=timexes_layer_name )
    else:
        return None


def extract_tags_from_position( content, pos ):
    '''Extract all (consecutive) tags from the given position 
       in the content string. Returns a list of extracted tags,
       and the last position in the (last) ending tag. '''
    tags = []
    symbol = content[pos]
    if symbol == '<':
        # Extract tags
        cur_tag = []
        while pos < len(content):
            symbol = content[pos]
            cur_tag.append( symbol )
            if symbol == '>':
                tags.append( ''.join(cur_tag) )
                # chk for consecutive tags:
                # check if the next symbol is a tag start
                if pos + 1 < len(content) and \
                   content[pos + 1] == '<':
                    # start collecting next tag
                    cur_tag = []
                else:
                    break
            pos += 1
    return tags, pos


def fix_timex_start_end_locations( clean_text, raw_timexes ):
    '''Fixes/Adjusts timex tags' start and end positions:  
       trims whitespace and quotation marks around timex phrases, 
       and removes redundant punctuation from the end of timex 
       phrases.
    '''
    text_str = ''.join(clean_text)
    for timex in raw_timexes:
        if '_start' in timex:
            while text_str[timex['_start']].isspace() or \
                text_str[timex['_start']] in ['«']:
                timex['_start'] += 1
            while text_str[timex['_end']-1].isspace() or \
                text_str[timex['_end']-1] in ['?',',','!', '»']:
                timex['_end'] -= 1
    return raw_timexes


def import_tml_file( fpath, fname, timexes_layer_name='gold_timexes' ):
    '''Imports content of given tml file as an EstNLTK Text object.
       Preserves text's layout and structure as it is in the original
       tml file.
       Populates the Text object with metadata (creation date) and a 
       flat timexes layer, naming it 'gold_timexes' by default.
       Returns the Text object.'''
    # Read file content
    file_content = None
    with open( fpath, 'r', encoding='utf-8' ) as in_f:
        file_content = in_f.read()
    # Clean XML auxiliary stuff
    file_content = re.sub('<\?xml[^<>]+>','', file_content)
    file_content = re.sub('</?TimeML>','', file_content)
    file_content = re.sub('^\s+','', file_content)
    file_content = re.sub('\s+$','', file_content)
    # Collect annotations from the file content
    tagged_index = 0
    clean_text     = []
    raw_timexes    = []
    nested_timexes = []
    while tagged_index < len(file_content):
        symbol = file_content[ tagged_index ]
        if symbol == '<':
            # Extract tags
            tags, tagged_index = extract_tags_from_position( file_content, tagged_index )
            assert len(tags) > 0
            for tag_str in tags:
                if tag_str.lower().startswith('<timex'):
                    tag_attribs = parse_tag_attributes( tag_str )
                    if tag_str.lower().strip().endswith('/>'):
                        # an empty TIMEX tag (can also be DCT )
                        tag_attribs = parse_tag_attributes( tag_str )
                        assert '_start' not in tag_attribs and '_end' not in tag_attribs
                        raw_timexes.append( tag_attribs )
                    else:
                        # TIMEX tag starting a phrase
                        tag_attribs = parse_tag_attributes( tag_str )
                        assert '_start' not in tag_attribs
                        tag_attribs['_start'] = len(clean_text)
                        nested_timexes.append( tag_attribs )
                elif tag_str.lower().startswith('</timex'):
                    # TIMEX tag ending a phrase
                    tag_attribs = nested_timexes.pop()
                    assert '_start' in tag_attribs
                    assert '_end' not in tag_attribs
                    tag_attribs['_end'] = len(clean_text)
                    assert 'tid' in tag_attribs, '(!) Timex missing attrib "tid": {!r}'.format(tag_attribs)
                    assert 'type' in tag_attribs, '(!) Timex missing attrib "type": {!r}'.format(tag_attribs)
                    raw_timexes.append( tag_attribs )
        else:
            clean_text.append( symbol )
        tagged_index += 1
    # Construct new text object
    if len(clean_text) > 0:
        # Fix start/end locations of timexes
        raw_timexes = fix_timex_start_end_locations( clean_text, raw_timexes )
        metadata = [{}]
        text_str = ''.join(clean_text)
        text_str = re.sub('\s+',' ', text_str)
        raw_token_count = len(text_str.split())
        return create_new_text_obj( fname, metadata, len(clean_text), clean_text, \
                                    raw_token_count, raw_timexes, timexes_layer_name=timexes_layer_name )
    else:
        return None

