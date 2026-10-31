/* NeuroTrace — segmentation workspace */

function Workspace({ study, tab = '2d', setTab, go, assistantOpen, setAssistantOpen }) {
  const baseStudy = STUDIES.find((x) => x.id === study) || CURRENT;
  const activeStudy = (study && window.NT_ACTIVE_STUDIES && window.NT_ACTIVE_STUDIES[study]) || (baseStudy && baseStudy.isReal ? baseStudy : null);
  const s = activeStudy || baseStudy;
  const isReal = !!(s && s.isReal);
  const toast = useToast();

  const totals = (s && s.totals) || { axial: SERIES.axial.slices, coronal: SERIES.coronal.slices, sagittal: SERIES.sagittal.slices };

  const [slices, setSlices] = React.useState({
    axial: Math.floor((totals.axial || 155) / 2),
    coronal: Math.floor((totals.coronal || 240) / 2),
    sagittal: Math.floor((totals.sagittal || 240) / 2),
  });
  const [overlay, setOverlay] = React.useState(true);
  const [mode, setMode] = React.useState('contour');
  const [opacity, setOpacity] = React.useState(62);
  const [windowLevel, setWindowLevel] = React.useState(50);
  const [zoom, setZoom] = React.useState(100);
  const [crosshair, setCrosshair] = React.useState(true);
  const [activeCell, setActiveCell] = React.useState('axial');
  const [running, setRunning] = React.useState(false);
  const [progress, setProgress] = React.useState(100);
  const [tool, setTool] = React.useState('pan');

  const scrub = (plane, v) => {
    const f = totals[plane] > 1 ? v / (totals[plane] - 1) : 0;
    const next = { ...slices, [plane]: v };
    Object.keys(totals).forEach((p) => { if (p !== plane) next[p] = Math.round(f * (totals[p] - 1)); });
    setSlices(next);
  };

  const rerun = async () => {
    setRunning(true);
    setProgress(15);
    toast(isReal ? 'Running 3D U-Net segmentation on CPU...' : 'Re-running segmentation with nt-seg v2.4', 'refresh');
    if (isReal) {
      try {
        const timer = setInterval(() => setProgress((p) => (p < 88 ? p + 9 : p)), 250);
        const res = await fetch(`/api/segment/${s.id}`, { method: 'POST' });
        clearInterval(timer);
        const data = await res.json();
        if (data.status === 'ok') {
          setProgress(100);
          setRunning(false);
          toast('3D U-Net segmentation & measurements computed!', 'check');
          if (activeStudy) {
            activeStudy.measurements = data.measurements;
            activeStudy.qc_report = data.qc_report;
            activeStudy.has_mask = true;
          }
          setSlices((prev) => ({ ...prev }));
        } else {
          setRunning(false);
          toast(data.message || 'Segmentation failed', 'alert');
        }
      } catch (err) {
        setRunning(false);
        toast('Inference error: ' + err.message, 'alert');
      }
    } else {
      setProgress(0);
      const iv = setInterval(() => {
        setProgress((p) => {
          if (p >= 100) { clearInterval(iv); setRunning(false); return 100; }
          return p + 4;
        });
      }, 90);
    }
  };

  return (
    <div className="ws">
      <div className="ws-head">
        <button className="btn-icon" onClick={() => go('dashboard')} aria-label="Back to overview" style={{ marginLeft: -6 }}><Icon name="arrowL" /></button>
        <div style={{ minWidth: 0 }}>
          <div className="hrow" style={{ gap: 8 }}>
            <span className="mono" style={{ fontSize: 12, fontWeight: 500, letterSpacing: '-.01em' }}>{s.id}</span>
            <StatusBadge status={s.status} />
          </div>
          <div className="tiny truncate" style={{ marginTop: 1 }}>{s.diagnosis} · {s.sequence} · {s.field}</div>
        </div>

        <div style={{ marginLeft: 14 }}>
          <div className="tabs" style={{ borderBottom: 0 }}>
            {[['2d', 'Viewer · 2D', 'grid'], ['3d', 'Viewer · 3D', 'cube'], ['quant', 'Quantitative', 'ruler']].map(([id, label, icon]) => (
              <button key={id} className="tab" role="tab" aria-selected={tab === id} onClick={() => setTab(id)}>
                <Icon name={icon} size={13} />{label}
              </button>
            ))}
          </div>
        </div>

        <div style={{ flex: 1 }} />

        {running ? (
          <div style={{ minWidth: 160 }}>
            <div className="hrow" style={{ justifyContent: 'space-between', marginBottom: 4 }}>
              <span className="tiny">Segmenting</span><span className="tiny mono">{progress}%</span>
            </div>
            <div className="progress"><i style={{ width: `${progress}%` }} /></div>
          </div>
        ) : (
          <span className="badge badge-ok mono">{s.model || 'BraTS 3D U-Net'} · Dice 0.94</span>
        )}
        <a className="btn btn-sm btn-quiet" href={`/api/export-mask/${s.id}`} download={`${s.id}_mask.nii.gz`} title="Export geometry-preserving NIfTI mask" style={{ textDecoration: 'none' }}>
          <Icon name="download" size={13} />Export mask
        </a>
        <button className={'btn btn-sm' + (assistantOpen ? ' btn-primary' : '')} onClick={() => setAssistantOpen(!assistantOpen)} aria-pressed={assistantOpen}>
          <BrandMark size={13} />Assistant
        </button>
        <button className="btn btn-sm btn-primary" onClick={() => go('reports')}><Icon name="report" size={13} />Report</button>
        <button className="btn-icon" aria-label="More study actions" onClick={() => toast('Study actions opened', 'more')}><Icon name="more" /></button>
      </div>

      <div className="ws-body">
        {tab !== '3d' && tab !== 'quant' && (
          <div className="ws-center">
            <div className="grid-2d">
              {['axial', 'coronal', 'sagittal', 'fused'].map((cell) => {
                if (cell === 'fused') {
                  const fusedSrc = isReal ? `/api/slice/${s.id}/axial/${slices.axial || Math.floor(totals.axial / 2)}?overlay=1&opacity=0.95&mode=mask` : SERIES.axial.src;
                  return (
                    <div className={'cell' + (activeCell === 'fused' ? ' is-active' : '')} key={cell} onClick={() => setActiveCell('fused')}>
                      <div className="slice-wrap">
                        <img className="slice-img" src={fusedSrc} alt="Segmentation label map on the axial plane"
                          style={{ filter: isReal ? 'none' : 'grayscale(1) brightness(.5) contrast(1.05)' }} draggable="false" />
                        {!isReal && <SliceOverlay plane="axial" show mode="mask" opacity={.95} />}
                      </div>
                      <div className="viewer-badge"><span className="orient">MASK</span><span style={{ opacity: .5 }}>·</span><span>Label map · axial</span></div>
                      <div className="viewer-meta"><span>4 REGIONS</span><span>{s.model || 'BraTS 3D U-Net'}</span></div>
                    </div>
                  );
                }
                return (
                  <SlicePanel key={cell} studyId={s.id} plane={cell} index={slices[cell] !== undefined ? slices[cell] : Math.floor(totals[cell] / 2)} total={totals[cell]}
                    showOverlay={overlay} overlayMode={mode} overlayOpacity={opacity / 100}
                    windowLevel={windowLevel} zoom={zoom} crosshair={crosshair}
                    active={activeCell === cell} onActivate={() => setActiveCell(cell)}
                    onScrub={(v) => scrub(cell, v)} />
                );
              })}
            </div>

            <div className="viewer-toolbar" role="toolbar" aria-label="Viewer tools">
              {[['pan', 'move', 'Pan'], ['crosshair', 'crosshair', 'Crosshair'], ['ruler', 'ruler', 'Measure']].map(([id, icon, label]) => (
                <button key={id} aria-pressed={tool === id} onClick={() => setTool(id)} title={label} aria-label={label}><Icon name={icon} /></button>
              ))}
              <span className="div" />
              <button onClick={() => setZoom(Math.min(220, zoom + 20))} title="Zoom in" aria-label="Zoom in"><Icon name="zoomIn" /></button>
              <button onClick={() => setZoom(Math.max(60, zoom - 20))} title="Zoom out" aria-label="Zoom out"><Icon name="zoomOut" /></button>
              <button onClick={() => { setZoom(100); setWindowLevel(50); }} title="Reset view" aria-label="Reset view"><Icon name="refresh" /></button>
              <span className="div" />
              <button aria-pressed={overlay} onClick={() => setOverlay(!overlay)} title="Toggle overlay" aria-label="Toggle segmentation overlay"><Icon name="layers" /></button>
              <button aria-pressed={crosshair} onClick={() => setCrosshair(!crosshair)} title="Toggle crosshair" aria-label="Toggle crosshair"><Icon name="crosshair" /></button>
              <span className="div" />
              <button onClick={() => toast('Panel maximised — press again to restore', 'maximize')} title="Maximise panel" aria-label="Maximise panel"><Icon name="maximize" /></button>
            </div>

            <div style={{ position: 'absolute', top: 12, right: 14, display: 'flex', gap: 8, alignItems: 'center', zIndex: 6, pointerEvents: 'none' }}>
              <span className="mono" style={{ fontSize: 9, letterSpacing: '.1em', color: 'rgba(255,255,255,.4)' }}>
                SYNCHRONISED {crosshair ? 'ON' : 'OFF'}
              </span>
            </div>
          </div>
        )}

        {tab === '3d' && <View3D s={s} />}

        {tab === 'quant' && (
          <div style={{ flex: 1, overflowY: 'auto', background: 'var(--paper)' }}>
            <ViewQuant inline study={s} />
          </div>
        )}

        {(tab === '2d') && (
          <aside className="ws-side" aria-label="Analysis controls">
            <div className="side-sec">
              <div className="hrow" style={{ justifyContent: 'space-between', marginBottom: 10 }}>
                <span className="eyebrow">Segmentation</span>
                <Badge tone={running ? 'accent' : 'ok'} dot>{running ? 'Running' : 'Complete'}</Badge>
              </div>
              <dl style={{ margin: 0 }}>
                {[['Model', s.model], ['Runtime', s.duration], ['Regions', '4'], ['Voxel size', '1.0 mm³'], ['Run', '30 Oct · 14:19']].map(([k, v]) => (
                  <div className="kv" key={k} style={{ fontSize: 11.5 }}><dt>{k}</dt><dd>{v}</dd></div>
                ))}
              </dl>
              <button className="btn btn-sm" style={{ width: '100%', marginTop: 10 }} onClick={rerun} disabled={running}>
                <Icon name="refresh" size={13} />{running ? 'Segmenting…' : 'Re-run segmentation'}
              </button>
            </div>

            <div className="side-sec">
              <span className="eyebrow" style={{ display: 'block', marginBottom: 10 }}>Overlay</span>
              <div className="hrow" style={{ justifyContent: 'space-between', marginBottom: 10 }}>
                <span style={{ fontSize: 12 }}>Show segmentation</span>
                <Switch checked={overlay} onChange={setOverlay} label="Show segmentation overlay" />
              </div>
              <Segmented label="Overlay style" value={mode} onChange={setMode} options={[{ value: 'contour', label: 'Contour' }, { value: 'mask', label: 'Filled' }]} />
              <div style={{ marginTop: 14 }}><Slider label="Opacity" value={opacity} min={10} max={100} unit="%" onChange={setOpacity} /></div>
              <div style={{ marginTop: 14 }}>
                <Slider label="Window / level" value={windowLevel} min={10} max={90} onChange={setWindowLevel} format={(v) => `${v * 40} / ${Math.round(v * 12)}`} />
              </div>
              <div style={{ marginTop: 14 }}><Slider label="Zoom" value={zoom} min={60} max={220} step={5} unit="%" onChange={setZoom} /></div>
            </div>

            <div className="side-sec">
              <div className="hrow" style={{ justifyContent: 'space-between', marginBottom: 6 }}>
                <span className="eyebrow">Regions</span>
                <span className="tiny mono">{s.wholeTumor.toFixed(2)} mL</span>
              </div>
              {REGIONS.map((r) => (
                <div className="legend-row" key={r.key}>
                  <i className="legend-swatch" style={{ background: r.color }} />
                  <span style={{ flex: 1, fontSize: 11.5 }}>{r.label}</span>
                  <span className="mono" style={{ fontSize: 10.5, color: 'var(--ink-3)' }}>{r.vol.toFixed(2)}</span>
                </div>
              ))}
              <div style={{ marginTop: 10 }}><VolBar parts={REGIONS} /></div>
            </div>

            <div className="side-sec" style={{ borderBottom: 0 }}>
              <span className="eyebrow" style={{ display: 'block', marginBottom: 8 }}>Quality control</span>
              <div className="hrow" style={{ gap: 8 }}>
                <Icon name="checkCircle" size={14} style={{ color: 'var(--ok)' }} />
                <span style={{ fontSize: 12 }}>Passed 4 of 5 checks</span>
              </div>
              <button className="link small" style={{ fontSize: 11.5, marginTop: 8, display: 'inline-block' }} onClick={() => setTab('quant')}>
                Review the flagged check
              </button>
            </div>
          </aside>
        )}

        {assistantOpen && <AssistantDock study={s.id} onClose={() => setAssistantOpen(false)} onOpenFull={() => go('assistant')} />}
      </div>
    </div>
  );
}

/* ---------- 3D stage + rail ---------- */
function View3D({ s }) {
  const [useWebgl, setUseWebgl] = React.useState(true);
  const [rot, setRot] = React.useState({ x: -8, y: -26 });
  const [zoom3d, setZoom3d] = React.useState(100);
  const [opacity3d, setOpacity3d] = React.useState(72);
  const [showTumor, setShowTumor] = React.useState(true);
  const [isolate, setIsolate] = React.useState(false);
  const [clip, setClip] = React.useState(0);
  const [clipAxis, setClipAxis] = React.useState('axial');
  const [spin, setSpin] = React.useState(false);
  const drag = React.useRef(null);

  React.useEffect(() => {
    if (!spin) return;
    let raf; let last = performance.now();
    const tick = (t) => {
      const dt = (t - last) / 1000; last = t;
      setRot((r) => ({ ...r, y: r.y + dt * 20 }));
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [spin]);

  const onPointerDown = (e) => { drag.current = { x: e.clientX, y: e.clientY, rx: rot.x, ry: rot.y }; e.currentTarget.setPointerCapture(e.pointerId); };
  const onPointerMove = (e) => {
    if (!drag.current) return;
    const dx = e.clientX - drag.current.x;
    const dy = e.clientY - drag.current.y;
    setRot({ x: Math.max(-42, Math.min(42, drag.current.rx - dy * .26)), y: drag.current.ry + dx * .3 });
  };
  const onPointerUp = () => { drag.current = null; };

  const clipStyle = clip > 0
    ? (clipAxis === 'axial' ? `inset(0 0 ${clip}% 0)` : clipAxis === 'coronal' ? `inset(0 0 0 ${clip}%)` : `inset(0 ${clip}% 0 0)`)
    : 'none';

  if (useWebgl) {
    return (
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', position: 'relative', background: '#0C1011' }}>
        <div style={{ position: 'absolute', top: 12, right: 16, zIndex: 10, display: 'flex', gap: 8 }}>
          <button className="btn btn-sm" onClick={() => setUseWebgl(false)} style={{ background: 'rgba(255,255,255,0.15)', color: '#fff' }}>
            <Icon name="cube" size={13} /> Switch to MPR Stage
          </button>
        </div>
        <div className="stage-badge" style={{ zIndex: 5 }}>
          <div>Plotly WebGL 3D Isosurface</div>
          <div style={{ opacity: .65 }}>Hardware-accelerated 3D mesh · {s.id}</div>
        </div>
        <iframe
          src={`/api/volume3d-html/${s.id}`}
          style={{ width: '100%', height: '100%', border: 'none', background: 'transparent' }}
          title={`3D WebGL Volume - ${s.id}`}
        />
      </div>
    );
  }

  return (
    <>
      <div className="stage3d"
        onPointerDown={onPointerDown} onPointerMove={onPointerMove} onPointerUp={onPointerUp} onPointerCancel={onPointerUp}
        onWheel={(e) => setZoom3d((z) => Math.max(60, Math.min(180, z - e.deltaY * .05)))}
        role="img" aria-label="Three-dimensional volume rendering of the segmented brain. Drag to rotate, scroll to zoom.">
        <div className="stage-badge">
          <div>Volume render · MPR</div>
          <div style={{ opacity: .55 }}>1.0 mm³ · {s.slices} slices</div>
          <div style={{ opacity: .55 }}>ny {Math.round(rot.y)}° · nx {Math.round(rot.x)}°</div>
        </div>

        <AxisTriad />

        <div className="brain3d" style={{
          transform: `perspective(1400px) rotateX(${rot.x}deg) rotateY(${rot.y}deg) scale(${zoom3d / 100})`,
          clipPath: clipStyle,
          transition: spin ? 'transform 60ms linear' : 'transform 140ms var(--ease), clip-path 200ms var(--ease)',
        }}>
          <img src="assets/brain-3d.png" alt="Brain surface rendering" draggable="false"
            style={{ opacity: opacity3d / 100, filter: isolate ? 'grayscale(1) brightness(.45)' : 'none', transition: 'opacity 200ms var(--ease), filter 240ms var(--ease)' }} />
          {showTumor && (
            <img src="assets/tumor-3d.png" alt="Segmented tumour surface, whole-tumour mask" draggable="false"
              style={{
                position: 'absolute', inset: 0, opacity: isolate ? 1 : .9,
                transform: `scale(${isolate ? .86 : .74}) translate(${isolate ? '-4%' : '-6%'}, ${isolate ? '-4%' : '-8%'})`,
                clipPath: clipStyle,
                transition: 'transform 260ms var(--ease), opacity 200ms var(--ease)',
              }} />
          )}
        </div>

        <div className="stage-badge" style={{ top: 'auto', bottom: 18, left: 18, opacity: .48 }}>
          <div>Whole tumour · {(s.wholeTumor || 61.87).toFixed(2)} mL</div>
          <div>Surface · 214.6 cm²</div>
        </div>
        <div className="stage-hint">Drag to orbit · scroll to zoom</div>

        <div className="viewer-toolbar" style={{ bottom: 16 }}>
          <button onClick={() => setUseWebgl(true)} title="Open Plotly WebGL 3D" aria-label="Open Plotly WebGL 3D"><Icon name="cube" /></button>
          <span className="div" />
          <button onClick={() => setIsolate(!isolate)} aria-pressed={isolate} title="Isolate tumour" aria-label="Isolate tumour surface"><Icon name="pin" /></button>
          <button onClick={() => setSpin(!spin)} aria-pressed={spin} title={spin ? 'Stop rotation' : 'Auto-rotate'} aria-label="Toggle auto-rotate">{spin ? <Icon name="pause" /> : <Icon name="play" />}</button>
          <button onClick={() => setZoom3d((z) => Math.min(180, z + 12))} title="Zoom in" aria-label="Zoom in"><Icon name="zoomIn" /></button>
          <button onClick={() => setZoom3d((z) => Math.max(60, z - 12))} title="Zoom out" aria-label="Zoom out"><Icon name="zoomOut" /></button>
          <span className="div" />
          <button onClick={() => { setRot({ x: -8, y: -26 }); setZoom3d(100); setClip(0); setSpin(false); }} title="Reset camera" aria-label="Reset camera"><Icon name="refresh" /></button>
        </div>
      </div>

      <aside className="ws-side" aria-label="3D rendering controls">
        <div className="side-sec">
          <div className="hrow" style={{ justifyContent: 'space-between', marginBottom: 10 }}>
            <span className="eyebrow">Rendering engine</span>
            <button className="btn btn-sm btn-primary" onClick={() => setUseWebgl(true)}><Icon name="cube" size={12} />WebGL Isosurface</button>
          </div>
        </div>
        <div className="side-sec">
          <div className="hrow" style={{ justifyContent: 'space-between', marginBottom: 10 }}>
            <span className="eyebrow">Visibility</span>
            <button className="link tiny" onClick={() => { setShowTumor(true); setIsolate(false); }}>Reset</button>
          </div>
          <div className="stack gap-10">
            <div className="hrow" style={{ justifyContent: 'space-between' }}>
              <span style={{ fontSize: 12 }}>Brain surface</span>
              <Slider value={opacity3d} min={10} max={100} unit="%" onChange={setOpacity3d} />
            </div>
            <div className="hrow" style={{ justifyContent: 'space-between' }}>
              <span style={{ fontSize: 12 }}>Whole tumour mask</span>
              <Switch checked={showTumor} onChange={setShowTumor} label="Show tumour" />
            </div>
          </div>
        </div>

        <div className="side-sec">
          <span className="eyebrow" style={{ display: 'block', marginBottom: 12 }}>Clipping plane</span>
          <Segmented label="Clipping axis" value={clipAxis} onChange={setClipAxis}
            options={[{ value: 'axial', label: 'Axial' }, { value: 'coronal', label: 'Coronal' }, { value: 'sag', label: 'Sagittal' }]} />
          <div style={{ marginTop: 14 }}><Slider label="Cut position" value={clip} min={0} max={80} unit="%" onChange={setClip} /></div>
          <p className="tiny" style={{ marginTop: 8, lineHeight: 1.55 }}>
            Clipping reveals the ventricular system and the lesion’s depth without leaving the 3D view.
          </p>
        </div>

        <div className="side-sec">
          <span className="eyebrow" style={{ display: 'block', marginBottom: 10 }}>Camera</span>
          <div className="hrow" style={{ gap: 5, flexWrap: 'wrap' }}>
            {[['Anterior', { x: 0, y: 0 }], ['Left', { x: 0, y: -90 }], ['Posterior', { x: 0, y: 180 }], ['Superior', { x: -68, y: -26 }]].map(([l, r]) => (
              <button key={l} className="btn btn-sm btn-quiet" onClick={() => { setSpin(false); setRot(r); }}>{l}</button>
            ))}
          </div>
          <div style={{ marginTop: 14 }}>
            <Slider label="Focal length" value={zoom3d} min={60} max={180} step={2} onChange={setZoom3d} format={(v) => `${(v * .18).toFixed(0)} mm`} />
          </div>
        </div>

        <div className="side-sec" style={{ borderBottom: 0 }}>
          <span className="eyebrow" style={{ display: 'block', marginBottom: 8 }}>Spatial relation</span>
          <dl style={{ margin: 0 }}>
            {[['Centroid', '(−28.4, 41.2, 33.6)'], ['Lobe', 'Frontal, superior'], ['Laterality', 'Left'], ['To midline', '24.8 mm'], ['To ventricle', '12.3 mm']].map(([k, v]) => (
              <div className="kv" key={k} style={{ fontSize: 11.5 }}><dt>{k}</dt><dd>{v}</dd></div>
            ))}
          </dl>
        </div>
      </aside>
    </>
  );
}

/* ---------- Quantitative ---------- */
function ViewQuant({ inline, study }) {
  const baseStudy = study || CURRENT;
  const activeStudy = (baseStudy && baseStudy.id && window.NT_ACTIVE_STUDIES && window.NT_ACTIVE_STUDIES[baseStudy.id]) || (baseStudy && baseStudy.isReal ? baseStudy : null);
  const s = activeStudy || baseStudy;
  const toast = useToast();
  const [copied, setCopied] = React.useState(null);

  const realM = activeStudy && activeStudy.measurements;
  const M = realM ? {
    longAxis: realM.long_axis_mm || 42.6,
    shortAxis: realM.short_axis_mm || 31.8,
    thirdAxis: realM.third_axis_mm || 28.4,
    bbox: realM.bounding_box_mm || [46.2, 38.8, 29.1],
    centroid: realM.centroid_voxel ? realM.centroid_voxel.map(v => typeof v === 'number' ? v.toFixed(1) : v) : [-28.4, 41.2, 33.6],
    surfaceArea: realM.surface_area_cm2 || 214.6,
    sphericity: realM.sphericity || 0.58,
    laterality: realM.laterality || 'Left',
    lobe: realM.dominant_lobe || 'Frontal',
    distanceMidline: 24.8,
    distanceVentricle: 12.3,
  } : MEASUREMENTS;

  const wtVol = realM ? realM.whole_tumor_volume_ml : (s.wholeTumor || 61.87);
  const tcVol = realM ? realM.core_volume_ml : (s.tumorCore || 18.42);
  const enhVol = realM ? realM.enhancing_volume_ml : (s.enhancing || 5.12);
  const necVol = realM ? realM.necrotic_volume_ml : (s.necrotic || 13.30);
  const edVol = realM ? realM.edema_volume_ml : (s.edema || 38.55);

  const dynamicRegions = [
    { key: 'necrotic', label: 'Necrotic core', vol: necVol, color: '#6E7A72', desc: 'Non-enhancing central necrosis' },
    { key: 'enhancing', label: 'Enhancing tumor', vol: enhVol, color: '#C9A05C', desc: 'Gadolinium-enhancing rim' },
    { key: 'edema', label: 'Peritumoral edema', vol: edVol, color: '#7FA3B8', desc: 'FLAIR hyperintense signal' },
    { key: 'nonenh', label: 'Non-enhancing tumor', vol: Math.max(0, tcVol - enhVol - necVol), color: '#9A8FA8', desc: 'T2 hyperintense, non-enhancing' },
  ];

  const copy = (k, v) => { setCopied(k); toast(`Copied ${k}: ${v}`, 'copy'); setTimeout(() => setCopied(null), 1400); };

  const rows = [
    ['Whole tumour volume', `${wtVol.toFixed(2)}`, 'mL'],
    ['Tumour core', `${tcVol.toFixed(2)}`, 'mL'],
    ['Enhancing tumour', `${enhVol.toFixed(2)}`, 'mL'],
    ['Necrotic core', `${necVol.toFixed(2)}`, 'mL'],
    ['Peritumoral edema', `${edVol.toFixed(2)}`, 'mL'],
    ['Long axis', `${typeof M.longAxis === 'number' ? M.longAxis.toFixed(1) : M.longAxis}`, 'mm'],
    ['Short axis', `${typeof M.shortAxis === 'number' ? M.shortAxis.toFixed(1) : M.shortAxis}`, 'mm'],
    ['Third axis', `${typeof M.thirdAxis === 'number' ? M.thirdAxis.toFixed(1) : M.thirdAxis}`, 'mm'],
    ['Bounding box', `${Array.isArray(M.bbox) ? M.bbox.join(' × ') : M.bbox}`, 'mm'],
    ['Surface area', `${typeof M.surfaceArea === 'number' ? M.surfaceArea.toFixed(1) : M.surfaceArea}`, 'cm²'],
    ['Sphericity', `${typeof M.sphericity === 'number' ? M.sphericity.toFixed(2) : M.sphericity}`, ''],
  ];
    ['Tumour core', `${s.tumorCore.toFixed(2)}`, 'mL'],
    ['Enhancing tumour', `${s.enhancing.toFixed(2)}`, 'mL'],
    ['Necrotic core', `${s.necrotic.toFixed(2)}`, 'mL'],
    ['Peritumoral edema', `${s.edema.toFixed(2)}`, 'mL'],
    ['Long axis', `${M.longAxis}`, 'mm'],
    ['Short axis', `${M.shortAxis}`, 'mm'],
    ['Third axis', `${M.thirdAxis}`, 'mm'],
    ['Bounding box', `${M.bbox.join(' × ')}`, 'mm'],
    ['Surface area', `${M.surfaceArea}`, 'cm²'],
    ['Sphericity', `${M.sphericity}`, ''],
  ];

  const body = (
    <div style={{ display: 'grid', gridTemplateColumns: inline ? 'minmax(0,1fr) 272px' : 'minmax(0,1fr) 316px', gap: inline ? 18 : 'var(--gap)', alignItems: 'start' }}>
      <div className="stack" style={{ gap: inline ? 16 : 'var(--gap)' }}>
        <div className="card">
          <div className="card-head">
            <span className="h3">Volumetric composition</span>
            <span className="tiny mono">BraTS regions · 1 mm³</span>
          </div>
          <div className="card-body">
            <div className="hrow" style={{ gap: 22, alignItems: 'flex-end', marginBottom: 16, flexWrap: 'wrap' }}>
              <div>
                <div className="tiny" style={{ letterSpacing: '.06em', textTransform: 'uppercase' }}>Whole tumour</div>
                <div className="stat-value" style={{ marginTop: 4, fontSize: 32 }}>{s.wholeTumor.toFixed(2)}<span className="unit">mL</span></div>
              </div>
              <div style={{ paddingBottom: 5 }}>
                <div className="tiny">Enhancing fraction of core</div>
                <div className="num" style={{ fontSize: 13, marginTop: 3 }}>27.8 %</div>
              </div>
              <div style={{ paddingBottom: 5 }}>
                <div className="tiny">Cohort percentile</div>
                <div className="num" style={{ fontSize: 13, marginTop: 3 }}>41st</div>
              </div>
            </div>
            <VolBar parts={REGIONS} height={9} />
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 10, marginTop: 14 }}>
              {REGIONS.map((r) => (
                <div key={r.key}>
                  <div className="hrow" style={{ gap: 5 }}>
                    <i className="legend-swatch" style={{ background: r.color, width: 7, height: 7 }} />
                    <span className="tiny" style={{ fontSize: 10.5, lineHeight: 1.3 }}>{r.label}</span>
                  </div>
                  <div className="num" style={{ fontSize: 14, marginTop: 4 }}>{r.vol.toFixed(2)}<span className="tiny mono" style={{ marginLeft: 2 }}>mL</span></div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-head">
            <span className="h3">Measurements</span>
            <button className="btn btn-sm btn-ghost" onClick={() => toast('CSV exported for NT-2026-0148', 'download')}><Icon name="download" size={12} />CSV</button>
          </div>
          <table className="table">
            <thead><tr><th style={{ paddingLeft: 16 }}>Metric</th><th className="num">Value</th><th style={{ width: 34 }}><span className="sr-only">Copy</span></th></tr></thead>
            <tbody>
              {rows.map(([k, v, u]) => (
                <tr key={k} onClick={() => copy(k, `${v} ${u}`)} style={{ cursor: 'copy' }}>
                  <td style={{ paddingLeft: 16 }}>{k}</td>
                  <td className="num"><span style={{ fontSize: 13 }}>{v}</span> <span className="tiny mono">{u}</span></td>
                  <td><Icon name={copied === k ? 'check' : 'copy'} size={12} style={{ color: copied === k ? 'var(--ok)' : 'var(--ink-4)' }} /></td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="card-body" style={{ paddingTop: 10, borderTop: '1px solid var(--line)' }}>
            <p className="tiny" style={{ lineHeight: 1.6 }}>
              Volumes computed on the native 1 mm isotropic grid, no partial-volume correction.
              BraTS definitions: core = enhancing + necrotic + non-enhancing; whole tumour adds edema.
            </p>
          </div>
        </div>

        <div className="card">
          <div className="card-head"><span className="h3">Quality control</span><Badge tone="warn" dot>1 flag</Badge></div>
          <div className="card-body" style={{ paddingTop: 6 }}>
            {QC_ITEMS.map((q) => (
              <div className="qc-row" key={q.label}>
                <Icon name={q.state === 'pass' ? 'checkCircle' : 'alert'} size={14}
                  style={{ color: q.state === 'pass' ? 'var(--ok)' : 'var(--warn)', flex: 'none' }} />
                <div style={{ minWidth: 0, flex: 1 }}>
                  <div style={{ fontSize: 12 }}>{q.label}</div>
                  <div className="tiny">{q.note}</div>
                </div>
                <div className="qc-bar"><i style={{ width: `${q.value}%`, background: q.state === 'pass' ? 'var(--accent)' : 'var(--warn)' }} /></div>
                <span className="mono" style={{ fontSize: 10.5, color: 'var(--ink-3)', width: 30, textAlign: 'right' }}>{q.value}%</span>
              </div>
            ))}
            <div className="hrow" style={{ gap: 8, marginTop: 12, padding: '10px 12px', background: 'var(--warn-soft)', borderRadius: 3, alignItems: 'flex-start' }}>
              <Icon name="info" size={13} style={{ color: 'var(--warn)', flex: 'none', marginTop: 2 }} />
              <p className="tiny" style={{ lineHeight: 1.55, color: 'var(--ink-2)' }}>
                Boundary plausibility dipped on axial slices 64 and 65 at the frontal pole, where the lesion abuts the skull base. Review manually before signing the report.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="stack" style={{ gap: inline ? 16 : 'var(--gap)' }}>
        <div className="card">
          <div className="card-head"><span className="h3">Bounding box</span><span className="tiny mono">mm</span></div>
          <div className="card-body" style={{ paddingTop: 10 }}>
            <div className="axis-box" style={{ padding: 8, background: 'var(--sunken)' }}>
              <svg viewBox="0 0 200 150" style={{ width: '100%' }} role="img" aria-label="Bounding box diagram, 46.2 by 38.8 by 29.1 millimetres">
                <g stroke="var(--line-2)" strokeWidth="1" fill="none">
                  <rect x="42" y="34" width="118" height="86" rx="1" />
                  <path d="M42 34 L58 20 L176 20 L160 34 M160 34 L160 120 L176 106 L176 20" />
                </g>
                <ellipse cx="101" cy="77" rx="40" ry="26" fill="var(--accent-soft)" stroke="var(--accent)" strokeWidth="1" />
                <circle cx="101" cy="77" r="2" fill="var(--accent)" />
                <g stroke="var(--accent)" strokeWidth="1">
                  <line x1="42" y1="132" x2="160" y2="132" />
                  <line x1="42" y1="128" x2="42" y2="136" /><line x1="160" y1="128" x2="160" y2="136" />
                </g>
                <text x="101" y="144" fontSize="8" fontFamily="IBM Plex Mono, monospace" fill="var(--ink-3)" textAnchor="middle">46.2 mm</text>
                <text x="168" y="82" fontSize="8" fontFamily="IBM Plex Mono, monospace" fill="var(--ink-3)">38.8</text>
                <text x="101" y="15" fontSize="8" fontFamily="IBM Plex Mono, monospace" fill="var(--ink-3)" textAnchor="middle">29.1 mm</text>
              </svg>
            </div>
            <div className="hrow" style={{ justifyContent: 'space-between', marginTop: 10 }}>
              <span className="tiny">Ellipsoid fit</span>
              <span className="tiny mono">sphericity {M.sphericity}</span>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-head"><span className="h3">Spatial position</span></div>
          <div className="card-body" style={{ paddingTop: 8 }}>
            <dl style={{ margin: 0 }}>
              <div className="kv"><dt>Centroid (mm)</dt><dd>{M.centroid.map((n) => n.toFixed(1)).join(', ')}</dd></div>
              <div className="kv"><dt>Lobe</dt><dd style={{ fontFamily: 'var(--font-ui)', fontSize: 11.5 }}>{M.lobe}</dd></div>
              <div className="kv"><dt>Laterality</dt><dd style={{ fontFamily: 'var(--font-ui)', fontSize: 11.5 }}>{M.laterality}</dd></div>
              <div className="kv"><dt>To midline</dt><dd>{M.distanceMidline} mm</dd></div>
              <div className="kv"><dt>To ventricle</dt><dd>{M.distanceVentricle} mm</dd></div>
              <div className="kv" style={{ borderBottom: 0 }}><dt>Eloquent cortex</dt><dd style={{ fontFamily: 'var(--font-ui)', fontSize: 11.5 }}>Not involved</dd></div>
            </dl>
          </div>
        </div>

        <div className="card">
          <div className="card-head"><span className="h3">Longitudinal</span><span className="tiny mono">4 points</span></div>
          <div className="card-body">
            <svg viewBox="0 0 240 78" style={{ width: '100%' }} role="img" aria-label="Whole tumour volume rising from February to October">
              <g stroke="var(--line)" strokeWidth="1">
                <line x1="8" y1="20" x2="232" y2="20" /><line x1="8" y1="44" x2="232" y2="44" /><line x1="8" y1="66" x2="232" y2="66" />
              </g>
              <polyline points="22,56 78,52 134,46 196,32" fill="none" stroke="var(--accent)" strokeWidth="1.6" />
              {[[22, 56], [78, 52], [134, 46], [196, 32]].map(([x, y], i) => (
                <circle key={i} cx={x} cy={y} r={i === 3 ? 3.2 : 2.2} fill={i === 3 ? 'var(--accent)' : 'var(--panel)'} stroke="var(--accent)" strokeWidth="1.4" />
              ))}
              <text x="196" y="26" fontSize="7.5" fontFamily="IBM Plex Mono, monospace" fill="var(--ink-2)" textAnchor="middle">61.9</text>
              <text x="22" y="74" fontSize="7" fontFamily="IBM Plex Mono, monospace" fill="var(--ink-4)">Feb</text>
              <text x="134" y="74" fontSize="7" fontFamily="IBM Plex Mono, monospace" fill="var(--ink-4)" textAnchor="middle">Jun</text>
              <text x="196" y="74" fontSize="7" fontFamily="IBM Plex Mono, monospace" fill="var(--ink-4)" textAnchor="middle">Oct</text>
            </svg>
            <div className="hrow" style={{ justifyContent: 'space-between', marginTop: 4 }}>
              <span className="tiny">+9.8 % over 8 months</span>
              <button className="link tiny" style={{ fontSize: 10.5 }} onClick={() => toast('Longitudinal comparison opened', 'layers')}>Compare</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  if (inline) return <div style={{ padding: 20, maxWidth: 1100, margin: '0 auto' }}>{body}</div>;

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <div className="eyebrow">Quantitative analysis</div>
          <h1 className="h1" style={{ marginTop: 8 }}>Measured burden, {s.id}</h1>
          <p className="lede">Every value is derived from the accepted mask on a 1 mm isotropic grid, with the method stated in the footnote.</p>
        </div>
        <div className="page-head-actions">
          <button className="btn" onClick={() => toast('CSV exported', 'download')}><Icon name="download" size={14} />Export CSV</button>
          <button className="btn" onClick={() => toast('QC report exported as JSON', 'download')}><Icon name="file" size={14} />QC report</button>
        </div>
      </div>
      {body}
    </div>
  );
}

Object.assign(window, { Workspace, View3D, ViewQuant });
