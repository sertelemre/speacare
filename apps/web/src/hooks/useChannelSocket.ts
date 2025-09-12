import { useEffect, useRef } from 'react';

export function useChannelSocket(channelId: number | null) {
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!channelId) {
      return;
    }

    // This won't work directly because the hook can't get the token from Zustand store
    // on the server side or in a way that's clean.
    // A better approach would be to pass the token to the hook or handle auth
    // via cookies, which Channels' AuthMiddlewareStack can read.
    // For now, we assume the connection will work for a logged-in user
    // if the browser has the correct session cookies.
    // The proper way to pass the JWT is via a query parameter or subprotocol,
    // but that requires backend changes. Let's proceed with cookies for now.

    const socket = new WebSocket(
      `ws://${window.location.host.replace(':3000', ':8000')}/ws/channel/${channelId}/`
    );

    socket.onopen = () => {
      console.log(`WebSocket connected to channel ${channelId}`);
      ws.current = socket;
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('Received message:', data);
      // Here, we would update the UI state with the new message
    };

    socket.onclose = () => {
      console.log(`WebSocket disconnected from channel ${channelId}`);
      ws.current = null;
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    // Cleanup on component unmount
    return () => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.close();
      }
    };
  }, [channelId]);

  // Function to send messages (if needed later)
  const sendMessage = (message: any) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    }
  };

  return { sendMessage };
}
