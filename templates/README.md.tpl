<div align="center">

[![My Skills](https://skillicons.dev/icons?i=python,java,cpp,rust,ruby,js,html,css&theme=dark&perline=8)](https://skillicons.dev)
[![My Tools](https://skillicons.dev/icons?i=spring,react,nodejs,docker,git,github,githubactions,linux,bash,vscode&theme=dark&perline=10)](https://skillicons.dev)

</div>

---

<div align="center">

<img src="metrics.general.svg" width="49%" alt="GitHub Stats" />
<img src="https://streak-stats.demolab.com/?user=jguida941&theme=tokyonight&hide_border=true&background=1a1b27&ring=7AA2F7&fire=ff9e64&currStreakNum=7AA2F7&sideNums=7AA2F7&currStreakLabel=7AA2F7&sideLabels=a9b1d6&dates=565f89" width="49%" alt="GitHub Streak" />

</div>

<div align="center">

<img src="metrics.languages.svg" width="49%" alt="Top Languages" />

</div>

---

### By The Numbers

<div align="center">

<!-- REPO_HEALTH -->

</div>

---

<div align="center">

<img src="metrics.isocalendar.svg" alt="Contribution Calendar" />

</div>

<div align="center">

<img src="metrics.habits.svg" alt="Coding Habits" />

</div>

---

<!-- CUSTOM_STATS -->

### Recently Created

<!-- RECENT_REPOS -->

### Latest Activity

| Repository | Last Contributed |
|------------|-----------------|
{{- range recentContributions 10}}
| [**{{.Repo.Name}}**]({{.Repo.URL}}) | {{humanize .OccurredAt}} |
{{- end}}

### Recent Releases

| Repository | Version | Released |
|------------|---------|----------|
{{- range recentReleases 5}}
| [**{{.Name}}**]({{.URL}}) | [`{{.LastRelease.TagName}}`]({{.LastRelease.URL}}) | {{humanize .LastRelease.PublishedAt}} |
{{- end}}

### Recent Pull Requests

| PR | Repository | Status | Opened |
|----|------------|--------|--------|
{{- range recentPullRequests 5}}
| [{{.Title}}]({{.URL}}) | [**{{.Repo.Name}}**]({{.Repo.URL}}) | `{{.State}}` | {{humanize .CreatedAt}} |
{{- end}}
