--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: languages_tb; Type: TABLE; Schema: public; Owner: kleptog; Tablespace: 
--

CREATE TABLE languages_tb (
    language character varying NOT NULL,
    fullname character varying NOT NULL,
    enabled_ddtss boolean NOT NULL,
    translation_model text NOT NULL,
    milestone_high character varying,
    milestone_medium character varying,
    milestone_low character varying
);



--
-- Name: messages_tb; Type: TABLE; Schema: public; Owner: kleptog; Tablespace: 
--

CREATE TABLE messages_tb (
    message_id integer NOT NULL,
    language character varying,
    to_user character varying,
    for_description integer,
    from_user character varying,
    in_reply_to integer,
    "timestamp" integer NOT NULL,
    message character varying NOT NULL
);



--
-- Name: messages_tb_message_id_seq; Type: SEQUENCE; Schema: public; Owner: kleptog
--

CREATE SEQUENCE messages_tb_message_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;



--
-- Name: messages_tb_message_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: kleptog
--

ALTER SEQUENCE messages_tb_message_id_seq OWNED BY messages_tb.message_id;


--
-- Name: pendingtranslationreview_tb; Type: TABLE; Schema: public; Owner: kleptog; Tablespace: 
--

CREATE TABLE pendingtranslationreview_tb (
    pending_translation_id integer NOT NULL,
    username character varying NOT NULL
);



--
-- Name: pendingtranslations_tb; Type: TABLE; Schema: public; Owner: kleptog; Tablespace: 
--

CREATE TABLE pendingtranslations_tb (
    pending_translation_id SERIAL NOT NULL,
    description_id integer NOT NULL,
    language character varying NOT NULL,
    comment character varying,
    log character varying,
    firstupdate integer NOT NULL,
    long character varying,
    short character varying,
    oldlong character varying,
    oldshort character varying,
    lastupdate integer NOT NULL,
    owner_username character varying,
    owner_locktime integer,
    iteration integer NOT NULL,
    state integer NOT NULL
);



--
-- Name: userauthority_tb; Type: TABLE; Schema: public; Owner: kleptog; Tablespace: 
--

CREATE TABLE userauthority_tb (
    username character varying NOT NULL,
    language character varying NOT NULL,
    auth_level integer NOT NULL
);



--
-- Name: users_tb; Type: TABLE; Schema: public; Owner: kleptog; Tablespace: 
--

CREATE TABLE users_tb (
    username character varying NOT NULL,
    email character varying NOT NULL,
    realname character varying,
    active boolean NOT NULL,
    countreviews integer NOT NULL,
    counttranslations integer NOT NULL,
    key character varying NOT NULL,
    md5password character varying NOT NULL,
    lastseen integer NOT NULL,
    lastlanguage character varying,
    superuser boolean NOT NULL DEFAULT false,
    milestone character varying
);



--
-- Name: message_id; Type: DEFAULT; Schema: public; Owner: kleptog
--

ALTER TABLE messages_tb ALTER COLUMN message_id SET DEFAULT nextval('messages_tb_message_id_seq'::regclass);


--
-- Name: languages_tb_pkey; Type: CONSTRAINT; Schema: public; Owner: kleptog; Tablespace: 
--

ALTER TABLE ONLY languages_tb
    ADD CONSTRAINT languages_tb_pkey PRIMARY KEY (language);


--
-- Name: messages_tb_pkey; Type: CONSTRAINT; Schema: public; Owner: kleptog; Tablespace: 
--

ALTER TABLE ONLY messages_tb
    ADD CONSTRAINT messages_tb_pkey PRIMARY KEY (message_id);


--
-- Name: pendingtranslationreview_tb_pkey; Type: CONSTRAINT; Schema: public; Owner: kleptog; Tablespace: 
--

ALTER TABLE ONLY pendingtranslationreview_tb
    ADD CONSTRAINT pendingtranslationreview_tb_pkey PRIMARY KEY (pending_translation_id, username);


--
-- Name: pendingtranslations_tb_pending_translation_id_key; Type: CONSTRAINT; Schema: public; Owner: kleptog; Tablespace: 
--

ALTER TABLE ONLY pendingtranslations_tb
    ADD CONSTRAINT pendingtranslations_tb_pending_translation_id_key UNIQUE (pending_translation_id);


--
-- Name: pendingtranslations_tb_pkey; Type: CONSTRAINT; Schema: public; Owner: kleptog; Tablespace: 
--

ALTER TABLE ONLY pendingtranslations_tb
    ADD CONSTRAINT pendingtranslations_tb_pkey PRIMARY KEY (description_id, language);


--
-- Name: userauthority_tb_pkey; Type: CONSTRAINT; Schema: public; Owner: kleptog; Tablespace: 
--

ALTER TABLE ONLY userauthority_tb
    ADD CONSTRAINT userauthority_tb_pkey PRIMARY KEY (username, language);


--
-- Name: users_tb_pkey; Type: CONSTRAINT; Schema: public; Owner: kleptog; Tablespace: 
--

ALTER TABLE ONLY users_tb
    ADD CONSTRAINT users_tb_pkey PRIMARY KEY (username);


--
-- Name: messages_tb_from_user_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kleptog
--

ALTER TABLE ONLY messages_tb
    ADD CONSTRAINT messages_tb_from_user_fkey FOREIGN KEY (from_user) REFERENCES users_tb(username);


--
-- Name: messages_tb_language_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kleptog
--

ALTER TABLE ONLY messages_tb
    ADD CONSTRAINT messages_tb_language_fkey FOREIGN KEY (language) REFERENCES languages_tb(language);


--
-- Name: messages_tb_to_user_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kleptog
--

ALTER TABLE ONLY messages_tb
    ADD CONSTRAINT messages_tb_to_user_fkey FOREIGN KEY (to_user) REFERENCES users_tb(username);


--
-- Name: pendingtranslationreview_tb_pending_translation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kleptog
--

ALTER TABLE ONLY pendingtranslationreview_tb
    ADD CONSTRAINT pendingtranslationreview_tb_pending_translation_id_fkey FOREIGN KEY (pending_translation_id) REFERENCES pendingtranslations_tb(pending_translation_id);


--
-- Name: pendingtranslations_tb_description_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kleptog
--

ALTER TABLE ONLY pendingtranslations_tb
    ADD CONSTRAINT pendingtranslations_tb_description_id_fkey FOREIGN KEY (description_id) REFERENCES description_tb(description_id);


--
-- Name: pendingtranslations_tb_language_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kleptog
--

ALTER TABLE ONLY pendingtranslations_tb
    ADD CONSTRAINT pendingtranslations_tb_language_fkey FOREIGN KEY (language) REFERENCES languages_tb(language);


--
-- Name: userauthority_tb_language_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kleptog
--

ALTER TABLE ONLY userauthority_tb
    ADD CONSTRAINT userauthority_tb_language_fkey FOREIGN KEY (language) REFERENCES languages_tb(language);


--
-- Name: userauthority_tb_username_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kleptog
--

ALTER TABLE ONLY userauthority_tb
    ADD CONSTRAINT userauthority_tb_username_fkey FOREIGN KEY (username) REFERENCES users_tb(username);


--
-- Name: users_tb_lastlanguage_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kleptog
--

ALTER TABLE ONLY users_tb
    ADD CONSTRAINT users_tb_lastlanguage_fkey FOREIGN KEY (lastlanguage) REFERENCES languages_tb(language);


--
-- PostgreSQL database dump complete
--

