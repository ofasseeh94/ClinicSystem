import { useEffect, useState, type FormEvent } from 'react';
import type { FormDefinition, PatientRecord } from '../../../packages/shared-contracts/registry';
import { request, RequestError } from './api';
import { age, dateLabel, statusLabel } from './format';
import { BackgroundFields } from './BackgroundFields';
import { Encounters } from './Encounters';
const modules = ['Overview', 'Encounters', 'Growth', 'Vaccines', 'Development', 'Medications', 'Investigations', 'Documents', 'Tasks'];
interface Props { token: string; patient: PatientRecord; edit: () => void; back: () => void; saved: (p: PatientRecord) => void; onDirty: (dirty: boolean) => void }
export function PatientOverview({ token, patient, edit, back, saved, onDirty }: Props) {
  const [tab, setTab] = useState('Overview');
  const [encounterDirty, setEncounterDirty] = useState(false);
  useEffect(() => { onDirty(encounterDirty); return () => onDirty(false); }, [encounterDirty, onDirty]);
  const [adding, setAdding] = useState(false);
  const [definition, setDefinition] = useState<FormDefinition>();
  const [answers, setAnswers] = useState<Record<string, unknown>>({});
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  useEffect(() => { let active = true;
    request<FormDefinition>(token, '/v1/forms/background/versions/2').then(d => { if (active) setDefinition(d); }).catch(() => {});
    return () => { active = false; };
  }, [token]);
  async function submit(e: FormEvent) {
    e.preventDefault(); setSaving(true); setError('');
    try {
      const p = await request<PatientRecord>(token, `/v1/patients/${patient.patient_id}/form-responses`, { method: 'POST',
        headers: { 'If-Match': `"${patient.version}"` }, body: JSON.stringify({ form_key: 'background', version: definition!.version, answers }) });
      saved(p); setAdding(false); setAnswers({});
    } catch (e) { setError(e instanceof RequestError ? e.message : 'Unable to save history.'); }
    finally { setSaving(false); }
  }
  const allergy = patient.allergy_review_status;
  return <div><button className="text-button" disabled={encounterDirty} onClick={back}>← All patients</button>
    <section className="patient-header panel"><div className="avatar">{(patient.name_en || patient.name_ar).slice(0, 1)}</div>
      <div className="patient-title"><p className="eyebrow">{patient.clinic_code} · ACTIVE RECORD</p><h2 dir="auto">{patient.name_en || patient.name_ar}</h2>
        {patient.name_ar && patient.name_en && <p dir="rtl" lang="ar" className="arabic-name">{patient.name_ar}</p>}
        <p className="muted">{age(patient.dob, patient.dob_precision)} · {patient.dob} · Growth reference: {patient.growth_reference_sex}</p></div>
      <button className="secondary" disabled={encounterDirty} onClick={edit}>Correct details</button></section>
    <div className={`allergy-banner ${allergy === 'no_known' ? 'reviewed' : 'needs-review'}`}><strong>Allergy review: {allergy === 'no_known' ? 'no known allergies' : statusLabel(allergy)}</strong>
      <span>{allergy === 'known' ? patient.allergies.map(a => `${a.substance}: ${a.reaction}`).join(' · ') : allergy === 'no_known' ? 'Recorded as reviewed. Check again at the next encounter.' : 'Confirm allergy history before clinical decisions.'}</span></div>
    <div className="record-tabs" role="tablist" aria-label="Patient sections">{modules.map(m => <button key={m} role="tab" id={`tab-${m}`} aria-controls={`panel-${m}`} aria-selected={tab === m} disabled={encounterDirty && tab !== m} onClick={() => setTab(m)}>{m}</button>)}</div>
    <section role="tabpanel" id={`panel-${tab}`} aria-labelledby={`tab-${tab}`}>
      {tab === 'Encounters' ? <Encounters token={token} patientId={patient.patient_id} onDirty={setEncounterDirty} /> : tab !== 'Overview' ? <div className="panel empty-state"><span className="empty-symbol">○</span><h3>{tab} will be built in a later unit</h3><p>This section has no records or clinical calculations yet.</p><p className="muted">Patient identity and saved background remain available in Overview.</p></div> : <div className="overview-grid">
        <section className="panel"><h3>Identity & contact</h3><dl><dt>Date of birth</dt><dd>{patient.dob} <span className="chip">{patient.dob_precision}</span></dd><dt>Birth date source</dt><dd>{patient.dob_source}</dd>
          <dt>Guardian</dt><dd dir="auto">{patient.guardian.name}</dd><dt>Phone</dt><dd>{patient.guardian.phone_e164}</dd><dt>Relationship</dt><dd>{patient.guardian.relation}</dd>
          <dt>Guardian authority</dt><dd><span className="chip">{patient.contact_authority}</span></dd><dt>Aliases</dt><dd dir="auto">{patient.aliases.join(', ') || 'Not recorded'}</dd></dl>
          <p className="source-note">Source: staff registration · Updated {dateLabel(patient.updated_at)} · Version {patient.version}</p></section>
        <section className="panel background-card"><div className="panel-heading compact"><h3>Medical & birth background</h3><button className="secondary" disabled={!definition || adding} onClick={() => setAdding(true)}>Add background</button></div>
          {adding && <form onSubmit={submit} className="background-add">{error && <p role="alert" className="notice error">{error}</p>}{definition && <BackgroundFields definition={definition} answers={answers} onChange={setAnswers} />}
            <p className="hint">Adds a new dated response. Previous background entries stay unchanged.</p><div className="actions"><button type="button" className="secondary" onClick={() => { setAdding(false); setError(''); }}>Cancel</button><button className="primary" disabled={saving || Object.keys(answers).length === 0}>{saving ? 'Saving…' : 'Save background'}</button></div></form>}
          {patient.background_responses.length === 0 ? <div className="small-empty"><p>No background history recorded.</p><p className="muted">Missing answers do not mean a negative medical history.</p></div> :
            [...patient.background_responses].reverse().map(r => <article className="history-entry" key={r.id}><p className="source-note">{dateLabel(r.created_at)} · Form {r.form_key} v{r.version} · Staff recorded</p>
              <dl>{Object.entries(r.answers).map(([key, value]) => <div key={key}><dt>{r.schema_definition.fields.find(f => f.key === key)?.label ?? key}</dt><dd dir="auto">{statusLabel(String(value))}</dd></div>)}</dl></article>)}
        </section><section className="panel full-width"><h3>Record activity</h3><div className="activity-row"><span className="activity-dot"/><div><strong>Patient record created</strong><p className="muted">{dateLabel(patient.created_at)} · {patient.created_by}</p></div></div>
          <p className="source-note">Identity corrections are retained in restricted audit records. Visit notes and dated measurements are available in Encounters.</p></section>
      </div>}
    </section></div>;
}
