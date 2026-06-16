// update-standings.mjs
// ---------------------------------------------------------------------------
// Pushes championship standings into Ghost so the theme's standings widget can
// read them (the widget reads a #standings-<series> post's `#standings-data`
// code-injection block via the Content API).
//
// This is the "rewrite the PHP in JS" piece — it runs OUTSIDE Ghost (cron /
// GitHub Action / your VPS) and writes into Ghost via the Admin API.
//
// SETUP
//   1. In Ghost Admin → Settings → Integrations → Add custom integration.
//      Copy the Admin API Key (looks like "id:secret") and the API URL.
//   2. npm i @tryghost/admin-api
//   3. Set env vars:  GHOST_ADMIN_API_URL, GHOST_ADMIN_API_KEY
//   4. Create one post per series with internal tag #standings-supercars /
//      #standings-f1 (see DATA-WIDGETS.md). This script updates that post.
//   5. Run:  node automation/update-standings.mjs
//      (schedule it after each race weekend)
// ---------------------------------------------------------------------------

import GhostAdminAPI from '@tryghost/admin-api';

const GHOST_URL = process.env.GHOST_ADMIN_API_URL;   // e.g. https://news.speedcafe.com
const GHOST_KEY = process.env.GHOST_ADMIN_API_KEY;   // e.g. 64f...:9a3...

if (!GHOST_URL || !GHOST_KEY) {
    console.error('Set GHOST_ADMIN_API_URL and GHOST_ADMIN_API_KEY environment variables.');
    process.exit(1);
}

const api = new GhostAdminAPI({ url: GHOST_URL, key: GHOST_KEY, version: 'v5.0' });

// Which series to publish, and the human title shown above each table.
const SERIES = [
    { key: 'supercars', title: '2026 Supercars Championship' },
    { key: 'f1',        title: '2026 Formula 1 Championship' },
];

// ---------------------------------------------------------------------------
// TODO: replace this with your real results feed.
// Return an array of rows. Recognised keys (alternatives in DATA-WIDGETS.md):
//   place, driver, team, car_number, wins, poles, points, car_num_bg
// ---------------------------------------------------------------------------
async function fetchStandings(seriesKey) {
    // Example shape — wire this up to your timing/results provider:
    // const res = await fetch(`https://your-results-feed/${seriesKey}.json`);
    // return (await res.json()).rows;
    throw new Error(`fetchStandings("${seriesKey}") not implemented — plug in your results feed.`);
}

function buildInjection(payload) {
    // Pretty-print so it's still readable if someone opens the post in Ghost.
    const json = JSON.stringify(payload, null, 2);
    return `<script id="standings-data" type="application/json">\n${json}\n</script>`;
}

async function updateSeries({ key, title }) {
    const standings = await fetchStandings(key);
    if (!Array.isArray(standings) || standings.length === 0) {
        console.warn(`[${key}] no rows returned — skipping.`);
        return;
    }

    const tag = `#standings-${key}`;
    const [post] = await api.posts.browse({ filter: `tag:hash-standings-${key}`, limit: 1 });
    if (!post) {
        console.error(`[${key}] no post found with internal tag ${tag}. Create one first (see DATA-WIDGETS.md).`);
        return;
    }

    const codeinjection_head = buildInjection({ title, standings });

    await api.posts.edit({
        id: post.id,
        updated_at: post.updated_at, // required by the Admin API for collision detection
        codeinjection_head,
    });

    console.log(`[${key}] updated "${post.title}" with ${standings.length} rows.`);
}

for (const series of SERIES) {
    try {
        await updateSeries(series);
    } catch (err) {
        console.error(`[${series.key}] failed:`, err.message);
    }
}
