import { useEffect, useRef } from 'react';
import { useMessageStore } from '@/store/messageStore';
import { useDocumentStore } from '@/store/documentStore';

export function useChannelSocket(channelId: number | null) {
  const ws = useRef<WebSocket | null>(null);
  const { addMessage } = useMessageStore();
  const { addDocument } = useDocumentStore();

  useEffect(() => {
    if (!channelId) {
      return;
    }

    // The WebSocket URL needs to include the protocol.
    // For local dev, it's 'ws'. In production, it would be 'wss'.
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const host = window.location.host.replace(':3000', ':8000'); // Dev environment specific
    const socket = new WebSocket(
      `${protocol}://${host}/ws/channel/${channelId}/`
    );

    socket.onopen = () => {
      console.log(`WebSocket connected to channel ${channelId}`);
      ws.current = socket;
    };

    socket.onmessage = (event) => {
      const eventData = JSON.parse(event.data);
      console.log('Received WebSocket event:', eventData);

      if (eventData.type === 'message.new' && eventData.message) {
        addMessage(eventData.message);
      } else if (eventData.type === 'doc.new' && eventData.document) {
        addDocument(eventData.document);
      }
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
