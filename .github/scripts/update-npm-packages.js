const fs = require('fs');
const https = require('https');

const username = process.env.NPM_USERNAME || 'aks-builds';

function fetchJson(url) {
  return new Promise((resolve, reject) => {
    https.get(url, { headers: { 'User-Agent': 'github-actions/update-npm-packages' } }, (res) => {
      let data = '';
      res.on('data', chunk => (data += chunk));
      res.on('end', () => {
        try { resolve(JSON.parse(data)); }
        catch (e) { reject(new Error(`Failed to parse JSON from ${url}: ${e.message}`)); }
      });
    }).on('error', reject);
  });
}

function encodeTypingLine(text) {
  return encodeURIComponent(text).replace(/%20/g, '+');
}

async function main() {
  const data = await fetchJson(
    `https://registry.npmjs.org/-/v1/search?text=maintainer:${username}&size=50`
  );

  const packages = data.objects
    .map(obj => obj.package)
    .sort((a, b) => a.name.localeCompare(b.name));

  if (packages.length === 0) {
    console.log('No npm packages found for maintainer:', username);
    return;
  }

  // Typing SVG that cycles through each package name
  const lines = packages
    .map(p => encodeTypingLine(`📦 ${p.name}`))
    .join(';');

  const typingSvg =
    `https://readme-typing-svg.demolab.com?font=Fira+Code&weight=500&size=17` +
    `&pause=1200&color=CB3837&center=true&vCenter=true&width=620&lines=${lines}`;

  // Two adjacent badges per package:
  //   left  (dark, npm logo + name)  → GitHub repo
  //   right (red, version)           → npmjs.com page
  const badges = packages
    .map(p => {
      const repoUrl = (p.links && p.links.repository)
        || `https://github.com/${username}/${p.name}`;
      const npmUrl = `https://www.npmjs.com/package/${p.name}`;

      // Name badge — label=empty collapses the left sliver; message=name; logo on left
      const nameBadge =
        `https://img.shields.io/static/v1?label=&message=${encodeURIComponent(p.name)}` +
        `&style=flat-square&color=1a1a2e&logo=npm&logoColor=white&labelColor=1a1a2e`;

      // Version badge — label=empty hides left sliver; right side = version in red
      const versionBadge =
        `https://img.shields.io/npm/v/${p.name}?style=flat-square&color=CB3837&label=`;

      // No whitespace between </a><a> so the two images render flush/joined
      return (
        `  <a href="${repoUrl}"><img src="${nameBadge}" alt="${p.name}"/></a>` +
        `<a href="${npmUrl}"><img src="${versionBadge}" alt="${p.name} version"/></a>`
      );
    })
    .join('\n');

  const section =
    `<div align="center">\n\n` +
    `<img src="${typingSvg}" alt="npm packages"/>\n\n` +
    `<br/>\n\n` +
    `${badges}\n\n` +
    `</div>`;

  const readme = fs.readFileSync('README.md', 'utf-8');
  const start = '<!--START_SECTION:npm-packages-->';
  const end = '<!--END_SECTION:npm-packages-->';
  const pattern = new RegExp(`${start}[\\s\\S]*?${end}`);

  if (!readme.includes(start)) {
    console.error('Markers not found in README.md — add <!--START_SECTION:npm-packages--> and <!--END_SECTION:npm-packages-->');
    process.exit(1);
  }

  const updated = readme.replace(pattern, `${start}\n${section}\n${end}`);
  fs.writeFileSync('README.md', updated, 'utf-8');
  console.log(`Updated README.md with ${packages.length} npm package(s).`);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
