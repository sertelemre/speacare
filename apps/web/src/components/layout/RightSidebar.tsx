"use client";

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useDocumentStore } from '@/store/documentStore';
import api from '@/lib/api';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

// Mock channel ID for now
const CHANNEL_ID = 1;

const fetchDocuments = async (channelId: number) => {
    // This endpoint doesn't exist yet, we'll need to add it.
    // For now, we'll assume it exists and will return an empty array.
    try {
        const { data } = await api.get(`/api/channels/${channelId}/documents/`);
        return data;
    } catch (e) {
        console.warn("Failed to fetch documents, endpoint might not exist yet.");
        return [];
    }
};

function DocumentList() {
    const { documents, setDocuments } = useDocumentStore();

    const { data: initialDocs, isLoading } = useQuery({
        queryKey: ['documents', CHANNEL_ID],
        queryFn: () => fetchDocuments(CHANNEL_ID),
        enabled: !!CHANNEL_ID,
    });

    React.useEffect(() => {
        if (initialDocs) {
            setDocuments(initialDocs);
        }
    }, [initialDocs, setDocuments]);

    return (
        <div className="mt-4 space-y-3">
            {isLoading && <p className="text-sm text-gray-500">Loading...</p>}
            {documents.map(doc => (
                <div key={doc.id} className="rounded-lg border border-gray-200 bg-white p-3 dark:border-gray-700 dark:bg-gray-800">
                    <h3 className="font-semibold">{doc.title}</h3>
                    <p className="mt-1 text-xs text-gray-500">Type: {doc.doc_type}</p>
                </div>
            ))}
            {!isLoading && documents.length === 0 && <p className="text-sm text-gray-500">No documents yet.</p>}
        </div>
    );
}


export function RightSidebar() {
  return (
    <aside className="w-80 flex-shrink-0 border-l border-gray-200 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-900">
      <Tabs defaultValue="notes" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="notes">Notes</TabsTrigger>
          <TabsTrigger value="documents">Documents</TabsTrigger>
        </TabsList>
        <TabsContent value="notes">
            <div className="mt-4">
                <div className="rounded-lg border border-gray-200 bg-white p-3 dark:border-gray-700 dark:bg-gray-800">
                <h3 className="font-semibold">Meeting Summary</h3>
                <ul className="mt-2 list-disc space-y-1 pl-4 text-sm">
                    <li>Decision: Proceed with A/B test.</li>
                    <li>Action: PM to define test segments.</li>
                    <li>Risk: Potential churn from enterprise clients.</li>
                </ul>
                </div>
            </div>
        </TabsContent>
        <TabsContent value="documents">
            <DocumentList />
        </TabsContent>
      </Tabs>
    </aside>
  );
}
