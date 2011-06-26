set client_encoding='UTF8';

begin;
-- Load datafiles
\copy description_tb from description_tb.txt
\copy part_tb from part_tb.txt
\copy active_tb from active_tb.txt
\copy description_tag_tb from description_tag_tb.txt
\copy translation_tb from translation_tb.txt
\copy part_description_tb from part_description_tb.txt
\copy package_version_tb from package_version_tb.txt

-- Update sequences
select setval('description_tb_description_id_seq', (select max(description_id)+1 from description_tb));
select setval('part_tb_part_id_seq', (select max(part_id)+1 from part_tb));
select setval('description_tag_tb_description_tag_id_seq', (select max(description_tag_id)+1 from description_tag_tb));
select setval('translation_tb_translation_id_seq', (select max(translation_id)+1 from translation_tb));
select setval('part_description_tb_part_description_id_seq', (select max(part_description_id)+1 from part_description_tb));
select setval('package_version_tb_package_version_id_seq', (select max(package_version_id)+1 from package_version_tb));

commit;
