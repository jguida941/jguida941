<div align="center">

[![My Skills](https://skillicons.dev/icons?i=python,java,cpp,rust,ruby,html&theme=dark&perline=6)](https://skillicons.dev)
[![My Tools](https://skillicons.dev/icons?i=spring,docker,git,github,githubactions,linux,bash,vscode&theme=dark&perline=8)](https://skillicons.dev)

</div>

<a href="{{ dashboard_url }}?from_snapshot={{ cache_bust }}#overview">
<picture>
  <source media="(max-width: 767px)" srcset="assets/dashboard_summary_mobile.svg?v={{ cache_bust }}">
  <img src="assets/dashboard_summary.svg?v={{ cache_bust }}" width="100%" alt="GitHub profile analytics: contributions, workflow configuration, language composition, recent repositories and projects. Exact values and definitions below.">
</picture>
</a>

[Weekly trend]({{ dashboard_url }}?from_snapshot={{ cache_bust }}#weekly-contributions) · [Calendar]({{ dashboard_url }}?from_snapshot={{ cache_bust }}#calendar-panel) · [Weekday totals]({{ dashboard_url }}?from_snapshot={{ cache_bust }}#rhythm-panel) · [Languages]({{ dashboard_url }}?from_snapshot={{ cache_bust }}#languages) · [Workflow configuration]({{ dashboard_url }}?from_snapshot={{ cache_bust }}#automation)

<details>
<summary>Read the numbers and definitions</summary>

Reported inventory means its completeness and freshness are unverified. Repository push dates and reported headlines are independent observations, with no inferred branch or delivery status. Snapshot {{ dashboard_summary.generated_at | e }}.

| Metric | Value | Population / period | Qualification |
| --- | ---: | --- | --- |
{% for fact in dashboard_summary.facts %}| {{ fact.label | e }} | {{ fact.display_value | e }} | {{ fact.population_id | replace('-', ' ') | e }}; {{ fact.window | e }} | {{ fact.quality.qualification | e }}{% if fact.range_start is defined and fact.range_start %}; {{ fact.range_start }} – {{ fact.range_end }}{% endif %} |
{% endfor %}

{{ dashboard_summary.automation.display.scope | e }} {{ dashboard_summary.automation.display.meaning | e }}

| Workflow population | Configured repositories | Eligible repositories | Workflow files | Observation |
| --- | ---: | ---: | ---: | --- |
{% for key in ['public','private','combined'] %}{% set row = dashboard_summary.automation.display[key] %}| {{ key | title }} | {{ row.configured_repos }} | {{ row.eligible_repos }} | {{ row.workflow_files }} | {{ row.qualification | e }} |
{% endfor %}

| Observed UTC dates | Weekly contributions | Week |
| --- | ---: | --- |
{% if dashboard_summary.weekly.display.available %}{% for row in dashboard_summary.weekly.model.points %}| {{ row.observed_start }} – {{ row.observed_end }} | {{ '{:,}'.format(row.contributions) }} | {{ 'Partial' if row.partial else 'Complete' }} |
{% endfor %}{% else %}Contribution trend unavailable.
{% endif %}

{{ dashboard_summary.rhythm.display.scope | e }} {{ dashboard_summary.rhythm.display.explanation | e }}

| Weekday | Contributions | Observed dates |
| --- | ---: | ---: |
{% for row in dashboard_summary.rhythm.display.rows %}| {{ row.weekday }} | {{ row.count_text }} | {{ row.days_observed }} |
{% endfor %}

| Language | Observed bytes | Share |
| --- | ---: | ---: |
{% for row in dashboard_summary.languages.all_rows %}| {{ row.name | e }} | {{ '{:,}'.format(row.bytes) }} | {{ row.display_value }} |
{% endfor %}

<details><summary>Daily calendar values</summary>

| UTC date | Contributions |
| --- | ---: |
{% for row in dashboard_summary.calendar.days %}| {{ row.date }} | {{ '{:,}'.format(row.count) }} |
{% endfor %}

</details>
</details>

<details>
<summary>Repository details and project links</summary>

{% for row in dashboard_summary.working %}- {% if row.url %}[{{ row.name | e }}]({{ row.url | e }}){% else %}{{ row.name | e }}{% endif %} — {{ row.language | default('Language unreported', true) | e }}; {{ 'private' if row.is_private else 'public' }}; repository pushed {{ row.pushed_at | e }}. {% if row.last_commit_msg is defined %}Reported headline: {{ row.last_commit_msg | e }}.{% endif %}
{% endfor %}

{% for row in dashboard_summary.projects %}- {% if row.url %}[{{ row.name | e }}]({{ row.url | e }}){% else %}{{ row.name | e }}{% endif %}: {{ row.description | default('') | e }} {{ row.language | default('Language unreported', true) | e }}; {{ row.stars | default('n/a') }} stars; {{ row.forks | default('n/a') }} forks.
{% endfor %}

{% for key,label in [('now','Now'),('next','Next'),('updates','Recent Updates')] %}{{ label }}:
{% for row in dashboard_summary.focus[key] %}- {% if row.url %}[{{ row.title | e }}]({{ row.url | e }}){% else %}{{ row.title | e }}{% endif %} — {{ row.detail | default('') | e }}
{% else %}- No planned item supplied.
{% endfor %}{% endfor %}

Recently created:
{% for row in dashboard_summary.recent_created %}- {{ row.name | e }} — {{ row.created_at | default('Date unavailable') | e }}
{% else %}- No recent creations observed.
{% endfor %}

</details>

<details>
<summary>Legacy visual detail</summary>

These compatibility images retain their existing presentation.

<img src="assets/raw_snapshot.svg?v={{ cache_bust }}" width="100%" alt="Raw Snapshot: the generated profile metric values and their qualifications.">

{% for label,path in legacy_visuals %}- [{{ label }}]({{ path }}?v={{ cache_bust }})
{% endfor %}

</details>

### Deep Dive Data

- [Open the full dashboard]({{ dashboard_url }}?from_snapshot={{ cache_bust }}#overview)
- [Open raw profile snapshot JSON](site/data/profile_snapshot.json)
- Generated by `python scripts/profile_cli.py generate-profile --validate` {{ generation_provenance }}
- A curated project matrix, recent delivery feed, top-language summary, and recent repository list are available in the dashboard + JSON.
