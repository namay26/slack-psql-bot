CREATE DATABASE analytics;

\c analytics

CREATE TABLE IF NOT EXISTS public.sales_daily (
    date        date            NOT NULL,
    region      text            NOT NULL,
    category    text            NOT NULL,
    revenue     numeric(12,2)   NOT NULL,
    orders      integer         NOT NULL,
    created_at  timestamptz     NOT NULL DEFAULT now(),
    PRIMARY KEY (date, region, category)
);

INSERT INTO public.sales_daily (date, region, category, revenue, orders) VALUES
    ('2025-09-01', 'North', 'Electronics', 125000.50, 310),
    ('2025-09-01', 'South', 'Grocery',     54000.00,  820),
    ('2025-09-01', 'West',  'Fashion',     40500.00,  190),
    ('2025-09-02', 'North', 'Electronics', 132500.00, 332),
    ('2025-09-02', 'West',  'Fashion',     45500.00,  210),
    ('2025-09-02', 'East',  'Grocery',     62000.00,  870)
ON CONFLICT DO NOTHING;
