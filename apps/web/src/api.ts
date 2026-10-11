import type { ApiProblem } from '../../../packages/shared-contracts/registry';
export class RequestError extends Error {
  constructor(public problem: ApiProblem) { super(problem.detail); }
}
export async function request<T>(token: string, path: string, options: RequestInit = {}): Promise<T> {
  let result: Response;
  try {
    result = await fetch(`/api${path}`, {
      ...options, headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}`, ...options.headers },
    });
  } catch {
    throw new RequestError({ title: 'connection_failed', status: 0, detail: 'The clinic server is unavailable. Your changes have not been saved.' });
  }
  if (!result.ok) {
    let problem: ApiProblem = { title: 'request_failed', status: result.status, detail: 'The request could not be completed. Please try again.' };
    try { problem = await result.json(); } catch { /* Keep the safe generic error. */ }
    if (!problem.detail) problem.detail = 'The clinic server is unavailable. Your changes have not been saved.';
    throw new RequestError(problem);
  }
  return result.json();
}
