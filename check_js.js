const fs = require('fs');
const c = fs.readFileSync('G:/My Drive/Projects/_studio/sidebar-agent.html','utf8');
// Extract the main JS block (last script tag before </body>)
const scripts = [...c.matchAll(/<script>([\s\S]*?)<\/script>/g)];
const mainJS = scripts[scripts.length-1][1];
try {
  new Function(mainJS);
  console.log('SYNTAX OK - JS is valid');
} catch(e) {
  console.log('SYNTAX ERROR: ' + e.message);
}
