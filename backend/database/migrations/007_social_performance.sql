-- 007_social_performance.sql
-- Tables: social accounts, scheduler posts, clip performance, brand kits

CREATE TABLE IF NOT EXISTS social_accounts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  platform VARCHAR(20) NOT NULL,
  platform_user_id VARCHAR(200) NOT NULL,
  platform_username VARCHAR(200),
  access_token_encrypted TEXT NOT NULL,
  refresh_token_encrypted TEXT,
  expires_at TIMESTAMP,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scheduled_posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clip_id UUID REFERENCES clips(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  platform VARCHAR(20) NOT NULL,
  scheduled_at TIMESTAMP NOT NULL,
  title TEXT,
  description TEXT,
  hashtags TEXT[],
  status VARCHAR(20) DEFAULT 'scheduled',
  attempts INTEGER DEFAULT 0,
  last_error TEXT,
  published_url TEXT,
  platform_post_id VARCHAR(200),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS clip_performance (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clip_id UUID REFERENCES clips(id) ON DELETE CASCADE,
  scheduled_post_id UUID REFERENCES scheduled_posts(id) ON DELETE SET NULL,
  platform VARCHAR(20),
  views INTEGER DEFAULT 0,
  likes INTEGER DEFAULT 0,
  comments INTEGER DEFAULT 0,
  shares INTEGER DEFAULT 0,
  avg_watch_time_seconds FLOAT,
  engagement_score FLOAT,
  predicted_score FLOAT,
  score_delta FLOAT,
  fetched_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS brand_kits (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(120) NOT NULL,
  logo_url TEXT,
  primary_color VARCHAR(16) DEFAULT '#7B61FF',
  secondary_color VARCHAR(16) DEFAULT '#FF61DC',
  caption_font VARCHAR(80) DEFAULT 'Plus Jakarta Sans',
  caption_style VARCHAR(40) DEFAULT 'minimal',
  intro_url TEXT,
  outro_url TEXT,
  logo_position VARCHAR(20) DEFAULT 'top-right',
  logo_opacity INTEGER DEFAULT 80,
  is_default BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_social_accounts_user_id ON social_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_social_accounts_platform ON social_accounts(platform);

CREATE INDEX IF NOT EXISTS idx_scheduled_posts_user_id ON scheduled_posts(user_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_posts_status ON scheduled_posts(status);
CREATE INDEX IF NOT EXISTS idx_scheduled_posts_scheduled_at ON scheduled_posts(scheduled_at);

CREATE INDEX IF NOT EXISTS idx_clip_performance_clip_id ON clip_performance(clip_id);
CREATE INDEX IF NOT EXISTS idx_clip_performance_platform ON clip_performance(platform);
CREATE INDEX IF NOT EXISTS idx_clip_performance_fetched_at ON clip_performance(fetched_at);

CREATE INDEX IF NOT EXISTS idx_brand_kits_user_id ON brand_kits(user_id);
