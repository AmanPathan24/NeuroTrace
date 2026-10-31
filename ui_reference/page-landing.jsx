/* NeuroTrace — landing page */

function Landing({ go, theme, setTheme }) {
  return (
    <div className="landing">
      <nav className="landing-nav">
        <Brand size={18} onClick={() => {}} />
        <div className="nav-links">
          <a href="#method">Method</a>
          <a href="#capabilities">Capabilities</a>
          <a href="#workflow">Workflow</a>
          <a href="#trust">Validation</a>
        </div>
        <div style={{ flex: 1 }} />
        <div className="hrow" style={{ gap: 2, padding: 2, border: '1px solid var(--line)', borderRadius: 4, background: 'var(--sunken)' }}>
          <button className="btn-icon" style={{ width: 26, height: 24, background: theme === 'light' ? 'var(--panel)' : 'transparent', color: theme === 'light' ? 'var(--ink)' : 'var(--ink-3)' }} onClick={() => setTheme('light')} aria-label="Light theme"><Icon name="sun" size={14} /></button>
          <button className="btn-icon" style={{ width: 26, height: 24, background: theme === 'dark' ? 'var(--panel)' : 'transparent', color: theme === 'dark' ? 'var(--ink)' : 'var(--ink-3)' }} onClick={() => setTheme('dark')} aria-label="Dark theme"><Icon name="moon" size={14} /></button>
        </div>
        <button className="btn btn-ghost btn-sm" onClick={() => go('history')} style={{ marginLeft: 6 }}>Sign in</button>
        <button className="btn btn-primary btn-sm" onClick={() => go('dashboard')}>Get started</button>
      </nav>

      <div className="landing-wrap">
        <section className="hero">
          <div>
            <div className="hrow" style={{ gap: 9, marginBottom: 22 }}>
              <Badge tone="accent" mono>v2.4</Badge>
              <span className="small" style={{ fontSize: 11.5 }}>BraTS-2024 validated · 1,428 reference cases</span>
            </div>
            <h1 className="display" style={{ fontSize: 'clamp(34px, 4.4vw, 58px)', maxWidth: '15ch' }}>
              Segmentation you can defend, not just read.
            </h1>
            <p className="lede" style={{ marginTop: 22, maxWidth: '46ch' }}>
              NeuroTrace turns a NIfTI volume into a measured, quality-controlled tumour report —
              volumes, diameters, spatial relations and a research summary grounded in the numbers it computed.
            </p>
            <div className="hero-actions">
              <button className="btn btn-primary btn-lg" onClick={() => go('upload')}>
                Start an analysis <Icon name="arrowR" size={15} />
              </button>
              <button className="btn btn-lg btn-quiet" onClick={() => go('workspace')}>
                View a sample study
              </button>
            </div>
            <div className="hero-note">
              <div><b>2 m 41 s</b>Median analysis time</div>
              <div><b>0.94</b>Mean Dice, tumour core</div>
              <div><b>4</b>Outputs per study</div>
            </div>
          </div>

          <figure style={{ margin: 0 }}>
            <div className="specimen">
              <img src="assets/mri-axial.png" alt="Axial T1-weighted MRI with a ring-enhancing left frontal lesion" />
              <div className="specimen-label" style={{ top: 12, left: 14 }}>AX · SL 092 / 176</div>
              <div className="specimen-label" style={{ top: 12, right: 14, color: 'var(--overlay-line)' }}>● Segmented</div>
              <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }} aria-hidden="true">
                <ellipse cx="33.4" cy="28.6" rx="12.2" ry="11.4" fill="rgba(102,160,152,.20)" stroke="#8FD2C6" strokeWidth="0.9" strokeDasharray="3 2.5" vectorEffect="non-scaling-stroke" />
                <ellipse cx="33.4" cy="28.6" rx="8.6" ry="8.0" fill="none" stroke="#8FD2C6" strokeWidth="1.1" vectorEffect="non-scaling-stroke" />
                <line x1="33.4" y1="11" x2="33.4" y2="23" stroke="#8FD2C6" strokeWidth="0.8" vectorEffect="non-scaling-stroke" />
                <text x="33.4" y="8.4" fill="#8FD2C6" fontSize="3.1" fontFamily="IBM Plex Mono, monospace" textAnchor="middle">61.87 mL</text>
              </svg>
              <div className="specimen-caption">
                <span className="mono" style={{ fontSize: 9, letterSpacing: '.06em', color: 'rgba(255,255,255,.55)', textTransform: 'uppercase' }}>NT-2026-0148 · Glioma, left frontal</span>
                <span className="mono" style={{ fontSize: 9, letterSpacing: '.06em', color: 'rgba(255,255,255,.55)' }}>3.0 T</span>
              </div>
            </div>
            <figcaption className="tiny" style={{ marginTop: 10, display: 'flex', gap: 8, alignItems: 'flex-start' }}>
              <span className="mono" style={{ color: 'var(--accent)', fontSize: 10 }}>Fig. 1</span>
              De-identified study. Overlay shows the predicted whole-tumour envelope; volume computed at 1 mm isotropic resolution.
            </figcaption>
          </figure>
        </section>

        <div className="metrics-band">
          <StatCell label="Studies analysed" value="142" meta={<span>Last 30 days · +18</span>} />
          <StatCell label="Mean Dice score" value="0.94" meta={<span>Tumour core, n = 96</span>} />
          <StatCell label="Regions segmented" value="4" meta={<span>BraTS convention</span>} />
          <StatCell label="Median runtime" value="2:41" meta={<span>176-slice volume</span>} />
        </div>

        <section className="section" id="capabilities">
          <div className="section-head">
            <div>
              <div className="eyebrow">Capabilities</div>
              <h2 className="h1" style={{ marginTop: 8, fontSize: 26 }}>Built around the measurement</h2>
            </div>
            <p className="small" style={{ maxWidth: '38ch', textAlign: 'right' }}>
              Four things it does well, and nothing it does not.
            </p>
          </div>
          <div className="cap-grid">
            {[
              ['01', 'Orthogonal review', 'Axial, coronal and sagittal panels stay cross-referenced. Scrub any plane and the others follow — no re-registration step.'],
              ['02', 'Volumetric truth', 'Physical volumes per sub-region, three-axis diameters, bounding box and centroid in scanner coordinates, each with its method stated.'],
              ['03', 'Grounded reasoning', 'Gemma 4 answers only from the study’s own tables and named tools. Every figure is traceable to a row you can open.'],
            ].map(([n, t, d]) => (
              <div className="cap" key={n}>
                <div className="cap-num">{n}</div>
                <h3 className="h2" style={{ marginTop: 10, fontSize: 19 }}>{t}</h3>
                <p className="small" style={{ marginTop: 8, lineHeight: 1.62, maxWidth: '36ch' }}>{d}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="section" id="workflow">
          <div className="section-head">
            <div>
              <div className="eyebrow">Workflow</div>
              <h2 className="h1" style={{ marginTop: 8, fontSize: 26 }}>Five steps, one sitting</h2>
            </div>
          </div>
          <div className="flow">
            {[
              ['01', 'Upload', 'NIfTI or DICOM archive, validated on arrival'],
              ['02', 'Segment', 'Skull-strip, normalise, predict four regions'],
              ['03', 'Measure', 'Volumetry, QC, spatial relations'],
              ['04', 'Interpret', 'Grounded summary and cohort context'],
              ['05', 'Export', 'Mask, CSV, QC JSON and PDF report'],
            ].map(([n, t, d]) => (
              <div className="flow-step" key={n}>
                <div className="n">{n}</div>
                <div className="t">{t}</div>
                <div className="d">{d}</div>
              </div>
            ))}
          </div>
        </section>

        <section className="section" id="method">
          <div className="split-main" style={{ gridTemplateColumns: 'minmax(0,1fr) 340px' }}>
            <div>
              <div className="eyebrow">Method</div>
              <h2 className="h1" style={{ marginTop: 8, fontSize: 26, maxWidth: '22ch' }}>A model you can inspect, on a pipeline you can cite</h2>
              <div className="card" style={{ marginTop: 20 }}>
                <table className="table">
                  <thead>
                    <tr><th>Stage</th><th>Implementation</th><th className="num">Runtime</th></tr>
                  </thead>
                  <tbody>
                    {[
                      ['Skull stripping', 'HD-BET, threshold 0.5', '18 s'],
                      ['Intensity normalisation', 'Z-score, atlas-clipped', '6 s'],
                      ['Segmentation', 'nt-seg v2.4 · nnU-Net backbone', '104 s'],
                      ['Post-processing', 'Connected components ≥ 20 mm³', '9 s'],
                      ['Volumetry & QC', 'Deterministic, audited', '4 s'],
                    ].map(([a, b, c]) => (
                      <tr key={a} style={{ cursor: 'default' }}>
                        <td className="cell-strong">{a}</td>
                        <td>{b}</td>
                        <td className="num">{c}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <div className="card card-pad" id="trust">
              <div className="eyebrow" style={{ marginBottom: 12 }}>Validation</div>
              {[
                ['Tumour core Dice', '0.94'],
                ['Whole tumour Dice', '0.96'],
                ['Enhancing tumour Dice', '0.91'],
                ['Test set', 'BraTS 2024 · 250 cases'],
              ].map(([k, v], i, arr) => (
                <div className="kv" key={k} style={{ borderBottom: i === arr.length - 1 ? 0 : undefined }}>
                  <dt>{k}</dt><dd>{v}</dd>
                </div>
              ))}
              <hr className="rule" style={{ margin: '14px 0' }} />
              <p className="tiny" style={{ lineHeight: 1.65 }}>
                Research use only. Not a medical device. All figures reported on held-out,
                multi-institutional de-identified data.
              </p>
            </div>
          </div>
        </section>

        <section className="section">
          <div className="cta-band">
            <div>
              <div className="eyebrow" style={{ color: 'rgba(255,255,255,.5)' }}>Ready when you are</div>
              <h2 className="display" style={{ marginTop: 10, maxWidth: '19ch', letterSpacing: '-.02em' }}>
                Bring a volume. Leave with a defensible report.
              </h2>
            </div>
            <div className="hrow" style={{ gap: 10, flexWrap: 'wrap' }}>
              <button className="btn btn-lg" style={{ background: '#EDF1EF', borderColor: '#EDF1EF', color: '#101617' }} onClick={() => go('upload')}>
                Upload a study <Icon name="arrowR" size={15} />
              </button>
              <button className="btn btn-lg" style={{ background: 'transparent', borderColor: 'rgba(255,255,255,.24)', color: '#EDF1EF' }} onClick={() => go('dashboard')}>
                Explore the workspace
              </button>
            </div>
          </div>
        </section>

        <footer className="landing-foot">
          <div className="r" style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <BrandMark size={16} /> <span>NeuroTrace Research Platform</span>
          </div>
          <div style={{ display: 'flex', gap: 18 }}>
            <span>HIPAA-aligned</span><span>De-identified by default</span><span>© 2026</span>
          </div>
        </footer>
      </div>
    </div>
  );
}

Object.assign(window, { Landing });
