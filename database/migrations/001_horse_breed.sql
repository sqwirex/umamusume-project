-- Optional breed of a horse. Existing horse records retain NULL in this column.
ALTER TABLE horses ADD COLUMN breed TEXT;
