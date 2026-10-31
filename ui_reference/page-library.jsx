/* NeuroTrace — reports, history, settings */

function Reports({ study, go }) {
  const baseStudy = STUDIES.find((x) => x.id === study) || CURRENT;
  const activeStudy = (study && window.NT_ACTIVE_STUDIES && window.NT_ACTIVE_STUDIES[study]) || (baseStudy && baseStudy.isReal ? baseStudy : null);
  const s = activeStudy || baseStudy;
  const isReal = !!(s && s.isReal);
  const toast = useToast();
  const [sections, setSections] = React.useState({ findings: true, method: true, limitations: true, figures: true });
  const [version, setVersion] = React.useState('v3');

  return (
    <div className="page" style={{ maxWidth: 1320 }}>
      <div className="page-head no-print">
        <div>
          <div className="eyebrow">Research reports</div>
          <h1 className="h1" style={{ marginTop: 8 }}>Report preview</h1>
          <p className="lede">A publication-shaped artefact built from the accepted mask. Every figure is regenerated from the study, not screenshotted.</p>
        </div>
        <div className="page-head-actions">
          <a className="btn btn-primary" href={`/api/report/${s.id}`} download={`NeuroTrace_Report_${s.id}.pdf`} style={{ textDecoration: 'none' }}>
            <Icon name="download" size={14} />Download Signed PDF Report
          </a>
          <button className="btn" onClick={() => window.print()}><Icon name="report" size={14} />Browser Print</button>
          <button className="btn btn-quiet" onClick={() => toast('Link copied — expires in 7 days', 'link')}><Icon name="share" size={14} />Share</button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) 268px', gap: 26, alignItems: 'start' }}>
        <div className="report-page">
          <div className="report-head">
            <div>
              <div className="hrow" style={{ gap: 8, marginBottom: 8 }}>
                <BrandMark size={17} />
                <span className="serif" style={{ fontSize: 14 }}>NeuroTrace</span>
                <span className="tiny mono" style={{ marginLeft: 4 }}>Research report</span>
              </div>
              <h1 className="serif" style={{ fontSize: 27, fontWeight: 400, letterSpacing: '-.015em', lineHeight: 1.16, maxWidth: '22ch' }}>
                Segmentation and volumetric analysis of a left frontal mass
              </h1>
            </div>
            <div style={{ textAlign: 'right', flex: 'none' }}>
              <div className="mono" style={{ fontSize: 10.5, letterSpacing: '.06em' }}>{s.id}</div>
              <div className="tiny mono" style={{ marginTop: 3 }}>{version} · draft</div>
              <div className="tiny mono">30 Oct 2026</div>
            </div>
          </div>

          <dl className="report-meta">
            {[
              ['Patient', s.patient], ['Age / sex', `${s.age} / ${s.sex}`], ['Accession', s.accession], ['Field strength', s.field],
              ['Sequence', s.sequence], ['Matrix', s.matrix], ['Voxel size', '1.0 mm³'], ['Model', s.model],
            ].map(([k, v]) => (
              <div key={k}><dt>{k}</dt><dd className="mono" style={{ fontSize: 11 }}>{v}</dd></div>
            ))}
          </dl>

          {sections.findings && (
            <section className="report-sec">
              <h3>Findings</h3>
              <p>
                A left frontal mass was segmented at a whole-tumour volume of <strong>{s.wholeTumor.toFixed(2)} mL</strong>,
                comprising a {s.tumorCore.toFixed(2)} mL tumour core ({s.necrotic.toFixed(2)} mL necrotic,
                {' '}{s.enhancing.toFixed(2)} mL enhancing) and {s.edema.toFixed(2)} mL of peritumoral edema.
                Maximum axial diameter measured 42.6 mm on the long axis, with the centroid 24.8 mm from the midline
                and 12.3 mm from the left lateral ventricle.
              </p>
              <p style={{ marginTop: 8 }}>
                Corticomedullary differentiation is preserved in the contralateral hemisphere. The ventricular
                system is not displaced. No midline shift was measured. Enhancing fraction of the tumour core
                is 27.8 %, at the 41st percentile of the reference cohort at comparable volume.
              </p>
            </section>
          )}

          {sections.figures && (
            <section className="report-sec">
              <h3>Figures</h3>
              <div className="fig-grid">
                {[
                  ['Axial · SL ' + (isReal ? String(Math.floor((s.totals ? s.totals.axial : 155) / 2)).padStart(3, '0') : '092'), isReal ? `/api/slice/${s.id}/axial/${Math.floor((s.totals ? s.totals.axial : 155) / 2)}?overlay=1&opacity=0.7&mode=contour` : 'assets/mri-axial.png'],
                  ['Coronal · SL ' + (isReal ? String(Math.floor((s.totals ? s.totals.coronal : 240) / 2)).padStart(3, '0') : '085'), isReal ? `/api/slice/${s.id}/coronal/${Math.floor((s.totals ? s.totals.coronal : 240) / 2)}?overlay=1&opacity=0.7&mode=contour` : 'assets/mri-coronal.png'],
                  ['Sagittal · SL ' + (isReal ? String(Math.floor((s.totals ? s.totals.sagittal : 240) / 2)).padStart(3, '0') : '092'), isReal ? `/api/slice/${s.id}/sagittal/${Math.floor((s.totals ? s.totals.sagittal : 240) / 2)}?overlay=1&opacity=0.7&mode=contour` : 'assets/mri-sagittal.png'],
                ].map(([cap, src], i) => (
                  <figure className="fig" key={cap}>
                    <img src={src} alt={cap} />
                    {!isReal && (
                      <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ position: 'absolute', inset: 6, width: 'calc(100% - 12px)', height: 'calc(100% - 12px)' }} aria-hidden="true">
                        {i === 2
                          ? <ellipse cx="46.2" cy="30.6" rx="5.4" ry="4.6" fill="none" stroke="#8FD2C6" strokeWidth="1" vectorEffect="non-scaling-stroke" />
                          : <ellipse cx="33.5" cy={i === 0 ? 28.6 : 30.4} rx="8.3" ry="8.2" fill="none" stroke="#8FD2C6" strokeWidth="1" vectorEffect="non-scaling-stroke" />}
                      </svg>
                    )}
                    <figcaption>{cap}</figcaption>
                  </figure>
                ))}
              </div>
              <p className="tiny" style={{ marginTop: 8, color: 'var(--ink-3)' }}>
                <strong>Fig. 1–3.</strong> Orthogonal MRI slices with the predicted whole-tumour envelope
                overlaid in teal. Slice indices refer to the native acquisition.
              </p>
            </section>
          )}

          <section className="report-sec">
            <h3>Volumetric summary</h3>
            <table className="table" style={{ fontSize: 11.5 }}>
              <thead><tr><th>Region</th><th>Definition</th><th className="num">Volume</th><th className="num">% of whole</th></tr></thead>
              <tbody>
                {REGIONS.map((r) => (
                  <tr key={r.key} style={{ cursor: 'default' }}>
                    <td className="cell-strong"><span className="legend-swatch" style={{ background: r.color, display: 'inline-block', marginRight: 6, verticalAlign: '-1px' }} />{r.label}</td>
                    <td>{r.desc}</td>
                    <td className="num">{r.vol.toFixed(2)} mL</td>
                    <td className="num">{((r.vol / s.wholeTumor) * 100).toFixed(1)}%</td>
                  </tr>
                ))}
                <tr style={{ cursor: 'default' }}>
                  <td className="cell-strong" style={{ borderTop: '1px solid var(--line-2)' }}>Whole tumour</td>
                  <td style={{ borderTop: '1px solid var(--line-2)' }}>All regions combined</td>
                  <td className="num cell-strong" style={{ borderTop: '1px solid var(--line-2)' }}>{s.wholeTumor.toFixed(2)} mL</td>
                  <td className="num" style={{ borderTop: '1px solid var(--line-2)' }}>100%</td>
                </tr>
              </tbody>
            </table>
          </section>

          {sections.method && (
            <section className="report-sec">
              <h3>Method</h3>
              <p>
                Volumes were skull-stripped with HD-BET (threshold 0.5) and normalised by z-score against a
                co-registered atlas. Four-region segmentation used nt-seg v2.4, an nnU-Net backbone trained on
                BraTS 2024 with connected-component filtering at 20 mm³. Volumetry was computed on the native
                1 mm isotropic grid without partial-volume correction. Region definitions follow the BraTS
                convention: tumour core comprises enhancing, necrotic and non-enhancing tumour; whole tumour
                adds peritumoral edema.
              </p>
              <p style={{ marginTop: 8 }}>
                Automated quality control scored five checks; boundary plausibility was flagged at 88 % on axial
                slices 64–65, where the lesion abuts the skull base. The contour was confirmed by manual review
                before signature.
              </p>
            </section>
          )}

          {sections.limitations && (
            <section className="report-sec">
              <h3>Limitations</h3>
              <p>
                Single timepoint; no histopathological confirmation available at the time of analysis. The model
                was validated on adult glioma and meningioma cohorts and has reduced sensitivity for lesions under
                0.5 mL or with extensive extra-axial contact. This report is a research output and does not
                constitute a diagnosis.
              </p>
            </section>
          )}

          <div style={{ marginTop: 30, paddingTop: 14, borderTop: '1px solid var(--line)', display: 'flex', justifyContent: 'space-between', gap: 20 }}>
            <div>
              <div className="tiny mono" style={{ letterSpacing: '.06em', textTransform: 'uppercase' }}>Prepared by</div>
              <div className="serif" style={{ fontSize: 15, marginTop: 4 }}>Dr A. Kessler</div>
              <div className="tiny">Research lead · Northgate Academic Neuroimaging</div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div className="tiny mono" style={{ letterSpacing: '.06em', textTransform: 'uppercase' }}>Hash</div>
              <div className="tiny mono" style={{ marginTop: 4 }}>3f9a…c41e</div>
              <div className="tiny">Reproducible from stored mask</div>
            </div>
          </div>
        </div>

        <div className="stack no-print" style={{ gap: 'var(--gap)', position: 'sticky', top: 0 }}>
          <div className="card">
            <div className="card-head"><span className="h3">Compose</span><Badge tone="warn" mono>Draft</Badge></div>
            <div className="card-body" style={{ paddingTop: 12 }}>
              <div className="stack gap-10">
                {[['findings', 'Findings'], ['figures', 'Figure plate'], ['method', 'Method'], ['limitations', 'Limitations']].map(([k, l]) => (
                  <div key={k} className="hrow" style={{ justifyContent: 'space-between' }}>
                    <span style={{ fontSize: 12.5 }}>{l}</span>
                    <Switch checked={sections[k]} onChange={(v) => setSections({ ...sections, [k]: v })} label={l} />
                  </div>
                ))}
              </div>
              <hr className="rule" style={{ margin: '14px 0' }} />
              <Field label="Version"><select className="select" value={version} onChange={(e) => setVersion(e.target.value)}><option>v3</option><option>v2</option><option>v1</option></select></Field>
              <div className="hrow" style={{ gap: 6, marginTop: 12 }}>
                <button className="btn btn-sm" style={{ flex: 1 }} onClick={() => toast('Draft saved', 'save')}><Icon name="save" size={12} />Save</button>
                <button className="btn btn-sm btn-quiet" onClick={() => toast('Preview refreshed from study data', 'refresh')}><Icon name="refresh" size={12} /></button>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-head"><span className="h3">Included outputs</span></div>
            <div className="card-body" style={{ paddingTop: 8 }}>
              {[['PDF report', '4 pages'], ['Segmentation mask', 'NIfTI · 6.2 MB'], ['Volumetry', 'CSV · 12 rows'], ['QC report', 'JSON · 5 checks']].map(([k, v]) => (
                <div className="kv" key={k} style={{ fontSize: 11.5 }}>
                  <dt style={{ display: 'flex', gap: 6, alignItems: 'center' }}><Icon name="file" size={11} style={{ color: 'var(--ink-3)' }} />{k}</dt>
                  <dd style={{ fontFamily: 'var(--font-ui)', fontSize: 11 }}>{v}</dd>
                </div>
              ))}
              <button className="btn btn-primary btn-sm" style={{ width: '100%', marginTop: 12 }} onClick={() => window.print()}>
                <Icon name="download" size={12} />Export all as PDF
              </button>
            </div>
          </div>

          <div className="card card-pad">
            <div className="eyebrow" style={{ marginBottom: 8 }}>Sign-off</div>
            <p className="tiny" style={{ lineHeight: 1.6 }}>
              Signing records your name, timestamp and the mask hash in the audit log. Reports cannot be
              edited after signature — create a new version instead.
            </p>
            <div className="hrow" style={{ gap: 6, marginTop: 10 }}>
              <span className="box" data-on="true" style={{ background: 'var(--accent)' }}><Icon name="check" size={9} /></span>
              <span className="tiny">QC flag reviewed manually</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------- history ---------- */
function History({ go, setStudy }) {
  const toast = useToast();
  const [q, setQ] = React.useState('');
  const [status, setStatus] = React.useState('all');
  const [sel, setSel] = React.useState([]);
  const [detail, setDetail] = React.useState(null);

  const rows = STUDIES.filter((s) => {
    const matchQ = !q || (s.id + s.diagnosis + s.patient).toLowerCase().includes(q.toLowerCase());
    const matchS = status === 'all' || s.status === status;
    return matchQ && matchS;
  });

  const toggle = (id) => setSel((p) => p.includes(id) ? p.filter((x) => x !== id) : [...p, id]);

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <div className="eyebrow">Library</div>
          <h1 className="h1" style={{ marginTop: 8 }}>Study history</h1>
          <p className="lede">142 studies since January. Every completed analysis carries its mask, volumetry, QC JSON and report.</p>
        </div>
        <div className="page-head-actions">
          <button className="btn" onClick={() => toast('Cohort manifest exported as CSV', 'download')}><Icon name="download" size={14} />Export manifest</button>
          <button className="btn btn-primary" onClick={() => go('upload')}><Icon name="upload" size={14} />New analysis</button>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 14 }}>
        <div className="hrow" style={{ padding: '11px 14px', gap: 10, flexWrap: 'wrap' }}>
          <div style={{ position: 'relative', flex: 1, minWidth: 200 }}>
            <Icon name="search" size={14} style={{ position: 'absolute', left: 10, top: 10, color: 'var(--ink-4)' }} />
            <input className="input" style={{ paddingLeft: 31 }} placeholder="Search by study ID, diagnosis or patient"
              value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search studies" />
          </div>
          <Segmented label="Status filter" value={status} onChange={setStatus} options={[
            { value: 'all', label: 'All' }, { value: 'complete', label: 'Complete' },
            { value: 'review', label: 'Review' }, { value: 'failed', label: 'Failed' }]} />
          <button className="btn btn-sm"><Icon name="filter" size={13} />Date range</button>
          <button className="btn btn-sm"><Icon name="layers" size={13} />Collection</button>
        </div>
      </div>

      {sel.length > 0 && (
        <div className="card fade-up" style={{ marginBottom: 14, padding: '9px 14px', background: 'var(--accent-soft)', borderColor: 'color-mix(in oklab, var(--accent) 24%, var(--line))' }}>
          <div className="hrow" style={{ gap: 10 }}>
            <span style={{ fontSize: 12.5, color: 'var(--accent-ink)', fontWeight: 500 }}>{sel.length} selected</span>
            <span className="tiny">·</span>
            <button className="btn btn-sm" onClick={() => toast(`${sel.length} masks queued for download`, 'download')}><Icon name="download" size={12} />Download masks</button>
            <button className="btn btn-sm" onClick={() => toast('Added to collection', 'layers')}><Icon name="layers" size={12} />Add to collection</button>
            <button className="btn btn-sm btn-ghost" style={{ marginLeft: 'auto' }} onClick={() => setSel([])}>Clear</button>
          </div>
        </div>
      )}

      <div className="card" style={{ overflow: 'hidden' }}>
        <table className="table">
          <thead>
            <tr>
              <th style={{ width: 34, paddingLeft: 14 }}><span className="sr-only">Select</span></th>
              <th>Study</th><th>Patient</th><th>Diagnosis</th>
              <th className="num">Whole tumour</th><th className="num">Confidence</th>
              <th>Status</th><th>Analysed</th><th style={{ width: 70 }}>Outputs</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((s) => (
              <tr key={s.id} onClick={() => setDetail(s)}>
                <td style={{ paddingLeft: 14 }} onClick={(e) => e.stopPropagation()}>
                  <button className="box" data-on={sel.includes(s.id)} onClick={() => toggle(s.id)}
                    aria-label={`Select ${s.id}`} style={{ background: sel.includes(s.id) ? 'var(--accent)' : 'var(--panel)', borderColor: sel.includes(s.id) ? 'var(--accent)' : 'var(--line-2)' }}>
                    {sel.includes(s.id) && <Icon name="check" size={9} stroke={3} style={{ color: '#fff' }} />}
                  </button>
                </td>
                <td className="cell-strong mono" style={{ fontSize: 11.5 }}>{s.id}</td>
                <td><div style={{ fontSize: 12 }}>{s.patient}</div><div className="tiny">{s.age}{s.sex}</div></td>
                <td><div className="truncate" style={{ maxWidth: 180, fontSize: 12 }}>{s.diagnosis}</div><div className="tiny">{s.sequence} · {s.field}</div></td>
                <td className="num">{s.wholeTumor ? `${s.wholeTumor.toFixed(2)}` : '—'}</td>
                <td className="num">{s.confidence ? s.confidence.toFixed(2) : '—'}</td>
                <td><StatusBadge status={s.status} /></td>
                <td className="mono tiny" style={{ fontSize: 10.5, whiteSpace: 'nowrap' }}>{s.analyzed.split(' ')[0]}</td>
                <td>
                  <div className="hrow" style={{ gap: 3 }}>
                    {s.status === 'complete' && ['report', 'download'].map((ic) => (
                      <button key={ic} className="btn-icon" style={{ width: 24, height: 24 }} aria-label={`Download ${ic}`}
                        onClick={(e) => { e.stopPropagation(); toast(`${ic === 'report' ? 'PDF report' : 'Mask archive'} downloaded`, 'download'); }}>
                        <Icon name={ic} size={13} />
                      </button>
                    ))}
                    {s.status !== 'complete' && <span className="tiny">—</span>}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length === 0 && (
          <EmptyState icon="search" title="No studies found" body="Try a different study ID or clear the status filter."
            action={<button className="btn btn-sm" onClick={() => { setQ(''); setStatus('all'); }}>Reset filters</button>} />
        )}
        <div className="hrow" style={{ padding: '10px 14px', borderTop: '1px solid var(--line)', justifyContent: 'space-between' }}>
          <span className="tiny mono">{rows.length} of 142 studies · page 1 of 24</span>
          <div className="hrow" style={{ gap: 4 }}>
            <button className="btn btn-sm btn-quiet" disabled><Icon name="chevL" size={12} />Previous</button>
            <button className="btn btn-sm btn-quiet">Next<Icon name="chevR" size={12} /></button>
          </div>
        </div>
      </div>

      {detail && (
        <>
          <div className="overlay" onClick={() => setDetail(null)} />
          <aside className="drawer" style={{ width: 420 }} role="dialog" aria-modal="true" aria-label={`Study ${detail.id} details`}>
            <div className="drawer-head">
              <div>
                <div className="eyebrow" style={{ marginBottom: 5 }}>Study detail</div>
                <div className="h2 mono" style={{ fontSize: 16 }}>{detail.id}</div>
                <div className="tiny" style={{ marginTop: 3 }}>{detail.diagnosis}</div>
              </div>
              <button className="btn-icon" onClick={() => setDetail(null)} aria-label="Close details"><Icon name="x" /></button>
            </div>
            <div className="drawer-body">
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 6, marginBottom: 18 }}>
                {['axial', 'coronal', 'sagittal'].map((p, i) => (
                  <div key={p} style={{ position: 'relative', background: 'var(--viewer)', borderRadius: 2, overflow: 'hidden', aspectRatio: '1' }}>
                    <img src={SERIES[p].src} alt={`${p} view`} style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: detail.status === 'failed' ? .15 : .85 }} />
                  </div>
                ))}
              </div>

              <dl style={{ margin: 0 }}>
                {[['Status', null], ['Patient', detail.patient], ['Age / sex', `${detail.age} / ${detail.sex}`], ['Accession', detail.accession],
                  ['Acquired', detail.acquired], ['Analysed', detail.analyzed], ['Sequence', detail.sequence], ['Field', detail.field],
                  ['Site', detail.site], ['Model', detail.model], ['Runtime', detail.duration]].map(([k, v]) => (
                  <div className="kv" key={k}>
                    <dt>{k}</dt>
                    <dd style={v === null ? {} : {}}>{v === null ? <StatusBadge status={detail.status} /> : v}</dd>
                  </div>
                ))}
              </dl>

              {detail.status === 'failed' && (
                <div style={{ marginTop: 16, padding: '11px 13px', background: 'var(--danger-soft)', borderRadius: 3 }}>
                  <div className="hrow" style={{ gap: 7, marginBottom: 5 }}>
                    <Icon name="alert" size={13} style={{ color: 'var(--danger)' }} />
                    <span style={{ fontSize: 11.5, fontWeight: 600, color: 'var(--danger)' }}>Analysis failed</span>
                  </div>
                  <p className="tiny" style={{ lineHeight: 1.55, color: 'var(--ink-2)' }}>{detail.error}</p>
                </div>
              )}

              {detail.status === 'complete' && (
                <>
                  <div className="note-block" style={{ marginTop: 8 }}>
                    <span className="eyebrow">Volumetry</span>
                    <div style={{ marginTop: 4 }}>
                      {REGIONS.map((r) => (
                        <div className="kv" key={r.key} style={{ fontSize: 11.5 }}>
                          <dt style={{ display: 'flex', gap: 6, alignItems: 'center' }}><i className="legend-swatch" style={{ background: r.color, width: 7, height: 7 }} />{r.label}</dt>
                          <dd>{r.vol.toFixed(2)} mL</dd>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="note-block">
                    <span className="eyebrow">Outputs</span>
                    <div className="stack gap-6" style={{ marginTop: 8 }}>
                      {[['Segmentation mask', 'NIfTI · 6.2 MB'], ['Volumetry table', 'CSV · 12 rows'], ['QC report', 'JSON · 5 checks'], ['PDF report', '4 pages']].map(([k, v]) => (
                        <button key={k} className="hrow" style={{ width: '100%', justifyContent: 'space-between', textAlign: 'left', padding: '6px 0' }}
                          onClick={() => toast(`${k} downloaded`, 'download')}>
                          <span className="hrow" style={{ gap: 8 }}>
                            <Icon name="download" size={12} style={{ color: 'var(--ink-3)' }} />
                            <span style={{ fontSize: 12 }}>{k}</span>
                          </span>
                          <span className="tiny mono">{v}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                </>
              )}
              <div className="hrow" style={{ gap: 8, marginTop: 18 }}>
                <button className="btn btn-primary btn-sm" onClick={() => { setStudy(detail.id); setDetail(null); go(detail.status === 'failed' ? 'upload' : 'workspace'); }}>
                  {detail.status === 'failed' ? 'Re-upload volume' : 'Open in workspace'}<Icon name="arrowR" size={12} />
                </button>
                <button className="btn btn-sm btn-quiet" onClick={() => { setDetail(null); go('reports'); }}>View report</button>
              </div>
            </div>
          </aside>
        </>
      )}
    </div>
  );
}

/* ---------- settings ---------- */
function Settings({ theme, setTheme, density, setDensity }) {
  const toast = useToast();
  const [model, setModel] = React.useState('nt-seg v2.4');
  const [assistModel, setAssistModel] = React.useState('Gemma 4 · 27B');
  const [retention, setRetention] = React.useState('7 years');
  const [anon, setAnon] = React.useState(true);
  const [telemetry, setTelemetry] = React.useState(false);
  const [autoRun, setAutoRun] = React.useState(true);
  const [notify, setNotify] = React.useState(true);
  const [tab, setTab] = React.useState('appearance');

  const nav = [
    ['appearance', 'Appearance', 'contrast'],
    ['model', 'Model configuration', 'cpu'],
    ['privacy', 'Privacy & data', 'shield'],
    ['defaults', 'Workspace defaults', 'settings'],
    ['account', 'Account', 'user'],
  ];

  return (
    <div className="page" style={{ maxWidth: 1080 }}>
      <div className="page-head">
        <div>
          <div className="eyebrow">Configuration</div>
          <h1 className="h1" style={{ marginTop: 8 }}>Settings</h1>
          <p className="lede">Changes apply immediately and are recorded in the workspace audit log.</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '188px minmax(0,1fr)', gap: 32, alignItems: 'start' }}>
        <nav className="stack" style={{ gap: 1, position: 'sticky', top: 0 }} aria-label="Settings sections">
          {nav.map(([id, label, icon]) => (
            <button key={id} className={'side-item' + (tab === id ? ' is-active' : '')} onClick={() => setTab(id)} style={{ padding: '8px 10px' }}>
              <Icon name={icon} size={14} />{label}
            </button>
          ))}
        </nav>

        <div className="stack" style={{ gap: 28 }}>
          {tab === 'appearance' && (
            <>
              <section>
                <h2 className="h2">Theme</h2>
                <p className="small" style={{ marginTop: 5 }}>Both themes are tuned independently — not an inverted palette.</p>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 16 }}>
                  {[['light', 'Light', 'Warm paper ground, ink text'], ['dark', 'Dark', 'Near-black ground, low-glare panels']].map(([id, l, d]) => (
                    <button key={id} onClick={() => setTheme(id)} aria-pressed={theme === id}
                      style={{
                        textAlign: 'left', border: `1px solid ${theme === id ? 'var(--accent)' : 'var(--line)'}`,
                        borderRadius: 5, padding: 10, background: 'var(--panel)',
                        boxShadow: theme === id ? '0 0 0 3px color-mix(in oklab, var(--accent) 12%, transparent)' : 'none',
                        transition: 'all var(--fast)',
                      }}>
                      <div style={{ height: 62, borderRadius: 3, background: id === 'light' ? '#FAFAF7' : '#0C1011', border: '1px solid var(--line)', padding: 8, display: 'flex', flexDirection: 'column', gap: 5 }}>
                        <div style={{ display: 'flex', gap: 5 }}>
                          <div style={{ width: 14, height: 14, borderRadius: 2, background: id === 'light' ? '#2C6E68' : '#6FB2A9' }} />
                          <div style={{ flex: 1, height: 5, marginTop: 4, background: id === 'light' ? '#D3D8D4' : '#2F3737', borderRadius: 1 }} />
                        </div>
                        <div style={{ flex: 1, background: id === 'light' ? '#FFFFFF' : '#131819', borderRadius: 2, border: `1px solid ${id === 'light' ? '#E4E7E4' : '#232A2A'}` }} />
                      </div>
                      <div className="hrow" style={{ justifyContent: 'space-between', marginTop: 9 }}>
                        <span style={{ fontSize: 12.5, fontWeight: 500 }}>{l}</span>
                        {theme === id && <Icon name="check" size={13} stroke={2.4} style={{ color: 'var(--accent)' }} />}
                      </div>
                      <div className="tiny" style={{ marginTop: 2 }}>{d}</div>
                    </button>
                  ))}
                </div>
                <div className="hrow" style={{ gap: 8, marginTop: 12 }}>
                  <button className="btn btn-sm" onClick={() => setTheme(window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')}>
                    <Icon name="contrast" size={12} />Match system
                  </button>
                  <span className="tiny mono" style={{ marginLeft: 'auto' }}>⌥T</span>
                </div>
              </section>

              <hr className="rule" />

              <section>
                <h2 className="h2">Density</h2>
                <p className="small" style={{ marginTop: 5 }}>Affects padding and row height across tables and panels. Type scale is unchanged.</p>
                <div className="stack gap-10" style={{ marginTop: 14, maxWidth: 420 }}>
                  {[['compact', 'Compact', 'Dense tables for cohort work'], ['balanced', 'Balanced', 'Default — clear hierarchy with room to breathe'], ['comfy', 'Comfortable', 'More spacing for long reading sessions']].map(([id, l, d]) => (
                    <button key={id} onClick={() => setDensity(id)} className="hrow" style={{ gap: 11, textAlign: 'left', alignItems: 'flex-start', padding: '9px 0' }}>
                      <span className="box" data-on={density === id} style={{ marginTop: 2 }}>{density === id && <Icon name="check" size={9} stroke={3} style={{ color: '#fff' }} />}</span>
                      <span style={{ flex: 1 }}>
                        <span style={{ fontSize: 12.5, display: 'block' }}>{l}</span>
                        <span className="tiny">{d}</span>
                      </span>
                    </button>
                  ))}
                </div>
              </section>

              <hr className="rule" />

              <section>
                <h2 className="h2">Typography</h2>
                <p className="small" style={{ marginTop: 5 }}>Editorial serif for display and figures, neutral sans for controls, mono for all measurements.</p>
                <div style={{ marginTop: 14, display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 12 }}>
                  {[['Display', 'Source Serif 4', 'var(--font-display)', 22], ['Interface', 'IBM Plex Sans', 'var(--font-ui)', 14], ['Measurements', 'IBM Plex Mono', 'var(--font-mono)', 13]].map(([k, f, ff, sz]) => (
                    <div key={k} className="card" style={{ padding: '12px 13px' }}>
                      <div className="tiny">{k}</div>
                      <div style={{ fontFamily: ff, fontSize: sz, marginTop: 6, letterSpacing: k === 'Display' ? '-.015em' : 0 }}>61.87 mL</div>
                      <div className="tiny mono" style={{ marginTop: 4, fontSize: 9.5 }}>{f}</div>
                    </div>
                  ))}
                </div>
              </section>

              <hr className="rule" />
              <section>
                <div className="hrow" style={{ justifyContent: 'space-between' }}>
                  <div><h2 className="h2" style={{ fontSize: 16 }}>Reduce motion</h2><p className="small" style={{ marginTop: 3 }}>Disables panel transitions and processing animations.</p></div>
                  <Switch checked={false} onChange={() => toast('Motion preference follows your system setting', 'info')} label="Reduce motion" />
                </div>
              </section>
            </>
          )}

          {tab === 'model' && (
            <>
              <section>
                <h2 className="h2">Segmentation model</h2>
                <p className="small" style={{ marginTop: 5 }}>Model version is recorded against every study and printed on reports.</p>
                <div className="card" style={{ marginTop: 14 }}>
                  <div className="card-body">
                    <div className="hrow" style={{ justifyContent: 'space-between', marginBottom: 12 }}>
                      <span className="h3">nt-seg</span>
                      <Badge tone="ok" dot>Default · validated</Badge>
                    </div>
                    <div className="stack gap-10">
                      {[['v2.4', 'nnU-Net backbone · BraTS 2024 · Dice 0.94', true], ['v2.3', 'Previous release · Dice 0.92', false], ['v3.0-rc1', 'Experimental · not for signed reports', false]].map(([v, d, def]) => (
                        <button key={v} className="hrow" style={{ gap: 10, textAlign: 'left', alignItems: 'flex-start', padding: '8px 0', opacity: def ? 1 : .85 }} onClick={() => setModel('nt-seg ' + v)}>
                          <span className="box" data-on={model === 'nt-seg ' + v} style={{ marginTop: 2 }}>{model === 'nt-seg ' + v && <Icon name="check" size={9} stroke={3} style={{ color: '#fff' }} />}</span>
                          <span style={{ flex: 1 }}>
                            <span className="mono" style={{ fontSize: 12 }}>{v}</span>
                            <span className="tiny" style={{ display: 'block', marginTop: 2 }}>{d}</span>
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </section>
              <hr className="rule" />
              <section>
                <h2 className="h2">Research assistant</h2>
                <div className="card" style={{ marginTop: 14 }}>
                  <div className="card-body">
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                      <Field label="Model">
                        <select className="select" value={assistModel} onChange={(e) => setAssistModel(e.target.value)}>
                          <option>Gemma 4 · 27B</option><option>Gemma 4 · 9B (fast)</option><option>Gemma 3 · 27B (legacy)</option>
                        </select>
                      </Field>
                      <Field label="Context window">
                        <select className="select"><option>128k tokens</option><option>32k tokens</option></select>
                      </Field>
                    </div>
                    <div className="hrow" style={{ justifyContent: 'space-between', marginTop: 14 }}>
                      <div><span style={{ fontSize: 12.5 }}>Allow literature search tool</span><div className="tiny" style={{ marginTop: 2 }}>Retrieves open-access abstracts only; disabled keeps answers purely internal.</div></div>
                      <Switch checked={true} onChange={() => {}} label="Literature search" />
                    </div>
                    <div className="hrow" style={{ justifyContent: 'space-between', marginTop: 12 }}>
                      <div><span style={{ fontSize: 12.5 }}>Show tool calls</span><div className="tiny" style={{ marginTop: 2 }}>Always visible in this build for auditability.</div></div>
                      <Switch checked={true} onChange={() => {}} label="Show tool calls" />
                    </div>
                  </div>
                </div>
              </section>
              <hr className="rule" />
              <section>
                <h2 className="h2">Processing</h2>
                <div className="hrow" style={{ justifyContent: 'space-between', marginTop: 12 }}>
                  <div><span style={{ fontSize: 12.5 }}>Run segmentation on upload</span><div className="tiny" style={{ marginTop: 2 }}>Otherwise the volume waits in the queue for manual start.</div></div>
                  <Switch checked={autoRun} onChange={setAutoRun} label="Run segmentation on upload" />
                </div>
                <div style={{ marginTop: 16, maxWidth: 360 }}>
                  <Field label="Compute target"><select className="select"><option>nous-2 · institutional GPU</option><option>Shared research pool</option><option>Local workstation</option></select></Field>
                </div>
              </section>
            </>
          )}

          {tab === 'privacy' && (
            <>
              <section>
                <h2 className="h2">Data handling</h2>
                <p className="small" style={{ marginTop: 5 }}>Defaults are the conservative option. Anything less strict is marked.</p>
                <div className="card" style={{ marginTop: 14 }}>
                  <div className="card-body">
                    {[
                      ['Strip headers on ingest', anon, setAnon, 'Removes patient name, ID and institution fields before storage.'],
                      ['Share anonymised usage metrics', telemetry, setTelemetry, 'No image data, no measurements. Off by default.'],
                    ].map(([l, v, set, d]) => (
                      <div key={l} className="hrow" style={{ justifyContent: 'space-between', padding: '11px 0', borderBottom: '1px solid var(--line)', alignItems: 'flex-start' }}>
                        <div style={{ maxWidth: '62%' }}><span style={{ fontSize: 12.5 }}>{l}</span><div className="tiny" style={{ marginTop: 3, lineHeight: 1.5 }}>{d}</div></div>
                        <Switch checked={v} onChange={set} label={l} />
                      </div>
                    ))}
                    <div className="hrow" style={{ justifyContent: 'space-between', paddingTop: 14, alignItems: 'flex-start' }}>
                      <div><span style={{ fontSize: 12.5 }}>Retention period</span><div className="tiny" style={{ marginTop: 3 }}>After this, masks and volumes are irreversibly deleted.</div></div>
                      <select className="select" style={{ width: 150 }} value={retention} onChange={(e) => setRetention(e.target.value)}>
                        <option>1 year</option><option>3 years</option><option>7 years</option><option>Indefinite</option>
                      </select>
                    </div>
                  </div>
                </div>
              </section>
              <hr className="rule" />
              <section>
                <h2 className="h2">Access</h2>
                <div className="card" style={{ marginTop: 14 }}>
                  <table className="table">
                    <thead><tr><th>Role</th><th>Can view</th><th>Can sign reports</th><th>Can configure</th></tr></thead>
                    <tbody>
                      {[['Research lead', 'All', 'Yes', 'Yes'], ['Fellow', 'All', 'No', 'No'], ['Technician', 'Own uploads', 'No', 'No']].map(([r, a, b, c]) => (
                        <tr key={r} style={{ cursor: 'default' }}>
                          <td className="cell-strong">{r}</td><td>{a}</td><td>{b}</td><td>{c}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="hrow" style={{ gap: 8, marginTop: 12 }}>
                  <button className="btn btn-sm" onClick={() => toast('Audit log opened', 'external')}><Icon name="external" size={12} />View audit log</button>
                  <button className="btn btn-sm btn-quiet" onClick={() => toast('Data export requested — 24 h', 'download')}><Icon name="download" size={12} />Export all data</button>
                </div>
              </section>
            </>
          )}

          {tab === 'defaults' && (
            <>
              <section>
                <h2 className="h2">Viewer defaults</h2>
                <div className="card" style={{ marginTop: 14 }}>
                  <div className="card-body" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                    <Field label="Default overlay"><select className="select"><option>Contour</option><option>Filled</option><option>Hidden</option></select></Field>
                    <Field label="Crosshair coupling"><select className="select"><option>All planes</option><option>Same plane only</option><option>Off</option></select></Field>
                    <Field label="Default window / level"><select className="select"><option>T1 brain</option><option>T1 + Gd</option><option>FLAIR</option></select></Field>
                    <Field label="Slice step"><select className="select"><option>1 slice</option><option>2 slices</option><option>5 slices</option></select></Field>
                  </div>
                </div>
              </section>
              <hr className="rule" />
              <section>
                <h2 className="h2">Notifications</h2>
                <div className="hrow" style={{ justifyContent: 'space-between', marginTop: 14 }}>
                  <div><span style={{ fontSize: 12.5 }}>Notify when an analysis completes</span><div className="tiny" style={{ marginTop: 2 }}>In-app and email for studies over 30 minutes in queue.</div></div>
                  <Switch checked={notify} onChange={setNotify} label="Notify on completion" />
                </div>
              </section>
              <hr className="rule" />
              <section>
                <h2 className="h2">Export defaults</h2>
                <div className="card" style={{ marginTop: 14 }}>
                  <div className="card-body" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                    <Field label="Report format"><select className="select"><option>PDF (A4)</option><option>PDF (Letter)</option><option>DOCX</option></select></Field>
                    <Field label="Figure resolution"><select className="select"><option>300 dpi</option><option>600 dpi</option></select></Field>
                  </div>
                </div>
              </section>
            </>
          )}

          {tab === 'account' && (
            <>
              <section>
                <h2 className="h2">Account</h2>
                <div className="card" style={{ marginTop: 14 }}>
                  <div className="card-body">
                    <div className="hrow" style={{ gap: 14 }}>
                      <div style={{ width: 46, height: 46, borderRadius: '50%', background: 'var(--accent-soft)', color: 'var(--accent-ink)', display: 'grid', placeItems: 'center', fontSize: 15, fontWeight: 600 }}>AK</div>
                      <div>
                        <div className="serif" style={{ fontSize: 17 }}>Dr Amara Kessler</div>
                        <div className="tiny">Research lead · Northgate Academic Neuroimaging</div>
                        <div className="tiny mono" style={{ marginTop: 2 }}>a.kessler@northgate.edu</div>
                      </div>
                    </div>
                    <hr className="rule" style={{ margin: '16px 0' }} />
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                      <Field label="Display name"><input className="input" defaultValue="Dr Amara Kessler" /></Field>
                      <Field label="Role"><select className="select"><option>Research lead</option><option>Fellow</option></select></Field>
                    </div>
                  </div>
                </div>
              </section>
              <hr className="rule" />
              <section>
                <h2 className="h2">Sessions</h2>
                <div className="card" style={{ marginTop: 14 }}>
                  {[['MacBook Pro · Chrome', 'Berlin, DE · active now', true], ['Lab workstation 04', 'Berlin, DE · 2 days ago', false]].map(([d, m, now]) => (
                    <div key={d} className="hrow" style={{ padding: '11px 16px', borderBottom: '1px solid var(--line)', justifyContent: 'space-between' }}>
                      <div><div style={{ fontSize: 12.5 }}>{d}</div><div className="tiny">{m}</div></div>
                      {now ? <Badge tone="ok" dot>This device</Badge> : <button className="btn btn-sm btn-quiet">Revoke</button>}
                    </div>
                  ))}
                </div>
              </section>
            </>
          )}

          <div className="hrow" style={{ gap: 8, paddingTop: 4 }}>
            <button className="btn btn-primary" onClick={() => toast('Settings saved', 'checkCircle')}>Save changes</button>
            <button className="btn btn-quiet" onClick={() => toast('Restored workspace defaults', 'refresh')}>Restore defaults</button>
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { Reports, History, Settings });
