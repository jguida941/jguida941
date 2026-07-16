"""reference_intake — the universal reference-capture ENGINE (W6).

The product spine: point at ANY served page and (1) CAPTURE it (acquire -> localize -> freeze ->
serve, with a URL security boundary and BACKUP-BEFORE-TRANSFORM restore points), (2) MEASURE
every aspect of it (the generic foreign-DOM rendered-facts probe: computed-style vector + DOM
structure + reachable pseudo-states, no dependence on the site's own hydration sentinels), and
(3) CONTRACT it against the closed reference-lane schemas + the 31-id aspect vocabulary.

  capture.py   W6-C  acquire/localize/freeze/serve_frozen/build_candidate_record
  security.py  W6-C  assert_capture_allowed (public http(s) only; SSRF/redirect denial)
  restore.py   W6-C  snapshot_target / guarded_transform (fail-closed backup-before-transform)
  probe_generic.py  W6-P  measure_page -> the full aspect vector for a served URL
  schema.py    W6-K  the §8 reference-lane record validators + the 31-id vocabulary cover
"""
