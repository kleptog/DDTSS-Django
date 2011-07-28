--
-- PostgreSQL database dump
--

SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: active_tb; Type: TABLE; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE TABLE active_tb (
    description_id integer NOT NULL
);


--
-- Name: description_tag_tb; Type: TABLE; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE TABLE description_tag_tb (
    description_tag_id integer NOT NULL,
    description_id integer NOT NULL,
    tag text NOT NULL,
    date_begin date NOT NULL,
    date_end date NOT NULL
);


--
-- Name: description_tag_tb_description_tag_id_seq; Type: SEQUENCE; Schema: public; Owner: ddtp
--

CREATE SEQUENCE description_tag_tb_description_tag_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


--
-- Name: description_tag_tb_description_tag_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: ddtp
--

ALTER SEQUENCE description_tag_tb_description_tag_id_seq OWNED BY description_tag_tb.description_tag_id;


--
-- Name: description_tb; Type: TABLE; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE TABLE description_tb (
    description_id integer NOT NULL,
    description_md5 text NOT NULL,
    description text NOT NULL,
    prioritize integer DEFAULT 10,
    package text NOT NULL,
    source text NOT NULL
);


--
-- Name: description_tb_description_id_seq; Type: SEQUENCE; Schema: public; Owner: ddtp
--

CREATE SEQUENCE description_tb_description_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


--
-- Name: description_tb_description_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: ddtp
--

ALTER SEQUENCE description_tb_description_id_seq OWNED BY description_tb.description_id;


--
-- Name: owner_tb; Type: TABLE; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE TABLE owner_tb (
    owner_id integer NOT NULL,
    owner text NOT NULL,
    language text NOT NULL,
    lastsend date NOT NULL,
    lastseen date DEFAULT '2000-01-01'::date,
    description_id integer NOT NULL
);


--
-- Name: owner_tb_owner_id_seq; Type: SEQUENCE; Schema: public; Owner: ddtp
--

CREATE SEQUENCE owner_tb_owner_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


--
-- Name: owner_tb_owner_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: ddtp
--

ALTER SEQUENCE owner_tb_owner_id_seq OWNED BY owner_tb.owner_id;


--
-- Name: package_version_tb; Type: TABLE; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE TABLE package_version_tb (
    package_version_id integer NOT NULL,
    package text NOT NULL,
    version text NOT NULL,
    description_id integer NOT NULL
);


--
-- Name: package_version_tb_package_version_id_seq; Type: SEQUENCE; Schema: public; Owner: ddtp
--

CREATE SEQUENCE package_version_tb_package_version_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


--
-- Name: package_version_tb_package_version_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: ddtp
--

ALTER SEQUENCE package_version_tb_package_version_id_seq OWNED BY package_version_tb.package_version_id;


--
-- Name: packages_tb; Type: TABLE; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE TABLE packages_tb (
    packages_id integer NOT NULL,
    package text NOT NULL,
    source text NOT NULL,
    version text NOT NULL,
    tag text,
    priority text NOT NULL,
    maintainer text NOT NULL,
    task text,
    section text NOT NULL,
    description text NOT NULL,
    description_md5 text NOT NULL
);


--
-- Name: packages_tb_packages_id_seq; Type: SEQUENCE; Schema: public; Owner: ddtp
--

CREATE SEQUENCE packages_tb_packages_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


--
-- Name: packages_tb_packages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: ddtp
--

ALTER SEQUENCE packages_tb_packages_id_seq OWNED BY packages_tb.packages_id;


--
-- Name: part_description_tb; Type: TABLE; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE TABLE part_description_tb (
    part_description_id integer NOT NULL,
    description_id integer NOT NULL,
    part_md5 text NOT NULL
);


--
-- Name: part_description_tb_part_description_id_seq; Type: SEQUENCE; Schema: public; Owner: ddtp
--

CREATE SEQUENCE part_description_tb_part_description_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


--
-- Name: part_description_tb_part_description_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: ddtp
--

ALTER SEQUENCE part_description_tb_part_description_id_seq OWNED BY part_description_tb.part_description_id;


--
-- Name: part_tb; Type: TABLE; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE TABLE part_tb (
    part_id integer NOT NULL,
    part_md5 text NOT NULL,
    part text NOT NULL,
    language text NOT NULL
);


--
-- Name: part_tb_part_id_seq; Type: SEQUENCE; Schema: public; Owner: ddtp
--

CREATE SEQUENCE part_tb_part_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


--
-- Name: part_tb_part_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: ddtp
--

ALTER SEQUENCE part_tb_part_id_seq OWNED BY part_tb.part_id;


--
-- Name: ppart_tb; Type: TABLE; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE TABLE ppart_tb (
    ppart_id integer NOT NULL,
    ppart_md5 text NOT NULL,
    ppart text NOT NULL,
    language text NOT NULL
);


--
-- Name: ppart_tb_ppart_id_seq; Type: SEQUENCE; Schema: public; Owner: ddtp
--

CREATE SEQUENCE ppart_tb_ppart_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


--
-- Name: ppart_tb_ppart_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: ddtp
--

ALTER SEQUENCE ppart_tb_ppart_id_seq OWNED BY ppart_tb.ppart_id;


--
-- Name: suggestion_tb; Type: TABLE; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE TABLE suggestion_tb (
    suggestion_id integer NOT NULL,
    package text NOT NULL,
    version text NOT NULL,
    description_md5 text NOT NULL,
    translation text NOT NULL,
    language text NOT NULL,
    importer text NOT NULL,
    importtime date NOT NULL
);


--
-- Name: suggestion_tb_suggestion_id_seq; Type: SEQUENCE; Schema: public; Owner: ddtp
--

CREATE SEQUENCE suggestion_tb_suggestion_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


--
-- Name: suggestion_tb_suggestion_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: ddtp
--

ALTER SEQUENCE suggestion_tb_suggestion_id_seq OWNED BY suggestion_tb.suggestion_id;


--
-- Name: translation_tb; Type: TABLE; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE TABLE translation_tb (
    translation_id integer NOT NULL,
    translation text NOT NULL,
    language text NOT NULL,
    description_id integer NOT NULL
);


--
-- Name: translation_tb_translation_id_seq; Type: SEQUENCE; Schema: public; Owner: ddtp
--

CREATE SEQUENCE translation_tb_translation_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


--
-- Name: translation_tb_translation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: ddtp
--

ALTER SEQUENCE translation_tb_translation_id_seq OWNED BY translation_tb.translation_id;


--
-- Name: version_tb; Type: TABLE; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE TABLE version_tb (
    version_id integer NOT NULL,
    version text NOT NULL,
    description_id integer NOT NULL
);


--
-- Name: version_tb_version_id_seq; Type: SEQUENCE; Schema: public; Owner: ddtp
--

CREATE SEQUENCE version_tb_version_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


--
-- Name: version_tb_version_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: ddtp
--

ALTER SEQUENCE version_tb_version_id_seq OWNED BY version_tb.version_id;


--
-- Name: description_tag_id; Type: DEFAULT; Schema: public; Owner: ddtp
--

ALTER TABLE description_tag_tb ALTER COLUMN description_tag_id SET DEFAULT nextval('description_tag_tb_description_tag_id_seq'::regclass);


--
-- Name: description_id; Type: DEFAULT; Schema: public; Owner: ddtp
--

ALTER TABLE description_tb ALTER COLUMN description_id SET DEFAULT nextval('description_tb_description_id_seq'::regclass);


--
-- Name: owner_id; Type: DEFAULT; Schema: public; Owner: ddtp
--

ALTER TABLE owner_tb ALTER COLUMN owner_id SET DEFAULT nextval('owner_tb_owner_id_seq'::regclass);


--
-- Name: package_version_id; Type: DEFAULT; Schema: public; Owner: ddtp
--

ALTER TABLE package_version_tb ALTER COLUMN package_version_id SET DEFAULT nextval('package_version_tb_package_version_id_seq'::regclass);


--
-- Name: packages_id; Type: DEFAULT; Schema: public; Owner: ddtp
--

ALTER TABLE packages_tb ALTER COLUMN packages_id SET DEFAULT nextval('packages_tb_packages_id_seq'::regclass);


--
-- Name: part_description_id; Type: DEFAULT; Schema: public; Owner: ddtp
--

ALTER TABLE part_description_tb ALTER COLUMN part_description_id SET DEFAULT nextval('part_description_tb_part_description_id_seq'::regclass);


--
-- Name: part_id; Type: DEFAULT; Schema: public; Owner: ddtp
--

ALTER TABLE part_tb ALTER COLUMN part_id SET DEFAULT nextval('part_tb_part_id_seq'::regclass);


--
-- Name: ppart_id; Type: DEFAULT; Schema: public; Owner: ddtp
--

ALTER TABLE ppart_tb ALTER COLUMN ppart_id SET DEFAULT nextval('ppart_tb_ppart_id_seq'::regclass);


--
-- Name: suggestion_id; Type: DEFAULT; Schema: public; Owner: ddtp
--

ALTER TABLE suggestion_tb ALTER COLUMN suggestion_id SET DEFAULT nextval('suggestion_tb_suggestion_id_seq'::regclass);


--
-- Name: translation_id; Type: DEFAULT; Schema: public; Owner: ddtp
--

ALTER TABLE translation_tb ALTER COLUMN translation_id SET DEFAULT nextval('translation_tb_translation_id_seq'::regclass);


--
-- Name: version_id; Type: DEFAULT; Schema: public; Owner: ddtp
--

ALTER TABLE version_tb ALTER COLUMN version_id SET DEFAULT nextval('version_tb_version_id_seq'::regclass);


--
-- Name: description_tb_description_md5_key; Type: CONSTRAINT; Schema: public; Owner: ddtp; Tablespace: 
--

ALTER TABLE ONLY description_tb
    ADD CONSTRAINT description_tb_description_md5_key UNIQUE (description_md5);


--
-- Name: description_tb_pkey; Type: CONSTRAINT; Schema: public; Owner: ddtp; Tablespace: 
--

ALTER TABLE ONLY description_tb
    ADD CONSTRAINT description_tb_pkey PRIMARY KEY (description_id);


--
-- Name: owner_tb_pkey; Type: CONSTRAINT; Schema: public; Owner: ddtp; Tablespace: 
--

ALTER TABLE ONLY owner_tb
    ADD CONSTRAINT owner_tb_pkey PRIMARY KEY (owner_id);


--
-- Name: package_version_tb_pkey; Type: CONSTRAINT; Schema: public; Owner: ddtp; Tablespace: 
--

ALTER TABLE ONLY package_version_tb
    ADD CONSTRAINT package_version_tb_pkey PRIMARY KEY (package_version_id);


--
-- Name: packages_tb_pkey; Type: CONSTRAINT; Schema: public; Owner: ddtp; Tablespace: 
--

ALTER TABLE ONLY packages_tb
    ADD CONSTRAINT packages_tb_pkey PRIMARY KEY (packages_id);


--
-- Name: part_description_tb_pkey; Type: CONSTRAINT; Schema: public; Owner: ddtp; Tablespace: 
--

ALTER TABLE ONLY part_description_tb
    ADD CONSTRAINT part_description_tb_pkey PRIMARY KEY (part_description_id);


--
-- Name: part_tb_pkey; Type: CONSTRAINT; Schema: public; Owner: ddtp; Tablespace: 
--

ALTER TABLE ONLY part_tb
    ADD CONSTRAINT part_tb_pkey PRIMARY KEY (part_id);


--
-- Name: ppart_tb_pkey; Type: CONSTRAINT; Schema: public; Owner: ddtp; Tablespace: 
--

ALTER TABLE ONLY ppart_tb
    ADD CONSTRAINT ppart_tb_pkey PRIMARY KEY (ppart_id);


--
-- Name: ppart_tb_ppart_md5_key; Type: CONSTRAINT; Schema: public; Owner: ddtp; Tablespace: 
--

ALTER TABLE ONLY ppart_tb
    ADD CONSTRAINT ppart_tb_ppart_md5_key UNIQUE (ppart_md5);


--
-- Name: suggestion_tb_pkey; Type: CONSTRAINT; Schema: public; Owner: ddtp; Tablespace: 
--

ALTER TABLE ONLY suggestion_tb
    ADD CONSTRAINT suggestion_tb_pkey PRIMARY KEY (suggestion_id);


--
-- Name: translation_tb_pkey; Type: CONSTRAINT; Schema: public; Owner: ddtp; Tablespace: 
--

ALTER TABLE ONLY translation_tb
    ADD CONSTRAINT translation_tb_pkey PRIMARY KEY (translation_id);


--
-- Name: version_tb_pkey; Type: CONSTRAINT; Schema: public; Owner: ddtp; Tablespace: 
--

ALTER TABLE ONLY version_tb
    ADD CONSTRAINT version_tb_pkey PRIMARY KEY (version_id);


--
-- Name: active_tb_1_idx; Type: INDEX; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE UNIQUE INDEX active_tb_1_idx ON active_tb USING btree (description_id);


--
-- Name: description_tag_tb_new_description_id_key; Type: INDEX; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE INDEX description_tag_tb_new_description_id_key ON description_tag_tb USING btree (description_id, tag);


--
-- Name: description_tag_tb_new_description_id_key1; Type: INDEX; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE INDEX description_tag_tb_new_description_id_key1 ON description_tag_tb USING btree (description_id);


--
-- Name: description_tb_1_idx; Type: INDEX; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE INDEX description_tb_1_idx ON description_tb USING btree (package);


--
-- Name: owner_tb_1_idx; Type: INDEX; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE INDEX owner_tb_1_idx ON owner_tb USING btree (language);


--
-- Name: owner_tb_2_idx; Type: INDEX; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE INDEX owner_tb_2_idx ON owner_tb USING btree (owner);


--
-- Name: owner_tb_3_idx; Type: INDEX; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE UNIQUE INDEX owner_tb_3_idx ON owner_tb USING btree (description_id, language);


--
-- Name: package_tb_1_idx; Type: INDEX; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE INDEX package_tb_1_idx ON packages_tb USING btree (package);


--
-- Name: package_tb_3_idx; Type: INDEX; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE UNIQUE INDEX package_tb_3_idx ON packages_tb USING btree (package, version);


--
-- Name: package_version_tb_1_idx; Type: INDEX; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE INDEX package_version_tb_1_idx ON package_version_tb USING btree (description_id);


--
-- Name: package_version_tb_2_idx; Type: INDEX; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE INDEX package_version_tb_2_idx ON package_version_tb USING btree (package);


--
-- Name: package_version_tb_3_idx; Type: INDEX; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE UNIQUE INDEX package_version_tb_3_idx ON package_version_tb USING btree (description_id, package, version);


--
-- Name: package_version_tb_4_idx; Type: INDEX; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE INDEX package_version_tb_4_idx ON package_version_tb USING btree (package, version);


--
-- Name: part_description_tb_1_idx; Type: INDEX; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE INDEX part_description_tb_1_idx ON part_description_tb USING btree (part_md5);


--
-- Name: part_description_tb_2_idx; Type: INDEX; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE UNIQUE INDEX part_description_tb_2_idx ON part_description_tb USING btree (part_md5, description_id);


--
-- Name: part_tb_1_idx; Type: INDEX; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE INDEX part_tb_1_idx ON part_tb USING btree (language);


--
-- Name: part_tb_2_idx; Type: INDEX; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE INDEX part_tb_2_idx ON part_tb USING btree (part_md5);


--
-- Name: part_tb_3_idx; Type: INDEX; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE UNIQUE INDEX part_tb_3_idx ON part_tb USING btree (part_md5, language);


--
-- Name: ppart_tb_1_idx; Type: INDEX; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE INDEX ppart_tb_1_idx ON ppart_tb USING btree (language);


--
-- Name: ppart_tb_2_idx; Type: INDEX; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE INDEX ppart_tb_2_idx ON ppart_tb USING btree (ppart_md5);


--
-- Name: ppart_tb_3_idx; Type: INDEX; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE UNIQUE INDEX ppart_tb_3_idx ON ppart_tb USING btree (ppart_md5, language);


--
-- Name: suggestion_tb_1_idx; Type: INDEX; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE INDEX suggestion_tb_1_idx ON suggestion_tb USING btree (package);


--
-- Name: suggestion_tb_2_idx; Type: INDEX; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE INDEX suggestion_tb_2_idx ON suggestion_tb USING btree (package, language, description_md5);


--
-- Name: translation_tb_1_idx; Type: INDEX; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE INDEX translation_tb_1_idx ON translation_tb USING btree (language);


--
-- Name: translation_tb_2_idx; Type: INDEX; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE UNIQUE INDEX translation_tb_2_idx ON translation_tb USING btree (description_id, language);


--
-- Name: version_tb_1_idx; Type: INDEX; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE INDEX version_tb_1_idx ON version_tb USING btree (description_id);


--
-- Name: version_tb_3_idx; Type: INDEX; Schema: public; Owner: ddtp; Tablespace: 
--

CREATE UNIQUE INDEX version_tb_3_idx ON version_tb USING btree (description_id, version);


--
-- Name: $1; Type: FK CONSTRAINT; Schema: public; Owner: ddtp
--

ALTER TABLE ONLY translation_tb
    ADD CONSTRAINT "$1" FOREIGN KEY (description_id) REFERENCES description_tb(description_id);


--
-- Name: $1; Type: FK CONSTRAINT; Schema: public; Owner: ddtp
--

ALTER TABLE ONLY owner_tb
    ADD CONSTRAINT "$1" FOREIGN KEY (description_id) REFERENCES description_tb(description_id);


--
-- Name: $1; Type: FK CONSTRAINT; Schema: public; Owner: ddtp
--

ALTER TABLE ONLY active_tb
    ADD CONSTRAINT "$1" FOREIGN KEY (description_id) REFERENCES description_tb(description_id);


--
-- Name: description_tag_tb_description_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: ddtp
--

ALTER TABLE ONLY description_tag_tb
    ADD CONSTRAINT description_tag_tb_description_id_fkey FOREIGN KEY (description_id) REFERENCES description_tb(description_id);


--
-- Name: package_version_tb_description_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: ddtp
--

ALTER TABLE ONLY package_version_tb
    ADD CONSTRAINT package_version_tb_description_id_fkey FOREIGN KEY (description_id) REFERENCES description_tb(description_id);


--
-- Name: part_description_tb_description_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: ddtp
--

ALTER TABLE ONLY part_description_tb
    ADD CONSTRAINT part_description_tb_description_id_fkey FOREIGN KEY (description_id) REFERENCES description_tb(description_id);


--
-- Name: version_tb_description_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: ddtp
--

ALTER TABLE ONLY version_tb
    ADD CONSTRAINT version_tb_description_id_fkey FOREIGN KEY (description_id) REFERENCES description_tb(description_id);


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

