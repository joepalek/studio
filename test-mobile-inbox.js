// Mobile Inbox End-to-End Test
// Run in Claude Code: node test-mobile-inbox.js

const SUPABASE_URL = 'https://nepnytazalthnjqpyzcx.supabase.co';
const SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5lcG55dGF6YWx0aG5qcXB5emN4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM3OTU4MDIsImV4cCI6MjA4OTM3MTgwMn0.ojPrZ51Jei32zdL2ORJ4SOVlopfv-9mZDj-U5sDz7rw';

async function test() {
  console.log('=== MOBILE INBOX END-TO-END TEST ===\n');

  // Test 1 — Write a test answer to Supabase
  console.log('Test 1: Writing test answer to Supabase...');
  const testPayload = {
    session_id: 'test_' + Date.now(),
    answers: {
      'test-question-001': 'Canvas overlay on video element',
      'test-question-002': 'Yes proceed with current approach'
    },
    total_answered: 2
  };

  try {
    const writeRes = await fetch(`${SUPABASE_URL}/rest/v1/mobile_answers`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'apikey': SUPABASE_KEY,
        'Authorization': 'Bearer ' + SUPABASE_KEY,
        'Prefer': 'return=minimal'
      },
      body: JSON.stringify(testPayload)
    });

    if (writeRes.ok) {
      console.log('  ✓ Write to Supabase: OK\n');
    } else {
      const err = await writeRes.text();
      console.log(`  ✗ Write failed: ${writeRes.status} — ${err}\n`);
      return;
    }
  } catch(e) {
    console.log(`  ✗ Write error: ${e.message}\n`);
    return;
  }

  // Test 2 — Read it back
  console.log('Test 2: Reading answers back from Supabase...');
  try {
    const readRes = await fetch(
      `${SUPABASE_URL}/rest/v1/mobile_answers?order=submitted_at.desc&limit=3`,
      {
        headers: {
          'apikey': SUPABASE_KEY,
          'Authorization': 'Bearer ' + SUPABASE_KEY
        }
      }
    );
    const rows = await readRes.json();
    if (rows && rows.length > 0) {
      console.log(`  ✓ Read from Supabase: ${rows.length} row(s) found`);
      console.log(`  Latest session: ${rows[0].session_id}`);
      console.log(`  Answers count: ${rows[0].total_answered}`);
      console.log(`  Submitted: ${rows[0].submitted_at}\n`);
    } else {
      console.log('  ✗ No rows returned\n');
    }
  } catch(e) {
    console.log(`  ✗ Read error: ${e.message}\n`);
  }

  // Test 3 — Check mobile-inbox.json is readable
  console.log('Test 3: Checking mobile-inbox.json...');
  const fs = require('fs');
  const inboxPath = 'G:/My Drive/Projects/_studio/mobile-inbox.json';
  if (fs.existsSync(inboxPath)) {
    try {
      const data = JSON.parse(fs.readFileSync(inboxPath, 'utf8'));
      console.log(`  ✓ mobile-inbox.json: ${Array.isArray(data) ? data.length : 0} questions\n`);
    } catch(e) {
      console.log(`  ✗ Parse error: ${e.message}\n`);
    }
  } else {
    console.log('  ~ mobile-inbox.json not found — will be created on next studio Refresh\n');
  }

  // Test 4 — Check studio can read Supabase answers (importMobileAnswers simulation)
  console.log('Test 4: Simulating studio importMobileAnswers...');
  try {
    const readRes = await fetch(
      `${SUPABASE_URL}/rest/v1/mobile_answers?order=submitted_at.desc&limit=10`,
      {
        headers: {
          'apikey': SUPABASE_KEY,
          'Authorization': 'Bearer ' + SUPABASE_KEY
        }
      }
    );
    const rows = await readRes.json();
    const pending = rows.filter(r => !r.applied);
    console.log(`  ✓ Supabase readable from Node: ${rows.length} total rows`);
    console.log(`  Pending (unapplied): ${pending.length} sessions`);

    if (pending.length > 0) {
      let totalAnswers = 0;
      pending.forEach(r => {
        const answers = r.answers || {};
        totalAnswers += Object.keys(answers).length;
      });
      console.log(`  Total answers waiting to apply: ${totalAnswers}`);
    }
    console.log();
  } catch(e) {
    console.log(`  ✗ Error: ${e.message}\n`);
  }

  console.log('=== TEST COMPLETE ===');
  console.log('');
  console.log('To apply pending mobile answers in studio:');
  console.log('  1. Open studio.html in browser');
  console.log('  2. Connect Drive');
  console.log('  3. Hit Refresh — importMobileAnswers() runs automatically');
  console.log('  4. Check inbox for answered items');
  console.log('');
  console.log('To verify mobile app loads questions:');
  console.log('  Open: https://joepalek.github.io/studio/mobile-inbox.html');
  console.log('  Questions should load from embedded array in the HTML');
}

test().catch(console.error);
