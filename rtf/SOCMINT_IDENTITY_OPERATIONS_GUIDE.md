# SOCMINT / Identity Investigation Operations Guide v2.0

## Pipeline Stages

### Stage A — Seed & Baseline
Input one or more seeds: username, email, full name, phone, domain.

### Stage B — Username Sweep (14+ tools)
sherlock, maigret, nexfil, blackbird, socialscan, whatsmyname, social-analyzer,
checkusernames, namechk, snoop, username-anarchy, osrframework, seekr, profil3r,
peekyou-cli, usersearch, sherlock-project

### Stage C — Email Pivot & Breach (9 tools)
holehe, h8mail, emailrep, ignorant, dehashed-cli, breach-parse, emailfinder,
haveibeenpwned, h8mail (local breach)

### Stage D — Social Media Deep Dive (9 tools)
instaloader, toutatis, twint, tinfoleak, socid-extractor, osintgram,
twscrape, snscrape, reddit-user-analyser

### Stage E — Domain & Name Intelligence (20+ tools)
theHarvester, spiderfoot, metagoofil, dnstwist, linkedin2username, crosslinked,
photon, recon-ng, sublist3r, subfinder, gau, waybackurls, amass, dnsdumpster,
spyonweb, onyphe, netlas, fullhunt, zoomeye, shodan, censys, urlscan, wigle

### Stage F — Code/Secrets Forensics (7 tools)
gitfive, octosuite, trufflehog, gitleaks, gitrecon, gharchive, intelowl

### Stage G — Phone OSINT (2 tools)
phoneinfoga, email2phonenumber

### Stage H — Dark Web & Breach (4 tools)
intelx, pwndb-cli, dehashed, skymem

### Stage I — Geolocation/Metadata (22 tools)
creepy, waybackpack, ghunt, sn0int, buster, osintgram, exiftool, foca, maltego,
recon-ng, archivebox, phantombuster, harpoon, cybelangel, tineye, netlytic,
social-searcher, mentionmapp, clearbit, fullcontact, pipl, linky-lady, shlink, hunter, waymore

### Stage J — Claude AI Correlation
Automated analysis of all gathered entities using Claude claude-sonnet-4-20250514.
Produces: confidence score, identity summary, cross-platform connections,
anomalies, risk assessment, next investigative steps.

### Stage K — Multi-Format Report
JSON / CSV / XLSX / PDF / HTML with auto-fallback chain.

## Example Commands

```bash
# Core investigation (fast)
python rtf.py module run osint/identity_fusion \
  --options '{"username":"target","output_format":"json"}'

# Full aggressive with AI
python rtf.py module run osint/identity_fusion \
  --options '{"username":"target","email":"t@example.com","domain":"example.com","tool_profile":"aggressive","use_ai":true,"output_format":"html"}'

# Via workflow
python rtf.py workflow run identity_fusion \
  --options '{"username":"target","output_format":"xlsx"}'
```
