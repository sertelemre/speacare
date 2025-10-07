import { useEffect, useRef } from 'react';
import { useMessageStore } from '@/store/messageStore';
import { useDocumentStore } from '@/store/documentStore';
import { useChannelControlStore } from '@/store/channelControlStore';
import { toast } from 'sonner';

export function useChannelSocket(channelId: number | null) {
  const ws = useRef<WebSocket | null>(null);
  const { addMessage, setMessages, addThinkingBot, removeThinkingBot } = useMessageStore();
  const { addDocument } = useDocumentStore();
  const { setChannelActive } = useChannelControlStore();

  useEffect(() => {
    if (!channelId) {
      return;
    }

    // The WebSocket URL needs to include the protocol.
    // For local dev, it's 'ws'. In production, it would be 'wss'.
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    // Direct connection to Daphne server on port 8002
    const socket = new WebSocket(
      `${protocol}://localhost:8002/ws/channel/${channelId}/`
    );

    socket.onopen = () => {
      console.log(`WebSocket connected to channel ${channelId}`);
      ws.current = socket;
    };

    socket.onmessage = (event) => {
      const eventData = JSON.parse(event.data);
      console.log('Received WebSocket event:', eventData);

      if (eventData.type === 'message.new' && eventData.message) {
        // Instant mesaj ekleme - delay yok
        console.log('Adding new message to store:', eventData.message);
        console.log('Message ID:', eventData.message.id);
        console.log('Message content:', eventData.message.content_md);
        addMessage(eventData.message);
        console.log('Message added to store successfully');
      } else if (eventData.type === 'doc.new' && eventData.document) {
        addDocument(eventData.document);
      } else if (eventData.type === 'bots_stopped') {
        setChannelActive(channelId, false);
        toast.info('Bot conversations stopped');
      } else if (eventData.type === 'bots_started') {
        setChannelActive(channelId, true);
        toast.info('Bot conversations started');
      } else if (eventData.type === 'messages_cleared') {
        setMessages([]);
        toast.info(eventData.message || 'Chat history cleared');
      } else if (eventData.type === 'bot_thinking') {
        addThinkingBot(eventData.bot_name);
      } else if (eventData.type === 'bot_finished_thinking') {
        removeThinkingBot(eventData.bot_name);
      }
    };

    socket.onclose = () => {
      console.log(`WebSocket disconnected from channel ${channelId}`);
      ws.current = null;
    };

    socket.onerror = (error) => {
      // Silently handle WebSocket errors - WebSocket routing is not configured yet
      console.log(`WebSocket connection failed for channel ${channelId} (this is expected)`);
    };

    // Cleanup on component unmount
    return () => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.close();
      }
    };
  }, [channelId, addDocument, addMessage, setMessages, addThinkingBot, removeThinkingBot, setChannelActive]);

  // Function to send messages (if needed later)
  const sendMessage = (message: unknown) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    }
  };

  return { sendMessage };
}
