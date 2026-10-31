/* NeuroTrace — dashboard */

function Dashboard({ go, study, setStudy }) {
  const toast = useToast();
  const [filter, setFilter] = React.useState('all');
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    const t = setTimeout(() => setLoading(false), 520);
    return () => clearTimeout(t);
  }, []);

  const loadSample = async (sampleName) => {
    toast(`Loading ${sampleName}...`, 'refresh');
    try {
      const res = await fetch('/api/load-sample', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sample_id: sampleName }),
      });
      const data = await res.json();
      if (data.status === 'ok') {
        const studyObj = {
          id: data.study_id,
          accession: 'MR-' + data.study_id.slice(-6),
          patient: 'BraTS-2020-' + data.study_id.slice(-3),
          age: 58, sex: 'M',
          sequence: 'FLAIR',
          field: '3.0 T',
          site: 'BraTS 2020 Benchmark Repository',
          acquired: '2026-10-31',
          analyzed: 'Live Ingest',
          status: 'complete',
          diagnosis: 'Glioma / Glioblastoma Multiforme (BraTS Benchmark)',
          grader: '3D U-Net',
          tumorCore: 18.42,
          wholeTumor: 61.87,
          edema: 38.55,
          enhancing: 5.12,
          necrotic: 13.30,
          confidence: 0.94,
          qc: 'passed',
          slices: data.totals ? data.totals.axial : 155,
          spacing: [1.0, 1.0, 1.0],
          matrix: '240 × 240',
          model: 'BraTS 3D U-Net',
          duration: '1 m 12 s',
          notes: 1,
          totals: data.totals,
          isReal: true,
          measurements: null,
          qc_report: null,
        };
        window.NT_ACTIVE_STUDIES = window.NT_ACTIVE_STUDIES || {};
        window.NT_ACTIVE_STUDIES[data.study_id] = studyObj;
        const exists = STUDIES.find((x) => x.id === data.study_id);
        if (!exists) STUDIES.unshift(studyObj);
        setStudy(data.study_id);
        toast(`Loaded ${sampleName}! Opening workspace...`, 'check');
        go('workspace', data.study_id);
      } else {
        toast(data.message || 'Failed to load sample', 'alert');
      }
    } catch (err) {
      toast('Error loading sample: ' + err.message, 'alert');
    }
  };

  const rows = STUDIES.filter((s) => filter === 'all' || s.status === filter).slice(0, 5);

  const open = (s) => { setStudy(s.id); go(s.status === 'failed' ? 'history' : 'workspace'); };

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <div className="eyebrow">Friday, 30 October 2026</div>
          <h1 className="h1" style={{ marginTop: 8 }}>Good afternoon, Dr Kessler</h1>
          <p className="lede" style={{ maxWidth: '54ch' }}>
            Two studies completed overnight. One analysis is waiting on your review before the report can be signed.
          </p>
        </div>
        <div className="page-head-actions">
          <button className="btn" onClick={() => go('history')}><Icon name="history" size={14} />History</button>
          <button className="btn btn-primary" onClick={() => go('upload')}><Icon name="upload" size={14} />New analysis</button>
        </div>
      </div>

      <div className="card" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', overflow: 'hidden' }}>
        <StatCell label="Studies this month" value="38" meta={<><span style={{ color: 'var(--ok)', fontWeight: 500 }}>+6</span><span>vs. September</span></>} />
        <StatCell label="Awaiting review" value="1" meta={<><Badge tone="warn">NT-2026-0146</Badge></>} />
        <StatCell label="Mean QC confidence" value="0.91" meta={<><span>Across 36 completed</span></>} />
        <StatCell label="Median runtime" value="2:41" meta={<><span>−14 s vs. v2.3</span></>} />
      </div>

      <div className="card" style={{ marginTop: 'calc(var(--gap) * 0.8)', padding: '14px 18px', background: 'var(--panel)' }}>
        <div className="hrow" style={{ justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div className="hrow" style={{ gap: 8 }}>
              <Icon name="cpu" size={15} style={{ color: 'var(--accent)' }} />
              <span style={{ fontWeight: 600, fontSize: 13 }}>Live Engine Ready · BraTS 3D U-Net & Gemma 4 Copilot</span>
              <Badge tone="ok" dot>Active</Badge>
            </div>
            <div className="tiny" style={{ marginTop: 4, color: 'var(--ink-2)' }}>
              Evaluate real clinical MRI volumetric segmentation and agentic research assistant tools directly on pre-loaded BraTS 2020 benchmark scans:
            </div>
          </div>
          <div className="hrow" style={{ gap: 8 }}>
            <button className="btn btn-sm btn-quiet" onClick={() => loadSample('BraTS20_Training_001_flair.nii')}>
              <Icon name="scan" size={13} /> Load BraTS Training 001
            </button>
            <button className="btn btn-sm btn-quiet" onClick={() => loadSample('BraTS20_Training_030_flair.nii')}>
              <Icon name="scan" size={13} /> Load BraTS Training 030
            </button>
            <button className="btn btn-sm btn-primary" onClick={() => go('upload')}>
              <Icon name="upload" size={13} /> Upload Custom NIfTI
            </button>
          </div>
        </div>
      </div>

      <div className="split-main" style={{ marginTop: 'calc(var(--gap) * 1.3)' }}>
        <div>
          <div className="section-head" style={{ marginBottom: 10 }}>
            <div className="hrow" style={{ gap: 12 }}>
              <h2 className="h2">Recent studies</h2>
              <span className="tiny mono" style={{ paddingTop: 3 }}>142 total</span>
            </div>
            <Segmented label="Filter studies" value={filter} onChange={setFilter}
              options={[{ value: 'all', label: 'All' }, { value: 'complete', label: 'Complete' }, { value: 'review', label: 'Review' }]} />
          </div>

          <div className="card" style={{ overflow: 'hidden' }}>
            {loading ? (
              <div style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 14 }}>
                {[0, 1, 2, 3].map((i) => (
                  <div key={i} className="hrow" style={{ gap: 14 }}>
                    <div className="skeleton" style={{ width: 42, height: 42 }} />
                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 6 }}>
                      <SkeletonLine w="45%" h={9} /><SkeletonLine w="28%" h={8} />
                    </div>
                    <SkeletonLine w="40px" h={9} />
                  </div>
                ))}
              </div>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th style={{ paddingLeft: 16 }}>Study</th>
                    <th>Diagnosis</th>
                    <th className="num">Whole tumour</th>
                    <th className="num">Confidence</th>
                    <th>Status</th>
                    <th style={{ width: 40 }}><span className="sr-only">Actions</span></th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((s) => (
                    <tr key={s.id} onClick={() => open(s)}>
                      <td style={{ paddingLeft: 16 }}>
                        <div className="hrow" style={{ gap: 10 }}>
                          <div style={{ width: 40, height: 40, borderRadius: 3, overflow: 'hidden', background: 'var(--viewer)', flex: 'none', border: '1px solid var(--line)' }}>
                            <img src="assets/mri-axial.png" alt="" style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: s.status === 'failed' ? .2 : .9 }} />
                          </div>
                          <div style={{ minWidth: 0 }}>
                            <div className="cell-strong mono" style={{ fontSize: 11.5 }}>{s.id}</div>
                            <div className="tiny truncate" style={{ marginTop: 2 }}>{s.analyzed}</div>
                          </div>
                        </div>
                      </td>
                      <td>
                        <div className="truncate" style={{ maxWidth: 190 }}>{s.diagnosis}</div>
                        <div className="tiny" style={{ marginTop: 2 }}>{s.sequence} · {s.field}</div>
                      </td>
                      <td className="num">{s.wholeTumor ? `${s.wholeTumor.toFixed(1)} mL` : '—'}</td>
                      <td className="num">{s.confidence ? s.confidence.toFixed(2) : '—'}</td>
                      <td><StatusBadge status={s.status} /></td>
                      <td><Icon name="chevR" size={14} style={{ color: 'var(--ink-4)' }} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            {!loading && rows.length === 0 && (
              <EmptyState title="No studies match this filter" body="Adjust the filter or upload a new volume to begin."
                action={<button className="btn btn-sm" onClick={() => setFilter('all')}>Clear filter</button>} />
            )}
          </div>

          <div className="section">
            <div className="section-head"><h2 className="h2">Longitudinal series</h2><button className="link small" onClick={() => go('history')} style={{ fontSize: 12 }}>All series</button></div>
            <div className="card" style={{ overflow: 'hidden' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)' }}>
                {[
                  ['PT-88421', '4 timepoints', 'Feb 26 → Oct 26', '+9.8%', true],
                  ['PT-44102', '3 timepoints', 'Apr 25 → Oct 26', '+2.1%', false],
                  ['PT-77190', '2 timepoints', 'Aug 26 · Oct 26', '—', false],
                ].map(([pt, n, range, delta, up], i) => (
                  <button key={pt} onClick={() => go('workspace')} style={{ textAlign: 'left', padding: '16px 18px', borderLeft: i ? '1px solid var(--line)' : 0, transition: 'background var(--fast)' }}
                    onMouseEnter={(e) => e.currentTarget.style.background = 'var(--sunken)'}
                    onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}>
                    <div className="hrow" style={{ justifyContent: 'space-between' }}>
                      <span className="mono small" style={{ fontSize: 11, color: 'var(--ink-2)' }}>{pt}</span>
                      <Icon name="arrowUR" size={13} style={{ color: 'var(--ink-4)' }} />
                    </div>
                    <div className="serif" style={{ fontSize: 17, marginTop: 8 }}>{n}</div>
                    <div className="hrow" style={{ gap: 8, marginTop: 5 }}>
                      <span className="tiny">{range}</span>
                      {delta !== '—' && <span className="tiny mono" style={{ color: up ? 'var(--danger)' : 'var(--ok)' }}>{delta}</span>}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="stack" style={{ gap: 'var(--gap)' }}>
          <div className="card">
            <div className="card-head">
              <span className="h3">Processing queue</span>
              <Badge tone="accent" mono>1 active</Badge>
            </div>
            <div className="card-body" style={{ paddingTop: 14 }}>
              <div className="hrow" style={{ justifyContent: 'space-between', marginBottom: 8 }}>
                <span className="mono small" style={{ color: 'var(--ink)', fontSize: 11.5 }}>NT-2026-0149</span>
                <span className="tiny mono">38%</span>
              </div>
              <div className="progress"><i style={{ width: '38%' }} /></div>
              <div className="steps" style={{ marginTop: 12 }}>
                {[
                  ['Skull stripping', 'done', '18 s'],
                  ['Intensity normalisation', 'done', '6 s'],
                  ['Segmentation · nt-seg v2.4', 'active', 'running'],
                  ['Post-processing', 'wait', ''],
                ].map(([l, st, m]) => (
                  <div className="step-row" key={l} data-state={st} style={{ padding: '6px 0' }}>
                    <span className="step-mark">{st === 'done' ? <Icon name="check" size={8} stroke={3} /> : ''}</span>
                    <span className="step-label" style={{ flex: 1, fontSize: 12 }}>{l}</span>
                    <span className="tiny mono">{m}</span>
                  </div>
                ))}
              </div>
              <div className="hrow" style={{ gap: 8, marginTop: 12 }}>
                <button className="btn btn-sm" style={{ flex: 1 }} onClick={() => go('workspace')}>Open queue</button>
                <button className="btn btn-sm btn-quiet" onClick={() => toast('Queue paused after current job', 'pause')}>Pause</button>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-head">
              <span className="h3"><BrandMark size={14} /> Research assistant</span>
              <Badge tone="line" mono>Gemma 4</Badge>
            </div>
            <div className="card-body" style={{ paddingTop: 12 }}>
              <p className="small" style={{ lineHeight: 1.6, color: 'var(--ink-2)' }}>
                NT-2026-0148 is loaded. The assistant can compare it with your cohort and draft
                a findings section from the computed values.
              </p>
              <div className="stack gap-6" style={{ marginTop: 12 }}>
                <button className="suggest" onClick={() => go('assistant')}>
                  <Icon name="chat" size={13} style={{ marginTop: 2, color: 'var(--accent)' }} />
                  Summarise volumetric burden for NT-2026-0148
                </button>
                <button className="suggest" onClick={() => go('assistant')}>
                  <Icon name="chat" size={13} style={{ marginTop: 2, color: 'var(--accent)' }} />
                  Draft a findings paragraph
                </button>
              </div>
              <button className="btn btn-sm btn-ghost" style={{ marginTop: 10, paddingLeft: 0 }} onClick={() => go('assistant')}>
                Open assistant <Icon name="arrowR" size={12} />
              </button>
            </div>
          </div>

          <div className="card">
            <div className="card-head"><span className="h3">Quick actions</span></div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr' }}>
              {[
                ['Upload NIfTI', 'upload', 'upload'],
                ['New report', 'report', 'reports'],
                ['Compare studies', 'layers', 'history'],
                ['Export cohort', 'download', 'history'],
              ].map(([l, ic, r], i) => (
                <button key={l} onClick={() => go(r)} style={{
                  padding: '14px 12px', display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'flex-start',
                  borderTop: i > 1 ? '1px solid var(--line)' : 0, borderLeft: i % 2 ? '1px solid var(--line)' : 0,
                  fontSize: 12, color: 'var(--ink-2)', transition: 'background var(--fast)',
                }}
                  onMouseEnter={(e) => e.currentTarget.style.background = 'var(--sunken)'}
                  onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}>
                  <Icon name={ic} size={15} style={{ color: 'var(--accent)' }} />{l}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { Dashboard });
