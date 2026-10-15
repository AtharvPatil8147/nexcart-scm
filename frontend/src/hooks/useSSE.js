/**
 * NexCart — useSSE Hook
 * Custom React hook for Server-Sent Events.
 * Connects to SSE endpoint, parses JSON, auto-reconnects on disconnect.
 */

import { useState, useEffect, useRef, useCallback } from 'react';

export default function useSSE(url) {
  const [data, setData] = useState(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState(null);
  const eventSourceRef = useRef(null);
  const reconnectTimerRef = useRef(null);

  const connect = useCallback(() => {
    if (!url) return;

    // Clean up existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    try {
      const es = new EventSource(url);
      eventSourceRef.current = es;

      es.onopen = () => {
        setConnected(true);
        setError(null);
      };

      es.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          setData(parsed);
        } catch {
          // If not JSON, store raw data
          setData(event.data);
        }
      };

      es.onerror = () => {
        setConnected(false);
        setError('SSE connection lost');
        es.close();

        // Auto-reconnect after 3 seconds
        reconnectTimerRef.current = setTimeout(() => {
          connect();
        }, 3000);
      };
    } catch (err) {
      setError(err.message);
      setConnected(false);
    }
  }, [url]);

  useEffect(() => {
    connect();

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
    };
  }, [connect]);

  return { data, connected, error };
}

// ✓ useSSE.js complete
