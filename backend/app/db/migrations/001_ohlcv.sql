-- migrations/001_ohlcv.sql
CREATE TABLE ohlcv (
    time        TIMESTAMPTZ     NOT NULL,
    symbol      TEXT            NOT NULL,
    open        NUMERIC(18, 6)  NOT NULL,
    high        NUMERIC(18, 6)  NOT NULL,
    low         NUMERIC(18, 6)  NOT NULL,
    close       NUMERIC(18, 6)  NOT NULL,
    volume      BIGINT          NOT NULL,
    vwap        NUMERIC(18, 6),
    timeframe   TEXT            NOT NULL DEFAULT '1D',
    source      TEXT            NOT NULL
);
-- Promote to hypertable, partition by 7-day chunks
SELECT create_hypertable('ohlcv', 'time', chunk_time_interval => INTERVAL '7 days');

-- Composite index: symbol first (equality), then time (range)
CREATE UNIQUE INDEX idx_ohlcv_symbol_time
    ON ohlcv (symbol, timeframe, time DESC);

-- Continuous aggregate for pre-computed weekly bars (query-time savings)
CREATE MATERIALIZED VIEW ohlcv_weekly
WITH (timescaledb.continuous) AS
    SELECT
        time_bucket('1 week', time) AS week,
        symbol,
        FIRST(open, time)           AS open,
        MAX(high)                   AS high,
        MIN(low)                    AS low,
        LAST(close, time)           AS close,
        SUM(volume)                 AS volume
    FROM ohlcv
    WHERE timeframe = '1D'
    GROUP BY week, symbol;

-- Retention policy: drop raw data older than 10 years
SELECT add_retention_policy('ohlcv', INTERVAL '10 years');

-- Additional tables
CREATE TABLE strategies (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT UNIQUE NOT NULL,
    params      JSONB NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE backtest_runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id     UUID REFERENCES strategies(id),
    symbol          TEXT NOT NULL,
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    metrics         JSONB,         
    equity_curve    JSONB,         
    trades          JSONB,         
    ran_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE positions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol          TEXT NOT NULL,
    quantity        NUMERIC(18, 6) NOT NULL,
    entry_price     NUMERIC(18, 6) NOT NULL,
    entry_time      TIMESTAMPTZ NOT NULL,
    exit_price      NUMERIC(18, 6),
    exit_time       TIMESTAMPTZ,
    side            TEXT CHECK (side IN ('long', 'short')),
    status          TEXT CHECK (status IN ('open', 'closed')) DEFAULT 'open',
    account_id      UUID NOT NULL
);