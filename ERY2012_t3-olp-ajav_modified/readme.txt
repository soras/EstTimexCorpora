-----------------------------------------------------------------------
 The ERY2012 corpus
 (modified version)
-----------------------------------------------------------------------
   This corpus consists of 113 Estonian texts with manually corrected 
  temporal expression annotations (total 1905 temporal expressions). 
  The corpus was initially used for the evaluation of Estonian Temporal 
  Expression Tagger (Ajavt) in (Orasmaa, 2012).
  
  After the publication, minor corrections have been made in the corpus, 
  so the numbers of words and timexes in this corpus are slightly 
  different than the numbers reported in the publication.

-----------------------------------------------------------------------
  Corpus structure
-----------------------------------------------------------------------
  Directories:
  [t3-olp-ajav] -- contains text files with morphological analyses (t3), 
                   clause boundary annotations (olp) and temporal 
                   expression annotations (ajav);
                   morphological analyses and clause boundary annotations 
                   have been produced automatically;
  [testlog] -- a directory reserved for saving results of the automated 
               evaluation (evaluation tools are not included in this 
               distribution);

-----------------------------------------------------------------------
  Corpus files and sources
-----------------------------------------------------------------------
   All of the corpus files have been taken from the Reference Corpus 
  of Estonian (Kaalep et al., 2010).

   The genre or the subgenre of the text file can be determined from 
  the prefix of the file:
    * aja-arvamus  -- Newspaper articles: Opinions
    * aja-eesti    -- Newspaper articles: Local (Estonian) news
    * aja-kultuur  -- Newspaper articles: Culture
    * aja-majandus -- Newspaper articles: Economy
    * aja-sport    -- Newspaper articles: Sport
    * aja-valismaa -- Newspaper articles: Foreign news
    * ajalugu      -- Historical articles
    * rkogu        -- Estonian parliament transcripts
    * sea          -- Estonian law texts

   All the corpus files should be in UTF-8 encoding. 

   Document creation time (DCT): the full creation date, if it is 
  available, can be found from the first line of each *.t3-olp-ajav
  file (an empty TIMEX with index "t0"); 
   Note that DCT is not always fully specified date, e.g. in case of
  historical articles, only the year when the article was written is 
  exactly known; 
   In parliament transcripts, the creation time is more detailed 
  than date, containing the exact time when the meeting began;

-----------------------------------------------------------------------
  The annotation format
-----------------------------------------------------------------------
  The TIMEX annotation format is based on the TIMEX3 in TimeML 
  ( http://www.timeml.org/site/index.html ).
  
  Exact description of the format can be found from:
   https://github.com/soras/EstTimeMLCorpus/blob/master/docs-et/ajav2ljendite_m2rgendamine_06.pdf
   (currently only in Estonian)

-----------------------------------------------------------------------
  References
-----------------------------------------------------------------------
  Kaalep, H. J., Muischnek, K., Uiboaed, K., and Veskis, K. (2010). The Estonian 
  Reference Corpus: Its Composition and Morphology-aware User Interface. In 
  Baltic HLT, pages 143–146.

  Orasmaa, S. (2012) "Automaatne ajaväljendite tuvastamine eestikeelsetes tekstides" 
  (Automatic Recognition and Normalization of Temporal Expressions in Estonian 
  Language Texts). Eesti Rakenduslingvistika Ühingu aastaraamat 8: 153-169.

