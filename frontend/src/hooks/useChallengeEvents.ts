import { useEffect, useRef } from 'react';
import { useAuth } from '@clerk/clerk-react';

interface ChallengeEvent {
  type: string;
  [key: string]: unknown;
}

/**
 * Subscribe to real-time SSE events for a challenge.
 * Calls onEvent whenever the server pushes an update.
 */
export function useChallengeEvents(
  challengeId: number | undefined,
  onEvent: (event: ChallengeEvent) => void,
) {
  const { getToken } = useAuth();
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  useEffect(() => {
    if (!challengeId) return;

    let eventSource: EventSource | null = null;
    let cancelled = false;

    async function connect() {
      const token = await getToken();
      if (cancelled || !token) return;

      // EventSource doesn't support custom headers, so pass token as query param
      // Backend will need to accept this — but for now we use a fetch-based approach
      const response = await fetch(`/api/challenges/${challengeId}/events`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (cancelled || !response.body) return;

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (!cancelled) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              onEventRef.current(data);
            } catch {
              // ignore parse errors
            }
          }
        }
      }
    }

    connect();

    return () => {
      cancelled = true;
    };
  }, [challengeId, getToken]);
}
