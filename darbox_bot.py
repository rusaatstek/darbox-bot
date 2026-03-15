<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>DARBOX — Парфюмерная подписка</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400&family=Manrope:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root {
  --accent: #EE2970;
  --accent-soft: rgba(238,41,112,0.15);
  --accent-glow: rgba(238,41,112,0.4);
  --bg: #0A0A0C;
  --bg-card: #141418;
  --bg-card-hover: #1A1A20;
  --bg-elevated: #1E1E24;
  --text: #F2F0ED;
  --text-secondary: #8A8890;
  --text-muted: #555560;
  --border: rgba(255,255,255,0.06);
  --border-accent: rgba(238,41,112,0.3);
  --gold: #D4A853;
  --gold-soft: rgba(212,168,83,0.15);
  --radius: 16px;
  --radius-sm: 10px;
  --radius-xs: 6px;
  --safe-bottom: env(safe-area-inset-bottom, 0px);
}

* { margin:0; padding:0; box-sizing:border-box; -webkit-tap-highlight-color:transparent; }
html { background: var(--bg); }
body {
  font-family: 'Manrope', sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  overflow-x: hidden;
  -webkit-font-smoothing: antialiased;
}

/* === SCROLLBAR === */
::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--text-muted); border-radius: 4px; }

/* === ANIMATIONS === */
@keyframes fadeUp {
  from { opacity:0; transform:translateY(24px); }
  to { opacity:1; transform:translateY(0); }
}
@keyframes fadeIn {
  from { opacity:0; }
  to { opacity:1; }
}
@keyframes scaleIn {
  from { opacity:0; transform:scale(0.92); }
  to { opacity:1; transform:scale(1); }
}
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 20px var(--accent-glow), 0 0 60px rgba(238,41,112,0.1); }
  50% { box-shadow: 0 0 30px var(--accent-glow), 0 0 80px rgba(238,41,112,0.2); }
}
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}
@keyframes radar-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
@keyframes slide-right {
  from { opacity:0; transform:translateX(-20px); }
  to { opacity:1; transform:translateX(0); }
}
@keyframes progress-fill {
  from { width: 0; }
}
@keyframes badge-pop {
  0% { transform: scale(0); }
  60% { transform: scale(1.2); }
  100% { transform: scale(1); }
}

.animate-up { animation: fadeUp 0.6s cubic-bezier(0.22,1,0.36,1) both; }
.animate-in { animation: fadeIn 0.5s ease both; }
.animate-scale { animation: scaleIn 0.5s cubic-bezier(0.22,1,0.36,1) both; }

/* === PAGE STRUCTURE === */
.app {
  max-width: 100%;
  min-height: 100vh;
  position: relative;
}

.page {
  display: none;
  padding: 0 16px 100px;
  min-height: 100vh;
}
.page.active { display: block; }

/* === HEADER === */
.header {
  position: sticky;
  top: 0;
  z-index: 100;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(10,10,12,0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border);
}
.header-back {
  width: 36px; height: 36px;
  border-radius: 50%;
  background: var(--bg-card);
  border: 1px solid var(--border);
  color: var(--text);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}
.header-back:active { transform: scale(0.92); background: var(--bg-elevated); }
.header-back svg { width: 18px; height: 18px; }
.header-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 20px;
  font-weight: 600;
  letter-spacing: 0.02em;
}

/* === BOTTOM NAV === */
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0; right: 0;
  z-index: 200;
  background: rgba(10,10,12,0.92);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-top: 1px solid var(--border);
  display: flex;
  padding: 8px 4px calc(8px + var(--safe-bottom));
}
.nav-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 6px 2px;
  cursor: pointer;
  transition: all 0.2s;
  border-radius: 12px;
  position: relative;
}
.nav-item svg { width: 22px; height: 22px; color: var(--text-muted); transition: all 0.25s; }
.nav-item span { font-size: 10px; color: var(--text-muted); font-weight: 500; transition: all 0.25s; letter-spacing: 0.02em; }
.nav-item.active svg { color: var(--accent); }
.nav-item.active span { color: var(--accent); }
.nav-item.active::before {
  content: '';
  position: absolute;
  top: -8px;
  left: 50%; transform: translateX(-50%);
  width: 20px; height: 3px;
  background: var(--accent);
  border-radius: 0 0 4px 4px;
}
.nav-item:active { transform: scale(0.92); }

/* === HOME PAGE === */
.hero {
  padding: 40px 0 24px;
  text-align: center;
  animation: fadeUp 0.7s cubic-bezier(0.22,1,0.36,1) both;
}
.hero-logo {
  font-family: 'Cormorant Garamond', serif;
  font-size: 42px;
  font-weight: 300;
  letter-spacing: 0.15em;
  margin-bottom: 2px;
  background: linear-gradient(135deg, var(--text) 0%, var(--text-secondary) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.hero-logo b { font-weight: 700; -webkit-text-fill-color: var(--accent); }
.hero-sub {
  font-size: 13px;
  color: var(--text-muted);
  letter-spacing: 0.25em;
  text-transform: uppercase;
  font-weight: 500;
}
.hero-tagline {
  margin-top: 20px;
  font-family: 'Cormorant Garamond', serif;
  font-size: 18px;
  font-weight: 300;
  font-style: italic;
  color: var(--text-secondary);
  line-height: 1.5;
}

/* === LEVEL BADGE === */
.level-card {
  margin: 24px 0;
  padding: 20px;
  background: linear-gradient(135deg, var(--bg-card) 0%, rgba(238,41,112,0.05) 100%);
  border: 1px solid var(--border-accent);
  border-radius: var(--radius);
  animation: fadeUp 0.7s 0.1s cubic-bezier(0.22,1,0.36,1) both;
  position: relative;
  overflow: hidden;
}
.level-card::before {
  content: '';
  position: absolute;
  top: -50%; right: -50%;
  width: 100%; height: 100%;
  background: radial-gradient(circle, rgba(238,41,112,0.08) 0%, transparent 70%);
  pointer-events: none;
}
.level-top { display: flex; align-items: center; gap: 14px; margin-bottom: 14px; position: relative; }
.level-icon {
  width: 52px; height: 52px;
  border-radius: 50%;
  background: var(--accent-soft);
  display: flex; align-items: center; justify-content: center;
  font-size: 24px;
  animation: float 3s ease-in-out infinite;
  border: 2px solid rgba(238,41,112,0.3);
}
.level-info { flex: 1; }
.level-name {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  color: var(--accent);
  font-weight: 700;
  margin-bottom: 2px;
}
.level-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 22px;
  font-weight: 600;
}
.level-xp {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
}
.level-bar {
  height: 6px;
  background: rgba(255,255,255,0.06);
  border-radius: 3px;
  overflow: hidden;
  position: relative;
}
.level-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), #FF6B9D);
  border-radius: 3px;
  animation: progress-fill 1.2s cubic-bezier(0.22,1,0.36,1) both;
  animation-delay: 0.4s;
  position: relative;
}
.level-bar-fill::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
}

/* === SECTION CARDS === */
.section-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 22px;
  font-weight: 500;
  margin: 28px 0 14px;
  padding-left: 2px;
}

.menu-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.menu-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px 14px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.22,1,0.36,1);
  position: relative;
  overflow: hidden;
}
.menu-card:active { transform: scale(0.96); }
.menu-card:hover { border-color: var(--border-accent); background: var(--bg-card-hover); }
.menu-card-icon {
  font-size: 28px;
  margin-bottom: 10px;
  display: block;
}
.menu-card-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 3px;
}
.menu-card-desc {
  font-size: 11px;
  color: var(--text-muted);
  line-height: 1.4;
}
.menu-card.accent {
  border-color: var(--border-accent);
  background: linear-gradient(135deg, var(--bg-card) 0%, rgba(238,41,112,0.06) 100%);
}
.menu-card.accent::after {
  content: '';
  position: absolute;
  top: 0; right: 0;
  width: 60px; height: 60px;
  background: radial-gradient(circle at top right, rgba(238,41,112,0.12), transparent);
  pointer-events: none;
}

/* === SUBSCRIPTION PAGE === */
.plan-cards { display: flex; flex-direction: column; gap: 12px; margin-top: 16px; }
.plan-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.22,1,0.36,1);
  position: relative;
  overflow: hidden;
}
.plan-card:active { transform: scale(0.98); }
.plan-card.selected {
  border-color: var(--accent);
  background: linear-gradient(135deg, var(--bg-card) 0%, rgba(238,41,112,0.08) 100%);
}
.plan-card.selected::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: var(--radius);
  padding: 1px;
  background: linear-gradient(135deg, var(--accent), transparent 60%);
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
}
.plan-popular {
  position: absolute;
  top: 12px; right: 12px;
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  padding: 4px 10px;
  background: var(--accent);
  color: #fff;
  border-radius: 20px;
  font-weight: 700;
}
.plan-format {
  font-family: 'Cormorant Garamond', serif;
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 4px;
}
.plan-desc { font-size: 12px; color: var(--text-secondary); margin-bottom: 12px; }
.plan-price {
  font-size: 28px;
  font-weight: 800;
  color: var(--accent);
}
.plan-price span { font-size: 14px; font-weight: 400; color: var(--text-muted); }

/* Duration selector */
.duration-section { margin-top: 24px; }
.duration-options { display: flex; gap: 8px; margin-top: 12px; }
.dur-btn {
  flex: 1;
  padding: 14px 8px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  text-align: center;
  cursor: pointer;
  transition: all 0.25s;
  color: var(--text);
  position: relative;
}
.dur-btn:active { transform: scale(0.96); }
.dur-btn.selected { border-color: var(--accent); background: var(--accent-soft); }
.dur-btn-months { font-size: 18px; font-weight: 700; display: block; }
.dur-btn-discount {
  font-size: 10px;
  color: var(--text-muted);
  margin-top: 2px;
  display: block;
}
.dur-btn.selected .dur-btn-discount { color: var(--accent); }
.dur-btn-badge {
  position: absolute;
  top: -6px; right: -4px;
  font-size: 9px;
  padding: 2px 6px;
  background: var(--gold);
  color: #000;
  border-radius: 8px;
  font-weight: 700;
}

/* Delivery */
.delivery-options { display: flex; flex-direction: column; gap: 8px; margin-top: 12px; }
.delivery-btn {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.25s;
  color: var(--text);
}
.delivery-btn:active { transform: scale(0.97); }
.delivery-btn.selected { border-color: var(--accent); background: var(--accent-soft); }
.delivery-btn-icon { font-size: 20px; }
.delivery-btn-info { flex: 1; }
.delivery-btn-name { font-size: 14px; font-weight: 600; }
.delivery-btn-detail { font-size: 11px; color: var(--text-muted); }
.delivery-btn-price { font-size: 14px; font-weight: 700; color: var(--accent); }

/* CTA */
.cta-btn {
  width: 100%;
  padding: 16px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--accent);
  color: #fff;
  font-family: 'Manrope', sans-serif;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.03em;
  cursor: pointer;
  margin-top: 24px;
  transition: all 0.25s;
  position: relative;
  overflow: hidden;
}
.cta-btn:active { transform: scale(0.97); }
.cta-btn::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
  background-size: 200% 100%;
  animation: shimmer 3s infinite;
}
.cta-total {
  text-align: center;
  margin-top: 12px;
  font-size: 13px;
  color: var(--text-muted);
}

/* === PROFILE PAGE === */
.profile-header {
  text-align: center;
  padding: 30px 0 20px;
}
.profile-avatar {
  width: 80px; height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent), #FF6B9D);
  display: flex; align-items: center; justify-content: center;
  font-size: 32px;
  margin: 0 auto 14px;
  border: 3px solid var(--bg);
  box-shadow: 0 0 0 2px var(--accent);
  animation: pulse-glow 3s ease-in-out infinite;
}
.profile-name {
  font-family: 'Cormorant Garamond', serif;
  font-size: 26px;
  font-weight: 600;
}
.profile-level {
  font-size: 12px;
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: 0.15em;
  font-weight: 700;
  margin-top: 4px;
}
.profile-stats {
  display: flex;
  gap: 1px;
  margin: 20px 0;
  background: var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}
.profile-stat {
  flex: 1;
  padding: 16px 8px;
  text-align: center;
  background: var(--bg-card);
}
.profile-stat-val {
  font-size: 22px;
  font-weight: 800;
  color: var(--accent);
}
.profile-stat-label {
  font-size: 10px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-top: 2px;
}

/* === DNA RADAR === */
.dna-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px 16px;
  margin: 16px 0;
}
.dna-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 20px;
  text-align: center;
  margin-bottom: 20px;
}
.radar-container {
  width: 100%;
  max-width: 300px;
  margin: 0 auto;
  aspect-ratio: 1;
}
.radar-container svg { width: 100%; height: 100%; }

/* === BADGES === */
.badges-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-top: 16px;
}
.badge-item {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px 8px;
  text-align: center;
  transition: all 0.25s;
}
.badge-item.earned {
  border-color: var(--gold);
  background: linear-gradient(135deg, var(--bg-card) 0%, var(--gold-soft) 100%);
}
.badge-icon {
  font-size: 30px;
  display: block;
  margin-bottom: 8px;
}
.badge-item:not(.earned) .badge-icon { filter: grayscale(1) opacity(0.3); }
.badge-name {
  font-size: 10px;
  font-weight: 600;
  color: var(--text-secondary);
  line-height: 1.3;
}
.badge-item:not(.earned) .badge-name { color: var(--text-muted); }

/* === DIARY PAGE === */
.diary-entry {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px;
  margin-bottom: 10px;
  transition: all 0.25s;
}
.diary-entry:active { transform: scale(0.98); }
.diary-date {
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.diary-mood {
  background: var(--accent-soft);
  color: var(--accent);
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: 600;
}
.diary-aroma {
  font-family: 'Cormorant Garamond', serif;
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 6px;
}
.diary-text {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
}
.diary-rating { display: flex; gap: 12px; margin-top: 10px; }
.diary-rating-item {
  font-size: 11px;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  gap: 4px;
}
.diary-rating-item .stars { color: var(--gold); font-size: 12px; }

/* Fab button */
.fab {
  position: fixed;
  bottom: 80px;
  right: 16px;
  width: 52px; height: 52px;
  border-radius: 50%;
  background: var(--accent);
  border: none;
  color: #fff;
  font-size: 24px;
  cursor: pointer;
  box-shadow: 0 4px 20px var(--accent-glow);
  z-index: 150;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.25s;
}
.fab:active { transform: scale(0.9); }

/* === TASTE MAP === */
.taste-chart {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  margin: 16px 0;
}
.taste-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}
.taste-label {
  width: 80px;
  font-size: 12px;
  color: var(--text-secondary);
  text-align: right;
  flex-shrink: 0;
}
.taste-track {
  flex: 1;
  height: 8px;
  background: rgba(255,255,255,0.04);
  border-radius: 4px;
  overflow: hidden;
}
.taste-fill {
  height: 100%;
  border-radius: 4px;
  animation: progress-fill 1s cubic-bezier(0.22,1,0.36,1) both;
}
.taste-val {
  width: 30px;
  font-size: 12px;
  font-weight: 700;
  color: var(--text-secondary);
}

/* === GIFT PAGE === */
.gift-card-preview {
  margin: 24px auto;
  max-width: 320px;
  aspect-ratio: 1.6;
  background: linear-gradient(135deg, #1a0a12 0%, #2a0a18 40%, #0a0a0c 100%);
  border: 1px solid var(--border-accent);
  border-radius: var(--radius);
  padding: 28px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  position: relative;
  overflow: hidden;
  animation: scaleIn 0.6s cubic-bezier(0.22,1,0.36,1) both;
}
.gift-card-preview::before {
  content: '';
  position: absolute;
  top: -30%; right: -30%;
  width: 60%; height: 60%;
  background: radial-gradient(circle, rgba(238,41,112,0.15), transparent 70%);
  pointer-events: none;
}
.gift-card-preview::after {
  content: '';
  position: absolute;
  bottom: -20%; left: -20%;
  width: 50%; height: 50%;
  background: radial-gradient(circle, rgba(212,168,83,0.08), transparent 70%);
  pointer-events: none;
}
.gift-brand {
  font-family: 'Cormorant Garamond', serif;
  font-size: 28px;
  font-weight: 300;
  letter-spacing: 0.1em;
  position: relative;
}
.gift-brand b { font-weight: 700; color: var(--accent); }
.gift-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  color: var(--text-muted);
  margin-top: 4px;
}
.gift-amount {
  font-size: 36px;
  font-weight: 800;
  background: linear-gradient(135deg, var(--accent), #FF6B9D, var(--gold));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  position: relative;
}

/* === REFERRAL === */
.ref-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px;
  text-align: center;
  margin: 16px 0;
}
.ref-link-box {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 12px;
}
.ref-link {
  flex: 1;
  font-size: 13px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: left;
}
.ref-copy {
  padding: 8px 14px;
  background: var(--accent);
  border: none;
  border-radius: var(--radius-xs);
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  font-family: 'Manrope', sans-serif;
}
.ref-copy:active { transform: scale(0.95); }
.ref-reward {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 16px;
  padding: 12px;
  background: var(--gold-soft);
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 600;
  color: var(--gold);
}

/* === QUESTIONNAIRE === */
.q-progress {
  display: flex;
  gap: 3px;
  margin: 16px 0;
}
.q-dot {
  flex: 1;
  height: 4px;
  border-radius: 2px;
  background: rgba(255,255,255,0.06);
  transition: all 0.4s;
}
.q-dot.done { background: var(--accent); }
.q-dot.current { background: linear-gradient(90deg, var(--accent), #FF6B9D); }

.q-question {
  font-family: 'Cormorant Garamond', serif;
  font-size: 24px;
  font-weight: 500;
  line-height: 1.3;
  margin: 24px 0 20px;
  animation: fadeUp 0.4s cubic-bezier(0.22,1,0.36,1) both;
}
.q-options { display: flex; flex-direction: column; gap: 8px; }
.q-option {
  padding: 14px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.25s;
  font-size: 14px;
  color: var(--text);
  display: flex;
  align-items: center;
  gap: 10px;
}
.q-option:active { transform: scale(0.97); }
.q-option.selected { border-color: var(--accent); background: var(--accent-soft); }
.q-option-check {
  width: 20px; height: 20px;
  border-radius: 50%;
  border: 2px solid var(--text-muted);
  display: flex; align-items: center; justify-content: center;
  transition: all 0.25s;
  flex-shrink: 0;
}
.q-option.selected .q-option-check {
  border-color: var(--accent);
  background: var(--accent);
}
.q-option.selected .q-option-check::after {
  content: '✓';
  font-size: 12px;
  color: #fff;
}
.q-next {
  padding: 14px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--bg-elevated);
  color: var(--text-muted);
  font-family: 'Manrope', sans-serif;
  font-size: 14px;
  font-weight: 600;
  width: 100%;
  margin-top: 16px;
  cursor: pointer;
  transition: all 0.25s;
}
.q-next.ready { background: var(--accent); color: #fff; }
.q-next:active { transform: scale(0.97); }

/* === CHAT === */
.chat-messages {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px 0;
}
.chat-msg {
  max-width: 80%;
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.5;
  animation: scaleIn 0.3s cubic-bezier(0.22,1,0.36,1) both;
}
.chat-msg.user {
  align-self: flex-end;
  background: var(--accent);
  color: #fff;
  border-bottom-right-radius: 4px;
}
.chat-msg.admin {
  align-self: flex-start;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-bottom-left-radius: 4px;
}
.chat-msg-time {
  font-size: 10px;
  color: var(--text-muted);
  margin-top: 4px;
}
.chat-input-area {
  position: fixed;
  bottom: 68px;
  left: 0; right: 0;
  padding: 12px 16px;
  background: rgba(10,10,12,0.95);
  backdrop-filter: blur(20px);
  display: flex;
  gap: 8px;
  z-index: 150;
}
.chat-input {
  flex: 1;
  padding: 12px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 24px;
  color: var(--text);
  font-family: 'Manrope', sans-serif;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}
.chat-input:focus { border-color: var(--accent); }
.chat-input::placeholder { color: var(--text-muted); }
.chat-send {
  width: 44px; height: 44px;
  border-radius: 50%;
  background: var(--accent);
  border: none;
  color: #fff;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}
.chat-send:active { transform: scale(0.9); }

/* Utility */
.spacer { height: 16px; }
.divider { height: 1px; background: var(--border); margin: 20px 0; }
.text-accent { color: var(--accent); }
.text-gold { color: var(--gold); }
.text-muted { color: var(--text-muted); }
.text-center { text-align: center; }
.mt-8 { margin-top: 8px; }
.mt-16 { margin-top: 16px; }
.mt-24 { margin-top: 24px; }
</style>
</head>
<body>

<div class="app" id="app">

  <!-- ============ HOME PAGE ============ -->
  <div class="page active" id="page-home">
    <div class="hero">
      <div class="hero-logo">DAR<b>BOX</b></div>
      <div class="hero-sub">парфюмерная подписка</div>
      <div class="hero-tagline">Откройте свой идеальный аромат<br>через персональный подбор</div>
    </div>

    <div class="level-card">
      <div class="level-top">
        <div class="level-icon">🌿</div>
        <div class="level-info">
          <div class="level-name">Уровень 2</div>
          <div class="level-title">Исследователь</div>
          <div class="level-xp">340 / 600 XP</div>
        </div>
      </div>
      <div class="level-bar">
        <div class="level-bar-fill" style="width:57%"></div>
      </div>
    </div>

    <div class="section-title">Ваша подписка</div>
    <div class="menu-grid">
      <div class="menu-card accent" onclick="navigateTo('subscription')">
        <span class="menu-card-icon">📦</span>
        <div class="menu-card-title">Подписка</div>
        <div class="menu-card-desc">Выбрать тариф и оформить</div>
      </div>
      <div class="menu-card" onclick="navigateTo('profile')">
        <span class="menu-card-icon">👤</span>
        <div class="menu-card-title">Профиль</div>
        <div class="menu-card-desc">Ваш ольфакторный портрет</div>
      </div>
      <div class="menu-card" onclick="navigateTo('diary')">
        <span class="menu-card-icon">📔</span>
        <div class="menu-card-title">Дневник</div>
        <div class="menu-card-desc">Записи об ароматах</div>
      </div>
      <div class="menu-card" onclick="navigateTo('taste')">
        <span class="menu-card-icon">🎯</span>
        <div class="menu-card-title">Карта вкуса</div>
        <div class="menu-card-desc">Аналитика предпочтений</div>
      </div>
    </div>

    <div class="section-title">Бонусы</div>
    <div class="menu-grid">
      <div class="menu-card" onclick="navigateTo('badges')">
        <span class="menu-card-icon">🏆</span>
        <div class="menu-card-title">Ачивки</div>
        <div class="menu-card-desc">3 из 12 получено</div>
      </div>
      <div class="menu-card" onclick="navigateTo('referral')">
        <span class="menu-card-icon">🎁</span>
        <div class="menu-card-title">Друзьям</div>
        <div class="menu-card-desc">10% за каждого друга</div>
      </div>
      <div class="menu-card" onclick="navigateTo('gift')">
        <span class="menu-card-icon">💌</span>
        <div class="menu-card-title">Сертификат</div>
        <div class="menu-card-desc">Подарить подписку</div>
      </div>
      <div class="menu-card" onclick="navigateTo('chat')">
        <span class="menu-card-icon">💬</span>
        <div class="menu-card-title">Чат</div>
        <div class="menu-card-desc">Написать парфюмеру</div>
      </div>
    </div>

    <div class="spacer"></div>
  </div>

  <!-- ============ SUBSCRIPTION PAGE ============ -->
  <div class="page" id="page-subscription">
    <div class="header">
      <div class="header-back" onclick="navigateTo('home')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
      </div>
      <div class="header-title">Подписка</div>
    </div>

    <div class="section-title">Выберите формат</div>
    <div class="plan-cards">
      <div class="plan-card selected" onclick="selectPlan(this, 0)">
        <div class="plan-format">8 × 3 мл</div>
        <div class="plan-desc">8 ароматов в миниатюрах — попробуйте всё</div>
        <div class="plan-price">1 980 ₽ <span>/мес</span></div>
      </div>
      <div class="plan-card" onclick="selectPlan(this, 1)">
        <div class="plan-popular">Хит</div>
        <div class="plan-format">6 × 6 мл</div>
        <div class="plan-desc">Оптимальный формат на каждый день</div>
        <div class="plan-price">2 380 ₽ <span>/мес</span></div>
      </div>
      <div class="plan-card" onclick="selectPlan(this, 2)">
        <div class="plan-format">5 × 10 мл</div>
        <div class="plan-desc">Полноразмерные флаконы для ценителей</div>
        <div class="plan-price">3 580 ₽ <span>/мес</span></div>
      </div>
    </div>

    <div class="duration-section">
      <div class="section-title">Срок подписки</div>
      <div class="duration-options">
        <div class="dur-btn selected" onclick="selectDuration(this, 0)">
          <span class="dur-btn-months">2 мес</span>
          <span class="dur-btn-discount">без скидки</span>
        </div>
        <div class="dur-btn" onclick="selectDuration(this, 1)">
          <span class="dur-btn-months">4 мес</span>
          <span class="dur-btn-discount">−5%</span>
        </div>
        <div class="dur-btn" onclick="selectDuration(this, 2)">
          <div class="dur-btn-badge">−10%</div>
          <span class="dur-btn-months">6 мес</span>
          <span class="dur-btn-discount">выгодно</span>
        </div>
      </div>
    </div>

    <div class="duration-section">
      <div class="section-title">Доставка</div>
      <div class="delivery-options">
        <div class="delivery-btn selected" onclick="selectDelivery(this)">
          <span class="delivery-btn-icon">📮</span>
          <div class="delivery-btn-info">
            <div class="delivery-btn-name">Почта России</div>
            <div class="delivery-btn-detail">7–14 дней</div>
          </div>
          <div class="delivery-btn-price">280 ₽</div>
        </div>
        <div class="delivery-btn" onclick="selectDelivery(this)">
          <span class="delivery-btn-icon">📦</span>
          <div class="delivery-btn-info">
            <div class="delivery-btn-name">СДЭК</div>
            <div class="delivery-btn-detail">3–5 дней</div>
          </div>
          <div class="delivery-btn-price">280 ₽</div>
        </div>
        <div class="delivery-btn" onclick="selectDelivery(this)">
          <span class="delivery-btn-icon">🚗</span>
          <div class="delivery-btn-info">
            <div class="delivery-btn-name">Курьер Москва</div>
            <div class="delivery-btn-detail">1–2 дня</div>
          </div>
          <div class="delivery-btn-price">350 ₽</div>
        </div>
      </div>
    </div>

    <button class="cta-btn" onclick="alert('Переход к оплате')">Оформить подписку</button>
    <div class="cta-total">Итого: 1 980 ₽ + доставка 280 ₽ = <strong style="color:var(--accent)">2 260 ₽</strong></div>
    <div class="spacer"></div>
  </div>

  <!-- ============ PROFILE PAGE ============ -->
  <div class="page" id="page-profile">
    <div class="header">
      <div class="header-back" onclick="navigateTo('home')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
      </div>
      <div class="header-title">Профиль</div>
    </div>

    <div class="profile-header">
      <div class="profile-avatar">🌸</div>
      <div class="profile-name">Анна</div>
      <div class="profile-level">✦ Исследователь</div>
    </div>

    <div class="profile-stats">
      <div class="profile-stat">
        <div class="profile-stat-val">4</div>
        <div class="profile-stat-label">Боксов</div>
      </div>
      <div class="profile-stat">
        <div class="profile-stat-val">26</div>
        <div class="profile-stat-label">Ароматов</div>
      </div>
      <div class="profile-stat">
        <div class="profile-stat-val">18</div>
        <div class="profile-stat-label">Отзывов</div>
      </div>
      <div class="profile-stat">
        <div class="profile-stat-val">2</div>
        <div class="profile-stat-label">Друзей</div>
      </div>
    </div>

    <!-- DNA Radar -->
    <div class="dna-card">
      <div class="dna-title">Парфюмерная ДНК</div>
      <div class="radar-container" id="radar-chart"></div>
    </div>

    <div class="section-title">Ольфакторный портрет</div>
    <div class="diary-entry">
      <div class="diary-aroma" style="font-size:15px">Пол: Женский · Возраст: 25–34</div>
      <div class="diary-text">Повод: на каждый день · Интенсивность: средняя<br>Опыт: продвинутый · Сезон: весна/лето</div>
    </div>
    <div class="diary-entry">
      <div class="diary-aroma" style="font-size:15px">Любимые ноты</div>
      <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:8px">
        <span style="padding:4px 12px;background:var(--accent-soft);border-radius:20px;font-size:12px;color:var(--accent)">Цветочные</span>
        <span style="padding:4px 12px;background:var(--accent-soft);border-radius:20px;font-size:12px;color:var(--accent)">Мускусные</span>
        <span style="padding:4px 12px;background:var(--accent-soft);border-radius:20px;font-size:12px;color:var(--accent)">Фруктовые</span>
        <span style="padding:4px 12px;background:var(--gold-soft);border-radius:20px;font-size:12px;color:var(--gold)">Ваниль</span>
      </div>
    </div>

    <button class="cta-btn" onclick="navigateTo('questionnaire')" style="background:var(--bg-elevated);color:var(--text)">✏️ Пройти анкету заново</button>
    <div class="spacer"></div>
  </div>

  <!-- ============ DIARY PAGE ============ -->
  <div class="page" id="page-diary">
    <div class="header">
      <div class="header-back" onclick="navigateTo('home')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
      </div>
      <div class="header-title">Парфюмерный дневник</div>
    </div>

    <div style="padding-top:12px">
      <div class="diary-entry animate-up" style="animation-delay:0.05s">
        <div class="diary-date">14 марта 2026 <span class="diary-mood">🌸 Романтика</span></div>
        <div class="diary-aroma">Baccarat Rouge 540</div>
        <div class="diary-text">Невероятный шлейф, комплименты весь день. Идеален для свидания — тёплый, обволакивающий, с карамельной дымкой.</div>
        <div class="diary-rating">
          <div class="diary-rating-item"><span class="stars">★★★★★</span> Общее</div>
          <div class="diary-rating-item"><span class="stars">★★★★★</span> Стойкость</div>
          <div class="diary-rating-item"><span class="stars">★★★★☆</span> Шлейф</div>
        </div>
      </div>

      <div class="diary-entry animate-up" style="animation-delay:0.1s">
        <div class="diary-date">10 марта 2026 <span class="diary-mood">☀️ Энергия</span></div>
        <div class="diary-aroma">Aventus</div>
        <div class="diary-text">Свежий и дерзкий. Отлично для деловых встреч. Ананас и берёза — необычное, но гармоничное сочетание.</div>
        <div class="diary-rating">
          <div class="diary-rating-item"><span class="stars">★★★★☆</span> Общее</div>
          <div class="diary-rating-item"><span class="stars">★★★★★</span> Стойкость</div>
          <div class="diary-rating-item"><span class="stars">★★★☆☆</span> Шлейф</div>
        </div>
      </div>

      <div class="diary-entry animate-up" style="animation-delay:0.15s">
        <div class="diary-date">5 марта 2026 <span class="diary-mood">🌙 Вечер</span></div>
        <div class="diary-aroma">Black Orchid</div>
        <div class="diary-text">Тёмный, загадочный. Чёрная орхидея и трюфель создают чувственный вечерний образ. Не на каждый день.</div>
        <div class="diary-rating">
          <div class="diary-rating-item"><span class="stars">★★★★☆</span> Общее</div>
          <div class="diary-rating-item"><span class="stars">★★★★★</span> Стойкость</div>
          <div class="diary-rating-item"><span class="stars">★★★★★</span> Шлейф</div>
        </div>
      </div>
    </div>

    <button class="fab" onclick="alert('Добавить запись')">+</button>
    <div class="spacer"></div>
  </div>

  <!-- ============ TASTE MAP PAGE ============ -->
  <div class="page" id="page-taste">
    <div class="header">
      <div class="header-back" onclick="navigateTo('home')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
      </div>
      <div class="header-title">Карта вкуса</div>
    </div>

    <div class="dna-card" style="margin-top:16px">
      <div class="dna-title">Топ-5 фаворитов</div>
      <div style="display:flex;flex-direction:column;gap:10px">
        <div style="display:flex;align-items:center;gap:12px">
          <span style="font-size:20px">🥇</span>
          <div style="flex:1">
            <div style="font-weight:600;font-size:14px">Baccarat Rouge 540</div>
            <div style="font-size:11px;color:var(--text-muted)">Maison Francis Kurkdjian</div>
          </div>
          <div style="font-size:14px;font-weight:700;color:var(--gold)">4.8</div>
        </div>
        <div style="display:flex;align-items:center;gap:12px">
          <span style="font-size:20px">🥈</span>
          <div style="flex:1">
            <div style="font-weight:600;font-size:14px">Lost Cherry</div>
            <div style="font-size:11px;color:var(--text-muted)">Tom Ford</div>
          </div>
          <div style="font-size:14px;font-weight:700;color:var(--text-secondary)">4.6</div>
        </div>
        <div style="display:flex;align-items:center;gap:12px">
          <span style="font-size:20px">🥉</span>
          <div style="flex:1">
            <div style="font-weight:600;font-size:14px">Delina</div>
            <div style="font-size:11px;color:var(--text-muted)">Parfums de Marly</div>
          </div>
          <div style="font-size:14px;font-weight:700;color:var(--text-secondary)">4.5</div>
        </div>
      </div>
    </div>

    <div class="taste-chart">
      <div class="dna-title" style="margin-bottom:16px">Ваши предпочтения</div>
      <div class="taste-bar"><span class="taste-label">Цветочные</span><div class="taste-track"><div class="taste-fill" style="width:88%;background:linear-gradient(90deg,var(--accent),#FF6B9D);animation-delay:0.1s"></div></div><span class="taste-val">88%</span></div>
      <div class="taste-bar"><span class="taste-label">Мускусные</span><div class="taste-track"><div class="taste-fill" style="width:75%;background:linear-gradient(90deg,#9B59B6,#C39BD3);animation-delay:0.2s"></div></div><span class="taste-val">75%</span></div>
      <div class="taste-bar"><span class="taste-label">Фруктовые</span><div class="taste-track"><div class="taste-fill" style="width:70%;background:linear-gradient(90deg,#F39C12,#F7DC6F);animation-delay:0.3s"></div></div><span class="taste-val">70%</span></div>
      <div class="taste-bar"><span class="taste-label">Древесные</span><div class="taste-track"><div class="taste-fill" style="width:55%;background:linear-gradient(90deg,#27AE60,#58D68D);animation-delay:0.4s"></div></div><span class="taste-val">55%</span></div>
      <div class="taste-bar"><span class="taste-label">Восточные</span><div class="taste-track"><div class="taste-fill" style="width:62%;background:linear-gradient(90deg,var(--gold),#F0D78C);animation-delay:0.5s"></div></div><span class="taste-val">62%</span></div>
      <div class="taste-bar"><span class="taste-label">Свежие</span><div class="taste-track"><div class="taste-fill" style="width:40%;background:linear-gradient(90deg,#3498DB,#85C1E9);animation-delay:0.6s"></div></div><span class="taste-val">40%</span></div>
      <div class="taste-bar"><span class="taste-label">Пудровые</span><div class="taste-track"><div class="taste-fill" style="width:48%;background:linear-gradient(90deg,#E8DAEF,#D2B4DE);animation-delay:0.7s"></div></div><span class="taste-val">48%</span></div>
    </div>
    <div class="spacer"></div>
  </div>

  <!-- ============ BADGES PAGE ============ -->
  <div class="page" id="page-badges">
    <div class="header">
      <div class="header-back" onclick="navigateTo('home')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
      </div>
      <div class="header-title">Ачивки</div>
    </div>

    <div style="text-align:center;padding:20px 0 8px">
      <div style="font-size:36px;font-weight:800;color:var(--gold)">3 <span style="font-size:16px;color:var(--text-muted);font-weight:400">из 12</span></div>
      <div style="font-size:12px;color:var(--text-muted);margin-top:4px">ачивок получено</div>
    </div>

    <div class="badges-grid">
      <div class="badge-item earned animate-scale" style="animation-delay:0.05s">
        <span class="badge-icon">🎉</span>
        <div class="badge-name">Первый бокс</div>
      </div>
      <div class="badge-item earned animate-scale" style="animation-delay:0.1s">
        <span class="badge-icon">📝</span>
        <div class="badge-name">5 отзывов</div>
      </div>
      <div class="badge-item earned animate-scale" style="animation-delay:0.15s">
        <span class="badge-icon">👥</span>
        <div class="badge-name">Привёл друга</div>
      </div>
      <div class="badge-item animate-scale" style="animation-delay:0.2s">
        <span class="badge-icon">📔</span>
        <div class="badge-name">10 записей</div>
      </div>
      <div class="badge-item animate-scale" style="animation-delay:0.25s">
        <span class="badge-icon">🔥</span>
        <div class="badge-name">3 месяца подряд</div>
      </div>
      <div class="badge-item animate-scale" style="animation-delay:0.3s">
        <span class="badge-icon">🧪</span>
        <div class="badge-name">50 ароматов</div>
      </div>
      <div class="badge-item animate-scale" style="animation-delay:0.35s">
        <span class="badge-icon">⭐</span>
        <div class="badge-name">20 отзывов</div>
      </div>
      <div class="badge-item animate-scale" style="animation-delay:0.4s">
        <span class="badge-icon">🎁</span>
        <div class="badge-name">Подарил сертификат</div>
      </div>
      <div class="badge-item animate-scale" style="animation-delay:0.45s">
        <span class="badge-icon">🏅</span>
        <div class="badge-name">Полгода с нами</div>
      </div>
      <div class="badge-item animate-scale" style="animation-delay:0.5s">
        <span class="badge-icon">💎</span>
        <div class="badge-name">100 ароматов</div>
      </div>
      <div class="badge-item animate-scale" style="animation-delay:0.55s">
        <span class="badge-icon">🌟</span>
        <div class="badge-name">5 друзей</div>
      </div>
      <div class="badge-item animate-scale" style="animation-delay:0.6s">
        <span class="badge-icon">👑</span>
        <div class="badge-name">Гуру парфюмерии</div>
      </div>
    </div>
    <div class="spacer"></div>
  </div>

  <!-- ============ REFERRAL PAGE ============ -->
  <div class="page" id="page-referral">
    <div class="header">
      <div class="header-back" onclick="navigateTo('home')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
      </div>
      <div class="header-title">Пригласить друга</div>
    </div>

    <div class="ref-card animate-up">
      <div style="font-size:48px;margin-bottom:12px">🎁</div>
      <div style="font-family:'Cormorant Garamond',serif;font-size:24px;font-weight:600;margin-bottom:8px">Поделитесь ароматами</div>
      <div style="font-size:13px;color:var(--text-secondary);line-height:1.5">Приглашайте друзей и получайте <strong style="color:var(--accent)">10% скидку</strong> на следующий бокс за каждого приглашённого</div>
      <div class="ref-link-box">
        <div class="ref-link">t.me/dararomabox_bot?start=ref_anna2026</div>
        <button class="ref-copy" onclick="copyRef(this)">Копировать</button>
      </div>
      <div class="ref-reward">🏆 Приглашено друзей: <strong>2</strong></div>
    </div>

    <div class="section-title">Как это работает</div>
    <div style="display:flex;flex-direction:column;gap:10px">
      <div class="diary-entry animate-up" style="animation-delay:0.1s">
        <div style="display:flex;gap:12px;align-items:center">
          <div style="width:36px;height:36px;border-radius:50%;background:var(--accent-soft);display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0">1</div>
          <div style="font-size:13px;line-height:1.4">Отправьте ссылку другу</div>
        </div>
      </div>
      <div class="diary-entry animate-up" style="animation-delay:0.15s">
        <div style="display:flex;gap:12px;align-items:center">
          <div style="width:36px;height:36px;border-radius:50%;background:var(--accent-soft);display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0">2</div>
          <div style="font-size:13px;line-height:1.4">Друг оформляет подписку</div>
        </div>
      </div>
      <div class="diary-entry animate-up" style="animation-delay:0.2s">
        <div style="display:flex;gap:12px;align-items:center">
          <div style="width:36px;height:36px;border-radius:50%;background:var(--accent-soft);display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0">3</div>
          <div style="font-size:13px;line-height:1.4">Вы получаете скидку 10% 🎉</div>
        </div>
      </div>
    </div>
    <div class="spacer"></div>
  </div>

  <!-- ============ GIFT CARD PAGE ============ -->
  <div class="page" id="page-gift">
    <div class="header">
      <div class="header-back" onclick="navigateTo('home')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
      </div>
      <div class="header-title">Подарочный сертификат</div>
    </div>

    <div class="gift-card-preview">
      <div>
        <div class="gift-brand">DAR<b>BOX</b></div>
        <div class="gift-label">подарочный сертификат</div>
      </div>
      <div class="gift-amount">3 580 ₽</div>
    </div>

    <div class="section-title">Номинал</div>
    <div class="duration-options">
      <div class="dur-btn" onclick="selectGiftAmount(this, '1 980')">
        <span class="dur-btn-months" style="font-size:15px">1 980 ₽</span>
        <span class="dur-btn-discount">3мл × 8</span>
      </div>
      <div class="dur-btn" onclick="selectGiftAmount(this, '2 380')">
        <span class="dur-btn-months" style="font-size:15px">2 380 ₽</span>
        <span class="dur-btn-discount">6мл × 6</span>
      </div>
      <div class="dur-btn selected" onclick="selectGiftAmount(this, '3 580')">
        <span class="dur-btn-months" style="font-size:15px">3 580 ₽</span>
        <span class="dur-btn-discount">10мл × 5</span>
      </div>
    </div>

    <button class="cta-btn mt-24" onclick="alert('Оформить сертификат')">Подарить сертификат 💌</button>
    <div class="spacer"></div>
  </div>

  <!-- ============ QUESTIONNAIRE PAGE ============ -->
  <div class="page" id="page-questionnaire">
    <div class="header">
      <div class="header-back" onclick="navigateTo('profile')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
      </div>
      <div class="header-title">Анкета</div>
    </div>

    <div class="q-progress" id="q-progress"></div>
    <div id="q-content"></div>
    <div class="spacer"></div>
  </div>

  <!-- ============ CHAT PAGE ============ -->
  <div class="page" id="page-chat">
    <div class="header">
      <div class="header-back" onclick="navigateTo('home')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
      </div>
      <div class="header-title">Чат с парфюмером</div>
    </div>

    <div class="chat-messages" id="chat-messages">
      <div class="chat-msg admin">Привет! 👋 Я помогу подобрать идеальные ароматы для вашего бокса. Расскажите, что вам нравится?<div class="chat-msg-time">10:24</div></div>
      <div class="chat-msg user">Хочу что-то сладкое и тёплое на весну<div class="chat-msg-time">10:26</div></div>
      <div class="chat-msg admin">Отличный выбор! Для тёплой весны рекомендую попробовать направления с ванилью, карамелью и цветочными нотами. Добавлю в ваш следующий бокс 🌸<div class="chat-msg-time">10:28</div></div>
    </div>

    <div class="chat-input-area">
      <input class="chat-input" placeholder="Написать сообщение..." id="chat-input">
      <button class="chat-send" onclick="sendChat()">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 2L11 13"/><path d="M22 2l-7 20-4-9-9-4 20-7z"/></svg>
      </button>
    </div>
    <div class="spacer" style="height:120px"></div>
  </div>

  <!-- ============ BOTTOM NAV ============ -->
  <nav class="bottom-nav" id="bottom-nav">
    <div class="nav-item active" onclick="navigateTo('home')" data-page="home">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
      <span>Главная</span>
    </div>
    <div class="nav-item" onclick="navigateTo('diary')" data-page="diary">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>
      <span>Дневник</span>
    </div>
    <div class="nav-item" onclick="navigateTo('taste')" data-page="taste">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 000 20 14.5 14.5 0 000-20"/><path d="M2 12h20"/></svg>
      <span>Вкус</span>
    </div>
    <div class="nav-item" onclick="navigateTo('profile')" data-page="profile">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
      <span>Профиль</span>
    </div>
    <div class="nav-item" onclick="navigateTo('chat')" data-page="chat">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
      <span>Чат</span>
    </div>
  </nav>
</div>

<script>
// === TELEGRAM WEBAPP INIT ===
const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
  tg.setHeaderColor('#0A0A0C');
  tg.setBackgroundColor('#0A0A0C');
}

// === NAVIGATION ===
let currentPage = 'home';
const pageHistory = ['home'];

function navigateTo(page) {
  const current = document.getElementById('page-' + currentPage);
  const target = document.getElementById('page-' + page);
  if (!target) return;
  
  current.classList.remove('active');
  target.classList.add('active');
  
  // Update nav
  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.toggle('active', item.dataset.page === page);
  });
  
  // Show/hide bottom nav on chat page
  document.getElementById('bottom-nav').style.display = page === 'chat' ? 'none' : 'flex';
  
  // FAB visibility
  const fab = document.querySelector('.fab');
  if (fab) fab.style.display = page === 'diary' ? 'flex' : 'none';
  
  currentPage = page;
  window.scrollTo(0, 0);
  
  // Init page-specific content
  if (page === 'profile') initRadar();
  if (page === 'questionnaire') initQuestionnaire();
}

// === PLAN SELECTION ===
const planPrices = [1980, 2380, 3580];
let selectedPlan = 0;
let selectedDuration = 0;
const discounts = [0, 0.05, 0.10];
const deliveryPrices = [280, 280, 350];
let selectedDeliveryIdx = 0;

function selectPlan(el, idx) {
  selectedPlan = idx;
  document.querySelectorAll('.plan-card').forEach(c => c.classList.remove('selected'));
  el.classList.add('selected');
  updateTotal();
}

function selectDuration(el, idx) {
  selectedDuration = idx;
  document.querySelectorAll('.dur-btn').forEach(c => c.classList.remove('selected'));
  el.classList.add('selected');
  updateTotal();
}

function selectDelivery(el) {
  const btns = document.querySelectorAll('.delivery-btn');
  btns.forEach((b, i) => { b.classList.remove('selected'); if (b === el) selectedDeliveryIdx = i; });
  el.classList.add('selected');
  updateTotal();
}

function updateTotal() {
  const base = planPrices[selectedPlan];
  const disc = discounts[selectedDuration];
  const delivery = deliveryPrices[selectedDeliveryIdx];
  const discounted = Math.round(base * (1 - disc));
  const total = discounted + delivery;
  const totalEl = document.querySelector('.cta-total');
  if (totalEl) {
    totalEl.innerHTML = `Итого: ${discounted.toLocaleString('ru')} ₽ + доставка ${delivery} ₽ = <strong style="color:var(--accent)">${total.toLocaleString('ru')} ₽</strong>`;
  }
}

function selectGiftAmount(el, amount) {
  document.querySelectorAll('#page-gift .dur-btn').forEach(b => b.classList.remove('selected'));
  el.classList.add('selected');
  document.querySelector('.gift-amount').textContent = amount + ' ₽';
}

// === RADAR CHART ===
function initRadar() {
  const container = document.getElementById('radar-chart');
  if (!container || container.querySelector('svg')) return;
  
  const labels = ['Цветочные', 'Мускусные', 'Фруктовые', 'Древесные', 'Восточные', 'Свежие', 'Пудровые', 'Пряные'];
  const values = [0.88, 0.75, 0.70, 0.55, 0.62, 0.40, 0.48, 0.35];
  const n = labels.length;
  const cx = 150, cy = 150, r = 110;
  
  let svg = `<svg viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">`;
  
  // Grid circles
  for (let i = 1; i <= 4; i++) {
    const cr = r * i / 4;
    svg += `<circle cx="${cx}" cy="${cy}" r="${cr}" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>`;
  }
  
  // Axis lines & labels
  for (let i = 0; i < n; i++) {
    const angle = (Math.PI * 2 * i / n) - Math.PI / 2;
    const x = cx + r * Math.cos(angle);
    const y = cy + r * Math.sin(angle);
    svg += `<line x1="${cx}" y1="${cy}" x2="${x}" y2="${y}" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>`;
    
    const lx = cx + (r + 20) * Math.cos(angle);
    const ly = cy + (r + 20) * Math.sin(angle);
    svg += `<text x="${lx}" y="${ly}" text-anchor="middle" dominant-baseline="middle" fill="#8A8890" font-size="9" font-family="Manrope,sans-serif">${labels[i]}</text>`;
  }
  
  // Data polygon
  let points = '';
  for (let i = 0; i < n; i++) {
    const angle = (Math.PI * 2 * i / n) - Math.PI / 2;
    const x = cx + r * values[i] * Math.cos(angle);
    const y = cy + r * values[i] * Math.sin(angle);
    points += `${x},${y} `;
  }
  
  svg += `<polygon points="${points.trim()}" fill="rgba(238,41,112,0.15)" stroke="#EE2970" stroke-width="2"/>`;
  
  // Data points
  for (let i = 0; i < n; i++) {
    const angle = (Math.PI * 2 * i / n) - Math.PI / 2;
    const x = cx + r * values[i] * Math.cos(angle);
    const y = cy + r * values[i] * Math.sin(angle);
    svg += `<circle cx="${x}" cy="${y}" r="4" fill="#EE2970" stroke="#0A0A0C" stroke-width="2"/>`;
  }
  
  svg += `</svg>`;
  container.innerHTML = svg;
}

// === QUESTIONNAIRE ===
const questions = [
  { q: 'Для кого подбираем ароматы?', opts: ['Для себя (Ж)', 'Для себя (М)', 'В подарок (Ж)', 'В подарок (М)'] },
  { q: 'Ваш возраст?', opts: ['18–24', '25–34', '35–44', '45+'] },
  { q: 'Ваш образ жизни?', opts: ['Активный / спорт', 'Деловой / офис', 'Творческий', 'Домашний / уютный'] },
  { q: 'Повод для ароматов?', opts: ['На каждый день', 'Для работы', 'На свидание', 'Для особых случаев'] },
  { q: 'Какая интенсивность вам ближе?', opts: ['Лёгкая, еле уловимая', 'Средняя, для себя', 'Выраженная, с шлейфом', 'Мощная, на весь офис'] },
  { q: 'Ваш парфюмерный опыт?', opts: ['Новичок', 'Есть любимые ароматы', 'Продвинутый', 'Эксперт / коллекционер'] },
  { q: 'Какие ноты вам нравятся?', opts: ['Цветочные', 'Фруктовые', 'Древесные', 'Восточные / пряные'], multi: true },
  { q: 'А какие не переносите?', opts: ['Сладкие / приторные', 'Табачные / кожаные', 'Острые / пряные', 'Нет таких'], multi: true },
  { q: 'Предпочтительный сезон?', opts: ['Весна / Лето', 'Осень / Зима', 'Круглый год', 'Хочу под каждый сезон'] },
  { q: 'Готовы к экспериментам?', opts: ['Да, удивляйте!', 'Умеренно', 'Нет, классику', 'Только проверенное'] },
];

let qStep = 0;
let qAnswers = [];

function initQuestionnaire() {
  qStep = 0;
  qAnswers = [];
  renderQuestion();
}

function renderQuestion() {
  const prog = document.getElementById('q-progress');
  prog.innerHTML = questions.map((_, i) => 
    `<div class="q-dot ${i < qStep ? 'done' : i === qStep ? 'current' : ''}"></div>`
  ).join('');
  
  const content = document.getElementById('q-content');
  if (qStep >= questions.length) {
    content.innerHTML = `
      <div style="text-align:center;padding:40px 0">
        <div style="font-size:60px;margin-bottom:16px">✨</div>
        <div style="font-family:'Cormorant Garamond',serif;font-size:28px;font-weight:600;margin-bottom:8px">Готово!</div>
        <div style="font-size:14px;color:var(--text-secondary);line-height:1.5;margin-bottom:24px">Ваш ольфакторный портрет обновлён.<br>Мы подберём идеальные ароматы для вас.</div>
        <button class="cta-btn" onclick="navigateTo('profile')">Перейти в профиль</button>
      </div>`;
    return;
  }
  
  const q = questions[qStep];
  content.innerHTML = `
    <div class="q-question">${q.q}</div>
    <div class="q-options">
      ${q.opts.map((opt, i) => `
        <div class="q-option" onclick="selectQOption(this, ${i}, ${!!q.multi})">
          <div class="q-option-check"></div>
          ${opt}
        </div>
      `).join('')}
    </div>
    <button class="q-next" onclick="nextQuestion()" id="q-next-btn">Далее →</button>
  `;
}

let selectedQOptions = [];

function selectQOption(el, idx, multi) {
  if (multi) {
    el.classList.toggle('selected');
    if (el.classList.contains('selected')) {
      selectedQOptions.push(idx);
    } else {
      selectedQOptions = selectedQOptions.filter(i => i !== idx);
    }
  } else {
    document.querySelectorAll('.q-option').forEach(o => o.classList.remove('selected'));
    el.classList.add('selected');
    selectedQOptions = [idx];
  }
  document.getElementById('q-next-btn').classList.toggle('ready', selectedQOptions.length > 0);
}

function nextQuestion() {
  if (selectedQOptions.length === 0) return;
  qAnswers.push([...selectedQOptions]);
  selectedQOptions = [];
  qStep++;
  renderQuestion();
}

// === CHAT ===
function sendChat() {
  const input = document.getElementById('chat-input');
  const text = input.value.trim();
  if (!text) return;
  
  const msgs = document.getElementById('chat-messages');
  const now = new Date();
  const time = now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0');
  
  msgs.innerHTML += `<div class="chat-msg user">${text}<div class="chat-msg-time">${time}</div></div>`;
  input.value = '';
  msgs.scrollTop = msgs.scrollHeight;
  
  // Simulate reply
  setTimeout(() => {
    msgs.innerHTML += `<div class="chat-msg admin">Спасибо за сообщение! Парфюмер ответит в ближайшее время 💐<div class="chat-msg-time">${time}</div></div>`;
    msgs.scrollTop = msgs.scrollHeight;
  }, 1200);
}

document.getElementById('chat-input')?.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') sendChat();
});

// === COPY REFERRAL ===
function copyRef(btn) {
  const link = 't.me/dararomabox_bot?start=ref_anna2026';
  navigator.clipboard?.writeText(link).then(() => {
    btn.textContent = '✓';
    setTimeout(() => btn.textContent = 'Копировать', 2000);
  });
}

// === INIT ===
document.addEventListener('DOMContentLoaded', () => {
  // Stagger menu cards
  document.querySelectorAll('.menu-card').forEach((card, i) => {
    card.style.animation = `fadeUp 0.5s ${0.1 + i * 0.06}s cubic-bezier(0.22,1,0.36,1) both`;
  });
});
</script>

</body>
</html>
