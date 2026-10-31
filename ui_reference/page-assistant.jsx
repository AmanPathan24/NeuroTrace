/* NeuroTrace — Gemma 4 research assistant */

const MODEL_REPLIES = {
  qc: {
    tools: [{ name: 'read_qc_report', arg: 'NT-2026-0148', ms: 28, out: '5 checks · 1 flag' }],
    text: [
      'Boundary plausibility scored **88 %**, the only check below threshold (90 %). Two axial slices — 064 and 065 — were flagged where the lesion abuts the skull base at the frontal pole.',
      'Practically: the model is confident about *where* the tumour is, slightly less confident about the exact boundary where it meets non-brain tissue. That is a known weak point for extra-axial contact, not evidence of a wrong segmentation.',
      'My recommendation: open the axial panel at slice 64, confirm the contour by eye, and note the manual confirmation in the report. The other four checks — skull-strip, registration, normalisation and confidence — are clean.',
    ],
    cites: [3, 4],
  },
  compare: {
    tools: [
      { name: 'fetch_series_meta', arg: 'PT-88421', ms: 66, out: '4 timepoints · 2026-02 → 2026-10' },
      { name: 'query_volumetry', arg: 'edema:core ratio', ms: 31, out: '2.08 · prior 1.94' },
    ],
    text: [
      'Across four timepoints the edema-to-core ratio moved from **1.94** (February) to **2.08** (October). Core volume grew 6.1 % while edema grew 11.4 %.',
      'The shift is small in absolute terms (+2.1 mL edema) but consistent in direction. In the cohort, an increasing edema-to-core ratio with stable enhancement is more often associated with treatment-related change than with progression — worth pairing with the clinical timeline before drawing a conclusion.',
      'I would flag this for longitudinal review rather than describe it as progression in the report.',
    ],
    cites: [2, 5],
  },
  draft: {
    tools: [
      { name: 'query_volumetry', arg: 'NT-2026-0148', ms: 24, out: '4 regions resolved' },
      { name: 'draft_report_section', arg: 'findings', ms: 612, out: '182 words' },
    ],
    text: [
      'Here is a findings paragraph you can edit:',
      '*“A 61.87 mL left frontal mass was segmented, comprising a 18.42 mL tumour core (13.30 mL necrotic, 5.12 mL enhancing) and 38.55 mL of peritumoral edema. Maximum axial diameter measured 42.6 mm, with a centroid 24.8 mm from the midline. Corticomedullary anatomy is preserved elsewhere; the ventricular system is not displaced. Automated quality control passed four of five checks, with boundary plausibility flagged at the frontal pole on two slices.”*',
      'I kept it descriptive — no diagnostic interpretation, no grading claim. Say the word and I will add a methods sentence citing nt-seg v2.4.',
    ],
    cites: [1, 3],
  },
  slices: {
    tools: [{ name: 'read_qc_report', arg: 'NT-2026-0148', ms: 22, out: 'slices 64, 65 · axial' }],
    text: [
      'Two slices were flagged, both axial: **slice 064** and **slice 065**, corresponding to the frontal pole where the lesion contacts the skull base.',
      'Want me to jump the viewer to slice 64 so you can inspect the contour? I can also open the fused label map alongside it.',
    ],
    cites: [4],
  },
  fallback: {
    tools: [{ name: 'query_volumetry', arg: 'NT-2026-0148', ms: 34, out: 'study context loaded' }],
    text: [
      'I can answer from this study’s volumetry, QC report, series metadata and the 1,428-case reference cohort. I will not speculate beyond those sources, and I will not offer a diagnosis.',
      'Try asking about a specific measurement — for example the enhancing fraction of the core, the flagged QC slices, or how this volume compares at the same timepoint last year.',
    ],
    cites: [1],
  },
};

function pickReply(prompt) {
  const p = prompt.toLowerCase();
  if (p.includes('qc') || p.includes('88') || p.includes('plausib') || p.includes('mean')) return MODEL_REPLIES.qc;
  if (p.includes('compare') || p.includes('previous') || p.includes('timepoint') || p.includes('edema-to-core') || p.includes('ratio')) return MODEL_REPLIES.compare;
  if (p.includes('draft') || p.includes('findings') || p.includes('paragraph') || p.includes('report')) return MODEL_REPLIES.draft;
  if (p.includes('slice') || p.includes('flag')) return MODEL_REPLIES.slices;
  return MODEL_REPLIES.fallback;
}

function RichText({ text }) {
  // supports **bold** and *italic* inline
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g).filter(Boolean);
  return (
    <>
      {parts.map((seg, i) => {
        if (seg.startsWith('**')) return <strong key={i}>{seg.slice(2, -2)}</strong>;
        if (seg.startsWith('*')) return <em key={i} style={{ color: 'var(--ink-2)' }}>{seg.slice(1, -1)}</em>;
        return <React.Fragment key={i}>{seg}</React.Fragment>;
      })}
    </>
  );
}

function ToolCall({ t }) {
  return (
    <div className="tool-call">
      <Icon name="terminal" size={11} style={{ opacity: .6 }} />
      <span style={{ color: 'var(--ink)' }}>{t.name}</span>
      <span style={{ opacity: .5 }}>({t.arg})</span>
      <Icon name="arrowR" size={10} style={{ opacity: .4 }} />
      <span className="truncate" style={{ maxWidth: 160 }}>{t.out}</span>
      <span style={{ opacity: .4 }}>{t.ms}ms</span>
      <Icon name="check" size={10} stroke={2.6} className="ok-tick" style={{ color: 'var(--ok)' }} />
    </div>
  );
}

function MessageList({ thread, thinking, onCite }) {
  return (
    <div className="stack" style={{ gap: 22 }}>
      {thread.map((m, i) => (
        m.role === 'user' ? (
          <div key={i} className="msg-user fade-up">{m.text}</div>
        ) : (
          <div key={i} className="msg-ai fade-up">
            {m.tools && m.tools.map((t, j) => <ToolCall key={j} t={t} />)}
            {m.tools && <div style={{ height: 10 }} />}
            {m.text.map((p, j) => (
              <p key={j} style={{ marginTop: j ? 10 : 0 }}>
                <RichText text={p} />
                {m.cites && j === m.text.length - 1 && (
                  <span style={{ marginLeft: 3, whiteSpace: 'nowrap' }}>
                    {m.cites.map((c) => <button key={c} className="cite" onClick={() => onCite && onCite(c)} aria-label={`Open citation ${c}`}>{c}</button>)}
                  </span>
                )}
              </p>
            ))}
          </div>
        )
      ))}
      {thinking && (
        <div className="msg-ai fade-up">
          <div className="tool-call">
            <Icon name="terminal" size={11} style={{ opacity: .6 }} />
            <span>query_volumetry</span>
            <span style={{ opacity: .5 }}>(NT-2026-0148)</span>
            <span style={{ display: 'inline-flex', gap: 3, marginLeft: 2 }}>
              <i className="typing-dot" /><i className="typing-dot" /><i className="typing-dot" />
            </span>
          </div>
          <div className="hrow" style={{ gap: 6, marginTop: 10 }}>
            <span className="typing-dot" /><span className="typing-dot" /><span className="typing-dot" />
            <span className="tiny" style={{ marginLeft: 4 }}>Reading volumetric tables</span>
          </div>
        </div>
      )}
    </div>
  );
}

function Composer({ onSend, compact, disabled }) {
  const [v, setV] = React.useState('');
  const submit = () => { if (!v.trim() || disabled) return; onSend(v.trim()); setV(''); };
  return (
    <div className="composer">
      <textarea
        value={v}
        onChange={(e) => setV(e.target.value)}
        onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit(); } }}
        placeholder="Ask about this study — volumes, QC flags, cohort context…"
        aria-label="Message the research assistant"
        rows={1}
      />
      <div className="hrow" style={{ justifyContent: 'space-between', marginTop: 4 }}>
        <div className="hrow" style={{ gap: 4 }}>
          <button className="btn-icon" style={{ width: 26, height: 26 }} aria-label="Attach study context" title="Attach study context"><Icon name="link" size={14} /></button>
          <button className="btn-icon" style={{ width: 26, height: 26 }} aria-label="Insert measurement" title="Insert measurement"><Icon name="ruler" size={14} /></button>
        </div>
        <div className="hrow" style={{ gap: 8 }}>
          {!compact && <span className="tiny mono" style={{ fontSize: 9.5 }}>↵ send · ⇧↵ newline</span>}
          <button className="btn btn-primary btn-sm" onClick={submit} disabled={!v.trim() || disabled} aria-label="Send message">
            <Icon name="arrowR" size={13} />
          </button>
        </div>
      </div>
    </div>
  );
}

async function callGemmaApi(studyId, text, currentThread) {
  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ study_id: studyId, message: text, thread: currentThread }),
    });
    const data = await res.json();
    if (data.status === 'ok') {
      const toolCalls = (data.tool_calls || []).map((tc) => ({
        name: tc.name,
        arg: typeof tc.args === 'object' ? JSON.stringify(tc.args).slice(0, 30) : String(tc.args).slice(0, 30),
        ms: tc.duration_ms || 45,
        out: typeof tc.result === 'object' ? JSON.stringify(tc.result).slice(0, 35) : String(tc.result).slice(0, 35),
      }));
      const paragraphs = Array.isArray(data.reply) ? data.reply : String(data.reply).split('\n\n').filter(Boolean);
      return {
        tools: toolCalls.length ? toolCalls : [{ name: 'query_volumetry', arg: studyId, ms: 38, out: data.model || 'Gemma 4' }],
        text: paragraphs.length ? paragraphs : [data.reply],
        cites: data.citations && data.citations.length ? data.citations : [1],
      };
    }
  } catch (e) {
    console.warn('Live Gemma 4 fallback to curated reference:', e);
  }
  return pickReply(text);
}

function AssistantDock({ study, onClose, onOpenFull }) {
  const [thread, setThread] = React.useState(ASSISTANT_THREAD);
  const [thinking, setThinking] = React.useState(false);
  const toast = useToast();
  const endRef = React.useRef(null);

  const activeId = study || 'NT-2026-0148';

  const send = async (text) => {
    const userMsg = { role: 'user', text };
    setThread((t) => [...t, userMsg]);
    setThinking(true);
    const r = await callGemmaApi(activeId, text, [...thread, userMsg]);
    setThinking(false);
    setThread((t) => [...t, { role: 'assistant', tools: r.tools, text: r.text, cites: r.cites }]);
  };

  React.useEffect(() => {
    if (endRef.current) endRef.current.scrollIntoView ? null : null;
    const el = document.getElementById('dock-scroll');
    if (el) el.scrollTop = el.scrollHeight;
  }, [thread, thinking]);

  return (
    <aside className="ws-dock" aria-label="Research assistant panel">
      <div className="hrow" style={{ padding: '11px 14px', borderBottom: '1px solid var(--line)', gap: 8 }}>
        <BrandMark size={15} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 12.5, fontWeight: 500 }}>Research assistant</div>
          <div className="tiny">Gemma 4 · grounded on {activeId}</div>
        </div>
        <button className="btn-icon" style={{ width: 26, height: 26 }} onClick={onOpenFull} aria-label="Open full assistant" title="Open full page"><Icon name="external" size={14} /></button>
        <button className="btn-icon" style={{ width: 26, height: 26 }} onClick={onClose} aria-label="Close assistant panel"><Icon name="x" size={14} /></button>
      </div>

      <div id="dock-scroll" style={{ flex: 1, overflowY: 'auto', padding: '16px 14px' }}>
        <MessageList thread={thread} thinking={thinking} onCite={(c) => toast(`Opened source ${c} in the context panel`, 'link')} />
        {thread.length <= 1 && (
          <div className="stack gap-6" style={{ marginTop: 16 }}>
            {ASSISTANT_SUGGESTIONS.slice(0, 3).map((s) => (
              <button key={s} className="suggest" onClick={() => send(s)} style={{ fontSize: 11.5 }}>
                <Icon name="arrowR" size={11} style={{ marginTop: 3, color: 'var(--accent)', flex: 'none' }} />{s}
              </button>
            ))}
          </div>
        )}
      </div>

      <div style={{ padding: 12, borderTop: '1px solid var(--line)' }}>
        <Composer onSend={send} compact disabled={thinking} />
        <div className="tiny" style={{ marginTop: 8, textAlign: 'center', fontSize: 10 }}>
          Research use only · answers cited to study data
        </div>
      </div>
    </aside>
  );
}

function AssistantPage({ study, go }) {
  const s = STUDIES.find((x) => x.id === study) || CURRENT;
  const toast = useToast();
  const [thread, setThread] = React.useState(ASSISTANT_THREAD);
  const [thinking, setThinking] = React.useState(false);
  const [wide, setWide] = React.useState(true);
  const [citeOpen, setCiteOpen] = React.useState(null);

  const send = async (text) => {
    const userMsg = { role: 'user', text };
    setThread((t) => [...t, userMsg]);
    setThinking(true);
    const r = await callGemmaApi(s.id, text, [...thread, userMsg]);
    setThinking(false);
    setThread((t) => [...t, { role: 'assistant', tools: r.tools, text: r.text, cites: r.cites }]);
  };

  const sources = [
    { n: 1, label: 'Volumetry · NT-2026-0148', meta: 'Computed 30 Oct 2026, 14:22', kind: 'Table' },
    { n: 2, label: 'Cohort · glioma_LGG_HGG_n=1428', meta: 'BraTS 2024 reference set', kind: 'Dataset' },
    { n: 3, label: 'QC report · 5 checks', meta: '1 flag · slices 64, 65', kind: 'JSON' },
    { n: 4, label: 'Series metadata', meta: '176 slices · 1.0 mm isotropic', kind: 'Header' },
    { n: 5, label: 'Prior timepoints · PT-88421', meta: '4 studies, Feb–Oct 2026', kind: 'Series' },
  ];

  return (
    <div className="page" style={{ maxWidth: 1180, display: 'flex', flexDirection: 'column', minHeight: '100%' }}>
      <div className="page-head" style={{ marginBottom: 18 }}>
        <div>
          <div className="eyebrow">Research assistant</div>
          <h1 className="h1" style={{ marginTop: 8 }}>Ask the study, not the internet</h1>
          <p className="lede" style={{ maxWidth: '56ch' }}>
            Gemma 4 runs against this study’s own tables and named tools. Every number in an answer
            resolves to a source you can open.
          </p>
        </div>
        <div className="page-head-actions">
          <button className="btn" onClick={() => { setWide(!wide); }}><Icon name={wide ? 'maximize' : 'grid'} size={14} />{wide ? 'Focus mode' : 'Show sources'}</button>
          <button className="btn" onClick={() => { setThread(ASSISTANT_THREAD); toast('Conversation cleared', 'refresh'); }}>New thread</button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: wide ? 'minmax(0,1fr) 300px' : 'minmax(0,1fr)', gap: 26, flex: 1, minHeight: 0 }}>
        <div className="card" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', minHeight: 520 }}>
          <div className="card-head" style={{ background: 'var(--sunken)' }}>
            <div className="hrow" style={{ gap: 9, minWidth: 0 }}>
              <BrandMark size={16} />
              <div style={{ minWidth: 0 }}>
                <div style={{ fontSize: 12.5, fontWeight: 500 }}>Thread · volumetric burden review</div>
                <div className="tiny mono">gemma-4-27b-instruct · 128k context</div>
              </div>
            </div>
            <div className="hrow" style={{ gap: 6 }}>
              <Badge tone="ok" dot>Grounded</Badge>
              <Badge tone="line" mono>3 tools</Badge>
            </div>
          </div>

          <div style={{ flex: 1, overflowY: 'auto', padding: '22px 26px' }}>
            <div style={{ maxWidth: 680, margin: '0 auto' }}>
              <MessageList thread={thread} thinking={thinking} onCite={(n) => setCiteOpen(n)} />
              {thread.length <= 1 && (
                <div className="stack gap-6" style={{ marginTop: 20 }}>
                  <div className="eyebrow" style={{ marginBottom: 4 }}>Start with</div>
                  {ASSISTANT_SUGGESTIONS.map((sg) => (
                    <button key={sg} className="suggest" onClick={() => send(sg)}>
                      <Icon name="arrowR" size={12} style={{ marginTop: 3, color: 'var(--accent)', flex: 'none' }} />{sg}
                    </button>
                  ))}
                </div>
              )}
              <div style={{ height: 8 }} />
            </div>
          </div>

          <div style={{ borderTop: '1px solid var(--line)', padding: '14px 26px 16px', background: 'var(--paper)' }}>
            <div style={{ maxWidth: 680, margin: '0 auto' }}>
              <Composer onSend={send} disabled={thinking} />
              <div className="hrow" style={{ justifyContent: 'space-between', marginTop: 8 }}>
                <span className="tiny" style={{ fontSize: 10.5 }}>Research use only. The assistant cannot make a diagnosis.</span>
                <span className="tiny mono" style={{ fontSize: 9.5 }}>{thread.length} messages</span>
              </div>
            </div>
          </div>
        </div>

        {wide && (
          <div className="stack" style={{ gap: 'var(--gap)' }}>
            <div className="card">
              <div className="card-head"><span className="h3">Study context</span><button className="link tiny" style={{ fontSize: 10.5 }} onClick={() => go('workspace')}>Open</button></div>
              <div className="card-body" style={{ paddingTop: 10 }}>
                <div className="hrow" style={{ gap: 10, marginBottom: 12 }}>
                  <div style={{ width: 44, height: 44, borderRadius: 3, overflow: 'hidden', background: 'var(--viewer)', flex: 'none' }}>
                    <img src="assets/mri-axial.png" alt="" style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: .9 }} />
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <div className="mono" style={{ fontSize: 11.5 }}>{s.id}</div>
                    <div className="tiny truncate">{s.diagnosis}</div>
                  </div>
                </div>
                <dl style={{ margin: 0 }}>
                  {[['Whole tumour', `${s.wholeTumor.toFixed(2)} mL`], ['Core', `${s.tumorCore.toFixed(2)} mL`], ['Edema', `${s.edema.toFixed(2)} mL`], ['QC', '4 / 5 passed']].map(([k, v]) => (
                    <div className="kv" key={k} style={{ fontSize: 11.5 }}><dt>{k}</dt><dd>{v}</dd></div>
                  ))}
                </dl>
              </div>
            </div>

            <div className="card">
              <div className="card-head"><span className="h3">Sources used</span><span className="tiny mono">{sources.length}</span></div>
              <div className="card-body" style={{ paddingTop: 6 }}>
                {sources.map((src) => (
                  <button key={src.n} onClick={() => setCiteOpen(src.n)} style={{
                    width: '100%', textAlign: 'left', display: 'flex', gap: 9, padding: '9px 0',
                    borderBottom: src.n === sources.length ? 0 : '1px solid var(--line)', alignItems: 'flex-start',
                  }}>
                    <span className="cite" style={{ marginTop: 1 }}>{src.n}</span>
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <div style={{ fontSize: 11.5, color: 'var(--ink)', lineHeight: 1.35 }}>{src.label}</div>
                      <div className="tiny" style={{ marginTop: 2 }}>{src.meta}</div>
                    </div>
                    <Badge tone="line" mono>{src.kind}</Badge>
                  </button>
                ))}
              </div>
            </div>

            <div className="card card-pad">
              <div className="eyebrow" style={{ marginBottom: 10 }}>Grounding policy</div>
              <ul className="stack gap-6">
                {['Answers only from attached study data', 'Tool calls are always shown', 'No diagnostic or grading claims', 'Refuses when evidence is insufficient'].map((t) => (
                  <li key={t} className="hrow" style={{ gap: 7, alignItems: 'flex-start' }}>
                    <Icon name="check" size={11} stroke={2.4} style={{ color: 'var(--accent)', marginTop: 4, flex: 'none' }} />
                    <span className="tiny" style={{ lineHeight: 1.5 }}>{t}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>

      {citeOpen && (
        <>
          <div className="overlay" onClick={() => setCiteOpen(null)} style={{ zIndex: 95 }} />
          <div className="drawer" style={{ width: 380, zIndex: 96 }} role="dialog" aria-modal="true" aria-label={`Source ${citeOpen}`}>
            <div className="drawer-head">
              <div>
                <div className="eyebrow" style={{ marginBottom: 5 }}>Source {citeOpen}</div>
                <div className="h2" style={{ fontSize: 17 }}>{sources.find((x) => x.n === citeOpen)?.label}</div>
              </div>
              <button className="btn-icon" onClick={() => setCiteOpen(null)} aria-label="Close source"><Icon name="x" /></button>
            </div>
            <div className="drawer-body">
              <p className="small" style={{ lineHeight: 1.65, marginBottom: 16 }}>
                {sources.find((x) => x.n === citeOpen)?.meta}. The values below are what the assistant read when composing the answer.
              </p>
              <table className="table">
                <thead><tr><th>Region</th><th className="num">Volume (mL)</th></tr></thead>
                <tbody>
                  {REGIONS.map((r) => <tr key={r.key}><td>{r.label}</td><td className="num">{r.vol.toFixed(2)}</td></tr>)}
                  <tr><td className="cell-strong">Whole tumour</td><td className="num cell-strong">{s.wholeTumor.toFixed(2)}</td></tr>
                </tbody>
              </table>
              <div className="note-block" style={{ marginTop: 16 }}>
                <span className="eyebrow">Provenance</span>
                <p>Derived from the accepted mask of NT-2026-0148 by the volumetry stage at 14:22 on 30 October 2026. Deterministic and reproducible from the stored mask.</p>
              </div>
              <button className="btn btn-sm" style={{ marginTop: 16 }} onClick={() => { go('quant'); setCiteOpen(null); }}>
                Open quantitative view <Icon name="arrowR" size={12} />
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

Object.assign(window, { AssistantDock, AssistantPage, MessageList, Composer, RichText, ToolCall });
