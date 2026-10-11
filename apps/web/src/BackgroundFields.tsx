import type { FormDefinition } from '../../../packages/shared-contracts/registry';
import { statusLabel } from './format';
interface Props { definition: FormDefinition; answers: Record<string, unknown>; onChange: (answers: Record<string, unknown>) => void }
export function BackgroundFields({ definition, answers, onChange }: Props) {
  function change(key: string, value: unknown) {
    const next = { ...answers };
    if (value === '') delete next[key]; else next[key] = value;
    onChange(next);
  }
  return <div className="field-grid background-fields">{definition.schema.fields.map(field => <label key={field.key}>
    {field.label}
    {field.type === 'enum' ? <select value={String(answers[field.key] ?? '')} required={field.required}
      onChange={e => change(field.key, e.target.value)}>
      <option value="">Not recorded</option>{field.options!.map(option => <option key={option} value={option}>{statusLabel(option)}</option>)}
    </select> : field.type === 'text' ? <textarea dir="auto" maxLength={field.max_length} value={String(answers[field.key] ?? '')}
      onChange={e => change(field.key, e.target.value)} /> : <input type="number" min={field.min} max={field.max}
      step={field.type === 'integer' ? 1 : 'any'} value={String(answers[field.key] ?? '')}
      onChange={e => change(field.key, e.target.value === '' ? '' : Number(e.target.value))} />}
  </label>)}</div>;
}
