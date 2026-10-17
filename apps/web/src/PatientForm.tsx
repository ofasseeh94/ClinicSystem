import { useEffect, useRef, useState, type FormEvent, type MouseEvent } from 'react';
import type { ApiProblem, FormDefinition, PatientInput, PatientRecord, PatientSummary } from '../../../packages/shared-contracts/registry';
import { request, RequestError } from './api';
import { BackgroundFields } from './BackgroundFields';
import { clinicToday } from './format';
const empty: PatientInput = { name_ar: '', name_en: '', dob: '', dob_precision: 'exact', dob_source: 'guardian',
  growth_reference_sex: 'unknown', guardian: { name: '', phone_e164: '', relation: 'unknown' }, aliases: [],
  allergy_review_status: 'unknown', allergies: [] };
function toInput(p: PatientRecord): PatientInput {
  return { name_ar: p.name_ar, name_en: p.name_en, dob: p.dob, dob_precision: p.dob_precision, dob_source: p.dob_source,
    growth_reference_sex: p.growth_reference_sex, guardian: p.guardian, aliases: p.aliases,
    allergy_review_status: p.allergy_review_status, allergies: p.allergies };
}
interface Props { token: string; patient?: PatientRecord; saved: (patient: PatientRecord, startVisit?: boolean) => void; canStartVisit?: boolean; cancel: () => void; openCandidate: (id: string) => void }
export function PatientForm({ token, patient, saved, cancel, openCandidate, canStartVisit }: Props) {
  const [data, setData] = useState<PatientInput>(patient ? toInput(patient) : empty);
  const [aliases, setAliases] = useState(patient?.aliases.join(', ') ?? '');
  const [expanded, setExpanded] = useState(false);
  const [definition, setDefinition] = useState<FormDefinition>();
  const [answers, setAnswers] = useState<Record<string, unknown>>({});
  const [reason, setReason] = useState('');
  const [duplicateReason, setDuplicateReason] = useState('');
  const [candidates, setCandidates] = useState<PatientSummary[]>([]);
  const [error, setError] = useState<ApiProblem>();
  const [saving, setSaving] = useState(false);
  const retry = useRef({ payload: '', key: '' });
  useEffect(() => { let active = true;
    request<FormDefinition>(token, '/v1/forms/background/versions/2').then(d => { if (active) setDefinition(d); }).catch(e => { if (active) setError(e.problem); });
    return () => { active = false; };
  }, [token]);
  function field<K extends keyof PatientInput>(key: K, value: PatientInput[K]) { setData({ ...data, [key]: value }); }
  async function submit(e: FormEvent, startVisit = false) {
    e.preventDefault();
    if (!data.name_ar.trim() && !data.name_en.trim()) { setError({ title: 'name_required', status: 422, detail: 'Enter at least one Arabic or English name.' }); return; }
    setSaving(true); setError(undefined);
    const input = { ...data, aliases: aliases.split(',').map(v => v.trim()).filter(Boolean) };
    const payload = JSON.stringify(patient ? { ...input, audit_reason: reason } : {
      ...input, ...(Object.keys(answers).length && definition ? { background: { form_key: definition.form_key, version: definition.version, answers } } : {}),
      ...(candidates.length && duplicateReason ? { duplicate_review_reason: duplicateReason } : {}),
    });
    if (retry.current.payload !== payload) retry.current = { payload, key: crypto.randomUUID() };
    try {
      const result = await request<PatientRecord>(token, patient ? `/v1/patients/${patient.patient_id}` : '/v1/patients', {
        method: patient ? 'PATCH' : 'POST', body: payload,
        headers: patient ? { 'If-Match': `"${patient.version}"` } : { 'Idempotency-Key': retry.current.key },
      }); saved(result, startVisit);
    } catch (e) {
      const problem = e instanceof RequestError ? e.problem : { title: 'unexpected', status: 0, detail: 'Unable to save. Please try again.' };
      setError(problem); if (problem.candidates) setCandidates(problem.candidates);
    } finally { setSaving(false); }
  }
  return <section className="panel form-panel"><div className="panel-heading"><div><p className="eyebrow">PATIENT REGISTRY</p>
    <h2>{patient ? 'Correct patient details' : 'Register a patient'}</h2><p className="muted">{patient ? 'Changes keep their history and require a correction reason.' : 'Start with the essentials. Add medical background when available.'}</p></div>
    <button type="button" className="secondary" disabled={saving} onClick={cancel}>Cancel</button></div>
    <form onSubmit={e => submit(e)}><fieldset disabled={saving}>{error && <div className="notice error" role="alert"><strong>{error.detail}</strong>
      {error.fields && <p>Fields to check: {error.fields.map(f => f.replace('body.', '').replaceAll('_', ' ')).join(', ')}</p>}
      {error.status === 412 && <button type="button" className="secondary" onClick={() => patient && openCandidate(patient.patient_id)}>Reload current record</button>}</div>}
    {candidates.length > 0 && <div className="notice duplicate"><h3>Possible existing records</h3><p>Open an existing record, or explain why this is a separate patient. Records are never merged automatically.</p>
      {candidates.map(c => <div className="candidate" key={c.patient_id}><span dir="auto">{c.name_en || c.name_ar} · {c.clinic_code} · {c.dob} · {c.masked_phone}</span><button type="button" className="secondary" onClick={() => openCandidate(c.patient_id)}>Open record</button></div>)}
      <label>Reason for creating a separate record<input minLength={5} maxLength={500} required value={duplicateReason} onChange={e => setDuplicateReason(e.target.value)} /></label></div>}
    <h3 className="section-heading"><span>01</span> Patient details</h3><div className="field-grid">
      <label>English name<input autoFocus dir="auto" maxLength={160} value={data.name_en} onChange={e => field('name_en', e.target.value)} autoComplete="off" /></label>
      <label>Arabic name<input dir="rtl" lang="ar" maxLength={160} value={data.name_ar} onChange={e => field('name_ar', e.target.value)} autoComplete="off" /></label>
      <label>Date of birth<input type="date" required min="1900-01-01" max={clinicToday()} value={data.dob} onChange={e => field('dob', e.target.value)} /></label>
      <label>Birth date precision<select value={data.dob_precision} onChange={e => field('dob_precision', e.target.value as PatientInput['dob_precision'])}><option value="exact">Exact date</option><option value="estimated">Estimated date</option><option value="month">Month known only</option><option value="year">Year known only</option></select></label>
      <label>Birth date source<select value={data.dob_source} onChange={e => field('dob_source', e.target.value as PatientInput['dob_source'])}><option value="guardian">Guardian reported</option><option value="document">Document</option><option value="imported">Imported</option><option value="unknown">Unknown</option></select></label>
      <label>Sex for growth reference<select value={data.growth_reference_sex} onChange={e => field('growth_reference_sex', e.target.value as PatientInput['growth_reference_sex'])}><option value="unknown">Unknown / not recorded</option><option value="female">Female</option><option value="male">Male</option></select></label>
    </div>{data.dob_precision !== 'exact' && <p className="hint">Use the earliest known date as an anchor (first day of the month or year). Exact age calculations remain unavailable.</p>}
    <h3 className="section-heading"><span>02</span> Guardian contact</h3><div className="field-grid">
      <label>Guardian full name<input dir="auto" required minLength={2} maxLength={160} value={data.guardian.name} onChange={e => field('guardian', { ...data.guardian, name: e.target.value })} autoComplete="off" /></label>
      <label>Guardian phone<input type="tel" required placeholder="+201000000000" maxLength={30} value={data.guardian.phone_e164} onChange={e => field('guardian', { ...data.guardian, phone_e164: e.target.value })} autoComplete="off" /></label>
      <label>Relationship<select value={data.guardian.relation} onChange={e => field('guardian', { ...data.guardian, relation: e.target.value as PatientInput['guardian']['relation'] })}><option value="unknown">Unknown</option><option value="mother">Mother</option><option value="father">Father</option><option value="guardian">Guardian</option><option value="other">Other</option></select></label>
      <label>Other names / aliases<input dir="auto" maxLength={1600} placeholder="Separate with commas" value={aliases} onChange={e => setAliases(e.target.value)} /></label>
    </div><p className="hint">Contact details do not verify guardian authority or grant parent access.</p>
    <h3 className="section-heading"><span>03</span> Allergy review</h3><label className="half">Allergy review status<select value={data.allergy_review_status} onChange={e => {
      const status = e.target.value as PatientInput['allergy_review_status']; setData({ ...data, allergy_review_status: status, allergies: status === 'known' ? [{ substance: '', reaction: '' }] : [] });
    }}><option value="unknown">Unknown</option><option value="not_assessed">Not assessed</option><option value="no_known">Reviewed: no known allergies</option><option value="known">Known allergies</option></select></label>
    {data.allergy_review_status === 'known' && <div className="allergy-fields">{data.allergies.map((a, i) => <div className="field-grid" key={i}>
      <label>Allergy substance {i + 1}<input dir="auto" required maxLength={160} value={a.substance} onChange={e => field('allergies', data.allergies.map((v, n) => n === i ? { ...v, substance: e.target.value } : v))} /></label>
      <label>Allergy reaction {i + 1}<input dir="auto" required maxLength={500} value={a.reaction} onChange={e => field('allergies', data.allergies.map((v, n) => n === i ? { ...v, reaction: e.target.value } : v))} /></label>
    </div>)}{data.allergies.length < 30 && <button type="button" className="secondary" onClick={() => field('allergies', [...data.allergies, { substance: '', reaction: '' }])}>Add allergy</button>}</div>}
    {!patient && <div className="expandable"><button type="button" className="expand-button" aria-expanded={expanded} onClick={() => setExpanded(!expanded)}><span><strong>Medical & birth background</strong><small>Optional · Versioned form · Unknown answers allowed</small></span><span>{expanded ? '−' : '+'}</span></button>
      {expanded && (definition ? <BackgroundFields definition={definition} answers={answers} onChange={setAnswers} /> : <p role="status">Background form unavailable. You can save the essential details and add history later.</p>)}</div>}
    {patient && <label>Correction reason<textarea required minLength={5} maxLength={500} value={reason} onChange={e => setReason(e.target.value)} /></label>}
    <div className="form-footer"><p className="hint">{patient ? 'Previous details stay in the restricted audit history.' : 'A unique clinic code is assigned after saving.'}</p>{!patient && canStartVisit && <button className="primary" type="button" disabled={saving} onClick={(e: MouseEvent<HTMLButtonElement>) => { const form = e.currentTarget.form!; if (form.reportValidity()) void submit(e, true); }}>Register and start visit</button>}<button className="secondary" type="submit" disabled={saving}>{saving ? 'Saving…' : patient ? 'Save correction' : 'Register patient'}</button></div>
    </fieldset></form></section>;
}
