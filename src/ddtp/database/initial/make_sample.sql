set client_encoding='UTF8';

-- First determine a sample of the database to dump
select distinct source into temp d_sources from description_tb where random() < 0.001 and source not like 'linux%';

select description_id into temp d_descr from description_tb where source in (select source from d_sources);

select distinct part_md5 into temp d_partmd5 from part_description_tb where description_id in (select description_id from d_descr);

-- Then dump it
\copy (select * from active_tb where description_id in (select description_id from d_descr)) to /tmp/active_tb.txt
\copy (select * from description_tag_tb where description_id in (select description_id from d_descr)) to /tmp/description_tag_tb.txt
\copy (select * from translation_tb where description_id in (select description_id from d_descr)) to /tmp/translation_tb.txt
\copy (select * from part_description_tb where description_id in (select description_id from d_descr)) to /tmp/part_description_tb.txt
\copy (select * from description_tb where description_id in (select description_id from d_descr)) to /tmp/description_tb.txt
\copy (select * from package_version_tb where description_id in (select description_id from d_descr)) to /tmp/package_version_tb.txt
\copy (select * from part_tb where part_md5 in (select part_md5 from d_partmd5)) to /tmp/part_tb.txt

-- And DDTSS stuff too

\copy languages_tb to /tmp/languages_tb.txt
\copy (select * from pendingtranslations_tb where description_id in (select description_id from d_descr)) to /tmp/pendingtranslations_tb.txt
\copy (select * from pendingtranslationreview_tb where pending_translation_id in (select pending_translation_id from pendingtranslations_tb where description_id in (select description_id from d_descr))) to /tmp/pendingtranslationreview_tb.txt
