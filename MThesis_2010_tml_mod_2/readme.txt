-----------------------------------------------------------------------
 The Mthesis2010 corpus
 (The TIMEX3 version)
-----------------------------------------------------------------------
  
  This corpus consists of 315 Estonian newspaper articles with manually
 corrected temporal expression (TIMEX3) annotations. The initial version
 of the corpus was created as a development and evaluation corpus for
 Estonian Temporal Expression Tagger (Ajavt) in my master's thesis 
 (Orasmaa, 2010).
 
  As the initial annotation format of the corpus was unstandard, the 
 corpus has been later converted into a TimeML TIMEX3-based annotation 
 format. The conversion process included:
    *) converting annotated temporal expressions into TIMEX3 format;
    *) removing temporal expressions without TIMEX3 value and type;
    *) splitting multi-document files into single-document files;
       (the initial corpus had files containing hundreds of documents 
        lumped together into single file)
    *) removing documents without any remaining TIMEX3-s;
 Most of the conversion has been done automatically, with few manual
 checking & corrections.

-----------------------------------------------------------------------
  Corpus structure
-----------------------------------------------------------------------
  Directories:
  [tml] -- contains TimeML (*.TML) files of the corpus; 
  [mrf] -- contains morphological analyses of *.TML files; 
           morphological analysis and disambiguation has been produced 
           automatically, using Filosoft's T3MESTA tool;
  [testlog] -- a directory reserved for saving results of the automated 
               evaluation (evaluation tools are not included in this 
               distribution);

-----------------------------------------------------------------------
  Corpus files and sources
-----------------------------------------------------------------------
  
   The corpus consists of articles from two Estonian daily newspapers 
  - "Postimees" and "Eesti Päevaleht" - from time period 2000-2010 
  (unequally distributed over the period);

   Following is a list of files in the corpus folder (the wildcard symbol 
  * indicates the numeric counter part or the date part in the file name, 
  merging together multiple file names matching a common pattern):
  
  020408_esileht_siseuudised_tallinn_321170.tml
    source: WEB ( www.postimees.ee )
    
  121107_tartu_postimees_294977.tml
    source: WEB ( www.postimees.ee )
    
  170408_tartu_postimees_324624.tml
    source: WEB ( www.postimees.ee )
    
  2000-04-19_postimees_1_*.tml
    30 articles, source: REF_CORPUS ( Postimees )
    
  2000-04-19_postimees_2_*.tml
    34 articles, source: REF_CORPUS ( Postimees )
  
  200508_esileht_krimi_331590.tml
    source: WEB ( www.postimees.ee )
    
  2006-08-12_EPL_*.tml
    82 articles, source: REF_CORPUS ( Eesti Päevaleht )
  
  2007-01-07_epl_*.tml
    7 articles, source: REF_CORPUS ( Eesti Päevaleht )
  
  2007-02-01_epl_*.tml
    17 articles, source: REF_CORPUS ( Eesti Päevaleht )
  
  2007-06-16_epl_*.tml
    73 articles, source: REF_CORPUS ( Eesti Päevaleht )

  2007-08-27_epl_*.tml
    20 articles, source: REF_CORPUS ( Eesti Päevaleht )
  
  2007-10-19_epl_*.tml
    23 articles, source: REF_CORPUS ( Eesti Päevaleht )
  
  2009-*_postimees.tml
    19 articles, source: WEB ( www.postimees.ee )

  2010-*_postimees.tml
    6 articles, source: WEB ( www.postimees.ee )


  Sources:
    WEB 
        The article text has been copied from the online version of 
        the newspaper; The general url of the newspaper is in 
        parenthesis;
        Usually, the first sentence is the title of the article;
        in most cases, the web page of the article can be found by 
        googling the exact title.
          
    REF_CORPUS
        The article has been taken from the Estonian Reference Corpus
        ( http://www.cl.ut.ee/korpused/segakorpus/index.php?lang=en )
        The name of the corresponding daily newspaper is indicated
        in parenthesis, and the prefix of the file name indicates 
        the publication date of the article.
        Originally, articles of the Corpus were fetched 
        by automatic web crawling programs, and they have gone through 
        multiple format conversions ever since.
        The article typically has a different tokenisation than the 
        original text had, and there can be some other differences due 
        to conversion errors (e.g. wrong characters due to encoding 
        conversion errors).


  All the corpus files should be in UTF-8 encoding. 
  
  The creation date of the document could be in the file name, but it 
  can always be found as an empty TIMEX3 at the beginning of the 
  file (a TIMEX3 with index "t0");
  
-----------------------------------------------------------------------
  The annotation format
-----------------------------------------------------------------------

 The corpus TML files should validate against "timeml_1.2.1_modified.dtd";

 Notable divergences from the standard TimeML format (http://www.timeml.org):
   value:
     XXXX-XX-WD       -  'WD' refers to a 'working day' or 'working days' 
                         (as opposed to 'weekends');
     XXXX-XX-XTXX     -  'TXX' refers to an unspecified hour;
     XXXX-XX-XTXX:XX  -  'TXX:XX' refers to an unspecified minute/moment;
   
   mod:
     FIRST_HALF       - refers to the first half of the time period
                        (e.g. "first half of the April");
     SECOND_HALF      - refers to the second half of the time period;
   
   
   SET-expressions:
     If semantics of the expression cannot be expressed with TIMEX3 value,
     the TIMEX2 value format is used instead, e.g.
        <TIMEX3 type="SET" value="XXXX-WXX-6">laupäeviti</TIMEX3>
        (on Saturdays)
     
     freq - is not duration (like specified in 'timeml_1.2.xsd'), but 
      contains an integer value and a time granularity;
     
   comment
     comments are allowed, unlike in 'timeml_1.2.xsd';
     (currently, all the comments are in Estonian)
     
       
-----------------------------------------------------------------------
  References
-----------------------------------------------------------------------

 Orasmaa, S. (2010). Ajaväljendite tuvastamine eestikeelses tekstis 
 (Recognition and Resolution of Estonian Temporal Expressions). Master’s 
 thesis, University of Tartu. (in Estonian).
  ( url: http://comserv.cs.ut.ee/forms/ati_report/downloader.php?file=F0E53012D5F88F71DD6E2E84830460F334E14EA2 )
 
    