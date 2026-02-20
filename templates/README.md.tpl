<div align="center">

[![My Skills](https://skillicons.dev/icons?i=python,java,cpp,rust,ruby,js,html,css&theme=dark&perline=8)](https://skillicons.dev)
[![My Tools](https://skillicons.dev/icons?i=spring,react,nodejs,docker,git,github,githubactions,linux,bash,vscode&theme=dark&perline=10)](https://skillicons.dev)

</div>

---

<div align="center">

<img src="https://github-readme-stats.vercel.app/api?username=jguida941&show_icons=true&theme=tokyonight&hide_border=true&bg_color=1a1b27&title_color=7AA2F7&icon_color=7AA2F7&text_color=a9b1d6&rank_icon=percentile" width="49%" alt="GitHub Stats" />
<img src="https://streak-stats.demolab.com/?user=jguida941&theme=tokyonight&hide_border=true&background=1a1b27&ring=7AA2F7&fire=ff9e64&currStreakNum=7AA2F7&sideNums=7AA2F7&currStreakLabel=7AA2F7&sideLabels=a9b1d6&dates=565f89" width="49%" alt="GitHub Streak" />

</div>

<div align="center">

<img src="https://github-readme-stats.vercel.app/api/top-langs/?username=jguida941&layout=donut&theme=tokyonight&hide_border=true&bg_color=1a1b27&title_color=7AA2F7&text_color=a9b1d6&langs_count=8" width="35%" alt="Top Languages" />

</div>

---

### Recently Created
{{range recentRepos 5}}
- [**{{.Name}}**]({{.URL}}){{if .Description}} — {{.Description}}{{end}}{{if .PrimaryLanguage}} `{{.PrimaryLanguage.Name}}`{{end}}
{{- end}}

### Latest Activity
{{range recentContributions 10}}
- [**{{.Repo.Name}}**]({{.Repo.URL}}){{if .Repo.Description}} — {{.Repo.Description}}{{end}} ({{humanize .OccurredAt}})
{{- end}}

### Recent Releases
{{range recentReleases 5}}
- [**{{.Name}}**]({{.URL}}) — [`{{.LastRelease.TagName}}`]({{.LastRelease.URL}}) ({{humanize .LastRelease.PublishedAt}})
{{- end}}

### Recent Pull Requests
{{range recentPullRequests 5}}
- [{{.Title}}]({{.URL}}) on [**{{.Repo.Name}}**]({{.Repo.URL}}) · `{{.State}}` ({{humanize .CreatedAt}})
{{- end}}
