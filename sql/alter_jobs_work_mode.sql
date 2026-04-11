-- Run once in MySQL Workbench (schema: priyanshu_career).
-- Adds structured work arrangement + employment type so filters match real data.

ALTER TABLE priyanshu_career.jobs
  ADD COLUMN work_mode VARCHAR(20) NOT NULL DEFAULT 'office'
    COMMENT 'office | remote | wfh | hybrid' AFTER location,
  ADD COLUMN employment_type VARCHAR(20) NOT NULL DEFAULT 'full_time'
    COMMENT 'full_time | part_time' AFTER work_mode;
