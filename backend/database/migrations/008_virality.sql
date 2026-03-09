-- 008_virality.sql
-- Ajout des colonnes de scoring viralite sur les clips.

ALTER TABLE clips ADD COLUMN IF NOT EXISTS virality_score FLOAT;
ALTER TABLE clips ADD COLUMN IF NOT EXISTS hook_text TEXT;
ALTER TABLE clips ADD COLUMN IF NOT EXISTS improvement_tip TEXT;
ALTER TABLE clips ADD COLUMN IF NOT EXISTS best_platform VARCHAR(20);

CREATE INDEX IF NOT EXISTS idx_clips_virality_score ON clips(virality_score);
CREATE INDEX IF NOT EXISTS idx_clips_best_platform ON clips(best_platform);
