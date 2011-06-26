set client_encoding='UTF8';

begin;
-- Load datafiles
\copy languages_tb from languages_tb.txt
\copy pendingtranslations_tb from pendingtranslations_tb.txt
\copy pendingtranslationreview_tb from pendingtranslationreview_tb.txt

-- Update sequences
select setval('pendingtranslations_tb_pending_translation_id_seq', (select max(pending_translation_id)+1 from pendingtranslations_tb));

commit;
