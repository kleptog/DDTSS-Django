set client_encoding='UTF8';

begin;
-- Load datafiles
\copy languages_tb from languages_tb.txt
\copy pendingtranslations_tb from pendingtranslations_tb.txt
\copy pendingtranslationreview_tb from pendingtranslationreview_tb.txt

commit;
