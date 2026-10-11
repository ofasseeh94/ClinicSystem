import type { DobPrecision } from '../../../packages/shared-contracts/registry';
export function clinicToday(): string {
  return new Intl.DateTimeFormat('en-CA', { timeZone: 'Africa/Cairo', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
}
export function age(dob: string, precision: DobPrecision, at = clinicToday()): string {
  if (precision !== 'exact') return 'Age uncertain';
  const [y, m, d] = dob.split('-').map(Number);
  const [ay, am, ad] = at.split('-').map(Number);
  const months = (ay - y) * 12 + am - m - (ad < d ? 1 : 0);
  if (months < 1) return `${Math.floor((Date.UTC(ay, am - 1, ad) - Date.UTC(y, m - 1, d)) / 86400000)} days`;
  if (months < 12) return `${months} months`;
  return `${Math.floor(months / 12)}y ${months % 12}m`;
}
export function dateLabel(value: string): string {
  return new Intl.DateTimeFormat('en-GB', { dateStyle: 'medium', timeZone: 'Africa/Cairo' }).format(new Date(value));
}
export function statusLabel(value: string): string { return value.replaceAll('_', ' '); }
