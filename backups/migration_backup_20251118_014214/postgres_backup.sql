--
-- PostgreSQL database dump
--

\restrict qagrMP9qS8zJYfICfXJs4EITHCUjs2rpxJZdrJ0ajV0Fm2z0n5grfwHq5Ca4rup

-- Dumped from database version 15.14
-- Dumped by pg_dump version 15.14

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: abtesteventtype; Type: TYPE; Schema: public; Owner: advakod
--

CREATE TYPE public.abtesteventtype AS ENUM (
    'VIEW',
    'CLICK',
    'CONVERSION',
    'CUSTOM'
);


ALTER TYPE public.abtesteventtype OWNER TO advakod;

--
-- Name: abteststatus; Type: TYPE; Schema: public; Owner: advakod
--

CREATE TYPE public.abteststatus AS ENUM (
    'DRAFT',
    'RUNNING',
    'PAUSED',
    'COMPLETED',
    'CANCELLED'
);


ALTER TYPE public.abteststatus OWNER TO advakod;

--
-- Name: abtesttype; Type: TYPE; Schema: public; Owner: advakod
--

CREATE TYPE public.abtesttype AS ENUM (
    'PAGE',
    'FEATURE',
    'ELEMENT',
    'FLOW'
);


ALTER TYPE public.abtesttype OWNER TO advakod;

--
-- Name: actiontype; Type: TYPE; Schema: public; Owner: advakod
--

CREATE TYPE public.actiontype AS ENUM (
    'LOGIN',
    'LOGOUT',
    'REGISTER',
    'CHAT_MESSAGE',
    'FILE_UPLOAD',
    'FILE_DOWNLOAD',
    'PROFILE_UPDATE',
    'PASSWORD_CHANGE',
    'TWO_FACTOR_ENABLE',
    'TWO_FACTOR_DISABLE',
    'API_ACCESS',
    'PAYMENT',
    'SUBSCRIPTION_CHANGE',
    'DATA_EXPORT',
    'DATA_DELETE',
    'ADMIN_ACTION',
    'ADMIN_LOGIN',
    'ADMIN_LOGOUT'
);


ALTER TYPE public.actiontype OWNER TO advakod;

--
-- Name: alertstatus; Type: TYPE; Schema: public; Owner: advakod
--

CREATE TYPE public.alertstatus AS ENUM (
    'ACTIVE',
    'ACKNOWLEDGED',
    'RESOLVED',
    'SUPPRESSED'
);


ALTER TYPE public.alertstatus OWNER TO advakod;

--
-- Name: incidentseverity; Type: TYPE; Schema: public; Owner: advakod
--

CREATE TYPE public.incidentseverity AS ENUM (
    'LOW',
    'MEDIUM',
    'HIGH',
    'CRITICAL'
);


ALTER TYPE public.incidentseverity OWNER TO advakod;

--
-- Name: incidentstatus; Type: TYPE; Schema: public; Owner: advakod
--

CREATE TYPE public.incidentstatus AS ENUM (
    'OPEN',
    'INVESTIGATING',
    'IDENTIFIED',
    'MONITORING',
    'RESOLVED',
    'CLOSED'
);


ALTER TYPE public.incidentstatus OWNER TO advakod;

--
-- Name: milestonestatus; Type: TYPE; Schema: public; Owner: advakod
--

CREATE TYPE public.milestonestatus AS ENUM (
    'PLANNING',
    'ACTIVE',
    'COMPLETED',
    'CANCELLED',
    'OVERDUE'
);


ALTER TYPE public.milestonestatus OWNER TO advakod;

--
-- Name: primarymetric; Type: TYPE; Schema: public; Owner: advakod
--

CREATE TYPE public.primarymetric AS ENUM (
    'CONVERSION_RATE',
    'CLICK_THROUGH_RATE',
    'BOUNCE_RATE',
    'SESSION_DURATION',
    'REVENUE_PER_USER',
    'RETENTION_RATE'
);


ALTER TYPE public.primarymetric OWNER TO advakod;

--
-- Name: projecthealth; Type: TYPE; Schema: public; Owner: advakod
--

CREATE TYPE public.projecthealth AS ENUM (
    'GREEN',
    'YELLOW',
    'RED'
);


ALTER TYPE public.projecthealth OWNER TO advakod;

--
-- Name: projectstatus; Type: TYPE; Schema: public; Owner: advakod
--

CREATE TYPE public.projectstatus AS ENUM (
    'PLANNING',
    'ACTIVE',
    'ON_HOLD',
    'COMPLETED',
    'CANCELLED'
);


ALTER TYPE public.projectstatus OWNER TO advakod;

--
-- Name: projecttype; Type: TYPE; Schema: public; Owner: advakod
--

CREATE TYPE public.projecttype AS ENUM (
    'SOFTWARE',
    'MARKETING',
    'RESEARCH',
    'OPERATIONS'
);


ALTER TYPE public.projecttype OWNER TO advakod;

--
-- Name: projectvisibility; Type: TYPE; Schema: public; Owner: advakod
--

CREATE TYPE public.projectvisibility AS ENUM (
    'PUBLIC',
    'PRIVATE',
    'TEAM'
);


ALTER TYPE public.projectvisibility OWNER TO advakod;

--
-- Name: severitylevel; Type: TYPE; Schema: public; Owner: advakod
--

CREATE TYPE public.severitylevel AS ENUM (
    'LOW',
    'MEDIUM',
    'HIGH',
    'CRITICAL'
);


ALTER TYPE public.severitylevel OWNER TO advakod;

--
-- Name: sprintstatus; Type: TYPE; Schema: public; Owner: advakod
--

CREATE TYPE public.sprintstatus AS ENUM (
    'PLANNING',
    'ACTIVE',
    'COMPLETED',
    'CANCELLED'
);


ALTER TYPE public.sprintstatus OWNER TO advakod;

--
-- Name: taskpriority; Type: TYPE; Schema: public; Owner: advakod
--

CREATE TYPE public.taskpriority AS ENUM (
    'LOW',
    'MEDIUM',
    'HIGH',
    'CRITICAL'
);


ALTER TYPE public.taskpriority OWNER TO advakod;

--
-- Name: taskstatus; Type: TYPE; Schema: public; Owner: advakod
--

CREATE TYPE public.taskstatus AS ENUM (
    'BACKLOG',
    'TODO',
    'IN_PROGRESS',
    'REVIEW',
    'TESTING',
    'DONE',
    'CANCELLED'
);


ALTER TYPE public.taskstatus OWNER TO advakod;

--
-- Name: tasktype; Type: TYPE; Schema: public; Owner: advakod
--

CREATE TYPE public.tasktype AS ENUM (
    'FEATURE',
    'BUG',
    'IMPROVEMENT',
    'MAINTENANCE',
    'RESEARCH',
    'DOCUMENTATION'
);


ALTER TYPE public.tasktype OWNER TO advakod;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: ab_test_events; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.ab_test_events (
    id integer NOT NULL,
    test_id integer NOT NULL,
    variant_id integer NOT NULL,
    participant_id integer NOT NULL,
    event_type public.abtesteventtype NOT NULL,
    event_name character varying(255) NOT NULL,
    event_data json,
    event_value double precision,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.ab_test_events OWNER TO advakod;

--
-- Name: ab_test_events_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.ab_test_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ab_test_events_id_seq OWNER TO advakod;

--
-- Name: ab_test_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.ab_test_events_id_seq OWNED BY public.ab_test_events.id;


--
-- Name: ab_test_participants; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.ab_test_participants (
    id integer NOT NULL,
    test_id integer NOT NULL,
    variant_id integer NOT NULL,
    user_id integer,
    session_id character varying(255),
    user_agent text,
    ip_address character varying(45),
    assigned_at timestamp with time zone DEFAULT now(),
    first_interaction_at timestamp with time zone,
    last_interaction_at timestamp with time zone,
    converted boolean NOT NULL,
    conversion_value double precision,
    conversion_at timestamp with time zone,
    session_duration integer,
    page_views integer NOT NULL,
    bounce boolean NOT NULL
);


ALTER TABLE public.ab_test_participants OWNER TO advakod;

--
-- Name: ab_test_participants_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.ab_test_participants_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ab_test_participants_id_seq OWNER TO advakod;

--
-- Name: ab_test_participants_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.ab_test_participants_id_seq OWNED BY public.ab_test_participants.id;


--
-- Name: ab_test_statistics; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.ab_test_statistics (
    id integer NOT NULL,
    test_id integer NOT NULL,
    analysis_date timestamp with time zone DEFAULT now(),
    sample_size integer NOT NULL,
    power double precision,
    effect_size double precision,
    bayesian_probability double precision,
    credible_interval_lower double precision,
    credible_interval_upper double precision,
    p_value double precision,
    t_statistic double precision,
    degrees_of_freedom integer,
    winner_variant_id integer,
    confidence_level double precision NOT NULL,
    is_significant boolean NOT NULL,
    uplift_percentage double precision,
    analysis_data json
);


ALTER TABLE public.ab_test_statistics OWNER TO advakod;

--
-- Name: ab_test_statistics_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.ab_test_statistics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ab_test_statistics_id_seq OWNER TO advakod;

--
-- Name: ab_test_statistics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.ab_test_statistics_id_seq OWNED BY public.ab_test_statistics.id;


--
-- Name: ab_test_variants; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.ab_test_variants (
    id integer NOT NULL,
    test_id integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    is_control boolean NOT NULL,
    traffic_percentage double precision NOT NULL,
    configuration json,
    participants_count integer NOT NULL,
    conversions_count integer NOT NULL,
    total_revenue double precision NOT NULL,
    conversion_rate double precision,
    confidence_interval_lower double precision,
    confidence_interval_upper double precision,
    statistical_significance boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.ab_test_variants OWNER TO advakod;

--
-- Name: ab_test_variants_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.ab_test_variants_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ab_test_variants_id_seq OWNER TO advakod;

--
-- Name: ab_test_variants_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.ab_test_variants_id_seq OWNED BY public.ab_test_variants.id;


--
-- Name: ab_tests; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.ab_tests (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    hypothesis text,
    type public.abtesttype NOT NULL,
    status public.abteststatus NOT NULL,
    traffic_allocation double precision NOT NULL,
    duration integer NOT NULL,
    sample_size integer NOT NULL,
    confidence_level double precision NOT NULL,
    primary_metric public.primarymetric NOT NULL,
    secondary_metrics json,
    results json,
    winner_variant_id integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    started_at timestamp with time zone,
    ended_at timestamp with time zone,
    created_by integer NOT NULL
);


ALTER TABLE public.ab_tests OWNER TO advakod;

--
-- Name: ab_tests_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.ab_tests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ab_tests_id_seq OWNER TO advakod;

--
-- Name: ab_tests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.ab_tests_id_seq OWNED BY public.ab_tests.id;


--
-- Name: admin_notifications; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.admin_notifications (
    id integer NOT NULL,
    user_id integer NOT NULL,
    type character varying(50) NOT NULL,
    title character varying(200) NOT NULL,
    message text NOT NULL,
    data json,
    priority character varying(20),
    read boolean,
    read_at timestamp without time zone,
    channels json,
    delivery_status json,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.admin_notifications OWNER TO advakod;

--
-- Name: admin_notifications_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.admin_notifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.admin_notifications_id_seq OWNER TO advakod;

--
-- Name: admin_notifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.admin_notifications_id_seq OWNED BY public.admin_notifications.id;


--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.audit_logs (
    id integer NOT NULL,
    user_id integer,
    action public.actiontype NOT NULL,
    resource character varying(255),
    resource_id character varying(255),
    ip_address character varying(45),
    user_agent text,
    session_id character varying(255),
    description text,
    details json,
    severity public.severitylevel,
    status character varying(50),
    error_message text,
    created_at timestamp with time zone DEFAULT now(),
    request_id character varying(255),
    duration_ms integer
);


ALTER TABLE public.audit_logs OWNER TO advakod;

--
-- Name: audit_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.audit_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.audit_logs_id_seq OWNER TO advakod;

--
-- Name: audit_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.audit_logs_id_seq OWNED BY public.audit_logs.id;


--
-- Name: availability_periods; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.availability_periods (
    id integer NOT NULL,
    resource_id integer NOT NULL,
    type character varying(50) NOT NULL,
    start_date timestamp with time zone NOT NULL,
    end_date timestamp with time zone NOT NULL,
    description text,
    is_approved boolean NOT NULL,
    approved_by integer,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.availability_periods OWNER TO advakod;

--
-- Name: availability_periods_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.availability_periods_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.availability_periods_id_seq OWNER TO advakod;

--
-- Name: availability_periods_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.availability_periods_id_seq OWNED BY public.availability_periods.id;


--
-- Name: backup_integrity_checks; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.backup_integrity_checks (
    id integer NOT NULL,
    backup_record_id integer NOT NULL,
    status character varying(50) NOT NULL,
    check_type character varying(100) NOT NULL,
    checked_at timestamp without time zone NOT NULL,
    check_duration_seconds double precision,
    passed boolean,
    error_message text,
    warnings json,
    details json,
    files_checked integer,
    size_verified integer,
    checksum_verified boolean
);


ALTER TABLE public.backup_integrity_checks OWNER TO advakod;

--
-- Name: backup_integrity_checks_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.backup_integrity_checks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.backup_integrity_checks_id_seq OWNER TO advakod;

--
-- Name: backup_integrity_checks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.backup_integrity_checks_id_seq OWNED BY public.backup_integrity_checks.id;


--
-- Name: backup_records; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.backup_records (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    backup_type character varying(50) NOT NULL,
    status character varying(50) NOT NULL,
    backup_path character varying(500),
    total_size integer,
    components json,
    created_at timestamp without time zone NOT NULL,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    created_by integer,
    description text,
    tags json,
    success boolean,
    error_message text,
    warnings json,
    retention_days integer,
    compression_enabled boolean,
    encryption_enabled boolean,
    duration_seconds double precision,
    files_count integer
);


ALTER TABLE public.backup_records OWNER TO advakod;

--
-- Name: backup_records_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.backup_records_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.backup_records_id_seq OWNER TO advakod;

--
-- Name: backup_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.backup_records_id_seq OWNED BY public.backup_records.id;


--
-- Name: backup_schedules; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.backup_schedules (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    enabled boolean,
    cron_expression character varying(100) NOT NULL,
    timezone character varying(50),
    backup_components json NOT NULL,
    retention_days integer,
    compression_enabled boolean,
    encryption_enabled boolean,
    notify_on_success boolean,
    notify_on_failure boolean,
    notification_channels json,
    notification_recipients json,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone,
    created_by integer,
    last_run_at timestamp without time zone,
    last_run_status character varying(50),
    next_run_at timestamp without time zone,
    total_runs integer,
    successful_runs integer,
    failed_runs integer
);


ALTER TABLE public.backup_schedules OWNER TO advakod;

--
-- Name: backup_schedules_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.backup_schedules_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.backup_schedules_id_seq OWNER TO advakod;

--
-- Name: backup_schedules_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.backup_schedules_id_seq OWNED BY public.backup_schedules.id;


--
-- Name: chat_messages; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.chat_messages (
    id integer NOT NULL,
    session_id integer NOT NULL,
    role character varying(20) NOT NULL,
    content text NOT NULL,
    message_metadata json,
    audio_url character varying(500),
    audio_duration integer,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.chat_messages OWNER TO advakod;

--
-- Name: chat_messages_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.chat_messages_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.chat_messages_id_seq OWNER TO advakod;

--
-- Name: chat_messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.chat_messages_id_seq OWNED BY public.chat_messages.id;


--
-- Name: chat_sessions; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.chat_sessions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    title character varying(255),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.chat_sessions OWNER TO advakod;

--
-- Name: chat_sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.chat_sessions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.chat_sessions_id_seq OWNER TO advakod;

--
-- Name: chat_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.chat_sessions_id_seq OWNED BY public.chat_sessions.id;


--
-- Name: cohort_analysis; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.cohort_analysis (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    cohort_type character varying(50) NOT NULL,
    period_type character varying(50) NOT NULL,
    start_date timestamp without time zone NOT NULL,
    end_date timestamp without time zone NOT NULL,
    data json,
    user_id integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.cohort_analysis OWNER TO advakod;

--
-- Name: cohort_analysis_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.cohort_analysis_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.cohort_analysis_id_seq OWNER TO advakod;

--
-- Name: cohort_analysis_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.cohort_analysis_id_seq OWNED BY public.cohort_analysis.id;


--
-- Name: custom_metrics; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.custom_metrics (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    formula text NOT NULL,
    unit character varying(50),
    format_type character varying(50),
    user_id integer NOT NULL,
    is_public boolean,
    category character varying(100),
    tags json,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.custom_metrics OWNER TO advakod;

--
-- Name: custom_metrics_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.custom_metrics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.custom_metrics_id_seq OWNER TO advakod;

--
-- Name: custom_metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.custom_metrics_id_seq OWNED BY public.custom_metrics.id;


--
-- Name: dashboard_widgets; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.dashboard_widgets (
    id integer NOT NULL,
    dashboard_id integer NOT NULL,
    widget_type character varying(100) NOT NULL,
    title character varying(255) NOT NULL,
    config json,
    "position" json,
    data_source character varying(255),
    refresh_interval integer,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.dashboard_widgets OWNER TO advakod;

--
-- Name: dashboard_widgets_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.dashboard_widgets_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dashboard_widgets_id_seq OWNER TO advakod;

--
-- Name: dashboard_widgets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.dashboard_widgets_id_seq OWNED BY public.dashboard_widgets.id;


--
-- Name: dashboards; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.dashboards (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    user_id integer NOT NULL,
    layout json,
    is_public boolean,
    is_default boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.dashboards OWNER TO advakod;

--
-- Name: dashboards_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.dashboards_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dashboards_id_seq OWNER TO advakod;

--
-- Name: dashboards_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.dashboards_id_seq OWNED BY public.dashboards.id;


--
-- Name: data_collection_logs; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.data_collection_logs (
    id integer NOT NULL,
    collection_type character varying(50) NOT NULL,
    source character varying(50) NOT NULL,
    total_found integer,
    total_processed integer,
    total_approved integer,
    total_rejected integer,
    duration_seconds integer,
    error_message text,
    created_by integer,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.data_collection_logs OWNER TO advakod;

--
-- Name: data_collection_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.data_collection_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.data_collection_logs_id_seq OWNER TO advakod;

--
-- Name: data_collection_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.data_collection_logs_id_seq OWNED BY public.data_collection_logs.id;


--
-- Name: document_analyses; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.document_analyses (
    id integer NOT NULL,
    user_id integer NOT NULL,
    filename character varying(255) NOT NULL,
    file_type character varying(50) NOT NULL,
    analysis_result text NOT NULL,
    risks_found json,
    recommendations text,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.document_analyses OWNER TO advakod;

--
-- Name: document_analyses_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.document_analyses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.document_analyses_id_seq OWNER TO advakod;

--
-- Name: document_analyses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.document_analyses_id_seq OWNED BY public.document_analyses.id;


--
-- Name: encrypted_messages; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.encrypted_messages (
    id integer NOT NULL,
    chat_session_id integer NOT NULL,
    sender_id integer NOT NULL,
    recipient_id integer NOT NULL,
    encrypted_content text NOT NULL,
    encryption_algorithm character varying(50) NOT NULL,
    message_hash character varying(64) NOT NULL,
    message_type character varying(50),
    is_read boolean,
    created_at double precision NOT NULL
);


ALTER TABLE public.encrypted_messages OWNER TO advakod;

--
-- Name: encrypted_messages_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.encrypted_messages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.encrypted_messages_id_seq OWNER TO advakod;

--
-- Name: encrypted_messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.encrypted_messages_id_seq OWNED BY public.encrypted_messages.id;


--
-- Name: encryption_keys; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.encryption_keys (
    id integer NOT NULL,
    user_id integer NOT NULL,
    key_type character varying(50) NOT NULL,
    key_data text NOT NULL,
    is_active boolean,
    created_at double precision NOT NULL,
    expires_at double precision
);


ALTER TABLE public.encryption_keys OWNER TO advakod;

--
-- Name: encryption_keys_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.encryption_keys_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.encryption_keys_id_seq OWNER TO advakod;

--
-- Name: encryption_keys_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.encryption_keys_id_seq OWNED BY public.encryption_keys.id;


--
-- Name: incident_updates; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.incident_updates (
    id integer NOT NULL,
    incident_id integer NOT NULL,
    message text NOT NULL,
    update_type character varying(50) NOT NULL,
    old_status public.incidentstatus,
    new_status public.incidentstatus,
    author_id integer NOT NULL,
    is_public boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.incident_updates OWNER TO advakod;

--
-- Name: incident_updates_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.incident_updates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.incident_updates_id_seq OWNER TO advakod;

--
-- Name: incident_updates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.incident_updates_id_seq OWNED BY public.incident_updates.id;


--
-- Name: incidents; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.incidents (
    id integer NOT NULL,
    title character varying(255) NOT NULL,
    description text,
    severity public.incidentseverity NOT NULL,
    status public.incidentstatus NOT NULL,
    source_system character varying(100) NOT NULL,
    source_id character varying(255),
    alert_rule character varying(255),
    assigned_to integer,
    created_by integer NOT NULL,
    project_id integer,
    related_task_id integer,
    started_at timestamp with time zone NOT NULL,
    acknowledged_at timestamp with time zone,
    resolved_at timestamp with time zone,
    affected_services json,
    affected_users_count integer NOT NULL,
    downtime_minutes double precision NOT NULL,
    incident_metadata json,
    tags json,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.incidents OWNER TO advakod;

--
-- Name: incidents_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.incidents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.incidents_id_seq OWNER TO advakod;

--
-- Name: incidents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.incidents_id_seq OWNED BY public.incidents.id;


--
-- Name: metric_alerts; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.metric_alerts (
    id integer NOT NULL,
    metric_id integer NOT NULL,
    name character varying(255) NOT NULL,
    condition character varying(50) NOT NULL,
    threshold double precision NOT NULL,
    is_active boolean,
    notification_channels json,
    user_id integer NOT NULL,
    last_triggered timestamp without time zone,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.metric_alerts OWNER TO advakod;

--
-- Name: metric_alerts_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.metric_alerts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.metric_alerts_id_seq OWNER TO advakod;

--
-- Name: metric_alerts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.metric_alerts_id_seq OWNED BY public.metric_alerts.id;


--
-- Name: metric_values; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.metric_values (
    id integer NOT NULL,
    metric_id integer NOT NULL,
    value double precision NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    labels json
);


ALTER TABLE public.metric_values OWNER TO advakod;

--
-- Name: metric_values_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.metric_values_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.metric_values_id_seq OWNER TO advakod;

--
-- Name: metric_values_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.metric_values_id_seq OWNED BY public.metric_values.id;


--
-- Name: milestones; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.milestones (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    project_id integer,
    status public.milestonestatus NOT NULL,
    start_date timestamp with time zone NOT NULL,
    due_date timestamp with time zone NOT NULL,
    completed_date timestamp with time zone,
    progress double precision NOT NULL,
    total_tasks integer NOT NULL,
    completed_tasks integer NOT NULL,
    total_story_points integer,
    completed_story_points integer NOT NULL,
    budget double precision,
    spent_budget double precision NOT NULL,
    currency character varying(3) NOT NULL,
    owner_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.milestones OWNER TO advakod;

--
-- Name: milestones_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.milestones_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.milestones_id_seq OWNER TO advakod;

--
-- Name: milestones_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.milestones_id_seq OWNED BY public.milestones.id;


--
-- Name: ml_predictions; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.ml_predictions (
    id integer NOT NULL,
    model_name character varying(255) NOT NULL,
    prediction_type character varying(100) NOT NULL,
    target_user_id integer,
    prediction_value double precision,
    confidence_score double precision,
    features json,
    model_version character varying(50),
    created_at timestamp without time zone,
    expires_at timestamp without time zone
);


ALTER TABLE public.ml_predictions OWNER TO advakod;

--
-- Name: ml_predictions_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.ml_predictions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ml_predictions_id_seq OWNER TO advakod;

--
-- Name: ml_predictions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.ml_predictions_id_seq OWNED BY public.ml_predictions.id;


--
-- Name: model_versions; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.model_versions (
    id integer NOT NULL,
    version character varying(20) NOT NULL,
    base_model character varying(100) NOT NULL,
    lora_config json,
    training_data_count integer,
    performance_metrics json,
    is_active boolean,
    model_path character varying(500),
    created_by integer,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.model_versions OWNER TO advakod;

--
-- Name: model_versions_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.model_versions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.model_versions_id_seq OWNER TO advakod;

--
-- Name: model_versions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.model_versions_id_seq OWNED BY public.model_versions.id;


--
-- Name: moderation_queue; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.moderation_queue (
    id integer NOT NULL,
    message_id integer NOT NULL,
    priority character varying(20) NOT NULL,
    reason character varying(100),
    assigned_to integer,
    status character varying(20) NOT NULL,
    confidence_score double precision,
    queue_metadata json,
    created_at timestamp with time zone DEFAULT now(),
    assigned_at timestamp with time zone,
    completed_at timestamp with time zone
);


ALTER TABLE public.moderation_queue OWNER TO advakod;

--
-- Name: moderation_queue_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.moderation_queue_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.moderation_queue_id_seq OWNER TO advakod;

--
-- Name: moderation_queue_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.moderation_queue_id_seq OWNED BY public.moderation_queue.id;


--
-- Name: moderation_reviews; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.moderation_reviews (
    id integer NOT NULL,
    message_id integer NOT NULL,
    moderator_id integer NOT NULL,
    star_rating integer NOT NULL,
    problem_categories json,
    comment text NOT NULL,
    suggested_fix text,
    status character varying(20) NOT NULL,
    priority character varying(20) NOT NULL,
    original_confidence double precision,
    review_metadata json,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.moderation_reviews OWNER TO advakod;

--
-- Name: moderation_reviews_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.moderation_reviews_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.moderation_reviews_id_seq OWNER TO advakod;

--
-- Name: moderation_reviews_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.moderation_reviews_id_seq OWNED BY public.moderation_reviews.id;


--
-- Name: moderator_stats; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.moderator_stats (
    id integer NOT NULL,
    moderator_id integer NOT NULL,
    total_reviews integer,
    points integer,
    badges json,
    rank character varying(20),
    average_rating double precision,
    category_stats json,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.moderator_stats OWNER TO advakod;

--
-- Name: moderator_stats_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.moderator_stats_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.moderator_stats_id_seq OWNER TO advakod;

--
-- Name: moderator_stats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.moderator_stats_id_seq OWNED BY public.moderator_stats.id;


--
-- Name: monitoring_alerts; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.monitoring_alerts (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    message text NOT NULL,
    severity public.incidentseverity NOT NULL,
    status public.alertstatus NOT NULL,
    source_system character varying(100) NOT NULL,
    rule_name character varying(255) NOT NULL,
    metric_name character varying(255),
    current_value double precision,
    threshold_value double precision,
    incident_id integer,
    auto_task_created boolean NOT NULL,
    created_task_id integer,
    started_at timestamp with time zone NOT NULL,
    acknowledged_at timestamp with time zone,
    resolved_at timestamp with time zone,
    labels json,
    annotations json,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.monitoring_alerts OWNER TO advakod;

--
-- Name: monitoring_alerts_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.monitoring_alerts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.monitoring_alerts_id_seq OWNER TO advakod;

--
-- Name: monitoring_alerts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.monitoring_alerts_id_seq OWNED BY public.monitoring_alerts.id;


--
-- Name: notification_history; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.notification_history (
    id integer NOT NULL,
    notification_id integer NOT NULL,
    channel character varying(50) NOT NULL,
    status character varying(20) NOT NULL,
    delivery_details json,
    error_message text,
    sent_at timestamp without time zone,
    delivered_at timestamp without time zone,
    failed_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.notification_history OWNER TO advakod;

--
-- Name: notification_history_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.notification_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.notification_history_id_seq OWNER TO advakod;

--
-- Name: notification_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.notification_history_id_seq OWNED BY public.notification_history.id;


--
-- Name: notification_templates; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.notification_templates (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    type character varying(50) NOT NULL,
    title_template character varying(200) NOT NULL,
    message_template text NOT NULL,
    email_template text,
    slack_template text,
    default_channels json,
    default_priority character varying(20),
    trigger_conditions json,
    active boolean,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.notification_templates OWNER TO advakod;

--
-- Name: notification_templates_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.notification_templates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.notification_templates_id_seq OWNER TO advakod;

--
-- Name: notification_templates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.notification_templates_id_seq OWNED BY public.notification_templates.id;


--
-- Name: operational_metrics; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.operational_metrics (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    display_name character varying(255) NOT NULL,
    description text,
    metric_type character varying(50) NOT NULL,
    unit character varying(20),
    category character varying(100) NOT NULL,
    source_system character varying(100) NOT NULL,
    query text NOT NULL,
    chart_type character varying(50) NOT NULL,
    color character varying(7),
    order_index integer NOT NULL,
    warning_threshold double precision,
    critical_threshold double precision,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.operational_metrics OWNER TO advakod;

--
-- Name: operational_metrics_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.operational_metrics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.operational_metrics_id_seq OWNER TO advakod;

--
-- Name: operational_metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.operational_metrics_id_seq OWNED BY public.operational_metrics.id;


--
-- Name: permissions; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.permissions (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    display_name character varying(150) NOT NULL,
    description text,
    resource character varying(50) NOT NULL,
    action character varying(50) NOT NULL,
    is_system boolean,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.permissions OWNER TO advakod;

--
-- Name: permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.permissions_id_seq OWNER TO advakod;

--
-- Name: permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.permissions_id_seq OWNED BY public.permissions.id;


--
-- Name: problem_categories; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.problem_categories (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    display_name character varying(100) NOT NULL,
    description text,
    severity integer NOT NULL,
    is_active boolean,
    icon character varying(10),
    display_order integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.problem_categories OWNER TO advakod;

--
-- Name: problem_categories_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.problem_categories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.problem_categories_id_seq OWNER TO advakod;

--
-- Name: problem_categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.problem_categories_id_seq OWNED BY public.problem_categories.id;


--
-- Name: project_allocations; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.project_allocations (
    id integer NOT NULL,
    resource_id integer NOT NULL,
    project_id integer NOT NULL,
    allocation double precision NOT NULL,
    role character varying(100) NOT NULL,
    start_date timestamp with time zone NOT NULL,
    end_date timestamp with time zone,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.project_allocations OWNER TO advakod;

--
-- Name: project_allocations_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.project_allocations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.project_allocations_id_seq OWNER TO advakod;

--
-- Name: project_allocations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.project_allocations_id_seq OWNED BY public.project_allocations.id;


--
-- Name: project_members; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.project_members (
    id integer NOT NULL,
    project_id integer NOT NULL,
    user_id integer NOT NULL,
    role character varying(50) NOT NULL,
    allocation double precision NOT NULL,
    is_active boolean NOT NULL,
    joined_at timestamp with time zone DEFAULT now(),
    left_at timestamp with time zone
);


ALTER TABLE public.project_members OWNER TO advakod;

--
-- Name: project_members_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.project_members_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.project_members_id_seq OWNER TO advakod;

--
-- Name: project_members_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.project_members_id_seq OWNED BY public.project_members.id;


--
-- Name: projects; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.projects (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    key character varying(10) NOT NULL,
    type public.projecttype NOT NULL,
    status public.projectstatus NOT NULL,
    visibility public.projectvisibility NOT NULL,
    health public.projecthealth NOT NULL,
    lead_id integer NOT NULL,
    start_date timestamp with time zone,
    end_date timestamp with time zone,
    budget double precision,
    spent_budget double precision NOT NULL,
    currency character varying(3) NOT NULL,
    progress double precision NOT NULL,
    total_tasks integer NOT NULL,
    completed_tasks integer NOT NULL,
    settings json,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.projects OWNER TO advakod;

--
-- Name: projects_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.projects_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.projects_id_seq OWNER TO advakod;

--
-- Name: projects_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.projects_id_seq OWNED BY public.projects.id;


--
-- Name: quality_evaluations; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.quality_evaluations (
    id integer NOT NULL,
    training_data_id integer NOT NULL,
    evaluation_type character varying(50) NOT NULL,
    score double precision NOT NULL,
    criteria json,
    evaluator_id integer,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.quality_evaluations OWNER TO advakod;

--
-- Name: quality_evaluations_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.quality_evaluations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.quality_evaluations_id_seq OWNER TO advakod;

--
-- Name: quality_evaluations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.quality_evaluations_id_seq OWNED BY public.quality_evaluations.id;


--
-- Name: report_executions; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.report_executions (
    id integer NOT NULL,
    template_id integer NOT NULL,
    status character varying(50),
    result_data json,
    error_message text,
    execution_time double precision,
    file_path character varying(500),
    created_at timestamp without time zone,
    completed_at timestamp without time zone
);


ALTER TABLE public.report_executions OWNER TO advakod;

--
-- Name: report_executions_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.report_executions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.report_executions_id_seq OWNER TO advakod;

--
-- Name: report_executions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.report_executions_id_seq OWNED BY public.report_executions.id;


--
-- Name: report_templates; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.report_templates (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    template_type character varying(100) NOT NULL,
    config json NOT NULL,
    schedule json,
    user_id integer NOT NULL,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.report_templates OWNER TO advakod;

--
-- Name: report_templates_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.report_templates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.report_templates_id_seq OWNER TO advakod;

--
-- Name: report_templates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.report_templates_id_seq OWNED BY public.report_templates.id;


--
-- Name: resource_allocations; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.resource_allocations (
    id integer NOT NULL,
    user_id integer NOT NULL,
    total_capacity double precision NOT NULL,
    role character varying(100) NOT NULL,
    department character varying(100) NOT NULL,
    hourly_rate double precision,
    currency character varying(3) NOT NULL,
    skills json,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.resource_allocations OWNER TO advakod;

--
-- Name: resource_allocations_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.resource_allocations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.resource_allocations_id_seq OWNER TO advakod;

--
-- Name: resource_allocations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.resource_allocations_id_seq OWNED BY public.resource_allocations.id;


--
-- Name: response_feedback; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.response_feedback (
    id integer NOT NULL,
    message_id integer NOT NULL,
    user_id integer NOT NULL,
    rating character varying(20) NOT NULL,
    reason character varying(100),
    comment text,
    feedback_metadata json,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.response_feedback OWNER TO advakod;

--
-- Name: response_feedback_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.response_feedback_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.response_feedback_id_seq OWNER TO advakod;

--
-- Name: response_feedback_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.response_feedback_id_seq OWNED BY public.response_feedback.id;


--
-- Name: restore_records; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.restore_records (
    id integer NOT NULL,
    backup_record_id integer NOT NULL,
    name character varying(255) NOT NULL,
    status character varying(50) NOT NULL,
    components_to_restore json NOT NULL,
    restore_options json,
    created_at timestamp without time zone NOT NULL,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    created_by integer NOT NULL,
    description text,
    success boolean,
    error_message text,
    warnings json,
    restored_components json,
    duration_seconds double precision,
    files_restored integer
);


ALTER TABLE public.restore_records OWNER TO advakod;

--
-- Name: restore_records_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.restore_records_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.restore_records_id_seq OWNER TO advakod;

--
-- Name: restore_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.restore_records_id_seq OWNED BY public.restore_records.id;


--
-- Name: role_permissions; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.role_permissions (
    role_id integer NOT NULL,
    permission_id integer NOT NULL,
    granted_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.role_permissions OWNER TO advakod;

--
-- Name: roles; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.roles (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    display_name character varying(100) NOT NULL,
    description text,
    is_system boolean,
    is_active boolean,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.roles OWNER TO advakod;

--
-- Name: roles_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.roles_id_seq OWNER TO advakod;

--
-- Name: roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.roles_id_seq OWNED BY public.roles.id;


--
-- Name: security_events; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.security_events (
    id integer NOT NULL,
    user_id integer,
    event_type character varying(100) NOT NULL,
    ip_address character varying(45),
    user_agent text,
    description text,
    details json,
    threat_level public.severitylevel,
    status character varying(50),
    resolved_at timestamp with time zone,
    resolved_by integer,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.security_events OWNER TO advakod;

--
-- Name: security_events_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.security_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.security_events_id_seq OWNER TO advakod;

--
-- Name: security_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.security_events_id_seq OWNED BY public.security_events.id;


--
-- Name: sprints; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.sprints (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    goal text,
    project_id integer,
    status public.sprintstatus NOT NULL,
    start_date timestamp with time zone NOT NULL,
    end_date timestamp with time zone NOT NULL,
    capacity integer NOT NULL,
    commitment integer NOT NULL,
    completed integer NOT NULL,
    velocity double precision NOT NULL,
    burndown_data json,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.sprints OWNER TO advakod;

--
-- Name: sprints_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.sprints_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sprints_id_seq OWNER TO advakod;

--
-- Name: sprints_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.sprints_id_seq OWNED BY public.sprints.id;


--
-- Name: task_attachments; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.task_attachments (
    id integer NOT NULL,
    task_id integer NOT NULL,
    file_name character varying(255) NOT NULL,
    file_size integer NOT NULL,
    file_type character varying(100) NOT NULL,
    file_path character varying(500) NOT NULL,
    uploaded_by integer NOT NULL,
    uploaded_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.task_attachments OWNER TO advakod;

--
-- Name: task_attachments_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.task_attachments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.task_attachments_id_seq OWNER TO advakod;

--
-- Name: task_attachments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.task_attachments_id_seq OWNED BY public.task_attachments.id;


--
-- Name: task_comments; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.task_comments (
    id integer NOT NULL,
    task_id integer NOT NULL,
    author_id integer NOT NULL,
    content text NOT NULL,
    is_edited boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.task_comments OWNER TO advakod;

--
-- Name: task_comments_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.task_comments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.task_comments_id_seq OWNER TO advakod;

--
-- Name: task_comments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.task_comments_id_seq OWNED BY public.task_comments.id;


--
-- Name: task_dependencies; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.task_dependencies (
    id integer NOT NULL,
    task_id integer NOT NULL,
    depends_on_task_id integer NOT NULL,
    type character varying(50) NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.task_dependencies OWNER TO advakod;

--
-- Name: task_dependencies_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.task_dependencies_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.task_dependencies_id_seq OWNER TO advakod;

--
-- Name: task_dependencies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.task_dependencies_id_seq OWNED BY public.task_dependencies.id;


--
-- Name: tasks; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.tasks (
    id integer NOT NULL,
    title character varying(255) NOT NULL,
    description text,
    type public.tasktype NOT NULL,
    status public.taskstatus NOT NULL,
    priority public.taskpriority NOT NULL,
    assignee_id integer,
    reporter_id integer NOT NULL,
    project_id integer,
    milestone_id integer,
    sprint_id integer,
    parent_task_id integer,
    estimated_hours double precision,
    actual_hours double precision NOT NULL,
    story_points integer,
    due_date timestamp with time zone,
    start_date timestamp with time zone,
    completed_date timestamp with time zone,
    labels json,
    custom_fields json,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.tasks OWNER TO advakod;

--
-- Name: tasks_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.tasks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.tasks_id_seq OWNER TO advakod;

--
-- Name: tasks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.tasks_id_seq OWNED BY public.tasks.id;


--
-- Name: time_entries; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.time_entries (
    id integer NOT NULL,
    user_id integer NOT NULL,
    task_id integer,
    project_id integer,
    description text NOT NULL,
    hours double precision NOT NULL,
    date timestamp with time zone NOT NULL,
    billable boolean NOT NULL,
    hourly_rate double precision,
    currency character varying(3) NOT NULL,
    status character varying(20) NOT NULL,
    approved_by integer,
    approved_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.time_entries OWNER TO advakod;

--
-- Name: time_entries_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.time_entries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.time_entries_id_seq OWNER TO advakod;

--
-- Name: time_entries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.time_entries_id_seq OWNED BY public.time_entries.id;


--
-- Name: token_balances; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.token_balances (
    id integer NOT NULL,
    user_id integer NOT NULL,
    balance integer DEFAULT 0 NOT NULL,
    total_earned integer DEFAULT 0 NOT NULL,
    total_spent integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.token_balances OWNER TO advakod;

--
-- Name: token_balances_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.token_balances_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.token_balances_id_seq OWNER TO advakod;

--
-- Name: token_balances_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.token_balances_id_seq OWNED BY public.token_balances.id;


--
-- Name: token_transactions; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.token_transactions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    amount integer NOT NULL,
    transaction_type character varying(50) NOT NULL,
    description text,
    chat_session_id integer,
    chat_message_id integer,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.token_transactions OWNER TO advakod;

--
-- Name: token_transactions_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.token_transactions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.token_transactions_id_seq OWNER TO advakod;

--
-- Name: token_transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.token_transactions_id_seq OWNED BY public.token_transactions.id;


--
-- Name: training_data; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.training_data (
    id integer NOT NULL,
    instruction text NOT NULL,
    input text,
    output text NOT NULL,
    source character varying(50) NOT NULL,
    quality_score double precision,
    complexity character varying(20),
    is_approved boolean,
    is_used_for_training boolean,
    approved_by integer,
    approved_at timestamp with time zone,
    meta_data json,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.training_data OWNER TO advakod;

--
-- Name: training_data_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.training_data_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.training_data_id_seq OWNER TO advakod;

--
-- Name: training_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.training_data_id_seq OWNED BY public.training_data.id;


--
-- Name: training_datasets; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.training_datasets (
    id integer NOT NULL,
    version character varying(20) NOT NULL,
    question text NOT NULL,
    bad_answer text NOT NULL,
    good_answer text NOT NULL,
    review_id integer,
    dataset_metadata json,
    used_in_training boolean,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.training_datasets OWNER TO advakod;

--
-- Name: training_datasets_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.training_datasets_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.training_datasets_id_seq OWNER TO advakod;

--
-- Name: training_datasets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.training_datasets_id_seq OWNED BY public.training_datasets.id;


--
-- Name: training_jobs; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.training_jobs (
    id integer NOT NULL,
    job_name character varying(100) NOT NULL,
    status character varying(20),
    training_data_count integer,
    hyperparameters json,
    progress double precision,
    current_epoch integer,
    total_epochs integer,
    loss double precision,
    accuracy double precision,
    error_message text,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    created_by integer,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.training_jobs OWNER TO advakod;

--
-- Name: training_jobs_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.training_jobs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.training_jobs_id_seq OWNER TO advakod;

--
-- Name: training_jobs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.training_jobs_id_seq OWNED BY public.training_jobs.id;


--
-- Name: user_role_history; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.user_role_history (
    id integer NOT NULL,
    user_id integer NOT NULL,
    role_id integer NOT NULL,
    action character varying(20) NOT NULL,
    assigned_by integer,
    reason text,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.user_role_history OWNER TO advakod;

--
-- Name: user_role_history_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.user_role_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_role_history_id_seq OWNER TO advakod;

--
-- Name: user_role_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.user_role_history_id_seq OWNED BY public.user_role_history.id;


--
-- Name: user_roles; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.user_roles (
    user_id integer NOT NULL,
    role_id integer NOT NULL,
    assigned_at timestamp with time zone DEFAULT now(),
    assigned_by integer
);


ALTER TABLE public.user_roles OWNER TO advakod;

--
-- Name: user_segments; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.user_segments (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    criteria json NOT NULL,
    user_count integer,
    is_dynamic boolean,
    user_id integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.user_segments OWNER TO advakod;

--
-- Name: user_segments_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.user_segments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_segments_id_seq OWNER TO advakod;

--
-- Name: user_segments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.user_segments_id_seq OWNED BY public.user_segments.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: advakod
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    username character varying(100) NOT NULL,
    hashed_password character varying(255) NOT NULL,
    full_name character varying(255),
    is_active boolean DEFAULT true,
    is_premium boolean DEFAULT false,
    is_admin boolean DEFAULT false,
    subscription_type character varying(50) DEFAULT 'free'::character varying,
    subscription_expires timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    company_name character varying(255),
    legal_form character varying(100),
    inn character varying(12),
    ogrn character varying(15),
    two_factor_enabled boolean DEFAULT false,
    two_factor_secret character varying(32),
    backup_codes text
);


ALTER TABLE public.users OWNER TO advakod;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: advakod
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO advakod;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: advakod
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: ab_test_events id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.ab_test_events ALTER COLUMN id SET DEFAULT nextval('public.ab_test_events_id_seq'::regclass);


--
-- Name: ab_test_participants id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.ab_test_participants ALTER COLUMN id SET DEFAULT nextval('public.ab_test_participants_id_seq'::regclass);


--
-- Name: ab_test_statistics id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.ab_test_statistics ALTER COLUMN id SET DEFAULT nextval('public.ab_test_statistics_id_seq'::regclass);


--
-- Name: ab_test_variants id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.ab_test_variants ALTER COLUMN id SET DEFAULT nextval('public.ab_test_variants_id_seq'::regclass);


--
-- Name: ab_tests id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.ab_tests ALTER COLUMN id SET DEFAULT nextval('public.ab_tests_id_seq'::regclass);


--
-- Name: admin_notifications id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.admin_notifications ALTER COLUMN id SET DEFAULT nextval('public.admin_notifications_id_seq'::regclass);


--
-- Name: audit_logs id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.audit_logs ALTER COLUMN id SET DEFAULT nextval('public.audit_logs_id_seq'::regclass);


--
-- Name: availability_periods id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.availability_periods ALTER COLUMN id SET DEFAULT nextval('public.availability_periods_id_seq'::regclass);


--
-- Name: backup_integrity_checks id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.backup_integrity_checks ALTER COLUMN id SET DEFAULT nextval('public.backup_integrity_checks_id_seq'::regclass);


--
-- Name: backup_records id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.backup_records ALTER COLUMN id SET DEFAULT nextval('public.backup_records_id_seq'::regclass);


--
-- Name: backup_schedules id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.backup_schedules ALTER COLUMN id SET DEFAULT nextval('public.backup_schedules_id_seq'::regclass);


--
-- Name: chat_messages id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.chat_messages ALTER COLUMN id SET DEFAULT nextval('public.chat_messages_id_seq'::regclass);


--
-- Name: chat_sessions id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.chat_sessions ALTER COLUMN id SET DEFAULT nextval('public.chat_sessions_id_seq'::regclass);


--
-- Name: cohort_analysis id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.cohort_analysis ALTER COLUMN id SET DEFAULT nextval('public.cohort_analysis_id_seq'::regclass);


--
-- Name: custom_metrics id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.custom_metrics ALTER COLUMN id SET DEFAULT nextval('public.custom_metrics_id_seq'::regclass);


--
-- Name: dashboard_widgets id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.dashboard_widgets ALTER COLUMN id SET DEFAULT nextval('public.dashboard_widgets_id_seq'::regclass);


--
-- Name: dashboards id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.dashboards ALTER COLUMN id SET DEFAULT nextval('public.dashboards_id_seq'::regclass);


--
-- Name: data_collection_logs id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.data_collection_logs ALTER COLUMN id SET DEFAULT nextval('public.data_collection_logs_id_seq'::regclass);


--
-- Name: document_analyses id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.document_analyses ALTER COLUMN id SET DEFAULT nextval('public.document_analyses_id_seq'::regclass);


--
-- Name: encrypted_messages id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.encrypted_messages ALTER COLUMN id SET DEFAULT nextval('public.encrypted_messages_id_seq'::regclass);


--
-- Name: encryption_keys id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.encryption_keys ALTER COLUMN id SET DEFAULT nextval('public.encryption_keys_id_seq'::regclass);


--
-- Name: incident_updates id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.incident_updates ALTER COLUMN id SET DEFAULT nextval('public.incident_updates_id_seq'::regclass);


--
-- Name: incidents id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.incidents ALTER COLUMN id SET DEFAULT nextval('public.incidents_id_seq'::regclass);


--
-- Name: metric_alerts id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.metric_alerts ALTER COLUMN id SET DEFAULT nextval('public.metric_alerts_id_seq'::regclass);


--
-- Name: metric_values id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.metric_values ALTER COLUMN id SET DEFAULT nextval('public.metric_values_id_seq'::regclass);


--
-- Name: milestones id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.milestones ALTER COLUMN id SET DEFAULT nextval('public.milestones_id_seq'::regclass);


--
-- Name: ml_predictions id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.ml_predictions ALTER COLUMN id SET DEFAULT nextval('public.ml_predictions_id_seq'::regclass);


--
-- Name: model_versions id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.model_versions ALTER COLUMN id SET DEFAULT nextval('public.model_versions_id_seq'::regclass);


--
-- Name: moderation_queue id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.moderation_queue ALTER COLUMN id SET DEFAULT nextval('public.moderation_queue_id_seq'::regclass);


--
-- Name: moderation_reviews id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.moderation_reviews ALTER COLUMN id SET DEFAULT nextval('public.moderation_reviews_id_seq'::regclass);


--
-- Name: moderator_stats id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.moderator_stats ALTER COLUMN id SET DEFAULT nextval('public.moderator_stats_id_seq'::regclass);


--
-- Name: monitoring_alerts id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.monitoring_alerts ALTER COLUMN id SET DEFAULT nextval('public.monitoring_alerts_id_seq'::regclass);


--
-- Name: notification_history id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.notification_history ALTER COLUMN id SET DEFAULT nextval('public.notification_history_id_seq'::regclass);


--
-- Name: notification_templates id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.notification_templates ALTER COLUMN id SET DEFAULT nextval('public.notification_templates_id_seq'::regclass);


--
-- Name: operational_metrics id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.operational_metrics ALTER COLUMN id SET DEFAULT nextval('public.operational_metrics_id_seq'::regclass);


--
-- Name: permissions id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.permissions ALTER COLUMN id SET DEFAULT nextval('public.permissions_id_seq'::regclass);


--
-- Name: problem_categories id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.problem_categories ALTER COLUMN id SET DEFAULT nextval('public.problem_categories_id_seq'::regclass);


--
-- Name: project_allocations id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.project_allocations ALTER COLUMN id SET DEFAULT nextval('public.project_allocations_id_seq'::regclass);


--
-- Name: project_members id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.project_members ALTER COLUMN id SET DEFAULT nextval('public.project_members_id_seq'::regclass);


--
-- Name: projects id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.projects ALTER COLUMN id SET DEFAULT nextval('public.projects_id_seq'::regclass);


--
-- Name: quality_evaluations id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.quality_evaluations ALTER COLUMN id SET DEFAULT nextval('public.quality_evaluations_id_seq'::regclass);


--
-- Name: report_executions id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.report_executions ALTER COLUMN id SET DEFAULT nextval('public.report_executions_id_seq'::regclass);


--
-- Name: report_templates id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.report_templates ALTER COLUMN id SET DEFAULT nextval('public.report_templates_id_seq'::regclass);


--
-- Name: resource_allocations id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.resource_allocations ALTER COLUMN id SET DEFAULT nextval('public.resource_allocations_id_seq'::regclass);


--
-- Name: response_feedback id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.response_feedback ALTER COLUMN id SET DEFAULT nextval('public.response_feedback_id_seq'::regclass);


--
-- Name: restore_records id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.restore_records ALTER COLUMN id SET DEFAULT nextval('public.restore_records_id_seq'::regclass);


--
-- Name: roles id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.roles ALTER COLUMN id SET DEFAULT nextval('public.roles_id_seq'::regclass);


--
-- Name: security_events id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.security_events ALTER COLUMN id SET DEFAULT nextval('public.security_events_id_seq'::regclass);


--
-- Name: sprints id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.sprints ALTER COLUMN id SET DEFAULT nextval('public.sprints_id_seq'::regclass);


--
-- Name: task_attachments id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.task_attachments ALTER COLUMN id SET DEFAULT nextval('public.task_attachments_id_seq'::regclass);


--
-- Name: task_comments id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.task_comments ALTER COLUMN id SET DEFAULT nextval('public.task_comments_id_seq'::regclass);


--
-- Name: task_dependencies id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.task_dependencies ALTER COLUMN id SET DEFAULT nextval('public.task_dependencies_id_seq'::regclass);


--
-- Name: tasks id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.tasks ALTER COLUMN id SET DEFAULT nextval('public.tasks_id_seq'::regclass);


--
-- Name: time_entries id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.time_entries ALTER COLUMN id SET DEFAULT nextval('public.time_entries_id_seq'::regclass);


--
-- Name: token_balances id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.token_balances ALTER COLUMN id SET DEFAULT nextval('public.token_balances_id_seq'::regclass);


--
-- Name: token_transactions id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.token_transactions ALTER COLUMN id SET DEFAULT nextval('public.token_transactions_id_seq'::regclass);


--
-- Name: training_data id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.training_data ALTER COLUMN id SET DEFAULT nextval('public.training_data_id_seq'::regclass);


--
-- Name: training_datasets id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.training_datasets ALTER COLUMN id SET DEFAULT nextval('public.training_datasets_id_seq'::regclass);


--
-- Name: training_jobs id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.training_jobs ALTER COLUMN id SET DEFAULT nextval('public.training_jobs_id_seq'::regclass);


--
-- Name: user_role_history id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.user_role_history ALTER COLUMN id SET DEFAULT nextval('public.user_role_history_id_seq'::regclass);


--
-- Name: user_segments id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.user_segments ALTER COLUMN id SET DEFAULT nextval('public.user_segments_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: ab_test_events; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.ab_test_events (id, test_id, variant_id, participant_id, event_type, event_name, event_data, event_value, created_at) FROM stdin;
\.


--
-- Data for Name: ab_test_participants; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.ab_test_participants (id, test_id, variant_id, user_id, session_id, user_agent, ip_address, assigned_at, first_interaction_at, last_interaction_at, converted, conversion_value, conversion_at, session_duration, page_views, bounce) FROM stdin;
\.


--
-- Data for Name: ab_test_statistics; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.ab_test_statistics (id, test_id, analysis_date, sample_size, power, effect_size, bayesian_probability, credible_interval_lower, credible_interval_upper, p_value, t_statistic, degrees_of_freedom, winner_variant_id, confidence_level, is_significant, uplift_percentage, analysis_data) FROM stdin;
\.


--
-- Data for Name: ab_test_variants; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.ab_test_variants (id, test_id, name, description, is_control, traffic_percentage, configuration, participants_count, conversions_count, total_revenue, conversion_rate, confidence_interval_lower, confidence_interval_upper, statistical_significance, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: ab_tests; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.ab_tests (id, name, description, hypothesis, type, status, traffic_allocation, duration, sample_size, confidence_level, primary_metric, secondary_metrics, results, winner_variant_id, created_at, updated_at, started_at, ended_at, created_by) FROM stdin;
\.


--
-- Data for Name: admin_notifications; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.admin_notifications (id, user_id, type, title, message, data, priority, read, read_at, channels, delivery_status, created_at, updated_at) FROM stdin;
1	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-15 21:15:13 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763241313", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-15T21:15:13.215068", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["email"]	\N	2025-11-15 21:15:13.300493	2025-11-15 21:15:13.300493
2	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-15 21:15:13 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763241313", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-15T21:15:13.215068", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["slack"]	\N	2025-11-15 21:15:13.336137	2025-11-15 21:15:13.336137
3	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 21:15:13 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763241313", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T21:15:13.343145", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["email"]	\N	2025-11-15 21:15:13.364187	2025-11-15 21:15:13.364187
4	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 21:15:13 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763241313", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T21:15:13.343145", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["slack"]	\N	2025-11-15 21:15:13.383627	2025-11-15 21:15:13.383627
5	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 21:15:13 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763241313", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T21:15:13.343145", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["sms"]	\N	2025-11-15 21:15:13.411238	2025-11-15 21:15:13.411238
6	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-15 21:20:35 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763241635", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-15T21:20:35.615862", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["email"]	\N	2025-11-15 21:20:35.678272	2025-11-15 21:20:35.678272
7	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-15 21:20:35 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763241635", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-15T21:20:35.615862", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["slack"]	\N	2025-11-15 21:20:35.712247	2025-11-15 21:20:35.712247
8	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 21:20:35 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763241635", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T21:20:35.717778", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["email"]	\N	2025-11-15 21:20:35.734998	2025-11-15 21:20:35.734998
9	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 21:20:35 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763241635", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T21:20:35.717778", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["slack"]	\N	2025-11-15 21:20:35.761372	2025-11-15 21:20:35.761372
10	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 21:20:35 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763241635", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T21:20:35.717778", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["sms"]	\N	2025-11-15 21:20:35.786085	2025-11-15 21:20:35.786085
11	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-15 21:50:55 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763243455", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-15T21:50:55.652479", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["email"]	\N	2025-11-15 21:50:55.709194	2025-11-15 21:50:55.709194
12	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-15 21:50:55 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763243455", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-15T21:50:55.652479", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["slack"]	\N	2025-11-15 21:50:55.736981	2025-11-15 21:50:55.736981
13	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 21:50:55 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763243455", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T21:50:55.743771", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["email"]	\N	2025-11-15 21:50:55.762456	2025-11-15 21:50:55.762456
14	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 21:50:55 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763243455", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T21:50:55.743771", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["slack"]	\N	2025-11-15 21:50:55.783276	2025-11-15 21:50:55.783276
15	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 21:50:55 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763243455", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T21:50:55.743771", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["sms"]	\N	2025-11-15 21:50:55.805819	2025-11-15 21:50:55.805819
16	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-15 21:54:06 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763243646", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-15T21:54:06.369802", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["email"]	\N	2025-11-15 21:54:06.444122	2025-11-15 21:54:06.444122
17	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-15 21:54:06 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763243646", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-15T21:54:06.369802", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["slack"]	\N	2025-11-15 21:54:06.481159	2025-11-15 21:54:06.481159
18	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 21:54:06 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763243646", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T21:54:06.488165", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["email"]	\N	2025-11-15 21:54:06.504792	2025-11-15 21:54:06.504792
19	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 21:54:06 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763243646", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T21:54:06.488165", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["slack"]	\N	2025-11-15 21:54:06.531557	2025-11-15 21:54:06.531557
20	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 21:54:06 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763243646", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T21:54:06.488165", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["sms"]	\N	2025-11-15 21:54:06.553734	2025-11-15 21:54:06.553734
21	1	alert_resolution	✅ Resolved: High CPU Usage	Alert 'High CPU Usage' has been resolved.	{"alert_id": "high_cpu_usage_1763243646", "alert_name": "High CPU Usage", "resolved_at": "2025-11-15T21:55:08.395399", "duration": "0:01:02.025597"}	low	f	\N	["email"]	\N	2025-11-15 21:55:08.402768	2025-11-15 21:55:08.402768
22	1	alert_resolution	✅ Resolved: High CPU Usage	Alert 'High CPU Usage' has been resolved.	{"alert_id": "high_cpu_usage_1763243646", "alert_name": "High CPU Usage", "resolved_at": "2025-11-15T21:55:08.395399", "duration": "0:01:02.025597"}	low	f	\N	["slack"]	\N	2025-11-15 21:55:08.418212	2025-11-15 21:55:08.418212
23	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763243646", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-15T21:55:08.422276", "duration": "0:01:01.934111"}	low	f	\N	["email"]	\N	2025-11-15 21:55:08.430339	2025-11-15 21:55:08.430339
24	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763243646", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-15T21:55:08.422276", "duration": "0:01:01.934111"}	low	f	\N	["slack"]	\N	2025-11-15 21:55:08.440715	2025-11-15 21:55:08.440715
25	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763243646", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-15T21:55:08.422276", "duration": "0:01:01.934111"}	low	f	\N	["sms"]	\N	2025-11-15 21:55:08.451627	2025-11-15 21:55:08.451627
26	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-15 21:57:16 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763243836", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-15T21:57:16.079977", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["email"]	\N	2025-11-15 21:57:16.151643	2025-11-15 21:57:16.151643
27	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-15 21:57:16 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763243836", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-15T21:57:16.079977", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["slack"]	\N	2025-11-15 21:57:16.19598	2025-11-15 21:57:16.19598
28	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 21:57:16 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763243836", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T21:57:16.199574", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["email"]	\N	2025-11-15 21:57:16.217737	2025-11-15 21:57:16.217737
29	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 21:57:16 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763243836", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T21:57:16.199574", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["slack"]	\N	2025-11-15 21:57:16.239018	2025-11-15 21:57:16.239018
30	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 21:57:16 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763243836", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T21:57:16.199574", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["sms"]	\N	2025-11-15 21:57:16.264998	2025-11-15 21:57:16.264998
31	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-15 22:05:53 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763244353", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-15T22:05:53.796215", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["email"]	\N	2025-11-15 22:05:53.877669	2025-11-15 22:05:53.877669
32	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-15 22:05:53 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763244353", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-15T22:05:53.796215", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["slack"]	\N	2025-11-15 22:05:53.911028	2025-11-15 22:05:53.911028
33	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 22:05:53 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763244353", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T22:05:53.917837", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["email"]	\N	2025-11-15 22:05:53.932504	2025-11-15 22:05:53.932504
34	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 22:05:53 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763244353", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T22:05:53.917837", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["slack"]	\N	2025-11-15 22:05:53.952039	2025-11-15 22:05:53.952039
35	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 22:05:53 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763244353", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T22:05:53.917837", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["sms"]	\N	2025-11-15 22:05:53.97184	2025-11-15 22:05:53.97184
36	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-15 22:13:53 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763244833", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-15T22:13:53.875202", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["email"]	\N	2025-11-15 22:13:53.935671	2025-11-15 22:13:53.935671
37	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-15 22:13:53 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763244833", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-15T22:13:53.875202", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["slack"]	\N	2025-11-15 22:13:53.965008	2025-11-15 22:13:53.965008
38	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 22:13:53 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763244833", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T22:13:53.970740", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["email"]	\N	2025-11-15 22:13:53.988076	2025-11-15 22:13:53.988076
39	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 22:13:53 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763244833", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T22:13:53.970740", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["slack"]	\N	2025-11-15 22:13:54.005006	2025-11-15 22:13:54.005006
40	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 22:13:53 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763244833", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T22:13:53.970740", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["sms"]	\N	2025-11-15 22:13:54.02381	2025-11-15 22:13:54.02381
41	1	alert_resolution	✅ Resolved: High CPU Usage	Alert 'High CPU Usage' has been resolved.	{"alert_id": "high_cpu_usage_1763244833", "alert_name": "High CPU Usage", "resolved_at": "2025-11-15T22:15:57.941955", "duration": "0:02:04.066753"}	low	f	\N	["email"]	\N	2025-11-15 22:15:57.950042	2025-11-15 22:15:57.950042
42	1	alert_resolution	✅ Resolved: High CPU Usage	Alert 'High CPU Usage' has been resolved.	{"alert_id": "high_cpu_usage_1763244833", "alert_name": "High CPU Usage", "resolved_at": "2025-11-15T22:15:57.941955", "duration": "0:02:04.066753"}	low	f	\N	["slack"]	\N	2025-11-15 22:15:57.961114	2025-11-15 22:15:57.961114
43	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763244833", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-15T22:15:57.964324", "duration": "0:02:03.993584"}	low	f	\N	["email"]	\N	2025-11-15 22:15:57.970698	2025-11-15 22:15:57.970698
44	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763244833", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-15T22:15:57.964324", "duration": "0:02:03.993584"}	low	f	\N	["slack"]	\N	2025-11-15 22:15:57.980935	2025-11-15 22:15:57.980935
45	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763244833", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-15T22:15:57.964324", "duration": "0:02:03.993584"}	low	f	\N	["sms"]	\N	2025-11-15 22:15:57.991862	2025-11-15 22:15:57.991862
46	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-15 22:22:51 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763245371", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-15T22:22:51.336433", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["email"]	\N	2025-11-15 22:22:51.417232	2025-11-15 22:22:51.417232
47	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-15 22:22:51 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763245371", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-15T22:22:51.336433", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["slack"]	\N	2025-11-15 22:22:51.471367	2025-11-15 22:22:51.471367
48	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 22:22:51 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763245371", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T22:22:51.484205", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["email"]	\N	2025-11-15 22:22:51.504551	2025-11-15 22:22:51.504551
49	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 22:22:51 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763245371", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T22:22:51.484205", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["slack"]	\N	2025-11-15 22:22:51.530579	2025-11-15 22:22:51.530579
50	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 22:22:51 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763245371", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T22:22:51.484205", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["sms"]	\N	2025-11-15 22:22:51.559208	2025-11-15 22:22:51.559208
51	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-15 22:25:05 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763245505", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-15T22:25:05.663185", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["email"]	\N	2025-11-15 22:25:05.743862	2025-11-15 22:25:05.743862
52	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-15 22:25:05 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763245505", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-15T22:25:05.663185", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["slack"]	\N	2025-11-15 22:25:05.775585	2025-11-15 22:25:05.775585
53	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 22:25:05 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763245505", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T22:25:05.785860", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["email"]	\N	2025-11-15 22:25:05.805428	2025-11-15 22:25:05.805428
54	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 22:25:05 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763245505", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T22:25:05.785860", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["slack"]	\N	2025-11-15 22:25:05.829347	2025-11-15 22:25:05.829347
55	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 22:25:05 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763245505", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T22:25:05.785860", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["sms"]	\N	2025-11-15 22:25:05.855195	2025-11-15 22:25:05.855195
56	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-15 22:29:23 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763245763", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-15T22:29:23.515971", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["email"]	\N	2025-11-15 22:29:23.581205	2025-11-15 22:29:23.581205
57	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-15 22:29:23 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763245763", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-15T22:29:23.515971", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["slack"]	\N	2025-11-15 22:29:23.618453	2025-11-15 22:29:23.618453
58	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 22:29:23 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763245763", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T22:29:23.626392", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["email"]	\N	2025-11-15 22:29:23.643707	2025-11-15 22:29:23.643707
59	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 22:29:23 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763245763", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T22:29:23.626392", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["slack"]	\N	2025-11-15 22:29:23.669597	2025-11-15 22:29:23.669597
60	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 22:29:23 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763245763", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T22:29:23.626392", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["sms"]	\N	2025-11-15 22:29:23.69711	2025-11-15 22:29:23.69711
61	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-15 22:34:10 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763246050", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-15T22:34:10.766378", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["email"]	\N	2025-11-15 22:34:10.838395	2025-11-15 22:34:10.838395
62	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-15 22:34:10 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763246050", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-15T22:34:10.766378", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["slack"]	\N	2025-11-15 22:34:10.881228	2025-11-15 22:34:10.881228
63	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 22:34:10 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763246050", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T22:34:10.887683", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["email"]	\N	2025-11-15 22:34:10.907942	2025-11-15 22:34:10.907942
64	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 22:34:10 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763246050", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T22:34:10.887683", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["slack"]	\N	2025-11-15 22:34:10.930034	2025-11-15 22:34:10.930034
65	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 22:34:10 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763246050", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T22:34:10.887683", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["sms"]	\N	2025-11-15 22:34:10.955045	2025-11-15 22:34:10.955045
66	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-15 22:39:17 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763246357", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-15T22:39:17.111275", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["email"]	\N	2025-11-15 22:39:17.162071	2025-11-15 22:39:17.162071
67	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-15 22:39:17 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763246357", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-15T22:39:17.111275", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["slack"]	\N	2025-11-15 22:39:17.190365	2025-11-15 22:39:17.190365
68	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 22:39:17 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763246357", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T22:39:17.196338", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["email"]	\N	2025-11-15 22:39:17.205377	2025-11-15 22:39:17.205377
69	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 22:39:17 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763246357", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T22:39:17.196338", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["slack"]	\N	2025-11-15 22:39:17.221223	2025-11-15 22:39:17.221223
70	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 22:39:17 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763246357", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T22:39:17.196338", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["sms"]	\N	2025-11-15 22:39:17.235958	2025-11-15 22:39:17.235958
71	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-15 22:52:40 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763247160", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-15T22:52:40.081943", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["email"]	\N	2025-11-15 22:52:40.145921	2025-11-15 22:52:40.145921
72	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-15 22:52:40 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763247160", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-15T22:52:40.081943", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["slack"]	\N	2025-11-15 22:52:40.186849	2025-11-15 22:52:40.186849
73	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 22:52:40 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763247160", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T22:52:40.196786", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["email"]	\N	2025-11-15 22:52:40.204622	2025-11-15 22:52:40.204622
74	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 22:52:40 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763247160", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T22:52:40.196786", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["slack"]	\N	2025-11-15 22:52:40.215872	2025-11-15 22:52:40.215872
75	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 22:52:40 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763247160", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T22:52:40.196786", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["sms"]	\N	2025-11-15 22:52:40.233599	2025-11-15 22:52:40.233599
76	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-15 23:08:57 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763248137", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-15T23:08:57.983868", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["email"]	\N	2025-11-15 23:08:58.021566	2025-11-15 23:08:58.021566
77	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-15 23:08:57 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763248137", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-15T23:08:57.983868", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["slack"]	\N	2025-11-15 23:08:58.066267	2025-11-15 23:08:58.066267
78	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 23:08:58 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763248138", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T23:08:58.074502", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["email"]	\N	2025-11-15 23:08:58.090729	2025-11-15 23:08:58.090729
79	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 23:08:58 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763248138", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T23:08:58.074502", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["slack"]	\N	2025-11-15 23:08:58.116096	2025-11-15 23:08:58.116096
80	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-15 23:08:58 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763248138", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-15T23:08:58.074502", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["sms"]	\N	2025-11-15 23:08:58.133399	2025-11-15 23:08:58.133399
81	1	alert_resolution	✅ Resolved: High CPU Usage	Alert 'High CPU Usage' has been resolved.	{"alert_id": "high_cpu_usage_1763248137", "alert_name": "High CPU Usage", "resolved_at": "2025-11-15T23:11:02.048751", "duration": "0:02:04.064883"}	low	f	\N	["email"]	\N	2025-11-15 23:11:02.071253	2025-11-15 23:11:02.071253
82	1	alert_resolution	✅ Resolved: High CPU Usage	Alert 'High CPU Usage' has been resolved.	{"alert_id": "high_cpu_usage_1763248137", "alert_name": "High CPU Usage", "resolved_at": "2025-11-15T23:11:02.048751", "duration": "0:02:04.064883"}	low	f	\N	["slack"]	\N	2025-11-15 23:11:02.115426	2025-11-15 23:11:02.115426
83	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763248138", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-15T23:11:02.122324", "duration": "0:02:04.047822"}	low	f	\N	["email"]	\N	2025-11-15 23:11:02.158616	2025-11-15 23:11:02.158616
84	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763248138", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-15T23:11:02.122324", "duration": "0:02:04.047822"}	low	f	\N	["slack"]	\N	2025-11-15 23:11:02.206892	2025-11-15 23:11:02.206892
85	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763248138", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-15T23:11:02.122324", "duration": "0:02:04.047822"}	low	f	\N	["sms"]	\N	2025-11-15 23:11:02.240425	2025-11-15 23:11:02.240425
86	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 99.0\nThreshold: 80.0\nStarted: 2025-11-15 23:12:04 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763248324", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 99.0, "threshold": 80.0, "started_at": "2025-11-15T23:12:04.112572", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["email"]	\N	2025-11-15 23:12:04.13994	2025-11-15 23:12:04.13994
87	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 99.0\nThreshold: 80.0\nStarted: 2025-11-15 23:12:04 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763248324", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 99.0, "threshold": 80.0, "started_at": "2025-11-15T23:12:04.112572", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["slack"]	\N	2025-11-15 23:12:04.162763	2025-11-15 23:12:04.162763
88	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 99.0\nThreshold: 95.0\nStarted: 2025-11-15 23:12:04 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763248324", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 99.0, "threshold": 95.0, "started_at": "2025-11-15T23:12:04.184543", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["email"]	\N	2025-11-15 23:12:04.205905	2025-11-15 23:12:04.205905
89	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 99.0\nThreshold: 95.0\nStarted: 2025-11-15 23:12:04 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763248324", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 99.0, "threshold": 95.0, "started_at": "2025-11-15T23:12:04.184543", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["slack"]	\N	2025-11-15 23:12:04.240313	2025-11-15 23:12:04.240313
90	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 99.0\nThreshold: 95.0\nStarted: 2025-11-15 23:12:04 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763248324", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 99.0, "threshold": 95.0, "started_at": "2025-11-15T23:12:04.184543", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["sms"]	\N	2025-11-15 23:12:04.267282	2025-11-15 23:12:04.267282
91	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763248324", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-15T23:14:08.179327", "duration": "0:02:03.994784"}	low	f	\N	["email"]	\N	2025-11-15 23:14:08.205866	2025-11-15 23:14:08.205866
92	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763248324", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-15T23:14:08.179327", "duration": "0:02:03.994784"}	low	f	\N	["slack"]	\N	2025-11-15 23:14:08.232992	2025-11-15 23:14:08.232992
93	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763248324", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-15T23:14:08.179327", "duration": "0:02:03.994784"}	low	f	\N	["sms"]	\N	2025-11-15 23:14:08.258979	2025-11-15 23:14:08.258979
94	1	alert_resolution	✅ Resolved: High CPU Usage	Alert 'High CPU Usage' has been resolved.	{"alert_id": "high_cpu_usage_1763248324", "alert_name": "High CPU Usage", "resolved_at": "2025-11-15T23:15:10.200550", "duration": "0:03:06.087978"}	low	f	\N	["email"]	\N	2025-11-15 23:15:10.211193	2025-11-15 23:15:10.211193
95	1	alert_resolution	✅ Resolved: High CPU Usage	Alert 'High CPU Usage' has been resolved.	{"alert_id": "high_cpu_usage_1763248324", "alert_name": "High CPU Usage", "resolved_at": "2025-11-15T23:15:10.200550", "duration": "0:03:06.087978"}	low	f	\N	["slack"]	\N	2025-11-15 23:15:10.223464	2025-11-15 23:15:10.223464
96	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-16 11:55:55 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763294155", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-16T11:55:55.707334", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["email"]	\N	2025-11-16 11:55:55.741201	2025-11-16 11:55:55.741201
97	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-16 11:55:55 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763294155", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-16T11:55:55.707334", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["slack"]	\N	2025-11-16 11:55:55.779826	2025-11-16 11:55:55.779826
98	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-16 11:55:55 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763294155", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-16T11:55:55.788464", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["email"]	\N	2025-11-16 11:55:55.810157	2025-11-16 11:55:55.810157
99	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-16 11:55:55 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763294155", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-16T11:55:55.788464", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["slack"]	\N	2025-11-16 11:55:55.838628	2025-11-16 11:55:55.838628
100	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-16 11:55:55 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763294155", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-16T11:55:55.788464", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["sms"]	\N	2025-11-16 11:55:55.86465	2025-11-16 11:55:55.86465
101	1	alert_resolution	✅ Resolved: High CPU Usage	Alert 'High CPU Usage' has been resolved.	{"alert_id": "high_cpu_usage_1763294155", "alert_name": "High CPU Usage", "resolved_at": "2025-11-16T11:57:59.790439", "duration": "0:02:04.083105"}	low	f	\N	["email"]	\N	2025-11-16 11:57:59.802246	2025-11-16 11:57:59.802246
102	1	alert_resolution	✅ Resolved: High CPU Usage	Alert 'High CPU Usage' has been resolved.	{"alert_id": "high_cpu_usage_1763294155", "alert_name": "High CPU Usage", "resolved_at": "2025-11-16T11:57:59.790439", "duration": "0:02:04.083105"}	low	f	\N	["slack"]	\N	2025-11-16 11:57:59.820501	2025-11-16 11:57:59.820501
103	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763294155", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-16T11:57:59.825447", "duration": "0:02:04.036983"}	low	f	\N	["email"]	\N	2025-11-16 11:57:59.833654	2025-11-16 11:57:59.833654
104	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763294155", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-16T11:57:59.825447", "duration": "0:02:04.036983"}	low	f	\N	["slack"]	\N	2025-11-16 11:57:59.849911	2025-11-16 11:57:59.849911
105	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763294155", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-16T11:57:59.825447", "duration": "0:02:04.036983"}	low	f	\N	["sms"]	\N	2025-11-16 11:57:59.862479	2025-11-16 11:57:59.862479
106	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-16 19:34:52 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763321692", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-16T19:34:52.134493", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["email"]	\N	2025-11-16 19:34:52.159738	2025-11-16 19:34:52.159738
107	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-16 19:34:52 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763321692", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-16T19:34:52.134493", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["slack"]	\N	2025-11-16 19:34:52.207624	2025-11-16 19:34:52.207624
108	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-16 19:34:52 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763321692", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-16T19:34:52.217937", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["email"]	\N	2025-11-16 19:34:52.234884	2025-11-16 19:34:52.234884
109	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-16 19:34:52 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763321692", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-16T19:34:52.217937", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["slack"]	\N	2025-11-16 19:34:52.2576	2025-11-16 19:34:52.2576
110	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-16 19:34:52 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763321692", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-16T19:34:52.217937", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["sms"]	\N	2025-11-16 19:34:52.286967	2025-11-16 19:34:52.286967
111	1	alert_resolution	✅ Resolved: High CPU Usage	Alert 'High CPU Usage' has been resolved.	{"alert_id": "high_cpu_usage_1763321692", "alert_name": "High CPU Usage", "resolved_at": "2025-11-16T19:40:02.312932", "duration": "0:05:10.178439"}	low	f	\N	["email"]	\N	2025-11-16 19:40:02.32659	2025-11-16 19:40:02.32659
112	1	alert_resolution	✅ Resolved: High CPU Usage	Alert 'High CPU Usage' has been resolved.	{"alert_id": "high_cpu_usage_1763321692", "alert_name": "High CPU Usage", "resolved_at": "2025-11-16T19:40:02.312932", "duration": "0:05:10.178439"}	low	f	\N	["slack"]	\N	2025-11-16 19:40:02.360029	2025-11-16 19:40:02.360029
113	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763321692", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-16T19:40:02.376936", "duration": "0:05:10.158999"}	low	f	\N	["email"]	\N	2025-11-16 19:40:02.395301	2025-11-16 19:40:02.395301
114	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763321692", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-16T19:40:02.376936", "duration": "0:05:10.158999"}	low	f	\N	["slack"]	\N	2025-11-16 19:40:02.472266	2025-11-16 19:40:02.472266
115	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763321692", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-16T19:40:02.376936", "duration": "0:05:10.158999"}	low	f	\N	["sms"]	\N	2025-11-16 19:40:02.520079	2025-11-16 19:40:02.520079
116	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-16 23:59:29 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763337569", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-16T23:59:29.146715", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["email"]	\N	2025-11-16 23:59:29.17029	2025-11-16 23:59:29.17029
133	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763337879", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-17T00:05:41.364489", "duration": "0:01:01.991524"}	low	f	\N	["email"]	\N	2025-11-17 00:05:41.372746	2025-11-17 00:05:41.372746
117	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-16 23:59:29 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763337569", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-16T23:59:29.146715", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["slack"]	\N	2025-11-16 23:59:29.205099	2025-11-16 23:59:29.205099
118	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-16 23:59:29 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763337569", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-16T23:59:29.212296", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["email"]	\N	2025-11-16 23:59:29.230509	2025-11-16 23:59:29.230509
119	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-16 23:59:29 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763337569", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-16T23:59:29.212296", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["slack"]	\N	2025-11-16 23:59:29.254529	2025-11-16 23:59:29.254529
120	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-16 23:59:29 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763337569", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-16T23:59:29.212296", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["sms"]	\N	2025-11-16 23:59:29.274465	2025-11-16 23:59:29.274465
121	1	alert_resolution	✅ Resolved: High CPU Usage	Alert 'High CPU Usage' has been resolved.	{"alert_id": "high_cpu_usage_1763337569", "alert_name": "High CPU Usage", "resolved_at": "2025-11-17T00:02:35.234849", "duration": "0:03:06.088134"}	low	f	\N	["email"]	\N	2025-11-17 00:02:35.245983	2025-11-17 00:02:35.245983
122	1	alert_resolution	✅ Resolved: High CPU Usage	Alert 'High CPU Usage' has been resolved.	{"alert_id": "high_cpu_usage_1763337569", "alert_name": "High CPU Usage", "resolved_at": "2025-11-17T00:02:35.234849", "duration": "0:03:06.088134"}	low	f	\N	["slack"]	\N	2025-11-17 00:02:35.258755	2025-11-17 00:02:35.258755
123	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763337569", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-17T00:02:35.263311", "duration": "0:03:06.051015"}	low	f	\N	["email"]	\N	2025-11-17 00:02:35.281582	2025-11-17 00:02:35.281582
124	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763337569", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-17T00:02:35.263311", "duration": "0:03:06.051015"}	low	f	\N	["slack"]	\N	2025-11-17 00:02:35.294837	2025-11-17 00:02:35.294837
125	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763337569", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-17T00:02:35.263311", "duration": "0:03:06.051015"}	low	f	\N	["sms"]	\N	2025-11-17 00:02:35.31109	2025-11-17 00:02:35.31109
126	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-17 00:04:39 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763337879", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-17T00:04:39.310211", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["email"]	\N	2025-11-17 00:04:39.340228	2025-11-17 00:04:39.340228
127	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-17 00:04:39 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763337879", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-17T00:04:39.310211", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["slack"]	\N	2025-11-17 00:04:39.367065	2025-11-17 00:04:39.367065
128	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-17 00:04:39 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763337879", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-17T00:04:39.372965", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["email"]	\N	2025-11-17 00:04:39.384963	2025-11-17 00:04:39.384963
129	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-17 00:04:39 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763337879", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-17T00:04:39.372965", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["slack"]	\N	2025-11-17 00:04:39.422013	2025-11-17 00:04:39.422013
130	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-17 00:04:39 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763337879", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-17T00:04:39.372965", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["sms"]	\N	2025-11-17 00:04:39.447111	2025-11-17 00:04:39.447111
131	1	alert_resolution	✅ Resolved: High CPU Usage	Alert 'High CPU Usage' has been resolved.	{"alert_id": "high_cpu_usage_1763337879", "alert_name": "High CPU Usage", "resolved_at": "2025-11-17T00:05:41.324406", "duration": "0:01:02.014195"}	low	f	\N	["email"]	\N	2025-11-17 00:05:41.333255	2025-11-17 00:05:41.333255
132	1	alert_resolution	✅ Resolved: High CPU Usage	Alert 'High CPU Usage' has been resolved.	{"alert_id": "high_cpu_usage_1763337879", "alert_name": "High CPU Usage", "resolved_at": "2025-11-17T00:05:41.324406", "duration": "0:01:02.014195"}	low	f	\N	["slack"]	\N	2025-11-17 00:05:41.354846	2025-11-17 00:05:41.354846
134	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763337879", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-17T00:05:41.364489", "duration": "0:01:01.991524"}	low	f	\N	["slack"]	\N	2025-11-17 00:05:41.386308	2025-11-17 00:05:41.386308
135	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763337879", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-17T00:05:41.364489", "duration": "0:01:01.991524"}	low	f	\N	["sms"]	\N	2025-11-17 00:05:41.398542	2025-11-17 00:05:41.398542
136	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-17 12:12:21 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763381541", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-17T12:12:21.268260", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["email"]	\N	2025-11-17 12:12:21.293291	2025-11-17 12:12:21.293291
137	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-17 12:12:21 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763381541", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-17T12:12:21.268260", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["slack"]	\N	2025-11-17 12:12:21.331692	2025-11-17 12:12:21.331692
138	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-17 12:12:21 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763381541", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-17T12:12:21.342038", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["email"]	\N	2025-11-17 12:12:21.359018	2025-11-17 12:12:21.359018
139	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-17 12:12:21 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763381541", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-17T12:12:21.342038", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["slack"]	\N	2025-11-17 12:12:21.384232	2025-11-17 12:12:21.384232
140	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-17 12:12:21 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763381541", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-17T12:12:21.342038", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["sms"]	\N	2025-11-17 12:12:21.416559	2025-11-17 12:12:21.416559
141	1	alert_resolution	✅ Resolved: High CPU Usage	Alert 'High CPU Usage' has been resolved.	{"alert_id": "high_cpu_usage_1763381541", "alert_name": "High CPU Usage", "resolved_at": "2025-11-17T12:16:29.414970", "duration": "0:04:08.146710"}	low	f	\N	["email"]	\N	2025-11-17 12:16:29.445766	2025-11-17 12:16:29.445766
142	1	alert_resolution	✅ Resolved: High CPU Usage	Alert 'High CPU Usage' has been resolved.	{"alert_id": "high_cpu_usage_1763381541", "alert_name": "High CPU Usage", "resolved_at": "2025-11-17T12:16:29.414970", "duration": "0:04:08.146710"}	low	f	\N	["slack"]	\N	2025-11-17 12:16:29.469168	2025-11-17 12:16:29.469168
143	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763381541", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-17T12:16:29.495200", "duration": "0:04:08.153162"}	low	f	\N	["email"]	\N	2025-11-17 12:16:29.509166	2025-11-17 12:16:29.509166
144	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763381541", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-17T12:16:29.495200", "duration": "0:04:08.153162"}	low	f	\N	["slack"]	\N	2025-11-17 12:16:29.535084	2025-11-17 12:16:29.535084
145	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763381541", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-17T12:16:29.495200", "duration": "0:04:08.153162"}	low	f	\N	["sms"]	\N	2025-11-17 12:16:29.552596	2025-11-17 12:16:29.552596
146	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-17 20:01:22 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763409682", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-17T20:01:22.870816", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["email"]	\N	2025-11-17 20:01:22.951034	2025-11-17 20:01:22.951034
147	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-17 20:01:22 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763409682", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-17T20:01:22.870816", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["slack"]	\N	2025-11-17 20:01:22.973328	2025-11-17 20:01:22.973328
148	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-17 20:01:22 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763409682", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-17T20:01:22.978149", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["email"]	\N	2025-11-17 20:01:22.988475	2025-11-17 20:01:22.988475
149	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-17 20:01:22 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763409682", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-17T20:01:22.978149", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["slack"]	\N	2025-11-17 20:01:23.005187	2025-11-17 20:01:23.005187
173	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763414835", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-17T21:29:19.576936", "duration": "0:02:04.021024"}	low	f	\N	["email"]	\N	2025-11-17 21:29:19.584031	2025-11-17 21:29:19.584031
150	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-17 20:01:22 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763409682", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-17T20:01:22.978149", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["sms"]	\N	2025-11-17 20:01:23.028221	2025-11-17 20:01:23.028221
151	1	alert_resolution	✅ Resolved: High CPU Usage	Alert 'High CPU Usage' has been resolved.	{"alert_id": "high_cpu_usage_1763409682", "alert_name": "High CPU Usage", "resolved_at": "2025-11-17T20:04:28.957439", "duration": "0:03:06.086623"}	low	f	\N	["email"]	\N	2025-11-17 20:04:28.969734	2025-11-17 20:04:28.969734
152	1	alert_resolution	✅ Resolved: High CPU Usage	Alert 'High CPU Usage' has been resolved.	{"alert_id": "high_cpu_usage_1763409682", "alert_name": "High CPU Usage", "resolved_at": "2025-11-17T20:04:28.957439", "duration": "0:03:06.086623"}	low	f	\N	["slack"]	\N	2025-11-17 20:04:28.985185	2025-11-17 20:04:28.985185
153	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763409682", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-17T20:04:28.991259", "duration": "0:03:06.013110"}	low	f	\N	["email"]	\N	2025-11-17 20:04:29.000049	2025-11-17 20:04:29.000049
154	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763409682", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-17T20:04:28.991259", "duration": "0:03:06.013110"}	low	f	\N	["slack"]	\N	2025-11-17 20:04:29.013939	2025-11-17 20:04:29.013939
155	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763409682", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-17T20:04:28.991259", "duration": "0:03:06.013110"}	low	f	\N	["sms"]	\N	2025-11-17 20:04:29.026143	2025-11-17 20:04:29.026143
156	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-17 21:02:26 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763413346", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-17T21:02:26.966607", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["email"]	\N	2025-11-17 21:02:27.0564	2025-11-17 21:02:27.0564
157	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-17 21:02:26 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763413346", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-17T21:02:26.966607", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["slack"]	\N	2025-11-17 21:02:27.083316	2025-11-17 21:02:27.083316
158	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-17 21:02:27 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763413347", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-17T21:02:27.087047", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["email"]	\N	2025-11-17 21:02:27.094682	2025-11-17 21:02:27.094682
159	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-17 21:02:27 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763413347", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-17T21:02:27.087047", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["slack"]	\N	2025-11-17 21:02:27.117058	2025-11-17 21:02:27.117058
160	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-17 21:02:27 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763413347", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-17T21:02:27.087047", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["sms"]	\N	2025-11-17 21:02:27.127186	2025-11-17 21:02:27.127186
161	1	alert_resolution	✅ Resolved: High CPU Usage	Alert 'High CPU Usage' has been resolved.	{"alert_id": "high_cpu_usage_1763413346", "alert_name": "High CPU Usage", "resolved_at": "2025-11-17T21:08:39.180751", "duration": "0:06:12.214144"}	low	f	\N	["email"]	\N	2025-11-17 21:08:39.192125	2025-11-17 21:08:39.192125
162	1	alert_resolution	✅ Resolved: High CPU Usage	Alert 'High CPU Usage' has been resolved.	{"alert_id": "high_cpu_usage_1763413346", "alert_name": "High CPU Usage", "resolved_at": "2025-11-17T21:08:39.180751", "duration": "0:06:12.214144"}	low	f	\N	["slack"]	\N	2025-11-17 21:08:39.207058	2025-11-17 21:08:39.207058
163	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763413347", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-17T21:08:39.212438", "duration": "0:06:12.125391"}	low	f	\N	["email"]	\N	2025-11-17 21:08:39.222019	2025-11-17 21:08:39.222019
164	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763413347", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-17T21:08:39.212438", "duration": "0:06:12.125391"}	low	f	\N	["slack"]	\N	2025-11-17 21:08:39.237845	2025-11-17 21:08:39.237845
165	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763413347", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-17T21:08:39.212438", "duration": "0:06:12.125391"}	low	f	\N	["sms"]	\N	2025-11-17 21:08:39.249041	2025-11-17 21:08:39.249041
166	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-17 21:27:15 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763414835", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-17T21:27:15.496987", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["email"]	\N	2025-11-17 21:27:15.523835	2025-11-17 21:27:15.523835
171	1	alert_resolution	✅ Resolved: High CPU Usage	Alert 'High CPU Usage' has been resolved.	{"alert_id": "high_cpu_usage_1763414835", "alert_name": "High CPU Usage", "resolved_at": "2025-11-17T21:29:19.550432", "duration": "0:02:04.053445"}	low	f	\N	["email"]	\N	2025-11-17 21:29:19.5614	2025-11-17 21:29:19.5614
167	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-17 21:27:15 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763414835", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-17T21:27:15.496987", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["slack"]	\N	2025-11-17 21:27:15.551098	2025-11-17 21:27:15.551098
168	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-17 21:27:15 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763414835", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-17T21:27:15.555912", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["email"]	\N	2025-11-17 21:27:15.575066	2025-11-17 21:27:15.575066
169	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-17 21:27:15 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763414835", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-17T21:27:15.555912", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["slack"]	\N	2025-11-17 21:27:15.591997	2025-11-17 21:27:15.591997
170	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-17 21:27:15 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763414835", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-17T21:27:15.555912", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["sms"]	\N	2025-11-17 21:27:15.612739	2025-11-17 21:27:15.612739
172	1	alert_resolution	✅ Resolved: High CPU Usage	Alert 'High CPU Usage' has been resolved.	{"alert_id": "high_cpu_usage_1763414835", "alert_name": "High CPU Usage", "resolved_at": "2025-11-17T21:29:19.550432", "duration": "0:02:04.053445"}	low	f	\N	["slack"]	\N	2025-11-17 21:29:19.5732	2025-11-17 21:29:19.5732
175	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763414835", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-17T21:29:19.576936", "duration": "0:02:04.021024"}	low	f	\N	["sms"]	\N	2025-11-17 21:29:19.605056	2025-11-17 21:29:19.605056
174	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763414835", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-17T21:29:19.576936", "duration": "0:02:04.021024"}	low	f	\N	["slack"]	\N	2025-11-17 21:29:19.594832	2025-11-17 21:29:19.594832
176	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-17 21:53:20 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763416400", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-17T21:53:20.958901", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["email"]	\N	2025-11-17 21:53:21.033127	2025-11-17 21:53:21.033127
177	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 80.0\nStarted: 2025-11-17 21:53:20 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763416400", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 80.0, "started_at": "2025-11-17T21:53:20.958901", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["slack"]	\N	2025-11-17 21:53:21.067711	2025-11-17 21:53:21.067711
178	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-17 21:53:21 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763416401", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-17T21:53:21.074719", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["email"]	\N	2025-11-17 21:53:21.090142	2025-11-17 21:53:21.090142
179	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-17 21:53:21 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763416401", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-17T21:53:21.074719", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["slack"]	\N	2025-11-17 21:53:21.110023	2025-11-17 21:53:21.110023
180	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 100.0\nThreshold: 95.0\nStarted: 2025-11-17 21:53:21 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763416401", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 100.0, "threshold": 95.0, "started_at": "2025-11-17T21:53:21.074719", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["sms"]	\N	2025-11-17 21:53:21.130093	2025-11-17 21:53:21.130093
181	1	alert_resolution	✅ Resolved: High CPU Usage	Alert 'High CPU Usage' has been resolved.	{"alert_id": "high_cpu_usage_1763416400", "alert_name": "High CPU Usage", "resolved_at": "2025-11-17T21:58:31.120118", "duration": "0:05:10.161217"}	low	f	\N	["email"]	\N	2025-11-17 21:58:31.132247	2025-11-17 21:58:31.132247
182	1	alert_resolution	✅ Resolved: High CPU Usage	Alert 'High CPU Usage' has been resolved.	{"alert_id": "high_cpu_usage_1763416400", "alert_name": "High CPU Usage", "resolved_at": "2025-11-17T21:58:31.120118", "duration": "0:05:10.161217"}	low	f	\N	["slack"]	\N	2025-11-17 21:58:31.148474	2025-11-17 21:58:31.148474
183	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763416401", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-17T21:58:31.152692", "duration": "0:05:10.077973"}	low	f	\N	["email"]	\N	2025-11-17 21:58:31.160497	2025-11-17 21:58:31.160497
184	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763416401", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-17T21:58:31.152692", "duration": "0:05:10.077973"}	low	f	\N	["slack"]	\N	2025-11-17 21:58:31.171591	2025-11-17 21:58:31.171591
185	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763416401", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-17T21:58:31.152692", "duration": "0:05:10.077973"}	low	f	\N	["sms"]	\N	2025-11-17 21:58:31.182191	2025-11-17 21:58:31.182191
186	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 99.0\nThreshold: 80.0\nStarted: 2025-11-17 21:59:33 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763416773", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 99.0, "threshold": 80.0, "started_at": "2025-11-17T21:59:33.159152", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["email"]	\N	2025-11-17 21:59:33.174518	2025-11-17 21:59:33.174518
187	1	alert	🚨 High CPU Usage	⚠️ High CPU Usage\n\nDescription: CPU usage is above threshold\nMetric: cpu_usage\nCurrent Value: 99.0\nThreshold: 80.0\nStarted: 2025-11-17 21:59:33 UTC\nTags: category=system, component=cpu\n	{"alert_id": "high_cpu_usage_1763416773", "alert_name": "High CPU Usage", "description": "CPU usage is above threshold", "severity": "warning", "metric_name": "cpu_usage", "current_value": 99.0, "threshold": 80.0, "started_at": "2025-11-17T21:59:33.159152", "tags": {"category": "system", "component": "cpu"}}	medium	f	\N	["slack"]	\N	2025-11-17 21:59:33.198087	2025-11-17 21:59:33.198087
188	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 99.0\nThreshold: 95.0\nStarted: 2025-11-17 21:59:33 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763416773", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 99.0, "threshold": 95.0, "started_at": "2025-11-17T21:59:33.204210", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["email"]	\N	2025-11-17 21:59:33.220484	2025-11-17 21:59:33.220484
189	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 99.0\nThreshold: 95.0\nStarted: 2025-11-17 21:59:33 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763416773", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 99.0, "threshold": 95.0, "started_at": "2025-11-17T21:59:33.204210", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["slack"]	\N	2025-11-17 21:59:33.242023	2025-11-17 21:59:33.242023
190	1	alert	🚨 Critical CPU Usage	🚨 Critical CPU Usage\n\nDescription: CPU usage is critically high\nMetric: cpu_usage\nCurrent Value: 99.0\nThreshold: 95.0\nStarted: 2025-11-17 21:59:33 UTC\nTags: category=system, component=cpu\n	{"alert_id": "critical_cpu_usage_1763416773", "alert_name": "Critical CPU Usage", "description": "CPU usage is critically high", "severity": "critical", "metric_name": "cpu_usage", "current_value": 99.0, "threshold": 95.0, "started_at": "2025-11-17T21:59:33.204210", "tags": {"category": "system", "component": "cpu"}}	high	f	\N	["sms"]	\N	2025-11-17 21:59:33.25907	2025-11-17 21:59:33.25907
191	1	alert_resolution	✅ Resolved: High CPU Usage	Alert 'High CPU Usage' has been resolved.	{"alert_id": "high_cpu_usage_1763416773", "alert_name": "High CPU Usage", "resolved_at": "2025-11-17T22:03:41.357348", "duration": "0:04:08.198196"}	low	f	\N	["email"]	\N	2025-11-17 22:03:41.371143	2025-11-17 22:03:41.371143
192	1	alert_resolution	✅ Resolved: High CPU Usage	Alert 'High CPU Usage' has been resolved.	{"alert_id": "high_cpu_usage_1763416773", "alert_name": "High CPU Usage", "resolved_at": "2025-11-17T22:03:41.357348", "duration": "0:04:08.198196"}	low	f	\N	["slack"]	\N	2025-11-17 22:03:41.383741	2025-11-17 22:03:41.383741
193	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763416773", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-17T22:03:41.388562", "duration": "0:04:08.184352"}	low	f	\N	["email"]	\N	2025-11-17 22:03:41.396468	2025-11-17 22:03:41.396468
194	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763416773", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-17T22:03:41.388562", "duration": "0:04:08.184352"}	low	f	\N	["slack"]	\N	2025-11-17 22:03:41.409034	2025-11-17 22:03:41.409034
195	1	alert_resolution	✅ Resolved: Critical CPU Usage	Alert 'Critical CPU Usage' has been resolved.	{"alert_id": "critical_cpu_usage_1763416773", "alert_name": "Critical CPU Usage", "resolved_at": "2025-11-17T22:03:41.388562", "duration": "0:04:08.184352"}	low	f	\N	["sms"]	\N	2025-11-17 22:03:41.420603	2025-11-17 22:03:41.420603
\.


--
-- Data for Name: audit_logs; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.audit_logs (id, user_id, action, resource, resource_id, ip_address, user_agent, session_id, description, details, severity, status, error_message, created_at, request_id, duration_ms) FROM stdin;
\.


--
-- Data for Name: availability_periods; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.availability_periods (id, resource_id, type, start_date, end_date, description, is_approved, approved_by, created_at) FROM stdin;
\.


--
-- Data for Name: backup_integrity_checks; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.backup_integrity_checks (id, backup_record_id, status, check_type, checked_at, check_duration_seconds, passed, error_message, warnings, details, files_checked, size_verified, checksum_verified) FROM stdin;
\.


--
-- Data for Name: backup_records; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.backup_records (id, name, backup_type, status, backup_path, total_size, components, created_at, started_at, completed_at, created_by, description, tags, success, error_message, warnings, retention_days, compression_enabled, encryption_enabled, duration_seconds, files_count) FROM stdin;
\.


--
-- Data for Name: backup_schedules; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.backup_schedules (id, name, description, enabled, cron_expression, timezone, backup_components, retention_days, compression_enabled, encryption_enabled, notify_on_success, notify_on_failure, notification_channels, notification_recipients, created_at, updated_at, created_by, last_run_at, last_run_status, next_run_at, total_runs, successful_runs, failed_runs) FROM stdin;
\.


--
-- Data for Name: chat_messages; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.chat_messages (id, session_id, role, content, message_metadata, audio_url, audio_duration, created_at) FROM stdin;
35	55	user	Какие кодексы ты знаешь?	\N	\N	\N	2025-11-14 17:57:49.304712+00
37	58	user	Какие кодексы та знаешь?	\N	\N	\N	2025-11-15 14:19:39.588265+00
38	58	assistant	В России действуют следующие основные кодексы:\n1. Гражданский кодекс РФ (ГК РФ)\n2. Уголовный кодекс РФ (УК РФ)\n3. Кодекс об административных правонарушениях РФ (КоАП РФ)\n4. Трудовой кодекс РФ (ТК РФ)\n5. Налоговый кодекс РФ (НК РФ) - состоит из двух частей\n6. Уголовно-процессуальный кодекс РФ (УПК РФ)\n7. Гражданский процессуальный кодекс РФ (ГПК РФ)\n8. Арбитражный процессуальный кодекс РФ (АПК РФ)\n9. Кодекс торгового мореплавания РФ\n10. Воздушный кодекс РФ\n11. Лесной кодекс РФ\n12. Водный кодекс РФ\n13. Земельный кодекс РФ\n14. Жилищный кодекс РФ\n15. Семейный кодекс РФ\n16. Таможенный кодекс РФ\n\nТакже существуют региональные кодексы, например:\n- Кодекс об административных правонарушениях субъектов РФ (в некоторых регионах)\n- Кодексы о земельных отношениях отдельных регионов\n\nНужно уточнить конкретный кодекс или раздел законодательства?	{"sources": [{"title": "Vistral-24B-Instruct", "text": "\\u041e\\u0442\\u0432\\u0435\\u0442 \\u043e\\u0442 \\u0440\\u0443\\u0441\\u0441\\u043a\\u043e\\u044f\\u0437\\u044b\\u0447\\u043d\\u043e\\u0439 \\u0418\\u0418-\\u043c\\u043e\\u0434\\u0435\\u043b\\u0438"}], "processing_time": 147.31325316429138, "context_used": false}	\N	\N	2025-11-15 14:19:39.594434+00
83	91	user	кто такой президент?	\N	\N	\N	2025-11-17 21:53:19.796072+00
84	91	assistant	Президент Российской Федерации — это высшее должностное лицо страны, избираемое гражданами России на основе всеобщего, равного и прямого избирательного права при тайном голосовании.  \n\n### **Основные функции Президента РФ** (ст. 83 Конституции РФ):  \n1. **Обеспечение согласованного функционирования органов государственной власти** – координирует работу Правительства, федеральных министерств и ведомств.  \n2. **Определение основных направлений внутренней и внешней политики государства** – утверждает военную доктрину, стратегию национальной безопасности, участвует в формировании внешнеполитического курса.  \n3. **Назначение Председателя Правительства** (с согласия Государственной Думы) и членов Правительства (по предложению Председателя).  \n4. **Подписание федеральных законов** – после их принятия Федеральным Собранием.  \n5. **Обращение к Федеральному Собранию** с ежегодными посланиями о положении в стране и основных направлениях внутренней и внешней политики.  \n6. **Руководство Советом Безопасности РФ** – координирует деятельность силовых структур и спецслужб.  \n7. **Назначение судей Конституционного, Верховного и других судов** (по представлению квалификационных коллегий).  \n8. **Представление кандидатур на должности Генерального прокурора, Председателя Центрального банка и др.**  \n9. **Применение права вето** на законы, принятые Федеральным Собранием.  \n10. **Обеспечение суверенитета и территориальной целостности РФ** – принимает меры по защите конституционного строя.  \n\n### **Порядок избрания** (ст. 81 Конституции РФ):  \n- Избирается на **6 лет** (с 2012 года, ранее – 4 года).  \n- Кандидат должен быть **гражданином РФ не моложе 35 лет**, постоянно проживающим в России не менее 25 лет.  \n- Выборы проводятся на основе **всеобщего, равного и прямого избирательного права** при тайном голосовании.  \n\n### **Ограничения полномочий** (ст. 93 Конституции РФ):  \n- Президент **не может** быть депутатом или занимать иную оплачиваемую должность.  \n- Запрещено совмещение президентских полномочий с членством в политических партиях (с 2012 года).  \n\n### **Особые полномочия** (ст. 92, 93 Конституции РФ):  \n- **Иммунитет** – Президент не может быть привлечен к ответственности за действия, совершенные в период исполнения обязанностей.  \n- **Отрешение от должности** – возможно только по решению Совета Федерации при выдвижении Государственной Думой по основаниям, предусмотренным ст. 93 Конституции РФ (государственная измена, совершение иного тяжкого преступления).  \n\nСейчас Президентом РФ является **Владимир Владимирович Путин** (с 2000 года, с перерывом в 2008–2012 гг.).  \n\nЕсли вам нужны дополнительные разъяснения по конкретным аспектам президентской власти, уточните вопрос.	{"sources": [{"title": "Vistral-24B", "text": "\\u041e\\u0442\\u0432\\u0435\\u0442 \\u043e\\u0442 \\u0440\\u0443\\u0441\\u0441\\u043a\\u043e\\u044f\\u0437\\u044b\\u0447\\u043d\\u043e\\u0439 \\u0418\\u0418-\\u043c\\u043e\\u0434\\u0435\\u043b\\u0438 Vistral-24B"}], "processing_time": 305.67479252815247, "context_used": true}	\N	\N	2025-11-17 21:53:19.805375+00
85	91	user	перечисли еще особые полномочия	\N	\N	\N	2025-11-17 21:58:57.492787+00
66	55	user	Напиши мне один кодекс, который ты считаешь важным	\N	\N	\N	2025-11-16 11:55:36.180307+00
67	55	assistant	Один из ключевых кодексов российского законодательства — **Гражданский кодекс Российской Федерации (ГК РФ)**.  \n\n### **Почему он важен?**  \n1. **Основы гражданского оборота** – регулирует отношения между физическими и юридическими лицами, включая договоры, обязательства, права собственности и интеллектуальную собственность.  \n2. **Защита прав участников гражданского оборота** – устанавливает механизмы защиты интересов сторон в сделках, спорах и недобросовестных действиях.  \n3. **Структурированность права** – разделен на части (общая, обязательственное, вещное, наследственное и др.), что упрощает применение норм.  \n4. **Влияние на другие отрасли права** – многие нормы ГК РФ применяются в арбитражном, семейном, предпринимательском и других видах законодательства.  \n\nЕсли вам нужен анализ конкретной статьи или раздела ГК РФ, уточните вопрос – помогу разобрать детали!	{"sources": [{"title": "Vistral-24B", "text": "\\u041e\\u0442\\u0432\\u0435\\u0442 \\u043e\\u0442 \\u0440\\u0443\\u0441\\u0441\\u043a\\u043e\\u044f\\u0437\\u044b\\u0447\\u043d\\u043e\\u0439 \\u0418\\u0418-\\u043c\\u043e\\u0434\\u0435\\u043b\\u0438 Vistral-24B"}], "processing_time": 113.74790787696838, "context_used": true}	\N	\N	2025-11-16 11:55:36.198121+00
86	91	assistant	Президент Российской Федерации обладает рядом особых полномочий, закреплённых в Конституции РФ (ст. 83–89). Вот их основные категории:  \n\n### **1. Внешняя политика**  \n- Определяет основные направления внешней политики государства.  \n- Ведёт переговоры и подписывает международные договоры (ратифицируются Федеральным Собранием).  \n- Назначает и отзывает дипломатических представителей по согласованию с МИД.  \n- Принимает верительные и отзывные грамоты иностранных дипломатов.  \n\n### **2. Военная сфера**  \n- Является Верховным Главнокомандующим Вооружёнными Силами РФ.  \n- Утверждает военную доктрину.  \n- Вводит военное положение (с согласия Совета Федерации).  \n- Принимает решение о применении Вооружённых Сил за пределами России (с согласия Совета Федерации).  \n\n### **3. Безопасность и оборона**  \n- Обеспечивает независимость и суверенитет страны.  \n- Осуществляет меры по защите конституционного строя.  \n- Утверждает доктрины национальной безопасности и противодействия терроризму.  \n\n### **4. Внутренняя политика**  \n- Обращается с ежегодными посланиями к Федеральному Собранию.  \n- Может распустить Государственную Думу в случаях, предусмотренных Конституцией.  \n- Назначает выборы в Думу и референдумы (по согласованию с Советом Федерации).  \n- Вводит чрезвычайное положение (с согласия Совета Федерации).  \n\n### **5. Судебная система**  \n- Назначает судей Конституционного и Верховного судов (по представлению квалификационных коллегий).  \n- Назначает Генерального прокурора (с согласия Совета Федерации).  \n\n### **6. Кадровые назначения**  \n- Назначает и освобождает от должности:  \n  - Председателя Правительства (с согласия Думы).  \n  - Заместителей Председателя Правительства и федеральных министров.  \n  - Руководителей федеральных органов исполнительной власти.  \n  - Полномочных представителей в федеральных округах.  \n\n### **7. Правовые акты**  \n- Издаёт указы и распоряжения, обязательные для исполнения на всей территории РФ.  \n- Обеспечивает соблюдение Конституции и федеральных законов.  \n\n### **8. Иные полномочия**  \n- Награждает государственными наградами РФ.  \n- Осуществляет помилование (по представлению комиссий).  \n- Обращается к гражданам с обращениями и выступлениями.  \n\nЭти полномочия делают Президента РФ ключевой фигурой в системе власти, сочетающей исполнительные, представительные и контрольные функции.  \n\nЕсли нужны уточнения по конкретным статьям Конституции или практике применения полномочий, уточните вопрос.	{"sources": [{"title": "Vistral-24B", "text": "\\u041e\\u0442\\u0432\\u0435\\u0442 \\u043e\\u0442 \\u0440\\u0443\\u0441\\u0441\\u043a\\u043e\\u044f\\u0437\\u044b\\u0447\\u043d\\u043e\\u0439 \\u0418\\u0418-\\u043c\\u043e\\u0434\\u0435\\u043b\\u0438 Vistral-24B"}], "processing_time": 273.4623324871063, "context_used": true}	\N	\N	2025-11-17 21:58:57.498596+00
76	85	user	Что будет за кражу продуктов в магазине?	\N	\N	\N	2025-11-17 12:12:17.181655+00
\.


--
-- Data for Name: chat_sessions; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.chat_sessions (id, user_id, title, created_at, updated_at) FROM stdin;
91	1	Новый чат 18.11.2025	2025-11-17 21:52:55.282783+00	\N
55	2	Новый чат	2025-11-14 17:57:49.296869+00	\N
58	2	Новый чат	2025-11-15 14:19:39.581524+00	\N
85	3	Новый чат	2025-11-17 12:12:17.175466+00	\N
\.


--
-- Data for Name: cohort_analysis; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.cohort_analysis (id, name, cohort_type, period_type, start_date, end_date, data, user_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: custom_metrics; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.custom_metrics (id, name, description, formula, unit, format_type, user_id, is_public, category, tags, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: dashboard_widgets; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.dashboard_widgets (id, dashboard_id, widget_type, title, config, "position", data_source, refresh_interval, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: dashboards; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.dashboards (id, name, description, user_id, layout, is_public, is_default, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: data_collection_logs; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.data_collection_logs (id, collection_type, source, total_found, total_processed, total_approved, total_rejected, duration_seconds, error_message, created_by, created_at) FROM stdin;
\.


--
-- Data for Name: document_analyses; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.document_analyses (id, user_id, filename, file_type, analysis_result, risks_found, recommendations, created_at) FROM stdin;
\.


--
-- Data for Name: encrypted_messages; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.encrypted_messages (id, chat_session_id, sender_id, recipient_id, encrypted_content, encryption_algorithm, message_hash, message_type, is_read, created_at) FROM stdin;
\.


--
-- Data for Name: encryption_keys; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.encryption_keys (id, user_id, key_type, key_data, is_active, created_at, expires_at) FROM stdin;
\.


--
-- Data for Name: incident_updates; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.incident_updates (id, incident_id, message, update_type, old_status, new_status, author_id, is_public, created_at) FROM stdin;
\.


--
-- Data for Name: incidents; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.incidents (id, title, description, severity, status, source_system, source_id, alert_rule, assigned_to, created_by, project_id, related_task_id, started_at, acknowledged_at, resolved_at, affected_services, affected_users_count, downtime_minutes, incident_metadata, tags, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: metric_alerts; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.metric_alerts (id, metric_id, name, condition, threshold, is_active, notification_channels, user_id, last_triggered, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: metric_values; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.metric_values (id, metric_id, value, "timestamp", labels) FROM stdin;
\.


--
-- Data for Name: milestones; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.milestones (id, name, description, project_id, status, start_date, due_date, completed_date, progress, total_tasks, completed_tasks, total_story_points, completed_story_points, budget, spent_budget, currency, owner_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: ml_predictions; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.ml_predictions (id, model_name, prediction_type, target_user_id, prediction_value, confidence_score, features, model_version, created_at, expires_at) FROM stdin;
\.


--
-- Data for Name: model_versions; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.model_versions (id, version, base_model, lora_config, training_data_count, performance_metrics, is_active, model_path, created_by, created_at) FROM stdin;
\.


--
-- Data for Name: moderation_queue; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.moderation_queue (id, message_id, priority, reason, assigned_to, status, confidence_score, queue_metadata, created_at, assigned_at, completed_at) FROM stdin;
\.


--
-- Data for Name: moderation_reviews; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.moderation_reviews (id, message_id, moderator_id, star_rating, problem_categories, comment, suggested_fix, status, priority, original_confidence, review_metadata, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: moderator_stats; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.moderator_stats (id, moderator_id, total_reviews, points, badges, rank, average_rating, category_stats, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: monitoring_alerts; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.monitoring_alerts (id, name, message, severity, status, source_system, rule_name, metric_name, current_value, threshold_value, incident_id, auto_task_created, created_task_id, started_at, acknowledged_at, resolved_at, labels, annotations, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: notification_history; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.notification_history (id, notification_id, channel, status, delivery_details, error_message, sent_at, delivered_at, failed_at, created_at) FROM stdin;
\.


--
-- Data for Name: notification_templates; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.notification_templates (id, name, type, title_template, message_template, email_template, slack_template, default_channels, default_priority, trigger_conditions, active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: operational_metrics; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.operational_metrics (id, name, display_name, description, metric_type, unit, category, source_system, query, chart_type, color, order_index, warning_threshold, critical_threshold, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: permissions; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.permissions (id, name, display_name, description, resource, action, is_system, created_at) FROM stdin;
\.


--
-- Data for Name: problem_categories; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.problem_categories (id, name, display_name, description, severity, is_active, icon, display_order, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: project_allocations; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.project_allocations (id, resource_id, project_id, allocation, role, start_date, end_date, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: project_members; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.project_members (id, project_id, user_id, role, allocation, is_active, joined_at, left_at) FROM stdin;
\.


--
-- Data for Name: projects; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.projects (id, name, description, key, type, status, visibility, health, lead_id, start_date, end_date, budget, spent_budget, currency, progress, total_tasks, completed_tasks, settings, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: quality_evaluations; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.quality_evaluations (id, training_data_id, evaluation_type, score, criteria, evaluator_id, created_at) FROM stdin;
\.


--
-- Data for Name: report_executions; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.report_executions (id, template_id, status, result_data, error_message, execution_time, file_path, created_at, completed_at) FROM stdin;
\.


--
-- Data for Name: report_templates; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.report_templates (id, name, description, template_type, config, schedule, user_id, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: resource_allocations; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.resource_allocations (id, user_id, total_capacity, role, department, hourly_rate, currency, skills, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: response_feedback; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.response_feedback (id, message_id, user_id, rating, reason, comment, feedback_metadata, created_at) FROM stdin;
\.


--
-- Data for Name: restore_records; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.restore_records (id, backup_record_id, name, status, components_to_restore, restore_options, created_at, started_at, completed_at, created_by, description, success, error_message, warnings, restored_components, duration_seconds, files_restored) FROM stdin;
\.


--
-- Data for Name: role_permissions; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.role_permissions (role_id, permission_id, granted_at) FROM stdin;
\.


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.roles (id, name, display_name, description, is_system, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: security_events; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.security_events (id, user_id, event_type, ip_address, user_agent, description, details, threat_level, status, resolved_at, resolved_by, created_at) FROM stdin;
\.


--
-- Data for Name: sprints; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.sprints (id, name, goal, project_id, status, start_date, end_date, capacity, commitment, completed, velocity, burndown_data, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: task_attachments; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.task_attachments (id, task_id, file_name, file_size, file_type, file_path, uploaded_by, uploaded_at) FROM stdin;
\.


--
-- Data for Name: task_comments; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.task_comments (id, task_id, author_id, content, is_edited, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: task_dependencies; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.task_dependencies (id, task_id, depends_on_task_id, type, created_at) FROM stdin;
\.


--
-- Data for Name: tasks; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.tasks (id, title, description, type, status, priority, assignee_id, reporter_id, project_id, milestone_id, sprint_id, parent_task_id, estimated_hours, actual_hours, story_points, due_date, start_date, completed_date, labels, custom_fields, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: time_entries; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.time_entries (id, user_id, task_id, project_id, description, hours, date, billable, hourly_rate, currency, status, approved_by, approved_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: token_balances; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.token_balances (id, user_id, balance, total_earned, total_spent, created_at, updated_at) FROM stdin;
1	1	1000	0	0	2025-11-13 22:14:24.179559	2025-11-13 22:14:24.179572
2	2	1000	0	0	2025-11-14 17:57:06.370647	2025-11-14 17:57:06.370651
3	3	1000	0	0	2025-11-17 12:11:59.447599	2025-11-17 12:11:59.447611
\.


--
-- Data for Name: token_transactions; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.token_transactions (id, user_id, amount, transaction_type, description, chat_session_id, chat_message_id, created_at) FROM stdin;
\.


--
-- Data for Name: training_data; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.training_data (id, instruction, input, output, source, quality_score, complexity, is_approved, is_used_for_training, approved_by, approved_at, meta_data, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: training_datasets; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.training_datasets (id, version, question, bad_answer, good_answer, review_id, dataset_metadata, used_in_training, created_at) FROM stdin;
\.


--
-- Data for Name: training_jobs; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.training_jobs (id, job_name, status, training_data_count, hyperparameters, progress, current_epoch, total_epochs, loss, accuracy, error_message, started_at, completed_at, created_by, created_at) FROM stdin;
\.


--
-- Data for Name: user_role_history; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.user_role_history (id, user_id, role_id, action, assigned_by, reason, created_at) FROM stdin;
\.


--
-- Data for Name: user_roles; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.user_roles (user_id, role_id, assigned_at, assigned_by) FROM stdin;
\.


--
-- Data for Name: user_segments; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.user_segments (id, name, description, criteria, user_count, is_dynamic, user_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: advakod
--

COPY public.users (id, email, username, hashed_password, full_name, is_active, is_premium, is_admin, subscription_type, subscription_expires, created_at, updated_at, company_name, legal_form, inn, ogrn, two_factor_enabled, two_factor_secret, backup_codes) FROM stdin;
1	aziz@bagbekov.ru	aziz	$pbkdf2-sha256$29000$mrPWWsuZcy6lVIrRuvfemw$JYeZC9Q4XKZ0Evgi7TxCXnd0TSBkgGq77xtoNU/fOJE	Aziz Bagbekov	t	f	f	free	\N	2025-11-09 22:05:00.287075+00	\N	\N	\N	\N	\N	f	\N	\N
2	alferov.viktor.1812@gmail.com	avv26	$pbkdf2-sha256$29000$v3cu5VyrlZJSqhWCMGaM8Q$lEp5SwEHUyYktBupKVCd5.VPXGM7XrasLfJqX9kRCNI	Виктор Алферов Алферов	t	f	f	free	\N	2025-11-14 17:55:42.230307+00	\N	ЮСИ	ИП	\N	\N	f	\N	\N
3	visotskyctac@mail.ru	Адвакотик	$2b$12$EkydwczszjrqaHANPbdQGOdlYtj95XNivDk5KFPjErt4QLlVlbPAm	Стас Стасов	t	f	f	free	\N	2025-11-17 12:11:28.772208+00	\N	ООО «Бнал»	ООО	6661313	1313666666	f	\N	\N
\.


--
-- Name: ab_test_events_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.ab_test_events_id_seq', 1, false);


--
-- Name: ab_test_participants_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.ab_test_participants_id_seq', 1, false);


--
-- Name: ab_test_statistics_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.ab_test_statistics_id_seq', 1, false);


--
-- Name: ab_test_variants_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.ab_test_variants_id_seq', 1, false);


--
-- Name: ab_tests_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.ab_tests_id_seq', 1, false);


--
-- Name: admin_notifications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.admin_notifications_id_seq', 195, true);


--
-- Name: audit_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.audit_logs_id_seq', 1, false);


--
-- Name: availability_periods_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.availability_periods_id_seq', 1, false);


--
-- Name: backup_integrity_checks_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.backup_integrity_checks_id_seq', 1, false);


--
-- Name: backup_records_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.backup_records_id_seq', 1, false);


--
-- Name: backup_schedules_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.backup_schedules_id_seq', 1, false);


--
-- Name: chat_messages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.chat_messages_id_seq', 86, true);


--
-- Name: chat_sessions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.chat_sessions_id_seq', 91, true);


--
-- Name: cohort_analysis_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.cohort_analysis_id_seq', 1, false);


--
-- Name: custom_metrics_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.custom_metrics_id_seq', 1, false);


--
-- Name: dashboard_widgets_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.dashboard_widgets_id_seq', 1, false);


--
-- Name: dashboards_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.dashboards_id_seq', 1, false);


--
-- Name: data_collection_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.data_collection_logs_id_seq', 1, false);


--
-- Name: document_analyses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.document_analyses_id_seq', 1, false);


--
-- Name: encrypted_messages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.encrypted_messages_id_seq', 1, false);


--
-- Name: encryption_keys_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.encryption_keys_id_seq', 1, false);


--
-- Name: incident_updates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.incident_updates_id_seq', 1, false);


--
-- Name: incidents_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.incidents_id_seq', 1, false);


--
-- Name: metric_alerts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.metric_alerts_id_seq', 1, false);


--
-- Name: metric_values_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.metric_values_id_seq', 1, false);


--
-- Name: milestones_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.milestones_id_seq', 1, false);


--
-- Name: ml_predictions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.ml_predictions_id_seq', 1, false);


--
-- Name: model_versions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.model_versions_id_seq', 1, false);


--
-- Name: moderation_queue_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.moderation_queue_id_seq', 1, false);


--
-- Name: moderation_reviews_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.moderation_reviews_id_seq', 1, false);


--
-- Name: moderator_stats_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.moderator_stats_id_seq', 1, false);


--
-- Name: monitoring_alerts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.monitoring_alerts_id_seq', 1, false);


--
-- Name: notification_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.notification_history_id_seq', 1, false);


--
-- Name: notification_templates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.notification_templates_id_seq', 1, false);


--
-- Name: operational_metrics_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.operational_metrics_id_seq', 1, false);


--
-- Name: permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.permissions_id_seq', 1, false);


--
-- Name: problem_categories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.problem_categories_id_seq', 1, false);


--
-- Name: project_allocations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.project_allocations_id_seq', 1, false);


--
-- Name: project_members_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.project_members_id_seq', 1, false);


--
-- Name: projects_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.projects_id_seq', 1, false);


--
-- Name: quality_evaluations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.quality_evaluations_id_seq', 1, false);


--
-- Name: report_executions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.report_executions_id_seq', 1, false);


--
-- Name: report_templates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.report_templates_id_seq', 1, false);


--
-- Name: resource_allocations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.resource_allocations_id_seq', 1, false);


--
-- Name: response_feedback_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.response_feedback_id_seq', 1, false);


--
-- Name: restore_records_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.restore_records_id_seq', 1, false);


--
-- Name: roles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.roles_id_seq', 1, false);


--
-- Name: security_events_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.security_events_id_seq', 1, false);


--
-- Name: sprints_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.sprints_id_seq', 1, false);


--
-- Name: task_attachments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.task_attachments_id_seq', 1, false);


--
-- Name: task_comments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.task_comments_id_seq', 1, false);


--
-- Name: task_dependencies_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.task_dependencies_id_seq', 1, false);


--
-- Name: tasks_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.tasks_id_seq', 1, false);


--
-- Name: time_entries_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.time_entries_id_seq', 1, false);


--
-- Name: token_balances_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.token_balances_id_seq', 3, true);


--
-- Name: token_transactions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.token_transactions_id_seq', 1, false);


--
-- Name: training_data_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.training_data_id_seq', 1, false);


--
-- Name: training_datasets_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.training_datasets_id_seq', 1, false);


--
-- Name: training_jobs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.training_jobs_id_seq', 1, false);


--
-- Name: user_role_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.user_role_history_id_seq', 1, false);


--
-- Name: user_segments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.user_segments_id_seq', 1, false);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: advakod
--

SELECT pg_catalog.setval('public.users_id_seq', 3, true);


--
-- Name: ab_test_events ab_test_events_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.ab_test_events
    ADD CONSTRAINT ab_test_events_pkey PRIMARY KEY (id);


--
-- Name: ab_test_participants ab_test_participants_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.ab_test_participants
    ADD CONSTRAINT ab_test_participants_pkey PRIMARY KEY (id);


--
-- Name: ab_test_statistics ab_test_statistics_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.ab_test_statistics
    ADD CONSTRAINT ab_test_statistics_pkey PRIMARY KEY (id);


--
-- Name: ab_test_variants ab_test_variants_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.ab_test_variants
    ADD CONSTRAINT ab_test_variants_pkey PRIMARY KEY (id);


--
-- Name: ab_tests ab_tests_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.ab_tests
    ADD CONSTRAINT ab_tests_pkey PRIMARY KEY (id);


--
-- Name: admin_notifications admin_notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.admin_notifications
    ADD CONSTRAINT admin_notifications_pkey PRIMARY KEY (id);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: availability_periods availability_periods_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.availability_periods
    ADD CONSTRAINT availability_periods_pkey PRIMARY KEY (id);


--
-- Name: backup_integrity_checks backup_integrity_checks_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.backup_integrity_checks
    ADD CONSTRAINT backup_integrity_checks_pkey PRIMARY KEY (id);


--
-- Name: backup_records backup_records_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.backup_records
    ADD CONSTRAINT backup_records_pkey PRIMARY KEY (id);


--
-- Name: backup_schedules backup_schedules_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.backup_schedules
    ADD CONSTRAINT backup_schedules_pkey PRIMARY KEY (id);


--
-- Name: chat_messages chat_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_pkey PRIMARY KEY (id);


--
-- Name: chat_sessions chat_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_pkey PRIMARY KEY (id);


--
-- Name: cohort_analysis cohort_analysis_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.cohort_analysis
    ADD CONSTRAINT cohort_analysis_pkey PRIMARY KEY (id);


--
-- Name: custom_metrics custom_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.custom_metrics
    ADD CONSTRAINT custom_metrics_pkey PRIMARY KEY (id);


--
-- Name: dashboard_widgets dashboard_widgets_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.dashboard_widgets
    ADD CONSTRAINT dashboard_widgets_pkey PRIMARY KEY (id);


--
-- Name: dashboards dashboards_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.dashboards
    ADD CONSTRAINT dashboards_pkey PRIMARY KEY (id);


--
-- Name: data_collection_logs data_collection_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.data_collection_logs
    ADD CONSTRAINT data_collection_logs_pkey PRIMARY KEY (id);


--
-- Name: document_analyses document_analyses_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.document_analyses
    ADD CONSTRAINT document_analyses_pkey PRIMARY KEY (id);


--
-- Name: encrypted_messages encrypted_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.encrypted_messages
    ADD CONSTRAINT encrypted_messages_pkey PRIMARY KEY (id);


--
-- Name: encryption_keys encryption_keys_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.encryption_keys
    ADD CONSTRAINT encryption_keys_pkey PRIMARY KEY (id);


--
-- Name: incident_updates incident_updates_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.incident_updates
    ADD CONSTRAINT incident_updates_pkey PRIMARY KEY (id);


--
-- Name: incidents incidents_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.incidents
    ADD CONSTRAINT incidents_pkey PRIMARY KEY (id);


--
-- Name: metric_alerts metric_alerts_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.metric_alerts
    ADD CONSTRAINT metric_alerts_pkey PRIMARY KEY (id);


--
-- Name: metric_values metric_values_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.metric_values
    ADD CONSTRAINT metric_values_pkey PRIMARY KEY (id);


--
-- Name: milestones milestones_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.milestones
    ADD CONSTRAINT milestones_pkey PRIMARY KEY (id);


--
-- Name: ml_predictions ml_predictions_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.ml_predictions
    ADD CONSTRAINT ml_predictions_pkey PRIMARY KEY (id);


--
-- Name: model_versions model_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.model_versions
    ADD CONSTRAINT model_versions_pkey PRIMARY KEY (id);


--
-- Name: model_versions model_versions_version_key; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.model_versions
    ADD CONSTRAINT model_versions_version_key UNIQUE (version);


--
-- Name: moderation_queue moderation_queue_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.moderation_queue
    ADD CONSTRAINT moderation_queue_pkey PRIMARY KEY (id);


--
-- Name: moderation_reviews moderation_reviews_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.moderation_reviews
    ADD CONSTRAINT moderation_reviews_pkey PRIMARY KEY (id);


--
-- Name: moderator_stats moderator_stats_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.moderator_stats
    ADD CONSTRAINT moderator_stats_pkey PRIMARY KEY (id);


--
-- Name: monitoring_alerts monitoring_alerts_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.monitoring_alerts
    ADD CONSTRAINT monitoring_alerts_pkey PRIMARY KEY (id);


--
-- Name: notification_history notification_history_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.notification_history
    ADD CONSTRAINT notification_history_pkey PRIMARY KEY (id);


--
-- Name: notification_templates notification_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.notification_templates
    ADD CONSTRAINT notification_templates_pkey PRIMARY KEY (id);


--
-- Name: operational_metrics operational_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.operational_metrics
    ADD CONSTRAINT operational_metrics_pkey PRIMARY KEY (id);


--
-- Name: permissions permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_pkey PRIMARY KEY (id);


--
-- Name: problem_categories problem_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.problem_categories
    ADD CONSTRAINT problem_categories_pkey PRIMARY KEY (id);


--
-- Name: project_allocations project_allocations_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.project_allocations
    ADD CONSTRAINT project_allocations_pkey PRIMARY KEY (id);


--
-- Name: project_members project_members_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_pkey PRIMARY KEY (id);


--
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);


--
-- Name: quality_evaluations quality_evaluations_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.quality_evaluations
    ADD CONSTRAINT quality_evaluations_pkey PRIMARY KEY (id);


--
-- Name: report_executions report_executions_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.report_executions
    ADD CONSTRAINT report_executions_pkey PRIMARY KEY (id);


--
-- Name: report_templates report_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.report_templates
    ADD CONSTRAINT report_templates_pkey PRIMARY KEY (id);


--
-- Name: resource_allocations resource_allocations_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.resource_allocations
    ADD CONSTRAINT resource_allocations_pkey PRIMARY KEY (id);


--
-- Name: response_feedback response_feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.response_feedback
    ADD CONSTRAINT response_feedback_pkey PRIMARY KEY (id);


--
-- Name: restore_records restore_records_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.restore_records
    ADD CONSTRAINT restore_records_pkey PRIMARY KEY (id);


--
-- Name: role_permissions role_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_pkey PRIMARY KEY (role_id, permission_id);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: security_events security_events_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.security_events
    ADD CONSTRAINT security_events_pkey PRIMARY KEY (id);


--
-- Name: sprints sprints_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.sprints
    ADD CONSTRAINT sprints_pkey PRIMARY KEY (id);


--
-- Name: task_attachments task_attachments_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.task_attachments
    ADD CONSTRAINT task_attachments_pkey PRIMARY KEY (id);


--
-- Name: task_comments task_comments_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.task_comments
    ADD CONSTRAINT task_comments_pkey PRIMARY KEY (id);


--
-- Name: task_dependencies task_dependencies_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.task_dependencies
    ADD CONSTRAINT task_dependencies_pkey PRIMARY KEY (id);


--
-- Name: tasks tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_pkey PRIMARY KEY (id);


--
-- Name: time_entries time_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.time_entries
    ADD CONSTRAINT time_entries_pkey PRIMARY KEY (id);


--
-- Name: token_balances token_balances_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.token_balances
    ADD CONSTRAINT token_balances_pkey PRIMARY KEY (id);


--
-- Name: token_transactions token_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.token_transactions
    ADD CONSTRAINT token_transactions_pkey PRIMARY KEY (id);


--
-- Name: training_data training_data_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.training_data
    ADD CONSTRAINT training_data_pkey PRIMARY KEY (id);


--
-- Name: training_datasets training_datasets_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.training_datasets
    ADD CONSTRAINT training_datasets_pkey PRIMARY KEY (id);


--
-- Name: training_jobs training_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.training_jobs
    ADD CONSTRAINT training_jobs_pkey PRIMARY KEY (id);


--
-- Name: user_role_history user_role_history_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.user_role_history
    ADD CONSTRAINT user_role_history_pkey PRIMARY KEY (id);


--
-- Name: user_roles user_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_pkey PRIMARY KEY (user_id, role_id);


--
-- Name: user_segments user_segments_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.user_segments
    ADD CONSTRAINT user_segments_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: idx_users_email; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX idx_users_email ON public.users USING btree (email);


--
-- Name: idx_users_is_active; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX idx_users_is_active ON public.users USING btree (is_active);


--
-- Name: idx_users_is_admin; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX idx_users_is_admin ON public.users USING btree (is_admin);


--
-- Name: idx_users_is_premium; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX idx_users_is_premium ON public.users USING btree (is_premium);


--
-- Name: idx_users_username; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX idx_users_username ON public.users USING btree (username);


--
-- Name: ix_ab_test_events_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_ab_test_events_id ON public.ab_test_events USING btree (id);


--
-- Name: ix_ab_test_participants_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_ab_test_participants_id ON public.ab_test_participants USING btree (id);


--
-- Name: ix_ab_test_statistics_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_ab_test_statistics_id ON public.ab_test_statistics USING btree (id);


--
-- Name: ix_ab_test_variants_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_ab_test_variants_id ON public.ab_test_variants USING btree (id);


--
-- Name: ix_ab_tests_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_ab_tests_id ON public.ab_tests USING btree (id);


--
-- Name: ix_ab_tests_name; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_ab_tests_name ON public.ab_tests USING btree (name);


--
-- Name: ix_admin_notifications_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_admin_notifications_id ON public.admin_notifications USING btree (id);


--
-- Name: ix_admin_notifications_priority; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_admin_notifications_priority ON public.admin_notifications USING btree (priority);


--
-- Name: ix_admin_notifications_read; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_admin_notifications_read ON public.admin_notifications USING btree (read);


--
-- Name: ix_admin_notifications_type; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_admin_notifications_type ON public.admin_notifications USING btree (type);


--
-- Name: ix_admin_notifications_user_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_admin_notifications_user_id ON public.admin_notifications USING btree (user_id);


--
-- Name: ix_audit_logs_action; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_audit_logs_action ON public.audit_logs USING btree (action);


--
-- Name: ix_audit_logs_created_at; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_audit_logs_created_at ON public.audit_logs USING btree (created_at);


--
-- Name: ix_audit_logs_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_audit_logs_id ON public.audit_logs USING btree (id);


--
-- Name: ix_audit_logs_request_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_audit_logs_request_id ON public.audit_logs USING btree (request_id);


--
-- Name: ix_audit_logs_session_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_audit_logs_session_id ON public.audit_logs USING btree (session_id);


--
-- Name: ix_audit_logs_severity; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_audit_logs_severity ON public.audit_logs USING btree (severity);


--
-- Name: ix_audit_logs_user_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_audit_logs_user_id ON public.audit_logs USING btree (user_id);


--
-- Name: ix_availability_periods_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_availability_periods_id ON public.availability_periods USING btree (id);


--
-- Name: ix_backup_integrity_checks_backup_record_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_backup_integrity_checks_backup_record_id ON public.backup_integrity_checks USING btree (backup_record_id);


--
-- Name: ix_backup_integrity_checks_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_backup_integrity_checks_id ON public.backup_integrity_checks USING btree (id);


--
-- Name: ix_backup_records_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_backup_records_id ON public.backup_records USING btree (id);


--
-- Name: ix_backup_records_name; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_backup_records_name ON public.backup_records USING btree (name);


--
-- Name: ix_backup_schedules_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_backup_schedules_id ON public.backup_schedules USING btree (id);


--
-- Name: ix_chat_messages_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_chat_messages_id ON public.chat_messages USING btree (id);


--
-- Name: ix_chat_sessions_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_chat_sessions_id ON public.chat_sessions USING btree (id);


--
-- Name: ix_cohort_analysis_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_cohort_analysis_id ON public.cohort_analysis USING btree (id);


--
-- Name: ix_custom_metrics_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_custom_metrics_id ON public.custom_metrics USING btree (id);


--
-- Name: ix_dashboard_widgets_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_dashboard_widgets_id ON public.dashboard_widgets USING btree (id);


--
-- Name: ix_dashboards_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_dashboards_id ON public.dashboards USING btree (id);


--
-- Name: ix_data_collection_logs_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_data_collection_logs_id ON public.data_collection_logs USING btree (id);


--
-- Name: ix_document_analyses_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_document_analyses_id ON public.document_analyses USING btree (id);


--
-- Name: ix_encrypted_messages_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_encrypted_messages_id ON public.encrypted_messages USING btree (id);


--
-- Name: ix_encryption_keys_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_encryption_keys_id ON public.encryption_keys USING btree (id);


--
-- Name: ix_incident_updates_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_incident_updates_id ON public.incident_updates USING btree (id);


--
-- Name: ix_incidents_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_incidents_id ON public.incidents USING btree (id);


--
-- Name: ix_incidents_title; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_incidents_title ON public.incidents USING btree (title);


--
-- Name: ix_metric_alerts_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_metric_alerts_id ON public.metric_alerts USING btree (id);


--
-- Name: ix_metric_values_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_metric_values_id ON public.metric_values USING btree (id);


--
-- Name: ix_milestones_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_milestones_id ON public.milestones USING btree (id);


--
-- Name: ix_milestones_name; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_milestones_name ON public.milestones USING btree (name);


--
-- Name: ix_ml_predictions_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_ml_predictions_id ON public.ml_predictions USING btree (id);


--
-- Name: ix_model_versions_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_model_versions_id ON public.model_versions USING btree (id);


--
-- Name: ix_moderation_queue_assigned_to; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_moderation_queue_assigned_to ON public.moderation_queue USING btree (assigned_to);


--
-- Name: ix_moderation_queue_created_at; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_moderation_queue_created_at ON public.moderation_queue USING btree (created_at);


--
-- Name: ix_moderation_queue_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_moderation_queue_id ON public.moderation_queue USING btree (id);


--
-- Name: ix_moderation_queue_message_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE UNIQUE INDEX ix_moderation_queue_message_id ON public.moderation_queue USING btree (message_id);


--
-- Name: ix_moderation_queue_priority; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_moderation_queue_priority ON public.moderation_queue USING btree (priority);


--
-- Name: ix_moderation_queue_status; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_moderation_queue_status ON public.moderation_queue USING btree (status);


--
-- Name: ix_moderation_reviews_created_at; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_moderation_reviews_created_at ON public.moderation_reviews USING btree (created_at);


--
-- Name: ix_moderation_reviews_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_moderation_reviews_id ON public.moderation_reviews USING btree (id);


--
-- Name: ix_moderation_reviews_message_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_moderation_reviews_message_id ON public.moderation_reviews USING btree (message_id);


--
-- Name: ix_moderation_reviews_moderator_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_moderation_reviews_moderator_id ON public.moderation_reviews USING btree (moderator_id);


--
-- Name: ix_moderation_reviews_priority; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_moderation_reviews_priority ON public.moderation_reviews USING btree (priority);


--
-- Name: ix_moderation_reviews_status; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_moderation_reviews_status ON public.moderation_reviews USING btree (status);


--
-- Name: ix_moderator_stats_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_moderator_stats_id ON public.moderator_stats USING btree (id);


--
-- Name: ix_moderator_stats_moderator_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE UNIQUE INDEX ix_moderator_stats_moderator_id ON public.moderator_stats USING btree (moderator_id);


--
-- Name: ix_moderator_stats_points; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_moderator_stats_points ON public.moderator_stats USING btree (points);


--
-- Name: ix_moderator_stats_rank; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_moderator_stats_rank ON public.moderator_stats USING btree (rank);


--
-- Name: ix_monitoring_alerts_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_monitoring_alerts_id ON public.monitoring_alerts USING btree (id);


--
-- Name: ix_monitoring_alerts_name; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_monitoring_alerts_name ON public.monitoring_alerts USING btree (name);


--
-- Name: ix_notification_history_channel; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_notification_history_channel ON public.notification_history USING btree (channel);


--
-- Name: ix_notification_history_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_notification_history_id ON public.notification_history USING btree (id);


--
-- Name: ix_notification_history_notification_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_notification_history_notification_id ON public.notification_history USING btree (notification_id);


--
-- Name: ix_notification_history_status; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_notification_history_status ON public.notification_history USING btree (status);


--
-- Name: ix_notification_templates_active; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_notification_templates_active ON public.notification_templates USING btree (active);


--
-- Name: ix_notification_templates_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_notification_templates_id ON public.notification_templates USING btree (id);


--
-- Name: ix_notification_templates_name; Type: INDEX; Schema: public; Owner: advakod
--

CREATE UNIQUE INDEX ix_notification_templates_name ON public.notification_templates USING btree (name);


--
-- Name: ix_notification_templates_type; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_notification_templates_type ON public.notification_templates USING btree (type);


--
-- Name: ix_operational_metrics_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_operational_metrics_id ON public.operational_metrics USING btree (id);


--
-- Name: ix_operational_metrics_name; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_operational_metrics_name ON public.operational_metrics USING btree (name);


--
-- Name: ix_permissions_action; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_permissions_action ON public.permissions USING btree (action);


--
-- Name: ix_permissions_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_permissions_id ON public.permissions USING btree (id);


--
-- Name: ix_permissions_name; Type: INDEX; Schema: public; Owner: advakod
--

CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);


--
-- Name: ix_permissions_resource; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_permissions_resource ON public.permissions USING btree (resource);


--
-- Name: ix_problem_categories_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_problem_categories_id ON public.problem_categories USING btree (id);


--
-- Name: ix_problem_categories_is_active; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_problem_categories_is_active ON public.problem_categories USING btree (is_active);


--
-- Name: ix_problem_categories_name; Type: INDEX; Schema: public; Owner: advakod
--

CREATE UNIQUE INDEX ix_problem_categories_name ON public.problem_categories USING btree (name);


--
-- Name: ix_project_allocations_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_project_allocations_id ON public.project_allocations USING btree (id);


--
-- Name: ix_project_members_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_project_members_id ON public.project_members USING btree (id);


--
-- Name: ix_projects_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_projects_id ON public.projects USING btree (id);


--
-- Name: ix_projects_key; Type: INDEX; Schema: public; Owner: advakod
--

CREATE UNIQUE INDEX ix_projects_key ON public.projects USING btree (key);


--
-- Name: ix_projects_name; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_projects_name ON public.projects USING btree (name);


--
-- Name: ix_quality_evaluations_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_quality_evaluations_id ON public.quality_evaluations USING btree (id);


--
-- Name: ix_report_executions_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_report_executions_id ON public.report_executions USING btree (id);


--
-- Name: ix_report_templates_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_report_templates_id ON public.report_templates USING btree (id);


--
-- Name: ix_resource_allocations_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_resource_allocations_id ON public.resource_allocations USING btree (id);


--
-- Name: ix_response_feedback_created_at; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_response_feedback_created_at ON public.response_feedback USING btree (created_at);


--
-- Name: ix_response_feedback_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_response_feedback_id ON public.response_feedback USING btree (id);


--
-- Name: ix_response_feedback_message_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_response_feedback_message_id ON public.response_feedback USING btree (message_id);


--
-- Name: ix_response_feedback_rating; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_response_feedback_rating ON public.response_feedback USING btree (rating);


--
-- Name: ix_response_feedback_user_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_response_feedback_user_id ON public.response_feedback USING btree (user_id);


--
-- Name: ix_restore_records_backup_record_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_restore_records_backup_record_id ON public.restore_records USING btree (backup_record_id);


--
-- Name: ix_restore_records_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_restore_records_id ON public.restore_records USING btree (id);


--
-- Name: ix_roles_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_roles_id ON public.roles USING btree (id);


--
-- Name: ix_roles_is_active; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_roles_is_active ON public.roles USING btree (is_active);


--
-- Name: ix_roles_name; Type: INDEX; Schema: public; Owner: advakod
--

CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);


--
-- Name: ix_security_events_created_at; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_security_events_created_at ON public.security_events USING btree (created_at);


--
-- Name: ix_security_events_event_type; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_security_events_event_type ON public.security_events USING btree (event_type);


--
-- Name: ix_security_events_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_security_events_id ON public.security_events USING btree (id);


--
-- Name: ix_security_events_threat_level; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_security_events_threat_level ON public.security_events USING btree (threat_level);


--
-- Name: ix_security_events_user_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_security_events_user_id ON public.security_events USING btree (user_id);


--
-- Name: ix_sprints_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_sprints_id ON public.sprints USING btree (id);


--
-- Name: ix_sprints_name; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_sprints_name ON public.sprints USING btree (name);


--
-- Name: ix_task_attachments_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_task_attachments_id ON public.task_attachments USING btree (id);


--
-- Name: ix_task_comments_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_task_comments_id ON public.task_comments USING btree (id);


--
-- Name: ix_task_dependencies_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_task_dependencies_id ON public.task_dependencies USING btree (id);


--
-- Name: ix_tasks_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_tasks_id ON public.tasks USING btree (id);


--
-- Name: ix_tasks_title; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_tasks_title ON public.tasks USING btree (title);


--
-- Name: ix_time_entries_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_time_entries_id ON public.time_entries USING btree (id);


--
-- Name: ix_token_balances_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_token_balances_id ON public.token_balances USING btree (id);


--
-- Name: ix_token_transactions_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_token_transactions_id ON public.token_transactions USING btree (id);


--
-- Name: ix_training_data_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_training_data_id ON public.training_data USING btree (id);


--
-- Name: ix_training_datasets_created_at; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_training_datasets_created_at ON public.training_datasets USING btree (created_at);


--
-- Name: ix_training_datasets_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_training_datasets_id ON public.training_datasets USING btree (id);


--
-- Name: ix_training_datasets_used_in_training; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_training_datasets_used_in_training ON public.training_datasets USING btree (used_in_training);


--
-- Name: ix_training_datasets_version; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_training_datasets_version ON public.training_datasets USING btree (version);


--
-- Name: ix_training_jobs_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_training_jobs_id ON public.training_jobs USING btree (id);


--
-- Name: ix_user_role_history_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_user_role_history_id ON public.user_role_history USING btree (id);


--
-- Name: ix_user_role_history_user_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_user_role_history_user_id ON public.user_role_history USING btree (user_id);


--
-- Name: ix_user_segments_id; Type: INDEX; Schema: public; Owner: advakod
--

CREATE INDEX ix_user_segments_id ON public.user_segments USING btree (id);


--
-- Name: ab_test_events ab_test_events_participant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.ab_test_events
    ADD CONSTRAINT ab_test_events_participant_id_fkey FOREIGN KEY (participant_id) REFERENCES public.ab_test_participants(id);


--
-- Name: ab_test_events ab_test_events_test_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.ab_test_events
    ADD CONSTRAINT ab_test_events_test_id_fkey FOREIGN KEY (test_id) REFERENCES public.ab_tests(id);


--
-- Name: ab_test_events ab_test_events_variant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.ab_test_events
    ADD CONSTRAINT ab_test_events_variant_id_fkey FOREIGN KEY (variant_id) REFERENCES public.ab_test_variants(id);


--
-- Name: ab_test_participants ab_test_participants_test_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.ab_test_participants
    ADD CONSTRAINT ab_test_participants_test_id_fkey FOREIGN KEY (test_id) REFERENCES public.ab_tests(id);


--
-- Name: ab_test_participants ab_test_participants_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.ab_test_participants
    ADD CONSTRAINT ab_test_participants_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: ab_test_participants ab_test_participants_variant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.ab_test_participants
    ADD CONSTRAINT ab_test_participants_variant_id_fkey FOREIGN KEY (variant_id) REFERENCES public.ab_test_variants(id);


--
-- Name: ab_test_statistics ab_test_statistics_test_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.ab_test_statistics
    ADD CONSTRAINT ab_test_statistics_test_id_fkey FOREIGN KEY (test_id) REFERENCES public.ab_tests(id);


--
-- Name: ab_test_statistics ab_test_statistics_winner_variant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.ab_test_statistics
    ADD CONSTRAINT ab_test_statistics_winner_variant_id_fkey FOREIGN KEY (winner_variant_id) REFERENCES public.ab_test_variants(id);


--
-- Name: ab_test_variants ab_test_variants_test_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.ab_test_variants
    ADD CONSTRAINT ab_test_variants_test_id_fkey FOREIGN KEY (test_id) REFERENCES public.ab_tests(id);


--
-- Name: ab_tests ab_tests_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.ab_tests
    ADD CONSTRAINT ab_tests_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: ab_tests ab_tests_winner_variant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.ab_tests
    ADD CONSTRAINT ab_tests_winner_variant_id_fkey FOREIGN KEY (winner_variant_id) REFERENCES public.ab_test_variants(id);


--
-- Name: admin_notifications admin_notifications_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.admin_notifications
    ADD CONSTRAINT admin_notifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: audit_logs audit_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: availability_periods availability_periods_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.availability_periods
    ADD CONSTRAINT availability_periods_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(id);


--
-- Name: availability_periods availability_periods_resource_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.availability_periods
    ADD CONSTRAINT availability_periods_resource_id_fkey FOREIGN KEY (resource_id) REFERENCES public.resource_allocations(id);


--
-- Name: chat_messages chat_messages_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.chat_sessions(id);


--
-- Name: chat_sessions chat_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: cohort_analysis cohort_analysis_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.cohort_analysis
    ADD CONSTRAINT cohort_analysis_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: custom_metrics custom_metrics_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.custom_metrics
    ADD CONSTRAINT custom_metrics_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: dashboard_widgets dashboard_widgets_dashboard_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.dashboard_widgets
    ADD CONSTRAINT dashboard_widgets_dashboard_id_fkey FOREIGN KEY (dashboard_id) REFERENCES public.dashboards(id);


--
-- Name: dashboards dashboards_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.dashboards
    ADD CONSTRAINT dashboards_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: data_collection_logs data_collection_logs_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.data_collection_logs
    ADD CONSTRAINT data_collection_logs_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: document_analyses document_analyses_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.document_analyses
    ADD CONSTRAINT document_analyses_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: encrypted_messages encrypted_messages_chat_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.encrypted_messages
    ADD CONSTRAINT encrypted_messages_chat_session_id_fkey FOREIGN KEY (chat_session_id) REFERENCES public.chat_sessions(id);


--
-- Name: encrypted_messages encrypted_messages_recipient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.encrypted_messages
    ADD CONSTRAINT encrypted_messages_recipient_id_fkey FOREIGN KEY (recipient_id) REFERENCES public.users(id);


--
-- Name: encrypted_messages encrypted_messages_sender_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.encrypted_messages
    ADD CONSTRAINT encrypted_messages_sender_id_fkey FOREIGN KEY (sender_id) REFERENCES public.users(id);


--
-- Name: encryption_keys encryption_keys_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.encryption_keys
    ADD CONSTRAINT encryption_keys_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: incident_updates incident_updates_author_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.incident_updates
    ADD CONSTRAINT incident_updates_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.users(id);


--
-- Name: incident_updates incident_updates_incident_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.incident_updates
    ADD CONSTRAINT incident_updates_incident_id_fkey FOREIGN KEY (incident_id) REFERENCES public.incidents(id);


--
-- Name: incidents incidents_assigned_to_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.incidents
    ADD CONSTRAINT incidents_assigned_to_fkey FOREIGN KEY (assigned_to) REFERENCES public.users(id);


--
-- Name: incidents incidents_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.incidents
    ADD CONSTRAINT incidents_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: incidents incidents_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.incidents
    ADD CONSTRAINT incidents_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- Name: incidents incidents_related_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.incidents
    ADD CONSTRAINT incidents_related_task_id_fkey FOREIGN KEY (related_task_id) REFERENCES public.tasks(id);


--
-- Name: metric_alerts metric_alerts_metric_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.metric_alerts
    ADD CONSTRAINT metric_alerts_metric_id_fkey FOREIGN KEY (metric_id) REFERENCES public.custom_metrics(id);


--
-- Name: metric_alerts metric_alerts_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.metric_alerts
    ADD CONSTRAINT metric_alerts_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: metric_values metric_values_metric_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.metric_values
    ADD CONSTRAINT metric_values_metric_id_fkey FOREIGN KEY (metric_id) REFERENCES public.operational_metrics(id);


--
-- Name: milestones milestones_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.milestones
    ADD CONSTRAINT milestones_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- Name: milestones milestones_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.milestones
    ADD CONSTRAINT milestones_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- Name: ml_predictions ml_predictions_target_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.ml_predictions
    ADD CONSTRAINT ml_predictions_target_user_id_fkey FOREIGN KEY (target_user_id) REFERENCES public.users(id);


--
-- Name: model_versions model_versions_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.model_versions
    ADD CONSTRAINT model_versions_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: moderation_queue moderation_queue_assigned_to_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.moderation_queue
    ADD CONSTRAINT moderation_queue_assigned_to_fkey FOREIGN KEY (assigned_to) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: moderation_queue moderation_queue_message_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.moderation_queue
    ADD CONSTRAINT moderation_queue_message_id_fkey FOREIGN KEY (message_id) REFERENCES public.chat_messages(id) ON DELETE CASCADE;


--
-- Name: moderation_reviews moderation_reviews_message_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.moderation_reviews
    ADD CONSTRAINT moderation_reviews_message_id_fkey FOREIGN KEY (message_id) REFERENCES public.chat_messages(id) ON DELETE CASCADE;


--
-- Name: moderation_reviews moderation_reviews_moderator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.moderation_reviews
    ADD CONSTRAINT moderation_reviews_moderator_id_fkey FOREIGN KEY (moderator_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: moderator_stats moderator_stats_moderator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.moderator_stats
    ADD CONSTRAINT moderator_stats_moderator_id_fkey FOREIGN KEY (moderator_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: monitoring_alerts monitoring_alerts_created_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.monitoring_alerts
    ADD CONSTRAINT monitoring_alerts_created_task_id_fkey FOREIGN KEY (created_task_id) REFERENCES public.tasks(id);


--
-- Name: monitoring_alerts monitoring_alerts_incident_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.monitoring_alerts
    ADD CONSTRAINT monitoring_alerts_incident_id_fkey FOREIGN KEY (incident_id) REFERENCES public.incidents(id);


--
-- Name: notification_history notification_history_notification_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.notification_history
    ADD CONSTRAINT notification_history_notification_id_fkey FOREIGN KEY (notification_id) REFERENCES public.admin_notifications(id);


--
-- Name: project_allocations project_allocations_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.project_allocations
    ADD CONSTRAINT project_allocations_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- Name: project_allocations project_allocations_resource_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.project_allocations
    ADD CONSTRAINT project_allocations_resource_id_fkey FOREIGN KEY (resource_id) REFERENCES public.resource_allocations(id);


--
-- Name: project_members project_members_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- Name: project_members project_members_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: projects projects_lead_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_lead_id_fkey FOREIGN KEY (lead_id) REFERENCES public.users(id);


--
-- Name: quality_evaluations quality_evaluations_evaluator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.quality_evaluations
    ADD CONSTRAINT quality_evaluations_evaluator_id_fkey FOREIGN KEY (evaluator_id) REFERENCES public.users(id);


--
-- Name: quality_evaluations quality_evaluations_training_data_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.quality_evaluations
    ADD CONSTRAINT quality_evaluations_training_data_id_fkey FOREIGN KEY (training_data_id) REFERENCES public.training_data(id);


--
-- Name: report_executions report_executions_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.report_executions
    ADD CONSTRAINT report_executions_template_id_fkey FOREIGN KEY (template_id) REFERENCES public.report_templates(id);


--
-- Name: report_templates report_templates_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.report_templates
    ADD CONSTRAINT report_templates_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: resource_allocations resource_allocations_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.resource_allocations
    ADD CONSTRAINT resource_allocations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: response_feedback response_feedback_message_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.response_feedback
    ADD CONSTRAINT response_feedback_message_id_fkey FOREIGN KEY (message_id) REFERENCES public.chat_messages(id) ON DELETE CASCADE;


--
-- Name: response_feedback response_feedback_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.response_feedback
    ADD CONSTRAINT response_feedback_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: role_permissions role_permissions_permission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES public.permissions(id) ON DELETE CASCADE;


--
-- Name: role_permissions role_permissions_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE CASCADE;


--
-- Name: security_events security_events_resolved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.security_events
    ADD CONSTRAINT security_events_resolved_by_fkey FOREIGN KEY (resolved_by) REFERENCES public.users(id);


--
-- Name: security_events security_events_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.security_events
    ADD CONSTRAINT security_events_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: sprints sprints_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.sprints
    ADD CONSTRAINT sprints_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- Name: task_attachments task_attachments_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.task_attachments
    ADD CONSTRAINT task_attachments_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id);


--
-- Name: task_attachments task_attachments_uploaded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.task_attachments
    ADD CONSTRAINT task_attachments_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES public.users(id);


--
-- Name: task_comments task_comments_author_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.task_comments
    ADD CONSTRAINT task_comments_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.users(id);


--
-- Name: task_comments task_comments_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.task_comments
    ADD CONSTRAINT task_comments_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id);


--
-- Name: task_dependencies task_dependencies_depends_on_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.task_dependencies
    ADD CONSTRAINT task_dependencies_depends_on_task_id_fkey FOREIGN KEY (depends_on_task_id) REFERENCES public.tasks(id);


--
-- Name: task_dependencies task_dependencies_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.task_dependencies
    ADD CONSTRAINT task_dependencies_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id);


--
-- Name: tasks tasks_assignee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_assignee_id_fkey FOREIGN KEY (assignee_id) REFERENCES public.users(id);


--
-- Name: tasks tasks_milestone_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_milestone_id_fkey FOREIGN KEY (milestone_id) REFERENCES public.milestones(id);


--
-- Name: tasks tasks_parent_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_parent_task_id_fkey FOREIGN KEY (parent_task_id) REFERENCES public.tasks(id);


--
-- Name: tasks tasks_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- Name: tasks tasks_reporter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_reporter_id_fkey FOREIGN KEY (reporter_id) REFERENCES public.users(id);


--
-- Name: tasks tasks_sprint_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_sprint_id_fkey FOREIGN KEY (sprint_id) REFERENCES public.sprints(id);


--
-- Name: time_entries time_entries_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.time_entries
    ADD CONSTRAINT time_entries_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(id);


--
-- Name: time_entries time_entries_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.time_entries
    ADD CONSTRAINT time_entries_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- Name: time_entries time_entries_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.time_entries
    ADD CONSTRAINT time_entries_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id);


--
-- Name: time_entries time_entries_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.time_entries
    ADD CONSTRAINT time_entries_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: token_balances token_balances_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.token_balances
    ADD CONSTRAINT token_balances_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: token_transactions token_transactions_chat_message_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.token_transactions
    ADD CONSTRAINT token_transactions_chat_message_id_fkey FOREIGN KEY (chat_message_id) REFERENCES public.chat_messages(id);


--
-- Name: token_transactions token_transactions_chat_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.token_transactions
    ADD CONSTRAINT token_transactions_chat_session_id_fkey FOREIGN KEY (chat_session_id) REFERENCES public.chat_sessions(id);


--
-- Name: token_transactions token_transactions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.token_transactions
    ADD CONSTRAINT token_transactions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: training_data training_data_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.training_data
    ADD CONSTRAINT training_data_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(id);


--
-- Name: training_datasets training_datasets_review_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.training_datasets
    ADD CONSTRAINT training_datasets_review_id_fkey FOREIGN KEY (review_id) REFERENCES public.moderation_reviews(id) ON DELETE SET NULL;


--
-- Name: training_jobs training_jobs_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.training_jobs
    ADD CONSTRAINT training_jobs_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: user_role_history user_role_history_assigned_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.user_role_history
    ADD CONSTRAINT user_role_history_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES public.users(id);


--
-- Name: user_role_history user_role_history_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.user_role_history
    ADD CONSTRAINT user_role_history_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE CASCADE;


--
-- Name: user_role_history user_role_history_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.user_role_history
    ADD CONSTRAINT user_role_history_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_roles user_roles_assigned_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES public.users(id);


--
-- Name: user_roles user_roles_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE CASCADE;


--
-- Name: user_roles user_roles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_segments user_segments_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: advakod
--

ALTER TABLE ONLY public.user_segments
    ADD CONSTRAINT user_segments_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--

\unrestrict qagrMP9qS8zJYfICfXJs4EITHCUjs2rpxJZdrJ0ajV0Fm2z0n5grfwHq5Ca4rup

