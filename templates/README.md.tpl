<div align="center">

[![My Skills](https://skillicons.dev/icons?i=python,java,cpp,rust,ruby,html&theme=dark&perline=6)](https://skillicons.dev)
[![My Tools](https://skillicons.dev/icons?i=spring,docker,git,github,githubactions,linux,bash,vscode&theme=dark&perline=8)](https://skillicons.dev)

</div>

---

<div align="center">

<img src="metrics.general.svg" width="49%" alt="GitHub Stats" />
<img src="https://streak-stats.demolab.com/?user={{ username }}&theme=tokyonight&hide_border=true&background=1a1b27&ring=7AA2F7&fire=ff9e64&currStreakNum=7AA2F7&sideNums=7AA2F7&currStreakLabel=7AA2F7&sideLabels=a9b1d6&dates=565f89" width="49%" alt="GitHub Streak" />

</div>

---

### Developer Quest

<div align="center">

<img src="assets/game_card.svg" alt="Developer Quest - RPG Game Card" />

</div>

---

### Play Developer Quest

<div align="center">

<a href="{{ game_url }}"><strong>Launch the playable mini-game</strong></a>

</div>

---

### By The Numbers

<div align="center">

<img src="assets/badges.svg" alt="Profile Badges" />

</div>

---

### Currently Working On

<div align="center">

<img src="assets/currently_working.svg" alt="Currently Working On" />

</div>

---

### Language Breakdown

<div align="center">

<img src="assets/lang_breakdown.svg" alt="Language Breakdown" />

</div>

---

### Contribution Calendar

<div align="center">

<img src="metrics.isocalendar.svg" alt="Contribution Calendar" />

</div>

---

### When I Code

<div align="center">

<img src="assets/activity_heatmap.svg" alt="Activity Heatmap" />

</div>

---

### Featured Projects

<div align="center">

<img src="assets/repo_spotlight.svg" alt="Featured Projects" />

</div>

---

### Recently Created

| Repository | Description | Language | Created |
|------------|-------------|----------|---------|
{%- for repo in recent_created %}
| [**{{ repo.name }}**]({{ repo.html_url }}) | {{ (repo.description or "n/a")[:80] | replace("|", ",") | replace("\n", " ") }} | `{{ repo.language or "n/a" }}` | {{ repo.created_at[:10] }} |
{%- endfor %}

### Latest Activity

| Repository | Last Contributed |
|------------|-----------------|
{%- for c in contributions %}
| [**{{ c.repo }}**]({{ c.url }}) | {{ c.time_ago }} |
{%- endfor %}

### Recent Releases

| Repository | Version | Released |
|------------|---------|----------|
{%- for r in releases %}
| [**{{ r.repo }}**]({{ r.repo_url }}) | [`{{ r.tag }}`]({{ r.url }}) | {{ r.time_ago }} |
{%- endfor %}

### Recent Pull Requests

| PR | Repository | Status | Opened |
|----|------------|--------|--------|
{%- for pr in pull_requests %}
| [{{ pr.title | replace("|", ",") | replace("\n", " ") }}]({{ pr.url }}) | [**{{ pr.repo }}**]({{ pr.repo_url }}) | `{{ pr.state }}` | {{ pr.time_ago }} |
{%- endfor %}
