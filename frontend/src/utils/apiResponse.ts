const responseDetail = (body: unknown): string | null => {
  if (!body || typeof body !== 'object' || !('detail' in body)) return null;
  return typeof body.detail === 'string' ? body.detail : null;
};

export const parseApiResponse = async <T>(response: Response): Promise<T> => {
  const contentType = response.headers.get('content-type')?.toLowerCase() ?? '';
  if (!contentType.includes('application/json')) {
    throw new Error('api_response_invalid');
  }

  let body: unknown;
  try {
    body = await response.json();
  } catch {
    throw new Error('api_response_invalid');
  }

  if (!response.ok) {
    throw new Error(responseDetail(body) ?? `HTTP ${response.status}`);
  }
  return body as T;
};
