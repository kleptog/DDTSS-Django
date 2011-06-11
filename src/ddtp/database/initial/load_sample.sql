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

commit;
