import { useEffect, useState, type FormEvent } from 'react';
import type { Encounter, EncounterNote, EncounterPage, Measurement } from '../../../packages/shared-contracts/encounters';
import { request } from './api';
import { statusLabel } from './format';

function dateLabel(value: string) { return new Intl.DateTimeFormat('en-GB', {dateStyle:'medium',timeStyle:'short',timeZone:'Africa/Cairo'}).format(new Date(value)); }
function fieldLabel(value: string) { const label = statusLabel(value); return label[0].toUpperCase()+label.slice(1); }

function localInput(value = new Date().toISOString()) {
  const d = new Date(value); return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0,16);
}
function iso(value: string) { return new Date(value).toISOString(); }
function measurementAge(m: Measurement, v: Encounter) {
  if (v.birth_context.precision !== 'exact') return 'Exact age at measurement unavailable';
  const parts = new Intl.DateTimeFormat('en-CA', {timeZone:'Africa/Cairo',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date(m.measured_at));
  const get = (type: string) => parts.find(p => p.type === type)!.value;
  const observed = Date.parse(`${get('year')}-${get('month')}-${get('day')}T00:00:00Z`);
  return `${Math.round((observed - Date.parse(v.birth_context.dob+'T00:00:00Z')) / 86400000)} days old at measurement`;
}
const sections = ['history', 'examination', 'assessment', 'plan'] as const;
export function Encounters({ token, patientId, onDirty }: { token: string; patientId: string; onDirty: (dirty: boolean) => void }) {
  const base = `/v1/patients/${patientId}/encounters`;
  const [page, setPage] = useState(1);
  const [timeline, setTimeline] = useState<EncounterPage>();
  const [visit, setVisit] = useState<Encounter>();
  const [note, setNote] = useState<EncounterNote>();
  const [measurements, setMeasurements] = useState<Measurement[]>([]);
  const [creating, setCreating] = useState(false);
  const [when, setWhen] = useState(localInput());
  const [reason, setReason] = useState('');
  const [consent, setConsent] = useState('');
  const [changeReason, setChangeReason] = useState('');
  const [addendum, setAddendum] = useState('');
  const [key, setKey] = useState(crypto.randomUUID());
  const [addendumKey, setAddendumKey] = useState(crypto.randomUUID());
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [canWrite, setCanWrite] = useState(false);
  const dirty = !!visit && (JSON.stringify(note) !== JSON.stringify(visit.note) || JSON.stringify(measurements) !== JSON.stringify(visit.measurements));
  const unsaved = dirty || (creating && !!(reason || consent)) || !!addendum;
  useEffect(() => { onDirty(unsaved); return () => onDirty(false); }, [unsaved, onDirty]);
  useEffect(() => {
    function warn(e: BeforeUnloadEvent) { if (unsaved) { e.preventDefault(); e.returnValue = ''; } }
    window.addEventListener('beforeunload', warn); return () => window.removeEventListener('beforeunload', warn);
  }, [unsaved]);
  function select(v: Encounter) { setVisit(v); setNote(v.note); setMeasurements(v.measurements); setChangeReason(''); setAddendum(''); setError(''); }
  async function refresh() { setTimeline(await request<EncounterPage>(token, `${base}?page=${page}`)); }
  useEffect(() => { let active = true;
    request<EncounterPage>(token, `${base}?page=${page}`).then(p => { if (active) setTimeline(p); }).catch(e => { if (active) setError(e.message); });
    request<{ roles: string[] }>(token, '/v1/session').then(s => { if (active) setCanWrite(s.roles.some(r => ['admin','clinician'].includes(r))); }).catch(e => { if (active) setError(e.message); });
    return () => { active = false; };
  }, [token, base, page]);
  async function perform(action: () => Promise<Encounter>) {
    setBusy(true); setError('');
    try { const v = await action(); select(v); setCreating(false); await refresh(); }
    catch (e) { setError(e instanceof Error ? e.message : 'Unable to save visit.'); }
    finally { setBusy(false); }
  }
  function start(e: FormEvent) { e.preventDefault(); void perform(() => request<Encounter>(token, base, {method:'POST',body:JSON.stringify({request_id:key,occurred_at:iso(when),reason,consent_context:consent})})); }
  function save(e: FormEvent) { e.preventDefault(); void perform(() => request<Encounter>(token, `${base}/${visit!.id}`, {method:'PUT',headers:{'If-Match':`"${visit!.version}"`},body:JSON.stringify({note,measurements,audit_reason:changeReason})})); }
  function transition(status: Encounter['status']) { void perform(() => request<Encounter>(token, `${base}/${visit!.id}/status`, {method:'POST',headers:{'If-Match':`"${visit!.version}"`},body:JSON.stringify({status,reason:changeReason})})); }
  function append(e: FormEvent) { e.preventDefault(); void perform(() => request<Encounter>(token, `${base}/${visit!.id}/addenda`, {method:'POST',body:JSON.stringify({request_id:addendumKey,reason:changeReason,content:addendum})})); }
  const editable = canWrite && visit?.status === 'draft';
  function editMeasurement(index: number, changes: Partial<Measurement>) { setMeasurements(old => old.map((m,i) => i === index ? {...m,...changes} : m)); }
  return <div className="encounter-layout">
    <section className="panel"><div className="panel-heading compact"><h3>Visit timeline</h3><button className="primary" disabled={busy || unsaved || !canWrite} onClick={() => {setCreating(true);setVisit(undefined);setReason('');setConsent('');setWhen(localInput());setKey(crypto.randomUUID());setError('');}}>Start visit</button></div>
      {!timeline && !error && <p>Loading visits…</p>}{timeline?.total === 0 && <p className="muted">No encounters recorded yet.</p>}
      {timeline?.items.map(v => <button className={`visit-item ${visit?.id === v.id ? 'selected' : ''}`} key={v.id} disabled={busy || unsaved} onClick={() => void perform(() => request<Encounter>(token, `${base}/${v.id}`))}><strong dir="auto">{v.reason}</strong><span>{dateLabel(v.occurred_at)} · {statusLabel(v.status)}</span></button>)}
      {timeline && timeline.total > 20 && <div className="actions"><button disabled={page === 1 || dirty || busy} onClick={() => setPage(page-1)}>Previous</button><span>Page {page}</span><button disabled={page*20 >= timeline.total || dirty || busy} onClick={() => setPage(page+1)}>Next</button></div>}
    </section>
    <section className="panel encounter-detail">{error && <p role="alert" className="notice error">{error} Unsaved entries remain here. Reload the visit to review its latest version.</p>}
      {creating ? <form onSubmit={start}><fieldset disabled={busy}><h3>Start a dated visit</h3><label>Visit date and time (device local time)<input type="datetime-local" required value={when} onChange={e => {setWhen(e.target.value);setKey(crypto.randomUUID());}}/></label><label>Visit reason<textarea required maxLength={1000} value={reason} onChange={e => {setReason(e.target.value);setKey(crypto.randomUUID());}}/></label><label>Consent context<textarea required maxLength={1000} value={consent} onChange={e => {setConsent(e.target.value);setKey(crypto.randomUUID());}}/></label><p className="hint">Record the actual context and limitations. This does not verify guardian authority.</p><button className="primary" disabled={busy}>Create draft visit</button> <button type="button" className="secondary" disabled={busy} onClick={() => {setCreating(false);setReason('');setConsent('');setError('');}}>Discard new visit</button></fieldset></form> : visit && note ? <>
        <div className="panel-heading compact"><h3 dir="auto">{visit.reason}</h3><span className="chip">{statusLabel(visit.status)} · v{visit.version}</span></div><p className="muted">{dateLabel(visit.occurred_at)} · {visit.created_by}</p>
        <p className="source-note">Birth context: {visit.birth_context.dob} ({visit.birth_context.precision}) · {visit.birth_context.age_days === null ? 'Exact age unavailable' : `${visit.birth_context.age_days} days old at visit`} · Patient version {visit.birth_context.patient_version}</p><p className="hint" dir="auto">Consent context: {visit.consent_context}</p>
        <form onSubmit={save}><fieldset disabled={!editable || busy}><legend className="sr-only">Encounter note</legend>{sections.map(s => <label key={s}>{fieldLabel(s)}<textarea rows={4} maxLength={10000} value={note[s]} onChange={e => setNote({...note,[s]:e.target.value})}/></label>)}
          <div className="field-grid">{(['allergy_review','medication_review'] as const).map(s => <label key={s}>{fieldLabel(s)}<select aria-label={fieldLabel(s)} value={note[s]} onChange={e => setNote({...note,[s]:e.target.value as EncounterNote[typeof s]})}><option value="not_reviewed">Not reviewed</option><option value="reviewed">Reviewed</option></select></label>)}</div>
          <h3 className="measurement-heading">Dated measurements</h3><p className="hint">Raw observations only. No growth percentiles, corrected age or clinical interpretation.</p>
          {measurements.map((m,i) => <div className="measurement-entry" key={i}><p className="source-note">{measurementAge(m, visit)}</p><div className="field-grid"><label>Measured at (device local time)<input type="datetime-local" required value={localInput(m.measured_at)} onChange={e => {if(e.target.value) editMeasurement(i,{measured_at:iso(e.target.value)});}}/></label>{(['weight_kg','length_cm','head_cm'] as const).map((s,j) => <label key={s}>{['Weight (kg)','Length / height (cm)','Head circumference (cm)'][j]}<input type="number" step="any" min="0.001" value={m[s] ?? ''} onChange={e => editMeasurement(i,{[s]:e.target.value === '' ? null : Number(e.target.value)})}/></label>)}
          <label>Position<select aria-label="Position" value={m.position} onChange={e => editMeasurement(i,{position:e.target.value as Measurement['position']})}>{['unknown','recumbent','standing'].map(s => <option key={s}>{s}</option>)}</select></label><label>Source<select aria-label="Source" value={m.source} onChange={e => editMeasurement(i,{source:e.target.value as Measurement['source']})}>{['clinic','guardian_report','external_record'].map(s => <option key={s} value={s}>{statusLabel(s)}</option>)}</select></label><label>Technique<input required maxLength={300} value={m.technique} onChange={e => editMeasurement(i,{technique:e.target.value})}/></label><label>Equipment / reported device<input required maxLength={300} value={m.equipment} onChange={e => editMeasurement(i,{equipment:e.target.value})}/></label></div><button type="button" className="text-button" onClick={() => setMeasurements(measurements.filter((_,j) => j !== i))}>Remove draft measurement</button></div>)}
          <button type="button" className="secondary" disabled={measurements.length >= 50} onClick={() => setMeasurements([...measurements,{measured_at:visit.occurred_at,weight_kg:null,length_cm:null,head_cm:null,position:'unknown',source:'clinic',technique:'',equipment:''}])}>Add measurement</button>
        </fieldset>
        {canWrite && !['signed','cancelled'].includes(visit.status) && <><label>Reason for save or status change<input disabled={busy} required minLength={5} maxLength={500} value={changeReason} onChange={e => setChangeReason(e.target.value)}/></label><div className="actions">{editable && <button className="primary" disabled={busy || !dirty}>Save draft</button>}<button type="button" className="secondary" disabled={busy || dirty || changeReason.trim().length < 5} onClick={() => transition(visit.status === 'draft' ? 'in_review' : 'draft')}>{visit.status === 'draft' ? 'Submit for review' : 'Return to draft'}</button>{visit.status === 'in_review' && <button type="button" className="primary" disabled={busy || changeReason.trim().length < 5} onClick={() => transition('signed')}>Sign encounter</button>}<button type="button" className="secondary" disabled={busy || dirty || changeReason.trim().length < 5} onClick={() => transition('cancelled')}>Cancel encounter</button></div></>}
        </form>
        {visit.signed_at && <p className="notice">Signed {dateLabel(visit.signed_at)} by {visit.signed_by}. This snapshot is immutable.</p>}{visit.cancellation_reason && <p className="notice" dir="auto">Cancellation: {visit.cancellation_reason}</p>}
        {visit.addenda.map(a => <article className="history-entry" key={a.id}><h3>Signed addendum</h3><p className="source-note">{dateLabel(a.signed_at)} · {a.signed_by} · {a.reason}</p><p className="note-content" dir="auto">{a.content}</p></article>)}
        {canWrite && visit.status === 'signed' && <form onSubmit={append}><h3>Add a signed addendum</h3><label>Correction reason<input disabled={busy} required minLength={5} maxLength={500} value={changeReason} onChange={e => {setChangeReason(e.target.value);setAddendumKey(crypto.randomUUID());}}/></label><label>Addendum text<textarea disabled={busy} required maxLength={10000} value={addendum} onChange={e => {setAddendum(e.target.value);setAddendumKey(crypto.randomUUID());}}/></label><p className="hint">Signing preserves the original note and appends an attributed correction.</p><button className="primary" disabled={busy}>Sign addendum</button></form>}
        {dirty && <p className="hint">Unsaved changes. Save before changing visits or status.</p>}<button className="text-button" disabled={busy} onClick={() => {if (!unsaved || window.confirm('Discard unsaved changes and reload this visit?')) void perform(() => request<Encounter>(token, `${base}/${visit.id}`));}}>Reload visit</button>
      </> : <div className="small-empty"><h3>Longitudinal encounter record</h3><p>Select a visit or start a new one.</p><p className="muted">Signed records stay unchanged. Corrections are linked as signed addenda.</p></div>}
    </section></div>;
}
