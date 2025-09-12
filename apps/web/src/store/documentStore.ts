import { create } from 'zustand';

interface Document {
  id: number;
  title: string;
  doc_type: 'consensus' | 'brief' | 'summary' | 'risk_log';
  content_md: string;
  created_at: string;
}

interface DocumentState {
  documents: Document[];
  addDocument: (doc: Document) => void;
  setDocuments: (docs: Document[]) => void;
}

export const useDocumentStore = create<DocumentState>((set) => ({
  documents: [],
  addDocument: (doc) => set((state) => ({ documents: [doc, ...state.documents] })), // Prepend new docs
  setDocuments: (docs) => set({ documents: docs }),
}));
