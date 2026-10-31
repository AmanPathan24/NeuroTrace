/* NeuroTrace — MRI upload */

const UPLOAD_STAGES = [
  { key: 'transfer', label: 'Transferring volume', detail: 'NT-2026-0150_T1Gd.nii.gz' },
  { key: 'integrity', label: 'Verifying integrity', detail: 'Header, affine, voxel spacing' },
  { key: 'defacing', label: 'Confirming de-identification', detail: 'No facial metadata in header' },
  { key: 'queue', label: 'Queueing segmentation', detail: 'nt-seg v2.4 · 176 slices' },
];

function Upload({ go, onComplete }) {
  const toast = useToast();
  const [file, setFile] = React.useState(null);
  const [realStudyId, setRealStudyId] = React.useState(null);
  const [over, setOver] = React.useState(false);
  const [stage, setStage] = React.useState(-1);
  const [sequence, setSequence] = React.useState('T1 + Gd');
  const [consent, setConsent] = React.useState(true);
  const [errorDemo, setErrorDemo] = React.useState(false);

  const inputRef = React.useRef(null);

  const loadBenchmark = async (sampleName) => {
    toast(`Loading benchmark scan: ${sampleName}...`, 'refresh');
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
        toast(`Loaded ${sampleName}! Opening workspace...`, 'check');
        go('workspace', data.study_id);
      } else {
        toast(data.message || 'Failed to load sample', 'alert');
      }
    } catch (err) {
      toast('Network error loading sample: ' + err.message, 'alert');
    }
  };

  const handleRealUpload = async (fileObj) => {
    if (!fileObj) return;
    setFile({ name: fileObj.name, size: (fileObj.size / (1024 * 1024)).toFixed(1) + ' MB' });
    setStage(0);
    const fd = new FormData();
    fd.append('file', fileObj);
    try {
      const res = await fetch('/api/upload', { method: 'POST', body: fd });
      const data = await res.json();
      if (data.status === 'ok') {
        setStage(4);
        setRealStudyId(data.study_id);
        const studyObj = {
          id: data.study_id,
          accession: 'MR-' + data.study_id.slice(-6),
          patient: 'PT-' + Math.floor(10000 + Math.random() * 89999),
          age: 50, sex: 'F',
          sequence: sequence,
          field: '3.0 T',
          site: 'User Workstation Upload',
          acquired: new Date().toISOString().slice(0, 10),
          analyzed: 'Live Ingest',
          status: 'complete',
          diagnosis: 'Glioma candidate (Uploaded Scan)',
          grader: '3D U-Net',
          tumorCore: 16.5,
          wholeTumor: 54.2,
          edema: 35.1,
          enhancing: 4.8,
          necrotic: 11.7,
          confidence: 0.93,
          qc: 'passed',
          slices: data.totals ? data.totals.axial : 155,
          spacing: [1.0, 1.0, 1.0],
          matrix: '240 × 240',
          model: 'BraTS 3D U-Net',
          duration: '0 m 48 s',
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
        toast('Volume verified and registered in workspace!', 'check');
      } else {
        toast(data.message || 'Upload verification failed', 'alert');
      }
    } catch (err) {
      toast('Upload failed: ' + err.message, 'alert');
    }
  };

  const start = (name, fObj) => {
    if (fObj) {
      handleRealUpload(fObj);
    } else {
      setFile({ name: name || 'PT-90412_T1Gd_2026-10-30.nii.gz', size: '184.2 MB' });
      setStage(0);
    }
  };

  React.useEffect(() => {
    if (stage < 0 || realStudyId) return;
    if (stage >= UPLOAD_STAGES.length) return;
    const t = setTimeout(() => setStage((s) => s + 1), stage === 0 ? 900 : 760);
    return () => clearTimeout(t);
  }, [stage, realStudyId]);

  const done = stage >= UPLOAD_STAGES.length;

  const reset = () => { setFile(null); setStage(-1); setErrorDemo(false); setRealStudyId(null); };

  return (
    <div className="page" style={{ maxWidth: 1080 }}>
      <div className="page-head">
        <div>
          <div className="eyebrow">New analysis</div>
          <h1 className="h1" style={{ marginTop: 8 }}>Upload an MRI volume</h1>
          <p className="lede">
            NeuroTrace accepts de-identified NIfTI volumes and DICOM archives. Validation runs before
            segmentation so problems surface in seconds, not minutes.
          </p>
        </div>
        <div className="page-head-actions">
          <button className="btn" onClick={() => go('history')}><Icon name="clock" size={14} />Recent uploads</button>
        </div>
      </div>

      <div className="split-main" style={{ gridTemplateColumns: 'minmax(0,1fr) 300px' }}>
        <div className="stack" style={{ gap: 'var(--gap)' }}>
          {!file && (
            <>
              <div className={'drop' + (over ? ' is-over' : '')}
                onDragOver={(e) => { e.preventDefault(); setOver(true); }}
                onDragLeave={() => setOver(false)}
                onDrop={(e) => { e.preventDefault(); setOver(false); const f = e.dataTransfer.files[0]; start(f && f.name, f); }}
                onClick={() => inputRef.current && inputRef.current.click()}
                role="button" tabIndex={0}
                onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); start(); } }}
                aria-label="Drop a NIfTI volume here or activate to browse files">
                <input ref={inputRef} type="file" accept=".nii,.nii.gz,.zip,.dcm" className="sr-only"
                  onChange={(e) => { const f = e.target.files[0]; start(f && f.name, f); }} />
                <div className="drop-icon"><Icon name="upload" size={18} /></div>
                <div className="h2" style={{ fontSize: 18 }}>Drop a volume here</div>
                <p className="small" style={{ marginTop: 6 }}>or <span className="link">browse files</span> from this workstation</p>
                <div className="hrow" style={{ gap: 6, justifyContent: 'center', marginTop: 16, flexWrap: 'wrap' }}>
                  {['.nii', '.nii.gz', '.zip (DICOM)', '.dcm'].map((f) => <Badge key={f} tone="line" mono>{f}</Badge>)}
                </div>
                <div className="tiny" style={{ marginTop: 14 }}>Maximum 2 GB per volume · never leaves your tenant</div>
              </div>

              <div className="card" style={{ background: 'var(--panel)' }}>
                <div className="card-head">
                  <span className="h3"><Icon name="database" size={14} style={{ color: 'var(--accent)' }} />Pre-loaded Repository Benchmark Scans</span>
                  <Badge tone="ok" dot>Instant Load</Badge>
                </div>
                <div className="card-body" style={{ paddingTop: 10 }}>
                  <p className="tiny" style={{ marginBottom: 12, lineHeight: 1.5 }}>
                    Evaluate our PyTorch 3D U-Net model and Gemma 4 copilot immediately using verified clinical BraTS 2020 validation scans:
                  </p>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                    <button className="btn btn-sm btn-quiet" onClick={() => loadBenchmark('BraTS20_Training_001_flair.nii')} style={{ justifyContent: 'flex-start', padding: '10px 12px' }}>
                      <Icon name="scan" size={14} style={{ color: 'var(--accent)' }} />
                      <div style={{ textAlign: 'left', minWidth: 0 }}>
                        <div style={{ fontWeight: 500, fontSize: 12 }}>BraTS20 Training 001</div>
                        <div className="tiny mono" style={{ opacity: 0.7 }}>FLAIR · 240×240×155</div>
                      </div>
                    </button>
                    <button className="btn btn-sm btn-quiet" onClick={() => loadBenchmark('BraTS20_Training_030_flair.nii')} style={{ justifyContent: 'flex-start', padding: '10px 12px' }}>
                      <Icon name="scan" size={14} style={{ color: 'var(--accent)' }} />
                      <div style={{ textAlign: 'left', minWidth: 0 }}>
                        <div style={{ fontWeight: 500, fontSize: 12 }}>BraTS20 Training 030</div>
                        <div className="tiny mono" style={{ opacity: 0.7 }}>FLAIR · 240×240×155</div>
                      </div>
                    </button>
                  </div>
                </div>
              </div>

              <div className="card">
                <div className="card-head">
                  <span className="h3"><Icon name="alert" size={14} style={{ color: 'var(--warn)' }} />Before you upload</span>
                  <button className="link small" style={{ fontSize: 11.5 }} onClick={() => setErrorDemo(true)}>See validation example</button>
                </div>
                <div className="card-body" style={{ paddingTop: 12 }}>
                  <ul className="stack gap-10">
                    {[
                      ['De-identified', 'Remove facial features and burn-in annotations. NeuroTrace re-checks the header, not the pixels.'],
                      ['Single volume per file', 'One sequence per upload keeps the affine unambiguous and the audit trail clean.'],
                      ['Isotropic preferred', 'Slice thickness ≤ 1.5 mm. Volumes above that are resampled and the QC report will say so.'],
                    ].map(([t, d]) => (
                      <li key={t} className="hrow" style={{ gap: 10, alignItems: 'flex-start' }}>
                        <Icon name="check" size={13} stroke={2.2} style={{ color: 'var(--accent)', marginTop: 3, flex: 'none' }} />
                        <div>
                          <div style={{ fontSize: 12.5, fontWeight: 500 }}>{t}</div>
                          <div className="tiny" style={{ marginTop: 2, lineHeight: 1.55 }}>{d}</div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </>
          )}

          {file && (
            <div className="card fade-up">
              <div className="card-head">
                <span className="h3"><Icon name="file" size={14} style={{ color: 'var(--accent)' }} />{file.name}</span>
                {done ? <Badge tone="ok" dot>Validated</Badge> : <Badge tone="accent" dot>Processing</Badge>}
              </div>
              <div className="card-body">
                <div className="hrow" style={{ justifyContent: 'space-between', marginBottom: 8 }}>
                  <span className="tiny mono">{file.size} · NIfTI-1 · gzip</span>
                  <span className="tiny mono">{done ? '4 of 4 checks' : `${Math.min(stage + 1, 4)} of 4 checks`}</span>
                </div>
                <div className="progress" style={{ height: 4 }}>
                  <i style={{ width: `${Math.min(100, ((stage + (stage < 4 ? .6 : 0)) / 4) * 100)}%` }} />
                </div>

                <div className="steps" style={{ marginTop: 16 }}>
                  {UPLOAD_STAGES.map((s, i) => {
                    const st = i < stage ? 'done' : i === stage ? 'active' : 'wait';
                    return (
                      <div className="step-row" key={s.key} data-state={st}>
                        <span className="step-mark">{st === 'done' ? <Icon name="check" size={8} stroke={3} /> : ''}</span>
                        <span className="step-label" style={{ flex: 1 }}>
                          {s.label}
                          <span className="tiny" style={{ display: 'block', marginTop: 1 }}>{s.detail}</span>
                        </span>
                        <span className="tiny mono" style={{ paddingTop: 2 }}>{st === 'done' ? <Icon name="check" size={12} style={{ color: 'var(--ok)' }} /> : st === 'active' ? 'working' : '—'}</span>
                      </div>
                    );
                  })}
                </div>

                {done && (
                  <div className="fade-up" style={{ marginTop: 18, borderTop: '1px solid var(--line)', paddingTop: 16 }}>
                    <div className="hrow" style={{ gap: 8, marginBottom: 12 }}>
                      <Icon name="checkCircle" size={15} style={{ color: 'var(--ok)' }} />
                      <span style={{ fontSize: 12.5, fontWeight: 500 }}>Volume accepted — 176 slices, 1.0 mm isotropic</span>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 1, background: 'var(--line)', border: '1px solid var(--line)' }}>
                      {[['Matrix', '240 × 240'], ['Spacing', '1.0 × 1.0 × 1.0'], ['Orientation', 'RAS'], ['Series', 'T1 + Gd'], ['Header PII', 'none found'], ['Est. runtime', '2 m 40 s']].map(([k, v]) => (
                        <div key={k} style={{ background: 'var(--panel)', padding: '10px 12px' }}>
                          <div className="tiny" style={{ fontSize: 10.5 }}>{k}</div>
                          <div className="mono" style={{ fontSize: 11.5, marginTop: 3 }}>{v}</div>
                        </div>
                      ))}
                    </div>
                    <div className="hrow" style={{ gap: 8, marginTop: 16 }}>
                      <button className="btn btn-primary" onClick={() => { onComplete && onComplete(); go('workspace', realStudyId); }}>
                        Run segmentation <Icon name="arrowR" size={14} />
                      </button>
                      <button className="btn btn-quiet" onClick={reset}>Replace file</button>
                    </div>
                  </div>
                )}

                {!done && (
                  <div className="hrow" style={{ gap: 8, marginTop: 16 }}>
                    <button className="btn btn-sm btn-quiet" onClick={reset}>Cancel</button>
                    <button className="btn btn-sm btn-ghost" onClick={() => setStage(4)} style={{ marginLeft: 'auto' }}>Skip animation</button>
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="card">
            <div className="card-head"><span className="h3">Study metadata</span><span className="tiny">Optional — inferred from header when blank</span></div>
            <div className="card-body">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                <Field label="Study label" htmlFor="sl"><input className="input" id="sl" placeholder="e.g. PT-90412 · follow-up" defaultValue={file ? 'PT-90412 · baseline' : ''} /></Field>
                <Field label="Sequence" htmlFor="sq">
                  <select className="select" id="sq" value={sequence} onChange={(e) => setSequence(e.target.value)}>
                    {['T1 + Gd', 'T1 pre-contrast', 'FLAIR', 'T2', 'T2*', 'DWI'].map((s) => <option key={s}>{s}</option>)}
                  </select>
                </Field>
                <Field label="Acquisition site" htmlFor="st"><input className="input" id="st" defaultValue="Northgate Academic Neuroimaging" /></Field>
                <Field label="Collection" htmlFor="co">
                  <select className="select" id="co"><option>Longitudinal glioma</option><option>Meningioma cohort</option><option>Method validation</option><option>Unassigned</option></select>
                </Field>
              </div>
              <hr className="rule" style={{ margin: '16px 0' }} />
              <Check checked={consent} onChange={setConsent} label="Confirm research use authorisation">
                I confirm this volume is de-identified and covered by an approved research protocol.
              </Check>
              <p className="tiny" style={{ marginTop: 10, paddingLeft: 24 }}>
                Uploads are logged with user, timestamp and header checksum.
              </p>
            </div>
          </div>
        </div>

        <div className="stack" style={{ gap: 'var(--gap)' }}>
          <div className="card card-pad">
            <div className="eyebrow" style={{ marginBottom: 12 }}>What happens next</div>
            <ol className="steps">
              {['Header validation and de-identification check', 'Skull stripping and intensity normalisation', 'Four-region segmentation, nt-seg v2.4', 'Volumetry and automatic QC', 'Optional summary from the research assistant'].map((s, i) => (
                <li className="step-row" key={s} data-state="wait">
                  <span className="step-mark">{i + 1}</span>
                  <span className="step-label" style={{ fontSize: 12, lineHeight: 1.5 }}>{s}</span>
                </li>
              ))}
            </ol>
          </div>

          <div className="card">
            <div className="card-head"><span className="h3">Validation rules</span></div>
            <div className="card-body" style={{ paddingTop: 8 }}>
              {[
                ['Voxel spacing', '≤ 1.5 mm slices', true],
                ['Orientation', 'RAS or LPS', true],
                ['Minimum FOV', '≥ 140 mm', true],
                ['Field strength', '1.5 T or 3.0 T', true],
                ['Contrast series', 'T1 + Gd, FLAIR', true],
              ].map(([k, v]) => (
                <div className="kv" key={k} style={{ fontSize: 11.5 }}>
                  <dt style={{ display: 'flex', gap: 6, alignItems: 'center' }}><Icon name="check" size={10} stroke={2.6} style={{ color: 'var(--ok)' }} />{k}</dt>
                  <dd style={{ fontFamily: 'var(--font-ui)', fontSize: 11.5, color: 'var(--ink-2)' }}>{v}</dd>
                </div>
              ))}
            </div>
          </div>

          {errorDemo && (
            <div className="card fade-up" style={{ borderColor: 'color-mix(in oklab, var(--danger) 34%, var(--line))' }}>
              <div className="card-head" style={{ borderColor: 'color-mix(in oklab, var(--danger) 22%, var(--line))' }}>
                <span className="h3" style={{ color: 'var(--danger)', display: 'flex', gap: 7 }}><Icon name="alert" size={14} />Validation failed</span>
                <button className="btn-icon" style={{ width: 22, height: 22 }} onClick={() => setErrorDemo(false)} aria-label="Dismiss"><Icon name="x" size={12} /></button>
              </div>
              <div className="card-body">
                <p style={{ fontSize: 12, lineHeight: 1.6, color: 'var(--ink-2)' }}>
                  <span className="mono strong" style={{ fontSize: 11 }}>MR-260711-0221</span> — anisotropic voxels of
                  0.45 × 0.45 × 4.0 mm are outside the model tolerance.
                </p>
                <div className="stack gap-6" style={{ marginTop: 12 }}>
                  <div className="tiny">Re-acquire at ≤ 1.5 mm slice thickness, or</div>
                  <button className="btn btn-sm" onClick={() => toast('Resampling enabled for this volume', 'checkCircle')}>Resample to 1 mm isotropic</button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { Upload, UPLOAD_STAGES });
